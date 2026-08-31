"""Doubled pawns count when they are close and when they last.

Design: docs/notes/design.detectors-name-consequences.md § 5

    "Doubled pawns are detected for pretty much any capture no matter how far
    away the pawns are. This should be counted only if they are directly one in
    front of the other or if there is only 1 square in between... Also the
    double pawns should be taken in the account if they are able to last for
    more then 3 moves, otherwise, they are in that state just until the end of
    exchange."

Two conditions, and the second needed the detector to see a span of positions
rather than one.
"""

from __future__ import annotations

import chess

from chesscoach.structure import (
    DOUBLED_PERSISTS_MOVES,
    MAX_DOUBLED_GAP,
    count_doubled,
    doubled_files,
    persistent_doubled,
)


def board(fen: str) -> chess.Board:
    return chess.Board(fen)


class TestDistance:
    def test_pawns_one_in_front_of_the_other_count(self):
        assert count_doubled(board("4k3/8/8/8/8/2P5/2P5/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_pawns_with_one_square_between_count(self):
        assert count_doubled(board("4k3/8/8/8/2P5/8/2P5/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_pawns_far_apart_do_not(self):
        # c2 and c6. The author: the advanced pawn is attacking, not obstructing,
        # and is usually about to be exchanged off.
        assert count_doubled(board("4k3/8/2P5/8/8/8/2P5/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_the_gap_is_the_authors_two(self):
        assert MAX_DOUBLED_GAP == 2

    def test_a_tripled_pawn_reads_as_worse_than_a_doubled_one(self):
        # Counting surplus rather than files, which is how it plays.
        tripled = board("4k3/8/8/8/2P5/2P5/2P5/4K3 w - - 0 1")
        assert count_doubled(tripled, chess.WHITE) == 2

    def test_pawns_on_different_files_are_not_doubled(self):
        assert count_doubled(board("4k3/8/8/8/8/8/2P1P3/4K3 w - - 0 1"), chess.WHITE) == 0

    def test_it_reports_which_file(self):
        assert doubled_files(board("4k3/8/8/8/8/2P5/2P5/4K3 w - - 0 1"), chess.WHITE) == {2}


class TestPersistence:
    def doubled_for(self, moves: int) -> list[chess.Board]:
        """`moves` positions with c-pawns doubled, then one where they are not."""
        held = board("4k3/8/8/8/8/2P5/2P5/4K3 w - - 0 1")
        resolved = board("4k3/8/8/8/8/2P5/3P4/4K3 w - - 0 1")
        return [held] * moves + [resolved]

    def test_a_transient_doubling_does_not_count(self):
        # Doubled for two of the player's moves and then resolved: the state
        # existed only until the end of an exchange.
        assert persistent_doubled(self.doubled_for(2), chess.WHITE) == frozenset()

    def test_doubling_that_outlasts_the_threshold_counts(self):
        assert persistent_doubled(self.doubled_for(6), chess.WHITE) == {2}

    def test_exactly_the_threshold_is_not_more_than_it(self):
        # "more then 3 moves", so three is not enough.
        assert persistent_doubled(
            self.doubled_for(DOUBLED_PERSISTS_MOVES), chess.WHITE
        ) == frozenset()
        assert persistent_doubled(
            self.doubled_for(DOUBLED_PERSISTS_MOVES + 1), chess.WHITE
        ) == {2}

    def test_two_short_episodes_do_not_add_up(self):
        # A file doubled twice briefly is not a lasting weakness, and a counter
        # that accumulated across episodes would say it was.
        held = board("4k3/8/8/8/8/2P5/2P5/4K3 w - - 0 1")
        clear = board("4k3/8/8/8/8/2P5/3P4/4K3 w - - 0 1")
        span = [held, held, clear, held, held, clear]
        assert persistent_doubled(span, chess.WHITE) == frozenset()

    def test_an_empty_span_is_not_an_error(self):
        assert persistent_doubled([], chess.WHITE) == frozenset()
