"""When the swarm is allowed to assert a weakness.

Implements docs/notes/architecture.confidence.md. Shared by every section agent
so the rule cannot drift between them.

Two properties matter more than the thresholds themselves:

  * counts are in **distinct games**, never instances. A player who hung a piece
    three times in one disastrous game did not show a pattern;
  * `focus` requires **replication** across a split of the player's own games.
    That is the E03 lesson as a runtime rule (L-008), not a review nicety.

Every number here is provisional and flagged for validation against real data.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.profile.models import ConfidenceTier

# Below this many games with data for the section, say nothing at all. A new
# account must produce no findings rather than invented ones.
MIN_GAMES_WITH_DATA = 10

WATCH_DISTINCT_GAMES = 3

FOCUS_DISTINCT_GAMES = 5
FOCUS_GAMES_WITH_DATA = 20

PRIORITY_DISTINCT_GAMES = 8

# `focus` only needs the interval to clear the comparison rate at all. That is
# too weak for the top tier: a claim whose lower bound sits a fraction above the
# population rate is real but marginal, and measurement showed exactly how
# fragile such claims are -- a 0.4 percentage point change in the reference
# population flipped one from `priority` to nothing at all. To be called a
# priority a claim must clear the comparison by a margin, not merely touch it.
PRIORITY_MARGIN = 1.25


@dataclass(frozen=True)
class ClaimStats:
    """What the confidence policy needs to know about a candidate claim."""

    distinct_games: int
    games_with_data: int
    rate: float
    baseline_rate: float
    ci95: tuple[float, float]
    replicated: bool


@dataclass(frozen=True)
class TierDecision:
    """The tier reached, and why."""

    tier: ConfidenceTier
    reasons: tuple[str, ...]
    insufficient_data: bool

    @property
    def is_assertable(self) -> bool:
        """Would this be shown to the player?"""
        return self.tier in (ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY)


def assign_tier(stats: ClaimStats) -> TierDecision:
    """Decide how much may be asserted about a candidate claim."""
    if stats.games_with_data < MIN_GAMES_WITH_DATA:
        return TierDecision(
            tier=ConfidenceTier.NONE,
            reasons=(f"only {stats.games_with_data} games with data",),
            insufficient_data=True,
        )

    if stats.rate <= stats.baseline_rate:
        return TierDecision(
            tier=ConfidenceTier.NONE,
            reasons=("rate is no worse than this player's own baseline",),
            insufficient_data=False,
        )

    if stats.distinct_games < WATCH_DISTINCT_GAMES:
        return TierDecision(
            tier=ConfidenceTier.NONE,
            reasons=(f"seen in only {stats.distinct_games} distinct games",),
            insufficient_data=False,
        )

    reasons = [f"distinct_games={stats.distinct_games}", f"games_with_data={stats.games_with_data}"]
    blockers = _focus_blockers(stats)
    if blockers:
        return TierDecision(
            tier=ConfidenceTier.WATCH, reasons=tuple(reasons + blockers), insufficient_data=False
        )

    reasons.append("interval excludes baseline")
    reasons.append("replicated across a split of the player's games")

    clears_by_margin = stats.ci95[0] >= stats.baseline_rate * PRIORITY_MARGIN
    if stats.distinct_games >= PRIORITY_DISTINCT_GAMES and clears_by_margin:
        reasons.append(f"distinct_games>={PRIORITY_DISTINCT_GAMES}")
        reasons.append(f"interval clears the comparison by {PRIORITY_MARGIN:g}x")
        return TierDecision(
            tier=ConfidenceTier.PRIORITY, reasons=tuple(reasons), insufficient_data=False
        )

    if stats.distinct_games >= PRIORITY_DISTINCT_GAMES:
        reasons.append("margin over the comparison rate too narrow for priority")

    return TierDecision(tier=ConfidenceTier.FOCUS, reasons=tuple(reasons), insufficient_data=False)


def _focus_blockers(stats: ClaimStats) -> list[str]:
    """Everything standing between this claim and being shown to the player."""
    blockers: list[str] = []
    if stats.distinct_games < FOCUS_DISTINCT_GAMES:
        blockers.append(f"fewer than {FOCUS_DISTINCT_GAMES} distinct games")
    if stats.games_with_data < FOCUS_GAMES_WITH_DATA:
        blockers.append(f"fewer than {FOCUS_GAMES_WITH_DATA} games with data")
    if stats.ci95[0] <= stats.baseline_rate:
        blockers.append("interval does not exclude the baseline rate")
    if not stats.replicated:
        blockers.append("not replicated across a split of the player's games")
    return blockers
