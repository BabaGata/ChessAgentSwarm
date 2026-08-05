"""Outpost and seventh-rank detectors, read from the conceding side.

Design: docs/notes/capacity.agents.s6-squares-and-files.md

The condition that matters is **permanence**: a knight a pawn can still evict is
not an outpost, and it is the condition casual definitions omit (E02, L-004).
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.squares import (
    OUTPOST,
    ROOK_SEVENTH,
    allowed,
    can_ever_be_covered,
    count_enemy_outposts,
    count_enemy_rooks_on_seventh,
    counts,
)


def board(fen: str) -> chess.Board:
    return chess.Board(fen)


class TestEnemyOutposts:
    def test_a_pawn_backed_unevictable_knight_counts(self):
        # Black knight on d3 (White's half), backed by a black pawn on e4, and
        # White has no c- or e-pawn left to challenge it.
        position = board("4k3/8/8/8/4p3/3n4/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 1

    def test_a_knight_a_pawn_can_still_evict_does_not(self):
        # Same knight, but White still has a c2 pawn — on the adjacent file and
        # behind the square, so it can advance to challenge. Permanence is the
        # whole difference between an outpost and an annoying knight.
        position = board("4k3/8/8/8/4p3/3n4/2P5/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_an_undefended_knight_is_not_an_outpost(self):
        position = board("4k3/8/8/8/8/3n4/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_a_knight_outside_the_players_half_does_not_count(self):
        # On the 7th rank from White's view it is deep in Black's own camp.
        position = board("4k3/8/3n4/4p3/8/8/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_enemy_outposts(chess.Board(), chess.WHITE) == 0


class TestCoverage:
    def test_a_pawn_behind_the_square_can_still_cover_it(self):
        position = board("4k3/8/8/8/8/3n4/2P5/4K3 w - - 0 1")

        assert can_ever_be_covered(position, chess.D3, chess.WHITE)

    def test_a_pawn_that_has_gone_past_cannot_come_back(self):
        position = board("4k3/8/2P5/8/8/3n4/8/4K3 w - - 0 1")

        assert not can_ever_be_covered(position, chess.D3, chess.WHITE)

    def test_a_pawn_on_the_same_file_does_not_cover_it(self):
        position = board("4k3/8/8/8/8/3n4/3P4/4K3 w - - 0 1")

        assert not can_ever_be_covered(position, chess.D3, chess.WHITE)


class TestRookOnTheSeventh:
    def test_an_enemy_rook_on_the_players_second_rank(self):
        assert count_enemy_rooks_on_seventh(board("4k3/8/8/8/8/8/1r6/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_both_rooks_count(self):
        position = board("4k3/8/8/8/8/8/1r3r2/4K3 w - - 0 1")

        assert count_enemy_rooks_on_seventh(position, chess.WHITE) == 2

    def test_it_is_measured_from_the_players_own_side(self):
        # A white rook on the 7th is Black's problem, not White's.
        position = board("4k3/1R6/8/8/8/8/8/4K3 w - - 0 1")

        assert count_enemy_rooks_on_seventh(position, chess.BLACK) == 1
        assert count_enemy_rooks_on_seventh(position, chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_enemy_rooks_on_seventh(chess.Board(), chess.WHITE) == 0


class TestWhatWasAllowed:
    def test_a_rook_arriving_is_allowed(self):
        before = board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/8/8/1r6/4K3 w - - 0 1")

        assert ROOK_SEVENTH in allowed(before, after, chess.WHITE)

    def test_a_rook_that_was_already_there_is_not_newly_allowed(self):
        position = board("4k3/8/8/8/8/8/1r6/4K3 w - - 0 1")

        assert allowed(position, position, chess.WHITE) == frozenset()

    def test_a_knight_settling_is_allowed(self):
        before = board("4k3/8/8/8/4p3/8/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/4p3/3n4/8/4K3 w - - 0 1")

        assert OUTPOST in allowed(before, after, chess.WHITE)

    def test_the_players_own_gains_are_not_concessions(self):
        before = board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        after = board("4k3/1R6/8/8/8/8/8/4K3 w - - 0 1")

        assert allowed(before, after, chess.WHITE) == frozenset()

    def test_both_can_be_allowed_at_once(self):
        before = board("4k3/8/8/8/4p3/8/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/4p3/3n4/1r6/4K3 w - - 0 1")

        assert allowed(before, after, chess.WHITE) == {OUTPOST, ROOK_SEVENTH}


@pytest.mark.parametrize("colour", [chess.WHITE, chess.BLACK])
def test_counts_report_every_feature(colour):
    assert set(counts(chess.Board(), colour)) == {OUTPOST, ROOK_SEVENTH}
