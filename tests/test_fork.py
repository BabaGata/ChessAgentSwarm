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

from chesscoach.tactics import _is_fork


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
