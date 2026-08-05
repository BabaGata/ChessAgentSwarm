"""Pawn-structure weakness detectors.

Design: docs/notes/capacity.agents.s5-pawn-structure.md

`isolated` and `backward` are ported from E02, where they were hand-verified on
real games; these tests pin the definitions rather than re-establish them.
`doubled` is new and has only this.

The negative cases matter more than the positive ones — a detector that fires on
everything is exactly the E02 failure (isolated pawns in 96 % of games), and the
conditions casual definitions omit are what separate a real backward pawn from a
merely rearmost one.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.structure import (
    BACKWARD,
    DOUBLED,
    ISOLATED,
    conceded,
    count_backward,
    count_doubled,
    count_isolated,
    weakness_counts,
)


def board(fen: str) -> chess.Board:
    return chess.Board(fen)


class TestIsolated:
    def test_a_lone_pawn_with_no_neighbours_is_isolated(self):
        # d4 alone on its file group. a2 and h2 are isolated too — no b- or
        # g-pawn — so the answer is three, not one. Kept as written because
        # getting this wrong is the easy mistake: the rook pawns look "normal".
        assert count_isolated(board("4k3/8/8/8/3P4/8/P6P/4K3 w - - 0 1"), chess.WHITE) == 3

    def test_a_rook_pawn_is_isolated_when_its_only_neighbour_file_is_empty(self):
        assert count_isolated(board("4k3/8/8/8/8/8/P7/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_a_rook_pawn_with_a_neighbour_is_not(self):
        assert count_isolated(board("4k3/8/8/8/8/8/PP6/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_a_pawn_with_an_adjacent_file_neighbour_is_not(self):
        assert count_isolated(board("4k3/8/8/8/3P4/4P3/8/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_a_neighbour_on_any_rank_counts(self):
        # Support is about the file, not about being alongside.
        assert count_isolated(board("4k3/8/8/8/3P4/8/4P3/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_enemy_pawns_do_not_support(self):
        assert count_isolated(board("4k3/4p3/8/8/3P4/8/8/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_the_starting_position_has_none(self):
        assert count_isolated(chess.Board(), chess.WHITE) == 0


class TestBackward:
    def test_the_full_definition(self):
        # White b2 pawn: neighbours a3 and c3 both advanced past it, undefended,
        # and b3 is covered by the black a4 pawn.
        position = board("4k3/8/8/8/p7/P1P5/1P6/4K3 w - - 0 1")

        assert count_backward(position, chess.WHITE) == 1

    def test_a_pawn_that_can_advance_safely_is_not_backward(self):
        # Same shape, but no enemy pawn covers b3 — it just walks forward.
        position = board("4k3/8/8/8/8/P1P5/1P6/4K3 w - - 0 1")

        assert count_backward(position, chess.WHITE) == 0

    def test_an_isolated_pawn_is_not_backward(self):
        # No neighbours at all: a different weakness, and counting it as both
        # would double-report one problem.
        assert count_backward(board("4k3/8/8/8/p7/8/1P6/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_a_defended_pawn_is_not_backward(self):
        # a2 defends b3... here c3 and a2: b2 is defended by a1? Use a3 defending b4.
        position = board("4k3/8/8/8/1P6/P1P5/8/4K3 w - - 0 1")

        assert count_backward(position, chess.WHITE) == 0

    def test_a_blocked_pawn_is_a_different_problem(self):
        # b3 occupied by a piece rather than covered by a pawn.
        position = board("4k3/8/8/8/8/PnP5/1P6/4K3 w - - 0 1")

        assert count_backward(position, chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_backward(chess.Board(), chess.WHITE) == 0


class TestDoubled:
    def test_two_pawns_on_a_file_is_one_surplus(self):
        assert count_doubled(board("4k3/8/8/8/3P4/3P4/8/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_three_on_a_file_is_two_surplus(self):
        # A tripled pawn reads as worse than a doubled one, which is how it plays.
        assert count_doubled(board("4k3/8/8/3P4/3P4/3P4/8/4K3 w - - 0 1"), chess.WHITE) == 2

    def test_pawns_on_different_files_are_not_doubled(self):
        assert count_doubled(board("4k3/8/8/8/3P4/4P3/8/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_doubled(chess.Board(), chess.WHITE) == 0

    def test_it_counts_only_the_asked_colour(self):
        position = board("4k3/3p4/3p4/8/8/8/8/4K3 w - - 0 1")

        assert count_doubled(position, chess.BLACK) == 1
        assert count_doubled(position, chess.WHITE) == 0


class TestConceding:
    def test_creating_a_doubled_pawn_is_a_concession(self):
        before = board("4k3/8/8/8/8/3P4/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/3P4/3P4/8/4K3 b - - 0 1")

        assert DOUBLED in conceded(before, after, chess.WHITE)

    def test_a_weakness_that_was_already_there_is_not_conceded(self):
        # E02's finding: presence is 96% of games, so only creation counts.
        position = board("4k3/8/8/8/3P4/8/P6P/4K3 w - - 0 1")

        assert conceded(position, position, chess.WHITE) == frozenset()

    def test_an_isolated_pawn_that_merely_advances_is_not_a_new_concession(self):
        # The reason counts are compared rather than squares: d4 -> d5 is the
        # same weakness on a different square.
        before = board("4k3/8/8/8/3P4/8/P6P/4K3 w - - 0 1")
        after = board("4k3/8/8/3P4/8/8/P6P/4K3 b - - 0 1")

        assert ISOLATED not in conceded(before, after, chess.WHITE)

    def test_the_opponents_weaknesses_are_not_the_players_concession(self):
        before = board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
        after = board("4k3/p1pppppp/8/1p6/8/8/PPPPPPPP/4K3 b - - 0 1")

        assert conceded(before, after, chess.WHITE) == frozenset()

    def test_several_weaknesses_can_be_conceded_at_once(self):
        before = board("4k3/8/8/8/8/8/PP6/4K3 w - - 0 1")
        after = board("4k3/8/8/8/P7/8/P7/4K3 b - - 0 1")

        assert conceded(before, after, chess.WHITE) >= {DOUBLED, ISOLATED}


class TestCounts:
    def test_every_feature_is_reported(self):
        counts = weakness_counts(chess.Board(), chess.WHITE)

        assert set(counts) == {ISOLATED, BACKWARD, DOUBLED}

    @pytest.mark.parametrize("colour", [chess.WHITE, chess.BLACK])
    def test_the_starting_position_is_clean_for_both_sides(self, colour):
        assert weakness_counts(chess.Board(), colour) == {ISOLATED: 0, BACKWARD: 0, DOUBLED: 0}
