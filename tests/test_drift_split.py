"""The date split E05 measures drift with.

Spec: docs/notes/experiments.e05-natural-drift.md

Small surface, but the whole of D9 rests on it. `--early-games` must shorten the
*measurement* period from its recent end while leaving the *outcome* period
untouched; slicing the wrong end would silently answer a different question —
"what if the finding came from older games" instead of "what if it came from
fewer" — and the result would look perfectly reasonable either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "e05-natural-drift"))

from run import split_by_date  # noqa: E402

from chesscoach.ingest.pgn import GameRecord  # noqa: E402


def a_game(day: int) -> GameRecord:
    return GameRecord(
        game_id=f"g{day:03d}",
        white="alice",
        black="bob",
        result="1-0",
        moves=("e4",),
        clocks=(None,),
        date=f"2026-01-{day:02d}",
    )


@pytest.fixture
def ten_games() -> tuple[GameRecord, ...]:
    # Deliberately out of order: the split must sort, not trust the input.
    return tuple(a_game(day) for day in (3, 7, 1, 9, 5, 10, 2, 8, 4, 6))


class TestHalving:
    def test_splits_into_earlier_and_later_by_date(self, ten_games):
        early, late = split_by_date(ten_games)

        assert [g.date for g in early] == [f"2026-01-0{d}" for d in range(1, 6)]
        assert [g.game_id for g in late] == [f"g{d:03d}" for d in range(6, 11)]

    def test_an_odd_count_gives_the_extra_game_to_the_later_half(self):
        early, late = split_by_date(tuple(a_game(day) for day in range(1, 8)))

        assert len(early) == 3
        assert len(late) == 4


class TestEarlyGamesCap:
    def test_keeps_the_games_nearest_the_split_not_the_oldest(self, ten_games):
        # The point of D9: fewer games to measure on, not older ones.
        early, _ = split_by_date(ten_games, early_games=2)

        assert [g.date for g in early] == ["2026-01-04", "2026-01-05"]

    def test_leaves_the_outcome_period_untouched(self, ten_games):
        _, uncapped = split_by_date(ten_games)
        _, capped = split_by_date(ten_games, early_games=2)

        assert capped == uncapped

    def test_a_cap_larger_than_the_half_changes_nothing(self, ten_games):
        assert split_by_date(ten_games, early_games=99) == split_by_date(ten_games)

    def test_no_cap_is_the_default(self, ten_games):
        assert split_by_date(ten_games, None) == split_by_date(ten_games)
