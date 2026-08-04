"""The significance test E06 rests on.

Spec: docs/notes/experiments.e06-progress-power.md

Hand-written rather than imported from scipy, so it needs checking against cases
whose answer is known by construction. A wrong p-value here would not look
wrong — it would look like a result.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "e06-progress-power"))

from power import fisher_one_sided  # noqa: E402


class TestFisherOneSided:
    def test_perfect_separation_of_two_against_two(self):
        # Hypergeometric(N=4, K=2, n=2): P(X>=2) = C(2,2)C(2,0)/C(4,2) = 1/6.
        assert fisher_one_sided(2, 2, 0, 2) == pytest.approx(1 / 6)

    def test_a_single_observation_each_way_is_a_coin_toss(self):
        # P(X>=1), X ~ Hypergeometric(N=2, K=1, n=1) = 1/2.
        assert fisher_one_sided(1, 1, 0, 1) == pytest.approx(0.5)

    def test_no_separation_is_nearly_certain_under_the_null(self):
        # P(X>=1) = 1 - C(2,0)C(2,2)/C(4,2) = 5/6.
        assert fisher_one_sided(1, 2, 1, 2) == pytest.approx(5 / 6)

    def test_every_outcome_met_gives_probability_one(self):
        # If nothing distinguishes the groups, P(X >= its minimum) is certain.
        assert fisher_one_sided(0, 3, 0, 3) == pytest.approx(1.0)

    def test_a_larger_separation_is_less_probable_under_the_null(self):
        assert fisher_one_sided(4, 10, 1, 10) < fisher_one_sided(3, 10, 2, 10)

    def test_e06s_own_table_is_not_significant(self):
        # The result the experiment reports. Pinned so that a change to the
        # statistic cannot quietly turn a null into a finding.
        assert fisher_one_sided(4, 16, 3, 36) == pytest.approx(0.120, abs=0.001)
