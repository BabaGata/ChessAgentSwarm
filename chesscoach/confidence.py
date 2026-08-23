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

import math

from dataclasses import dataclass

from chesscoach.profile.models import ConfidenceTier

# Below this many games with data for the section, say nothing at all. A new
# account must produce no findings rather than invented ones.
MIN_GAMES_WITH_DATA = 10

WATCH_DISTINCT_GAMES = 3

FOCUS_DISTINCT_GAMES = 5

# How much of the corpus a section must have been able to speak about before its
# claims may be asserted -- a **fraction**, because the absolute floor it replaces
# was measuring the window rather than the evidence.
#
# `games_with_data` counts the games in which a section found any diagnosable
# move, so its ceiling is the corpus size. The old `FOCUS_GAMES_WITH_DATA = 20`
# therefore demanded a perfect score from a 20-game corpus, where ordinary
# attrition lands at 18-19. Measured across the twelve review players
# (experiments.e43-focus-gates), it blocked **15 claims at a 20-game window and 0
# at 60** -- among them the reviewer's own top concern at 1.84x and 2.60x the peer
# rate, costing 15.1 and 10.5 points of win probability a game.
#
# 0.80 is the middle of an interval where the choice does not matter: E43 swept
# 0.70, 0.80 and 0.90 and all three were indistinguishable, fixing the defect
# completely and changing nothing at 60 games. Agreement between a 20-game and a
# 60-game read rose 66 % -> 75 %.
#
# This never weakens `MIN_GAMES_WITH_DATA`, which runs first and is what stops a
# new account producing findings at all.
FOCUS_GAMES_FRACTION = 0.80

PRIORITY_DISTINCT_GAMES = 8

# To be called a priority a claim must clear the comparison by a margin, not
# merely touch it. Measurement showed how fragile a bare-touch claim is -- a 0.4
# percentage point change in the reference population flipped one from `priority`
# to nothing at all.
PRIORITY_MARGIN = 1.25

# The same margin, required of `focus` too, but on the point estimate rather than
# the interval's lower bound -- so `focus` means "big enough and reliably real"
# and `priority` still means "big enough even at the pessimistic end".
#
# Without this, `focus` is a pure **significance** test: the interval must exclude
# the population rate, with no floor on **magnitude**. That was harmless while
# every claim carried ~100 opportunities per player, because at that sample size
# an effect only becomes significant once it is also worth mentioning. S5 arrived
# carrying **526**, and the two came apart: its pooled claim deviates by 1.24x at
# the 90th percentile -- statistically solid, and nothing a coach would say out
# loud (L-023, question D12).
#
# 1.25 is chosen to match PRIORITY_MARGIN rather than tuned, and it was checked
# against every finding the swarm currently asserts: the **smallest** of the 40 is
# 1.40, so this floor removes none of them. It exists to stop the next
# large-denominator section, not to prune the present ones.
FOCUS_MARGIN = 1.25


@dataclass(frozen=True)
class ClaimStats:
    """What the confidence policy needs to know about a candidate claim.

    Deliberately **not** carrying a population prior. Replacing the interval test
    with a posterior shrunk toward the peer population was built and measured in
    E20: it **halved** coverage at 24 games rather than raising it, because a
    Wilson bound computed from the player's own games is more permissive than a
    properly shrunk estimate. The shrinkage machinery survives in
    `chesscoach.shrinkage`, where the peer reference uses it; the gate does not.
    """

    distinct_games: int
    games_with_data: int
    # How many games the corpus held at all. `games_with_data` is measured
    # against this rather than against a constant, so the same coverage is not
    # judged differently for having been read over a shorter window (E43).
    # Zero means a section did not report it, and is refused rather than waved
    # through -- a wiring bug must not silently loosen the policy.
    corpus_games: int
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
    """Everything standing between this claim and being shown to the player.

    The distinct-game floors stay. They are not a sample-size test -- the
    posterior is -- they guard against **clustering**: three pieces hung in one
    disastrous game is not a pattern, however many opportunities the corpus
    holds, and no amount of shrinkage notices that.
    """
    blockers: list[str] = []
    if stats.distinct_games < FOCUS_DISTINCT_GAMES:
        blockers.append(f"fewer than {FOCUS_DISTINCT_GAMES} distinct games")
    needed = math.ceil(FOCUS_GAMES_FRACTION * stats.corpus_games)
    if stats.corpus_games <= 0 or stats.games_with_data < needed:
        blockers.append(
            f"data in {stats.games_with_data} of {stats.corpus_games} games, "
            f"under {FOCUS_GAMES_FRACTION:.0%} of the corpus"
        )
    if stats.ci95[0] <= stats.baseline_rate:
        blockers.append("interval does not exclude the baseline rate")
    if stats.rate < stats.baseline_rate * FOCUS_MARGIN:
        blockers.append(f"clears the comparison by less than {FOCUS_MARGIN:g}x")
    if not stats.replicated:
        blockers.append("not replicated across a split of the player's games")
    return blockers
