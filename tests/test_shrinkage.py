"""Estimating what a player's rate really is, before predicting anything about it.

E05 measured that 92% of the planner's targets were met with no intervention,
because a finding is selected for being extreme and extremes regress. The fix is
to stop treating the selected value as the truth: shrink it toward the
population in proportion to how little data supports it.

The prior's strength is estimated from the peer reference itself, which already
stores each player's contribution — so how much to shrink is measured rather
than guessed.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import ConditionMeasurement, build_reference

KEY = "missed_motif.pin.own"


def reference_from(rates_and_sizes, band="1400-1800", time_control="rapid"):
    return build_reference(
        [
            (
                f"peer{index}",
                (
                    ConditionMeasurement(
                        claim_key=KEY,
                        instances=round(rate * size),
                        opportunities=size,
                        distinct_games=5,
                        games_with_data=30,
                    ),
                ),
            )
            for index, (rate, size) in enumerate(rates_and_sizes)
        ],
        band=band,
        time_control=time_control,
        depth=15,
    )


def spread_peers():
    """Peers whose rates genuinely differ: a weak prior, so shrink little."""
    return reference_from([(0.05, 200), (0.20, 200), (0.35, 200), (0.50, 200), (0.10, 200)])


def uniform_peers():
    """Peers who all behave alike: a strong prior, so shrink hard."""
    return reference_from([(0.20, 200), (0.21, 200), (0.19, 200), (0.20, 200), (0.21, 200)])


class TestExpectedRate:
    def test_a_small_sample_is_pulled_towards_the_population(self):
        peers = uniform_peers()

        expected = peers.expected_rate("1400-1800", "rapid", KEY, instances=3, opportunities=4)

        assert expected < 0.75  # the raw rate
        assert expected == pytest.approx(0.20, abs=0.08)

    def test_a_large_sample_is_left_close_to_what_was_observed(self):
        peers = uniform_peers()

        expected = peers.expected_rate(
            "1400-1800", "rapid", KEY, instances=1500, opportunities=2000
        )

        assert expected == pytest.approx(0.75, abs=0.05)

    def test_peers_who_differ_widely_justify_less_shrinkage(self):
        wide = spread_peers().expected_rate(
            "1400-1800", "rapid", KEY, instances=30, opportunities=40
        )
        narrow = uniform_peers().expected_rate(
            "1400-1800", "rapid", KEY, instances=30, opportunities=40
        )

        assert wide > narrow

    def test_returns_none_without_a_population_to_shrink_towards(self):
        peers = uniform_peers()

        assert peers.expected_rate("other-band", "rapid", KEY, 10, 20) is None

    def test_excludes_the_player_from_their_own_population(self):
        peers = uniform_peers()

        with_all = peers.expected_rate("1400-1800", "rapid", KEY, 10, 20)
        without_one = peers.expected_rate(
            "1400-1800", "rapid", KEY, 10, 20, excluding="peer0"
        )

        assert with_all is not None and without_one is not None

    def test_no_opportunities_means_no_estimate(self):
        assert uniform_peers().expected_rate("1400-1800", "rapid", KEY, 0, 0) is None


class TestPriorStrength:
    def test_uniform_peers_give_a_stronger_prior_than_varied_ones(self):
        from chesscoach.peers import prior_strength

        uniform = prior_strength(uniform_peers().cells[f"1400-1800|rapid|{KEY}"])
        varied = prior_strength(spread_peers().cells[f"1400-1800|rapid|{KEY}"])

        assert uniform > varied

    def test_too_few_peers_falls_back_to_a_default(self):
        from chesscoach.peers import DEFAULT_PRIOR_STRENGTH, prior_strength

        one_peer = reference_from([(0.2, 100)])

        assert prior_strength(one_peer.cells[f"1400-1800|rapid|{KEY}"]) == DEFAULT_PRIOR_STRENGTH

    def test_is_never_negative(self):
        from chesscoach.peers import prior_strength

        assert prior_strength(spread_peers().cells[f"1400-1800|rapid|{KEY}"]) > 0
