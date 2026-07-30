"""The confidence policy: when the swarm may assert a weakness.

Implements docs/notes/architecture.confidence.md. Counts are in **distinct
games**, never instances: a player who hung a piece three times in one
disastrous game did not show a pattern, they had a bad day.
"""

from __future__ import annotations

from chesscoach.confidence import ClaimStats, assign_tier
from chesscoach.profile.models import ConfidenceTier


def counts(**overrides) -> ClaimStats:
    defaults = dict(
        distinct_games=6,
        games_with_data=25,
        rate=0.30,
        baseline_rate=0.10,
        ci95=(0.18, 0.45),
        replicated=True,
    )
    return ClaimStats(**{**defaults, **overrides})


class TestGate:
    def test_too_few_games_with_data_yields_nothing(self):
        # A new account must produce no findings, not invented ones.
        result = assign_tier(counts(games_with_data=6))

        assert result.tier is ConfidenceTier.NONE
        assert result.insufficient_data is True

    def test_enough_data_but_no_pattern_yields_none(self):
        result = assign_tier(counts(distinct_games=1, rate=0.10, ci95=(0.02, 0.30)))

        assert result.tier is ConfidenceTier.NONE
        assert result.insufficient_data is False


class TestPromotion:
    def test_three_distinct_games_reaches_watch(self):
        result = assign_tier(counts(distinct_games=3, games_with_data=12, replicated=False))

        assert result.tier is ConfidenceTier.WATCH

    def test_focus_requires_five_distinct_games_and_twenty_with_data(self):
        assert assign_tier(counts(distinct_games=5, games_with_data=20)).tier is ConfidenceTier.FOCUS
        assert assign_tier(counts(distinct_games=4, games_with_data=20)).tier is ConfidenceTier.WATCH

    def test_focus_requires_replication(self):
        # The E03 lesson as a runtime rule: an unreplicated effect is not shown.
        result = assign_tier(counts(replicated=False))

        assert result.tier is ConfidenceTier.WATCH
        assert "not replicated" in " ".join(result.reasons)

    def test_focus_requires_the_interval_to_exclude_the_baseline(self):
        # If the player's rate in-condition could plausibly equal their rate
        # out of it, there is nothing to report.
        result = assign_tier(counts(ci95=(0.08, 0.40), baseline_rate=0.10))

        assert result.tier is ConfidenceTier.WATCH

    def test_eight_distinct_games_reaches_priority(self):
        result = assign_tier(counts(distinct_games=8, games_with_data=30))

        assert result.tier is ConfidenceTier.PRIORITY

    def test_a_narrow_margin_over_the_comparison_is_only_focus(self):
        # Measured: a 0.4 percentage point change in the reference population
        # flipped a claim from priority to nothing. A claim that barely clears
        # the comparison is real but not a priority.
        result = assign_tier(
            counts(distinct_games=10, games_with_data=40, rate=0.13, ci95=(0.105, 0.20))
        )

        assert result.tier is ConfidenceTier.FOCUS
        assert any("too narrow" in reason for reason in result.reasons)

    def test_a_clear_margin_still_reaches_priority(self):
        result = assign_tier(
            counts(distinct_games=10, games_with_data=40, rate=0.35, ci95=(0.25, 0.45))
        )

        assert result.tier is ConfidenceTier.PRIORITY

    def test_a_rate_below_baseline_is_never_promoted(self):
        # Doing something *less* than usual is not a weakness.
        result = assign_tier(counts(rate=0.02, baseline_rate=0.10, ci95=(0.01, 0.05)))

        assert result.tier is ConfidenceTier.NONE


class TestReasons:
    def test_records_why_the_tier_was_reached(self):
        result = assign_tier(counts(distinct_games=8, games_with_data=30))

        assert any("distinct_games" in reason for reason in result.reasons)

    def test_is_deterministic(self):
        assert assign_tier(counts()) == assign_tier(counts())
