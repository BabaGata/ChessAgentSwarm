"""Costly because you meet it constantly, not because you handle it badly.

Every rate in this project is **conditional** — its denominator is
opportunities, so it measures how badly a player does once they are in a
condition. That is deliberate (S1: a per-move rate would mostly measure how
tactical the opponent made the game) and it has a blind spot the whole peer
comparison inherits: it cannot tell *"you play time pressure badly"* from
*"you are in time pressure constantly"*.

Measured across the twelve review players, of 327 (player, claim) pairs with
both a peer rate and a peer cost, **198 sat below the peer rate** and **21 of
those cost more than peers anyway**. Six ranked in a player's top five by cost
and two were a player's single most expensive pattern. Exposure was the driver
in every case:

    maikel5   time pressure   14.6% vs 15.3%   5.4/game vs 0.4   cost 14.8 vs 8.0
    bjagus    instant moves    9.4% vs  9.4%  15.8/game vs 9.2   cost 29.6 vs 27.4
    goydorak  endgames         7.0% vs  9.9%   8.7/game vs 5.3   cost 15.0 vs 11.2

The arbiter used to exclude all of these outright, on the reasoning that a thing
you do less than your peers is not a thing to work on. For a conditional rate
that reasoning does not hold, and the advice it protected was the wrong advice
anyway: telling maikel5 to work on their play in time pressure prescribes the
one thing they are already better than average at.
"""

from __future__ import annotations

from chesscoach.profile.models import Measurement


def a_measurement(**kwargs) -> Measurement:
    defaults = dict(
        instances=25,
        distinct_games=11,
        games_with_data=44,
        rate=0.146,
        peer_rate=0.153,
        opportunities=238,
        peer_opportunities_per_game=0.4,
        cost_wp=651.0,
        peer_cost_per_game=8.0,
    )
    return Measurement(**{**defaults, **kwargs})


class TestExposure:
    def test_it_is_opportunities_per_game(self):
        measurement = a_measurement(opportunities=238, games_with_data=44)

        assert measurement.exposure_per_game == 238 / 44

    def test_the_ratio_says_how_much_more_of_it_the_player_meets(self):
        measurement = a_measurement(opportunities=220, games_with_data=44,
                                    peer_opportunities_per_game=0.5)

        assert measurement.exposure_ratio == 10.0

    def test_no_opportunities_recorded_means_no_exposure_figure(self):
        # Every profile written before schema 14 is in this state, and it must
        # read as "unknown" rather than as zero.
        assert a_measurement(opportunities=None).exposure_per_game is None
        assert a_measurement(opportunities=None).exposure_ratio is None

    def test_no_peer_exposure_means_no_ratio(self):
        assert a_measurement(peer_opportunities_per_game=None).exposure_ratio is None

    def test_a_peer_exposure_of_zero_does_not_divide(self):
        assert a_measurement(peer_opportunities_per_game=0.0).exposure_ratio is None


class TestDrivenByExposure:
    def test_below_peer_rate_and_above_peer_cost_is_the_shape(self):
        # maikel5: handles it better than average, pays nearly twice as much.
        measurement = a_measurement(rate=0.146, peer_rate=0.153,
                                    cost_wp=651.0, peer_cost_per_game=8.0)

        assert measurement.cost_per_game > 8.0
        assert measurement.driven_by_exposure is True

    def test_an_equal_rate_still_counts(self):
        # bjagus: 9.4% against 9.4%, and 72% more instant moves per game. The
        # rate is doing no work at all, so the cost gap is entirely exposure.
        measurement = a_measurement(rate=0.094, peer_rate=0.094,
                                    cost_wp=1302.0, peer_cost_per_game=27.4)

        assert measurement.driven_by_exposure is True

    def test_being_worse_at_it_is_not_an_exposure_finding(self):
        # Above the peer rate is the ordinary case: the player really is worse
        # once in the condition, and the ordinary wording is correct.
        measurement = a_measurement(rate=0.30, peer_rate=0.15)

        assert measurement.driven_by_exposure is False

    def test_costing_no_more_than_peers_is_not_an_exposure_finding(self):
        # Better at it AND paying no more for it. Nothing to say.
        measurement = a_measurement(rate=0.10, peer_rate=0.15,
                                    cost_wp=44.0, peer_cost_per_game=8.0)

        assert measurement.cost_per_game < 8.0
        assert measurement.driven_by_exposure is False

    def test_it_needs_a_population_to_be_a_claim_at_all(self):
        assert a_measurement(peer_rate=None).driven_by_exposure is False
        assert a_measurement(peer_cost_per_game=None).driven_by_exposure is False

    def test_a_claim_that_cannot_price_itself_is_not_one(self):
        # Conceding a structure is a choice, not a mistake, so there is no cost
        # to compare and nothing to say about exposure either.
        assert a_measurement(cost_wp=None).driven_by_exposure is False

    def test_an_exposure_finding_always_has_a_positive_excess(self):
        # The property that made the first version of the report wiring wrong:
        # driven_by_exposure implies cost > peer_cost implies excess > 0, so any
        # branch checking the excess first will always win. The exposure case
        # must be tested BEFORE the ordinary positive-excess case, not after.
        measurement = a_measurement()

        assert measurement.driven_by_exposure is True
        assert measurement.excess_cost_per_game > 0
