"""A fork is two NEW attacks by the moved piece that definitely win material.

Design: docs/notes/design.detectors-name-consequences.md § 3

The author's definition, after marking the old detector wrong:

    "Forks are moves that occur when at least 2 pieces were newly (so they
    weren't attacked before) attacked by one single piece after moving that
    piece and the result is definite loss of material."

**The negative cases carry this file.** Building the positives by hand kept
producing positions that are not forks at all — a rook attacked alongside a
bishop simply steps to a square that defends it, and nothing is won. Searched
over random positions, only **3 of 1,014** knight double-attacks on a rook and a
bishop are genuine forks. The old detector counted all 1,014.

Every position below was verified against the rule rather than assumed.
"""

from __future__ import annotations

import chess

from chesscoach.tactics import Motif, _is_fork, detect_motifs


def forks(fen: str, san: str) -> bool:
    """Did playing `san` in `fen` fork anything?"""
    board = chess.Board(fen)
    move = board.parse_san(san)
    after = board.copy(stack=False)
    after.push(move)
    return _is_fork(board, after, move, board.turn)


class TestTheAuthorsExamples:
    def test_a_pawn_forking_a_knight_and_a_bishop(self):
        # "a pawn attacking a knight and a bishop that are separated by 1 square
        # in between after moving that pawn"
        #
        # The pawn is defended by c4: an undefended pawn walking between two
        # pieces is simply captured, and is not a fork.
        assert forks("4k3/8/2n1b3/8/2PP4/8/8/4K3 w - - 0 1", "d5")

    def test_a_knight_forking_a_rook_and_a_bishop(self):
        # "attacking by knight a rook and a bishop but bishop is undefended and
        # can not be defended by the rock, so after moving a rock the bishop
        # will fall or after moving a bishop the rook will fall"
        #
        # Nc4 hits b6 and d2, and neither piece can cover the other.
        assert forks("8/8/1b4K1/4N3/8/8/3r1k2/8 w - - 0 1", "Nc4")

    def test_the_family_fork_counts_even_though_a_king_cannot_be_won(self):
        # The commonest fork there is. A king is a target without being a prize,
        # so `wins_material` says nothing about it -- excluding it would blind
        # the detector to every fork that comes with check.
        assert forks("r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1", "Nc7+")


class TestTheCaseTheOldDetectorGotWrong:
    def test_a_double_attack_the_defender_answers_is_not_a_fork(self):
        # Queen and rook both newly attacked, and Black has six replies that
        # save both -- Qe5, Qe6, Qe4 all defend the rook while the queen
        # escapes. Attacking two pieces is not winning either of them.
        assert not forks("4k3/8/8/3q1r2/8/8/6N1/4K3 w - - 0 1", "Ne3")

    def test_a_defended_target_is_only_an_exchange(self):
        # The author's discriminating case: "If bishop was defended the rook
        # could be moved and there would occur only exchange of the pieces, not
        # material loss."
        assert not forks("4k3/8/3r4/8/3p4/N3b3/8/4K3 w - - 0 1", "Nc4")

    def test_a_rook_that_can_step_aside_and_still_defend_is_not_forked(self):
        # Rd3 and Re6 both escape AND cover the bishop. The old detector called
        # this a fork; nothing is won.
        assert not forks("4k3/8/3r4/8/8/N3b3/8/4K3 w - - 0 1", "Nc4")


class TestNewlyAttacked:
    def test_a_quiet_move_attacking_nothing_new_is_not_a_fork(self):
        assert not forks("4k3/8/2n1b3/8/8/8/3P4/4K3 w - - 0 1", "d3")

    def test_newly_means_newly_by_the_piece_that_moved(self):
        """The author, correcting this test's earlier reading:

        > *"the 2 newly attacked pieces can be attacked previously by some other
        > piece, but they both have to be attacked by the piece that was moved
        > ... the piece that was last moved did not create a fork, it newly
        > attacked just one piece."*

        Bb1 already attacks f5, and the knight attacks **both** d5 and f5 from
        e3 having attacked neither from g2. It forks them. That another piece
        also eyes one of the victims is not the knight's business.
        """
        assert forks("4k3/8/8/3r1b2/8/8/6N1/1B2K3 w - - 0 1", "Ne3")

    def test_a_move_that_newly_attacks_only_one_piece_is_not_a_fork(self):
        # The case the rule exists for: the rook slides along a rank it already
        # controlled, so it has newly attacked nothing at all.
        assert not forks("4r1k1/8/8/8/8/8/8/R5K1 w - - 0 1", "Ra2")

    def test_a_fork_survives_a_friendly_piece_sharing_a_victim(self):
        # E86 D-1. Ng4-f6+ hits the king on g8 and the rook on e8. Adding a
        # friendly rook on e1, which also attacks e8, must not stop it being a
        # fork -- a second attacker makes a fork stronger, not absent.
        assert forks("4r1k1/8/8/8/6N1/8/8/4R1K1 w - - 0 1", "Nf6+")
        assert forks("4r1k1/8/8/8/6N1/8/8/6K1 w - - 0 1", "Nf6+")


class TestTheAttackerMustSurvive:
    def test_a_forking_piece_that_is_simply_captured_wins_nothing(self):
        # b5 covers c4, so the knight is taken and there is no fork to speak of.
        assert not forks("4k3/8/3r4/1p6/8/N3b3/8/4K3 w - - 0 1", "Nc4")


class TestTheGameMustContinue:
    def test_checkmate_is_not_a_fork(self):
        # Q8c3# from a real game, which the detector counted as a fork because
        # "no reply saves the targets" is vacuously true when there is no reply.
        # Mate wins the game, not material. 104 of 1,779 corpus hits were this.
        assert not forks("2Q5/8/8/p7/P7/k7/2Q4K/8 w - - 5 60", "Q8c3#")

        # No stalemate fixture: a stalemating move leaves the king un-attacked,
        # so it never reaches two targets and would pass for the wrong reason.


class TestTheAuthorsLineRule:
    """Two pieces on one line through the attacker is a skewer, not a fork.

    The author, rejecting six of the ten marked fork rows for one reason:

    > *"This is a skewer, fork is only when one of the involved pieces is not
    > aligned on the same line/diagonal."*

    > *"Just a note, forks are usually done by knights, pawns and sometimes
    > queens, skewers are usually done by rooks, bishops and queens."*

    Every rejected row had the same geometry -- a **slider** hitting two pieces
    that lie on **one line through it**, usually in opposite directions, and
    usually with one of them the king. `Rd1+` hitting `Bb1` and `Kg1` is the
    shape: the check drives the king off the rank and the bishop falls.

    This is **narrower than the Lichess definition** the vocabulary is drawn
    from -- *"a move where a piece attacks two or more opposing pieces
    simultaneously"*, with no geometry in it -- and the author chose their rule
    over it knowing that ([[decisions.0019-fork-and-skewer-by-geometry]]). The
    material test does not change; only which name the position gets.
    """

    def motifs(self, fen: str, uci: str) -> frozenset[str]:
        return detect_motifs(chess.Board(fen), chess.Move.from_uci(uci))

    def test_a_rook_hitting_both_ways_along_a_rank_is_a_skewer(self):
        # Rd1+: the black rook checks Kg1 along the first rank and hits Bb1 the
        # other way down it. The author's `lichess.org/SuvK6tPc#72`.
        found = self.motifs("3r2k1/8/8/8/8/8/6PP/1B4K1 b - - 0 1", "d8d1")

        assert Motif.SKEWER in found
        assert Motif.FORK not in found

    def test_a_bishop_hitting_both_ways_along_a_diagonal_is_a_skewer(self):
        # Bg5+ checking Kc1 down the diagonal and hitting Qh6 up it, which is
        # `lichess.org/vmYdIpZ1#47`.
        found = self.motifs("k2b4/5n2/7Q/8/8/8/8/2K5 b - - 0 1", "d8g5")

        assert Motif.SKEWER in found
        assert Motif.FORK not in found

    def test_a_knight_is_still_a_fork(self):
        # Nc2+ hits Ke1 and Ra1. A knight can never attack along a line from
        # its own square, so the
        # rule cannot reach it -- which is the author's *"forks are usually done
        # by knights"* falling out rather than being written in.
        found = self.motifs("4k3/8/8/8/1n6/8/8/R3K3 b - - 0 1", "b4c2")

        assert Motif.FORK in found

    def test_a_queen_on_two_different_lines_is_still_a_fork(self):
        # Qe4+ hits Kh1 down one diagonal and Nb1 down the other: two lines,
        # so the pieces are not aligned with each other. The author accepted
        # `Qxh3+ -- target Kh1, target Pf3` for exactly this reason
        # (`lichess.org/IGCmSgiy#29`).
        found = self.motifs("4k3/4q3/8/8/8/8/8/1N5K b - - 0 1", "e7e4")

        assert Motif.FORK in found

    def test_a_double_attack_is_never_named_neither(self):
        """The property the split has to have: the two detectors cannot both
        refuse the same move.

        `_fork_on_one_line` is one predicate read from both sides, so they
        cannot both *claim* a move. The other half is not structural -- the two
        test the attacker's survival differently, `_lands_safely` here and
        `wins_material` there -- so a position could in principle leave `fork`
        under the line rule and fail the stricter test on the way in, and be
        named nothing. Swept over 60 games it never happens, which is why one
        guard serves both; this holds that measurement in place.

        It is a **weak test and says so**: it has never seen a failure, so it
        guards the invariant rather than reproducing a bug.
        """
        import chess.pgn
        from pathlib import Path

        from chesscoach.tactics import (
            _all_on_one_line,
            _loses_material_whatever_the_defender_does,
            _newly_attacked,
        )

        games = Path("data/raw/corpus-blitz").glob("*.pgn")
        source = next(iter(sorted(games)), None)
        if source is None:
            import pytest

            pytest.skip("no corpus available")

        with open(source, encoding="utf-8", errors="ignore") as handle:
            game = chess.pgn.read_game(handle)
        board = game.board()
        checked = orphaned = 0
        for played in game.mainline_moves():
            for move in board.legal_moves:
                after = board.copy(stack=False)
                after.push(move)
                targets = _newly_attacked(board, after, move, board.turn)
                if len(targets) < 2 or not _all_on_one_line(
                    after, move.to_square, targets
                ):
                    continue
                if not _loses_material_whatever_the_defender_does(
                    after, targets, board.turn
                ):
                    continue
                checked += 1
                found = {str(m) for m in detect_motifs(board, move)}
                orphaned += "fork" not in found and "skewer" not in found
            board.push(played)

        assert orphaned == 0, (
            f"{orphaned} of {checked} one-line double attacks are named neither "
            "-- the fork and skewer guards disagree about the same position"
        )
