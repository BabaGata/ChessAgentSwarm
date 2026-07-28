"""Unit tests for the E02 positional detectors.

Constructed positions where the correct answer is not in doubt. These test the
*definitions*; validation against real games (which measures whether the
definitions fire sensibly in practice) is run.py's job.
"""

from __future__ import annotations

import chess
import pytest

from detectors import (
    detect_backward_pawns,
    detect_isolated_pawns,
    detect_open_file_rooks,
    detect_outposts,
)


class TestOutposts:
    def test_detects_pawn_protected_knight_no_enemy_pawns_can_attack(self):
        # Arrange: white knight d5, protected by the e4 pawn; black has no pawns.
        board = chess.Board("4k3/8/8/3N4/4P3/8/8/4K3 w - - 0 1")

        # Act
        found = detect_outposts(board, chess.WHITE)

        # Assert
        assert len(found) == 1
        assert found[0].square_name == "d5"

    def test_rejects_when_an_enemy_pawn_can_still_advance_to_attack(self):
        # Arrange: same, but a black c7 pawn can play c6 hitting d5.
        board = chess.Board("4k3/2p5/8/3N4/4P3/8/8/4K3 w - - 0 1")

        assert detect_outposts(board, chess.WHITE) == []

    def test_rejects_knight_not_defended_by_a_pawn(self):
        # Arrange: knight on d5 with no pawn behind it.
        board = chess.Board("4k3/8/8/3N4/8/8/8/4K3 w - - 0 1")

        assert detect_outposts(board, chess.WHITE) == []

    def test_rejects_knight_on_own_half(self):
        # Arrange: knight on d3 -- protected, unattackable, but not advanced.
        board = chess.Board("4k3/8/8/8/8/3N4/2P5/4K3 w - - 0 1")

        assert detect_outposts(board, chess.WHITE) == []

    def test_detects_black_outpost_with_mirrored_geometry(self):
        # Arrange: black knight d4 protected by the e5 pawn, no white pawns.
        board = chess.Board("4k3/8/8/4p3/3n4/8/8/4K3 w - - 0 1")

        found = detect_outposts(board, chess.BLACK)

        assert len(found) == 1
        assert found[0].square_name == "d4"


class TestIsolatedPawns:
    def test_detects_pawn_with_no_neighbours_on_adjacent_files(self):
        # Arrange: white pawns a2 and d4, nothing on b or c/e.
        board = chess.Board("4k3/8/8/8/3P4/8/P7/4K3 w - - 0 1")

        found = detect_isolated_pawns(board, chess.WHITE)

        assert {f.square_name for f in found} == {"a2", "d4"}

    def test_names_a_d_file_isolani_the_isolated_queens_pawn(self):
        board = chess.Board("4k3/8/8/8/3P4/8/8/4K3 w - - 0 1")

        found = detect_isolated_pawns(board, chess.WHITE)

        assert found[0].detail == "isolated queen's pawn"

    def test_rejects_pawn_with_a_neighbour(self):
        # Arrange: d4 and e3 -- adjacent files, so neither is isolated.
        board = chess.Board("4k3/8/8/8/3P4/4P3/8/4K3 w - - 0 1")

        assert detect_isolated_pawns(board, chess.WHITE) == []


class TestBackwardPawns:
    def test_detects_rearmost_pawn_that_cannot_advance_safely(self):
        # Arrange: white c3 with both neighbours (b4, d4) advanced past it, and
        # a black d5 pawn covering c4 so it cannot advance.
        board = chess.Board("4k3/8/8/3p4/1P1P4/2P5/8/4K3 w - - 0 1")

        found = detect_backward_pawns(board, chess.WHITE)

        assert len(found) == 1
        assert found[0].square_name == "c3"

    def test_rejects_when_the_square_ahead_is_not_covered_by_an_enemy_pawn(self):
        # Arrange: same shape, but the black pawn is on d6 and does not cover c4.
        board = chess.Board("4k3/8/3p4/8/1P1P4/2P5/8/4K3 w - - 0 1")

        assert detect_backward_pawns(board, chess.WHITE) == []

    def test_rejects_isolated_pawn(self):
        # Arrange: c3 with no neighbours at all is isolated, not backward.
        board = chess.Board("4k3/8/8/3p4/8/2P5/8/4K3 w - - 0 1")

        assert detect_backward_pawns(board, chess.WHITE) == []

    def test_rejects_pawn_defended_by_another_pawn(self):
        # Arrange: c3 is defended by b2, so it is supported rather than backward.
        board = chess.Board("4k3/8/8/3p4/3P4/2P5/1P6/4K3 w - - 0 1")

        assert detect_backward_pawns(board, chess.WHITE) == []


class TestOpenFileRooks:
    def test_detects_rook_on_a_fully_open_file(self):
        board = chess.Board("4k3/8/8/8/8/8/8/4RK2 w - - 0 1")

        found = detect_open_file_rooks(board, chess.WHITE)

        assert len(found) == 1
        assert "open file" in found[0].name
        assert "semi" not in found[0].name

    def test_calls_it_semi_open_when_only_the_enemy_has_a_pawn_there(self):
        board = chess.Board("4k3/4p3/8/8/8/8/8/4RK2 w - - 0 1")

        found = detect_open_file_rooks(board, chess.WHITE)

        assert len(found) == 1
        assert found[0].name == "rook on semi-open file"

    def test_rejects_rook_blocked_by_its_own_pawn(self):
        board = chess.Board("4k3/8/8/8/8/8/4P3/4RK2 w - - 0 1")

        assert detect_open_file_rooks(board, chess.WHITE) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
