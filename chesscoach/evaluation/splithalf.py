"""Split-half replication.

Evaluation metric B1, and simultaneously the promotion rule in
docs/notes/architecture.confidence.md -- built once, used twice.

A measurement is split across two disjoint halves of the player's games and must
survive in both. It exists because of a specific failure: E03 found an effect
with lift 2.40 and a tidy mechanism for it, which reversed to 0.76 on held-out
players (L-008). A plausible mechanism is not evidence; it is what makes an
artefact convincing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from chesscoach.profile.models import wilson_interval

# Below this, a half is too small for the comparison to mean anything.
DEFAULT_MIN_GAMES_PER_HALF = 3

# successes, trials
Measure = Callable[[Sequence[str]], tuple[int, int]]


@dataclass(frozen=True)
class HalfMeasure:
    """The measurement on one half of the games."""

    n_games: int
    successes: int
    trials: int
    rate: float
    ci95: tuple[float, float]


@dataclass(frozen=True)
class SplitHalfResult:
    """Whether a measurement survived being split in two."""

    first: HalfMeasure
    second: HalfMeasure
    intervals_overlap: bool
    same_side_of_reference: bool
    insufficient_data: bool
    reference_rate: float | None = None

    @property
    def replicated(self) -> bool:
        """Both halves agree, and there was enough data to say so."""
        return (
            not self.insufficient_data and self.intervals_overlap and self.same_side_of_reference
        )

    def summary(self) -> str:
        verdict = "replicated" if self.replicated else "did NOT replicate"
        return (
            f"{verdict}: {self.first.rate:.3f} (n={self.first.trials}) "
            f"vs {self.second.rate:.3f} (n={self.second.trials})"
        )


def split_games(game_ids: Iterable[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Deterministically split games into two halves.

    Sorted first, then alternated, so the split depends on the set of games and
    not on the order they happened to arrive in.
    """
    ordered = sorted(set(game_ids))
    return tuple(ordered[0::2]), tuple(ordered[1::2])


def split_half_check(
    game_ids: Iterable[str],
    measure: Measure,
    reference_rate: float | None = None,
    min_games_per_half: int = DEFAULT_MIN_GAMES_PER_HALF,
) -> SplitHalfResult:
    """Measure both halves and decide whether the effect survived.

    `measure` maps a set of game ids to (successes, trials) — it is whatever the
    section agent counts, so this works for any claim without knowing what the
    claim is about.

    Replication requires the two halves' intervals to overlap and, when a
    reference rate is supplied, both halves to sit on the same side of it. The
    second condition is what stops "above peers" and "below peers" counting as
    agreement merely because both intervals are wide.
    """
    first_ids, second_ids = split_games(game_ids)
    first = _measure_half(first_ids, measure)
    second = _measure_half(second_ids, measure)

    insufficient = (
        first.n_games < min_games_per_half
        or second.n_games < min_games_per_half
        or first.trials == 0
        or second.trials == 0
    )

    return SplitHalfResult(
        first=first,
        second=second,
        intervals_overlap=_overlap(first.ci95, second.ci95),
        same_side_of_reference=_same_side(first.rate, second.rate, reference_rate),
        insufficient_data=insufficient,
        reference_rate=reference_rate,
    )


def _measure_half(game_ids: tuple[str, ...], measure: Measure) -> HalfMeasure:
    successes, trials = measure(game_ids) if game_ids else (0, 0)
    return HalfMeasure(
        n_games=len(game_ids),
        successes=successes,
        trials=trials,
        rate=successes / trials if trials else 0.0,
        ci95=wilson_interval(successes, trials),
    )


def _overlap(first: tuple[float, float], second: tuple[float, float]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def _same_side(first_rate: float, second_rate: float, reference: float | None) -> bool:
    if reference is None:
        return True
    return (first_rate >= reference) == (second_rate >= reference)
