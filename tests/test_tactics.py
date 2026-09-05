"""Tactical motif detectors.

Design: docs/notes/capacity.agents.s1-tactical-gaps.md

Every detector has at least one negative case, because the recorded failure mode
is **over-firing**: prior art documented a skewer detector firing 10-18x too
often, and E02 found plausible-looking detector code fires far too readily on
real boards. A detector that only has positive tests has not been tested.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.tactics import Motif, detect_motifs


def motifs(fen: str, uci: str) -> frozenset[str]:
    return detect_motifs(chess.Board(fen), chess.Move.from_uci(uci))


class TestFork:
    # The white king is off the e-file in these: with it on e1 the knight is
    # pinned by the e8 rook and cannot legally move at all.
    def test_knight_forking_king_and_rook(self):
        # Ne4-f6+ hits the king on g8 and the rook on e8.
        assert Motif.FORK in motifs("4r1k1/8/8/8/4N3/8/8/6K1 w - - 0 1", "e4f6")

    def test_not_a_fork_when_only_one_piece_is_attacked(self):
        assert Motif.FORK not in motifs("4r1k1/8/8/8/4N3/8/8/6K1 w - - 0 1", "e4d6")

    def test_not_a_fork_when_the_forking_piece_can_simply_be_taken(self):
        # Same fork, but a g7 pawn captures the knight on f6.
        assert Motif.FORK not in motifs("4r1k1/6p1/8/8/4N3/8/8/6K1 w - - 0 1", "e4f6")

    def test_ignores_targets_not_worth_winning(self):
        # A rook attacking two pawns, both defended, is not a fork.
        assert Motif.FORK not in motifs("4k3/8/8/8/8/1p1p4/2P1P3/R3K3 w - - 0 1", "a1a3")


class TestPin:
    def test_rook_pinning_a_knight_to_the_king(self):
        assert Motif.PIN in motifs("4k3/8/8/4n3/8/8/8/R5K1 w - - 0 1", "a1e1")

    def test_not_a_pin_when_a_pawn_stands_between(self):
        # The e7 pawn shields the king, so the knight is not pinned to anything.
        assert Motif.PIN not in motifs("4k3/4p3/8/4n3/8/8/8/R5K1 w - - 0 1", "a1e1")

    def test_not_a_pin_when_the_piece_behind_is_worth_less(self):
        # Pawn in front, knight behind: nothing worth pinning against.
        assert Motif.PIN not in motifs("4k3/8/8/4n3/8/4p3/8/R5K1 w - - 0 1", "a1e1")


class TestSkewer:
    # These two positions were rebuilt on 2026-08-23. The originals put the rook
    # on a1 attacking a piece on a5 with another behind it on a8 -- and in that
    # geometry the rear piece defends the front one, so Black simply answers
    # ...Qxa1 and wins a rook. They were legal, they exercised the geometry, and
    # they were not tactics. Once the detectors began asking whether the
    # attacking piece survives, both stopped firing, correctly. See L-044: a
    # fixture built to exercise a code path is not the same as a fixture that is
    # true. Diagonal versions with the attacker defended replace them.

    def test_bishop_skewering_a_queen_in_front_of_a_rook(self):
        # Bb2 hits Qf6 with Rh8 behind it; Rb1 defends b2, so ...Qxb2 Rxb2 is
        # queen for bishop and the skewer stands.
        assert Motif.SKEWER in motifs("k6r/8/5q2/8/8/8/6K1/1RB5 w - - 0 1", "c1b2")

    def test_the_reverse_arrangement_is_a_pin_not_a_skewer(self):
        # Rook in front, queen behind -- the less valuable piece is attacked
        # first. The rook on f6 does not attack b2, so the bishop is safe.
        found = motifs("k6q/8/5r2/8/8/8/6K1/2B5 w - - 0 1", "c1b2")

        assert Motif.SKEWER not in found
        assert Motif.PIN in found

    def test_a_pawn_behind_a_piece_is_not_a_skewer(self):
        # Geometrically lined up, but there is nothing behind worth winning.
        assert Motif.SKEWER not in motifs("4k3/8/p7/8/n7/8/8/3RK3 w - - 0 1", "d1a1")


class TestDiscoveredAttack:
    def test_moving_a_piece_off_the_line_reveals_an_attack(self):
        # Na3 steps aside and the a1 rook sees the queen on a8.
        assert Motif.DISCOVERED_ATTACK in motifs("q3k3/8/8/8/8/N7/8/R3K3 w - - 0 1", "a3b5")

    def test_not_discovered_when_nothing_is_revealed(self):
        # Same knight move, but the a-file holds no enemy piece.
        assert Motif.DISCOVERED_ATTACK not in motifs("4k3/8/8/8/8/N7/8/R3K3 w - - 0 1", "a3b5")


class TestHangingPiece:
    def test_capturing_an_undefended_piece(self):
        assert Motif.HANGING_PIECE in motifs("4k3/8/8/3n4/8/8/8/3RK3 w - - 0 1", "d1d5")

    def test_not_hanging_when_the_capture_can_be_answered(self):
        # The e6 pawn recaptures on d5.
        assert Motif.HANGING_PIECE not in motifs("4k3/8/4p3/3n4/8/8/8/3RK3 w - - 0 1", "d1d5")

    def test_a_quiet_move_is_never_a_hanging_piece_capture(self):
        assert Motif.HANGING_PIECE not in motifs("4k3/8/8/3n4/8/8/8/3RK3 w - - 0 1", "d1d4")

    def test_taking_a_loose_pawn_is_not_a_hanging_piece(self):
        # Measured: free pawn grabs were the bulk of this motif's firings on
        # real games, and "you hang pieces" is not a claim about pawns.
        assert Motif.HANGING_PIECE not in motifs("4k3/8/8/3p4/8/8/8/3RK3 w - - 0 1", "d1d5")


class TestBackRankMate:
    def test_rook_mating_a_king_boxed_in_by_its_own_pawns(self):
        assert Motif.BACK_RANK_MATE in motifs("6k1/5ppp/8/8/8/8/8/4R1K1 w - - 0 1", "e1e8")

    def test_not_mate_when_the_king_has_an_escape_square(self):
        # The h-pawn has moved, so Kh7 is available.
        assert Motif.BACK_RANK_MATE not in motifs("6k1/5pp1/7p/8/8/8/8/4R1K1 w - - 0 1", "e1e8")


class TestRemovingTheDefender:
    def test_capturing_the_piece_that_defended_another(self):
        """Rxc6 removes the bishop defending d5, and the knight cannot run.

        The king stands on d8, so Rd1 pins the knight: every legal reply leaves
        it winnable. **The old position had the king on e8**, where the knight
        simply hopped away -- so the capture won a free bishop but removed no
        defender, and the test was asserting the defect (E86 D-3).
        """
        assert Motif.REMOVING_THE_DEFENDER in motifs(
            "3k4/8/2b5/3n4/8/8/8/2RRK3 w - - 0 1", "c1c6"
        )

    def test_not_removal_when_the_loosened_piece_can_simply_run(self):
        # The same position with the king on e8: the knight is unpinned and
        # steps away, so nothing is won on the following move.
        assert Motif.REMOVING_THE_DEFENDER not in motifs(
            "4k3/8/2b5/3n4/8/8/8/2RRK3 w - - 0 1", "c1c6"
        )

    def test_not_removal_when_the_captured_piece_defended_nothing(self):
        assert Motif.REMOVING_THE_DEFENDER not in motifs(
            "4k3/8/2b5/8/8/8/8/2RRK3 w - - 0 1", "c1c6"
        )


class TestTrappedPiece:
    def test_attacking_a_piece_whose_every_escape_is_covered(self):
        # Bd4 hits the h8 knight; its only squares, f7 and g6, are covered by
        # the e6 and h5 pawns.
        assert Motif.TRAPPED_PIECE in motifs("k6n/8/4P3/7P/8/4B3/8/4K3 w - - 0 1", "e3d4")

    def test_not_trapped_when_one_escape_is_free(self):
        # Without the h5 pawn the knight simply hops to g6.
        assert Motif.TRAPPED_PIECE not in motifs("k6n/8/4P3/8/8/4B3/8/4K3 w - - 0 1", "e3d4")

    def test_pawns_are_not_reported_as_trapped(self):
        assert Motif.TRAPPED_PIECE not in motifs("4k3/1p6/8/8/8/8/8/3RK3 w - - 0 1", "d1b1")

    def test_a_piece_with_no_moves_at_all_is_not_trapped_by_us(self):
        # Measured: an undeveloped rook boxed in by its own knight and pawn was
        # reported as trapped, because "every escape is covered" is vacuously
        # true when there are none. Trapped means it had somewhere to go and we
        # took it away. Here Be5 attacks a1, but that rook was never going
        # anywhere -- its own a2 pawn and b1 knight see to that.
        assert Motif.TRAPPED_PIECE not in motifs(
            "4k3/8/5b2/8/8/8/P7/RN5K b - - 0 1", "f6e5"
        )


class TestDetectMotifs:
    def test_returns_a_frozen_set(self):
        assert isinstance(motifs("4k3/8/8/3n4/8/8/8/3RK3 w - - 0 1", "d1d5"), frozenset)

    def test_a_move_can_carry_several_motifs(self):
        found = motifs("4k3/8/8/4n3/8/8/8/R5K1 w - - 0 1", "a1e1")

        assert Motif.PIN in found

    def test_a_dull_move_carries_none(self):
        assert motifs("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1a2") == frozenset()

    def test_rejects_an_illegal_move(self):
        with pytest.raises(ValueError):
            motifs("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1b3")

    def test_does_not_mutate_the_board_it_is_given(self):
        board = chess.Board("4k3/8/8/3n4/8/8/8/3RK3 w - - 0 1")
        before = board.fen()

        detect_motifs(board, chess.Move.from_uci("d1d5"))

        assert board.fen() == before


class TestMotifNames:
    def test_names_match_the_lichess_theme_vocabulary(self):
        # Sharing the vocabulary is what makes external validation against the
        # CC0 puzzle database possible, and prescription possible later.
        assert Motif.FORK == "fork"
        assert Motif.DISCOVERED_ATTACK == "discoveredAttack"
        assert Motif.REMOVING_THE_DEFENDER == "capturingDefender"
        assert Motif.BACK_RANK_MATE == "backRankMate"
