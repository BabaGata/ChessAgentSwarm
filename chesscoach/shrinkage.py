"""How sure the swarm is about a rate, given how little of it there is.

Design: docs/notes/design.short-history-prioritisation.md § layer 2

The confidence policy asks threshold questions -- does the interval clear the
baseline, are there five distinct games. [[experiments.e16-shallow-corpus]]
measured the cost: at 24 games the swarm is silent for 43 % of players, and 96 %
of that silence is two gates making one complaint, *"too little evidence"*,
expressed as cliffs.

A posterior makes the same complaint continuously. The peer population is the
prior -- `peers.prior_strength` already estimates how hard to shrink, by method
of moments on a beta-binomial -- and a player's own games update it. Thin
evidence then fails to move the estimate off the population, which is what the
distinct-game floors were approximating all along, without a cliff and without a
number to tune.

It is also the regression-to-the-mean correction (R-15) applied at estimation
rather than patched afterwards: an extreme rate measured on few games *is*
mostly noise, and the posterior says so by construction.

**Exact, not approximate.** The regularised incomplete beta by continued
fraction, in the spirit of the hand-written Fisher exact test already in this
project. A normal approximation would be wrong in precisely the case that
matters -- few observations, where the posterior is skewed and the whole question
is whether the evidence is thin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Continued-fraction limits. 200 iterations is far past what converges for the
# a, b this project produces; the epsilon is near double precision.
_MAX_ITERATIONS = 200
_EPSILON = 3e-16
_TINY = 1e-300

# A population rate of exactly 0 or 1 would make the prior degenerate -- a Beta
# with a zero parameter is not a distribution. Nudged inside the open interval by
# less than any rate the swarm can measure.
_MIN_RATE = 1e-9


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Lentz's algorithm for the continued fraction of the incomplete beta."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _TINY:
        d = _TINY
    d = 1.0 / d
    h = d

    for m in range(1, _MAX_ITERATIONS + 1):
        m2 = 2 * m
        # Even step.
        numerator = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + numerator * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + numerator / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        h *= d * c
        # Odd step.
        numerator = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + numerator * d
        if abs(d) < _TINY:
            d = _TINY
        c = 1.0 + numerator / c
        if abs(c) < _TINY:
            c = _TINY
        d = 1.0 / d
        step = d * c
        h *= step
        if abs(step - 1.0) < _EPSILON:
            break

    return h


def betainc(a: float, b: float, x: float) -> float:
    """The regularised incomplete beta I_x(a, b) -- P(theta <= x) for Beta(a, b).

    Computed through log-gammas so the large counts a deep corpus produces
    (hundreds of thousands of opportunities) do not overflow.
    """
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    # The fraction converges quickly only on one side of the mode; the symmetry
    # identity covers the other.
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


@dataclass(frozen=True)
class Posterior:
    """What the swarm believes a player's true rate is, after seeing their games."""

    alpha: float
    beta: float

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def probability_above(self, rate: float) -> float:
        """How sure we are the player's true rate exceeds this one.

        The number that replaces *"does the interval exclude the baseline"* with
        something a person can read: 0.97 is a finding, 0.62 is a suspicion.
        """
        return 1.0 - betainc(self.alpha, self.beta, min(max(rate, 0.0), 1.0))

    def interval(self, mass: float = 0.95) -> tuple[float, float]:
        """The central credible interval, by bisection on the exact CDF.

        Bisection rather than a closed form because the inverse has none; 60
        halvings take the bracket below 1e-18, far past what any rate here means.
        """
        tail = (1.0 - mass) / 2.0
        return (self._quantile(tail), self._quantile(1.0 - tail))

    def _quantile(self, probability: float) -> float:
        low, high = 0.0, 1.0
        for _ in range(60):
            middle = (low + high) / 2.0
            if betainc(self.alpha, self.beta, middle) < probability:
                low = middle
            else:
                high = middle
        return (low + high) / 2.0


def posterior(
    instances: int, opportunities: int, population_rate: float, strength: float
) -> Posterior:
    """A player's rate, shrunk toward the population by an amount the data decides.

    `strength` is the prior's weight in pseudo-observations, from
    `peers.prior_strength`: when peers differ widely most of the spread is real
    and an individual's games are informative, so it is small; when peers are
    alike, most of any one measurement is noise, so it is large.

    The mean agrees exactly with `PeerReference.expected_rate` -- two shrinkage
    formulas in one system would be a defect waiting to be noticed when their
    predictions disagreed.
    """
    rate = min(max(population_rate, _MIN_RATE), 1.0 - _MIN_RATE)
    prior_successes = strength * rate
    prior_failures = strength * (1.0 - rate)
    return Posterior(
        alpha=prior_successes + instances,
        beta=prior_failures + max(0, opportunities - instances),
    )
