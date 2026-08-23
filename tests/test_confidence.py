"""The confidence policy: when the swarm may assert a weakness.

Implements docs/notes/architecture.confidence.md. Counts are in **distinct
games**, never instances: a player who hung a piece three times in one
disastrous game did not show a pattern, they had a bad day.
"""

from __future__ import annotations

from chesscoach.confidence import FOCUS_GAMES_FRACTION, ClaimStats, assign_tier
from chesscoach.profile.models import ConfidenceTier


def counts(**overrides) -> ClaimStats:
    defaults = dict(
        distinct_games=6,
        games_with_data=25,
        rate=0.30,
        baseline_rate=0.10,
        ci95=(0.18, 0.45),
        replicated=True,
        corpus_games=25,
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


class TestMagnitudeAsWellAsSignificance:
    """`focus` reaches the player, so it must require an effect worth hearing.

    Before FOCUS_MARGIN it required only that the interval exclude the
    population rate — a pure significance test. That stayed harmless while every
    claim carried ~100 opportunities, because at that size an effect becomes
    significant at about the point it becomes worth mentioning. S5 arrived with
    526 and the two came apart: 1.24x deviations, statistically solid and not
    worth saying (L-023, D12).
    """

    def test_a_reliable_but_tiny_deviation_does_not_reach_the_player(self):
        # A huge sample makes the interval tight enough to exclude the baseline
        # while the effect stays trivial.
        result = assign_tier(
            counts(rate=0.056, baseline_rate=0.050, ci95=(0.052, 0.060), distinct_games=15)
        )

        assert result.tier is ConfidenceTier.WATCH
        assert not result.is_assertable

    def test_and_it_says_why(self):
        result = assign_tier(
            counts(rate=0.056, baseline_rate=0.050, ci95=(0.052, 0.060), distinct_games=15)
        )

        assert any("less than 1.25x" in reason for reason in result.reasons)

    def test_a_deviation_worth_hearing_still_reaches_focus(self):
        # The smallest ratio the swarm currently asserts on real players is
        # 1.40, so the floor is set below every finding that exists today.
        result = assign_tier(counts(rate=0.140, baseline_rate=0.100, ci95=(0.105, 0.190)))

        assert result.is_assertable

    def test_the_floor_sits_below_every_finding_the_swarm_currently_makes(self):
        from chesscoach.confidence import FOCUS_MARGIN

        assert FOCUS_MARGIN <= 1.40

    def test_focus_is_easier_to_reach_than_priority(self):
        # The margin is the same number, but focus applies it to the point
        # estimate and priority to the pessimistic end of the interval. If that
        # ordering ever inverted, priority would become unreachable.
        from chesscoach.confidence import FOCUS_MARGIN, PRIORITY_MARGIN

        stats = counts(rate=0.140, baseline_rate=0.100, ci95=(0.105, 0.190), distinct_games=10)

        assert FOCUS_MARGIN <= PRIORITY_MARGIN
        assert assign_tier(stats).tier is ConfidenceTier.FOCUS


class TestReasons:
    def test_records_why_the_tier_was_reached(self):
        result = assign_tier(counts(distinct_games=8, games_with_data=30))

        assert any("distinct_games" in reason for reason in result.reasons)

    def test_is_deterministic(self):
        assert assign_tier(counts()) == assign_tier(counts())


class TestCorpusFraction:
    """The games floor must measure the evidence, not the size of the window.

    Screen: docs/notes/experiments.e43-focus-gates.md — the old absolute floor of
    20 blocked 15 claims at a 20-game corpus and 0 at a 60-game one, because
    `games_with_data` counts games in which the *section* found a diagnosable
    move and its ceiling is the corpus size.
    """

    def test_a_section_covering_most_of_a_short_corpus_reaches_focus(self):
        # The E43 case: 18 of 20 games is ordinary attrition, not thin evidence.
        # Under the old absolute floor of 20 this was refused.
        result = assign_tier(counts(games_with_data=18, corpus_games=20))

        assert result.tier is not ConfidenceTier.NONE
        assert result.is_assertable

    def test_a_section_covering_little_of_a_long_corpus_does_not(self):
        # 40 of 60 is 67 %, below the floor — the section was largely silent and
        # the old absolute rule would have waved it through on the count alone.
        result = assign_tier(counts(games_with_data=40, corpus_games=60))

        assert not result.is_assertable
        assert any("of the corpus" in reason for reason in result.reasons)

    def test_the_same_count_can_pass_or_fail_depending_on_the_corpus(self):
        # The whole point: 18 games with data is strong coverage of 20 games and
        # weak coverage of 60. The old rule could not tell those apart.
        assert assign_tier(counts(games_with_data=18, corpus_games=20)).is_assertable
        assert not assign_tier(counts(games_with_data=18, corpus_games=60)).is_assertable

    def test_the_absolute_minimum_still_applies_beneath_the_fraction(self):
        # A 5-game corpus would clear any fraction; MIN_GAMES_WITH_DATA is what
        # stops a new account producing findings, and the fraction never weakens it.
        result = assign_tier(counts(games_with_data=5, corpus_games=5))

        assert result.tier is ConfidenceTier.NONE
        assert result.insufficient_data

    def test_the_fraction_is_the_calibrated_one(self):
        # Stated as a test because it came from measurement: E43 swept 0.70, 0.80
        # and 0.90 and found them indistinguishable, so 0.80 is the middle of an
        # interval where the choice does not matter — not a tuned value.
        assert FOCUS_GAMES_FRACTION == 0.80

    def test_an_unknown_corpus_size_refuses_rather_than_waves_through(self):
        # Zero means a section did not report it. Treating that as "no floor"
        # would turn a wiring bug into a silent loosening of the policy.
        result = assign_tier(counts(games_with_data=25, corpus_games=0))

        assert not result.is_assertable
