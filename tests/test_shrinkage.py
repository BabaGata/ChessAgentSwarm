"""Step 4 — how sure are we, given how little we have?

Spec: docs/notes/design.short-history-prioritisation.md § layer 2

The confidence policy asks a threshold question — does the interval clear the
baseline, are there five distinct games — and E16 measured what that costs: at 24
games the swarm is silent for 43 % of players, and **96 %** of that silence is two
gates that are really one complaint, *"too little evidence"*, expressed as cliffs.

A posterior expresses the same complaint continuously. The peer reference already
supplies the prior (`prior_strength`, a method-of-moments beta-binomial); what is
missing is the uncertainty around the shrunk estimate, which is what decides
whether a claim may be asserted, merely suspected, or left unsaid.

Exact rather than approximate: the regularised incomplete beta function by
continued fraction, in the spirit of the hand-written Fisher exact test already
here. A normal approximation would be wrong in exactly the case that matters —
few observations, where the posterior is skewed.
"""

from __future__ import annotations

import math

import pytest

from chesscoach.shrinkage import Posterior, betainc, posterior


class TestTheIncompleteBeta:
    """Checked against identities rather than a table, so it needs no external source."""

    @pytest.mark.parametrize("x", [0.01, 0.25, 0.5, 0.75, 0.99])
    def test_uniform_case_is_the_identity(self, x):
        # I_x(1,1) = x
        assert betainc(1.0, 1.0, x) == pytest.approx(x, abs=1e-12)

    @pytest.mark.parametrize("x,a", [(0.3, 2.0), (0.7, 5.0), (0.5, 0.5)])
    def test_beta_of_one_is_a_power(self, x, a):
        # I_x(a,1) = x**a
        assert betainc(a, 1.0, x) == pytest.approx(x**a, rel=1e-10)

    @pytest.mark.parametrize("x,b", [(0.3, 2.0), (0.7, 5.0), (0.5, 0.5)])
    def test_alpha_of_one_is_the_complement(self, x, b):
        # I_x(1,b) = 1 - (1-x)**b
        assert betainc(1.0, b, x) == pytest.approx(1 - (1 - x) ** b, rel=1e-10)

    @pytest.mark.parametrize("a,b,x", [(2.0, 3.0, 0.4), (7.5, 2.5, 0.8), (30.0, 70.0, 0.31)])
    def test_the_symmetry_identity_holds(self, a, b, x):
        # I_x(a,b) = 1 - I_{1-x}(b,a)
        assert betainc(a, b, x) == pytest.approx(1 - betainc(b, a, 1 - x), abs=1e-12)

    def test_a_symmetric_beta_has_half_its_mass_below_the_middle(self):
        assert betainc(8.0, 8.0, 0.5) == pytest.approx(0.5, abs=1e-12)

    def test_it_is_bounded(self):
        assert betainc(3.0, 4.0, 0.0) == 0.0
        assert betainc(3.0, 4.0, 1.0) == 1.0

    def test_it_survives_the_large_counts_a_deep_corpus_produces(self):
        # 250,000 opportunities is a real figure from the peer reference; a naive
        # implementation overflows on the gamma functions here.
        value = betainc(50_000.0, 200_000.0, 0.2)

        assert 0.0 <= value <= 1.0
        assert math.isfinite(value)


class TestTheShrunkEstimate:
    def test_no_evidence_leaves_the_player_at_the_population(self):
        belief = posterior(instances=0, opportunities=0, population_rate=0.2, strength=50.0)

        assert belief.mean == pytest.approx(0.2)

    def test_a_little_evidence_moves_it_a_little(self):
        # 4 in 10 looks like 40%, but against a 20% population and 50
        # pseudo-observations it is barely evidence at all.
        belief = posterior(instances=4, opportunities=10, population_rate=0.2, strength=50.0)

        assert 0.20 < belief.mean < 0.25

    def test_a_lot_of_evidence_moves_it_a_lot(self):
        belief = posterior(instances=400, opportunities=1000, population_rate=0.2, strength=50.0)

        assert belief.mean > 0.38

    def test_the_estimate_matches_the_reference_shrinkage(self):
        # Must agree with PeerReference.expected_rate, which the progress check
        # already relies on. Two shrinkage formulas in one system would be a bug
        # waiting for someone to notice the predictions disagree.
        instances, opportunities, population, strength = 30, 200, 0.2, 50.0
        expected = (instances + strength * population) / (opportunities + strength)

        assert posterior(instances, opportunities, population, strength).mean == pytest.approx(
            expected
        )


class TestHowSure:
    def test_thin_evidence_is_not_convincing(self):
        # Two occurrences where the population expects one. This is the case the
        # distinct-games floor existed to block, and the posterior blocks it
        # without a threshold: it simply is not sure.
        belief = posterior(instances=2, opportunities=20, population_rate=0.05, strength=50.0)

        assert belief.probability_above(0.05) < 0.9

    def test_the_same_rate_on_much_more_evidence_is_convincing(self):
        belief = posterior(instances=100, opportunities=1000, population_rate=0.05, strength=50.0)

        assert belief.probability_above(0.05) > 0.99

    def test_being_at_the_population_is_a_coin_flip(self):
        belief = posterior(instances=20, opportunities=100, population_rate=0.2, strength=50.0)

        assert belief.probability_above(0.2) == pytest.approx(0.5, abs=0.05)

    def test_being_below_the_population_is_unconvincing(self):
        belief = posterior(instances=5, opportunities=100, population_rate=0.2, strength=50.0)

        assert belief.probability_above(0.2) < 0.05


class TestTheInterval:
    def test_it_brackets_the_estimate(self):
        belief = posterior(instances=40, opportunities=200, population_rate=0.1, strength=50.0)
        low, high = belief.interval()

        assert low < belief.mean < high

    def test_more_evidence_narrows_it(self):
        thin = posterior(instances=4, opportunities=20, population_rate=0.1, strength=50.0)
        thick = posterior(instances=400, opportunities=2000, population_rate=0.1, strength=50.0)

        def width(b: Posterior) -> float:
            low, high = b.interval()
            return high - low

        assert width(thick) < width(thin) / 3

    def test_it_stays_inside_the_unit_interval(self):
        low, high = posterior(0, 5, population_rate=0.001, strength=50.0).interval()

        assert 0.0 <= low <= high <= 1.0


def test_a_population_that_never_does_it_is_handled():
    # A claim with a zero population rate would make the prior degenerate.
    belief = posterior(instances=1, opportunities=10, population_rate=0.0, strength=50.0)

    assert 0.0 <= belief.mean <= 1.0
    assert math.isfinite(belief.probability_above(0.0))
