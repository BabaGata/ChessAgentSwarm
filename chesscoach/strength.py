"""Estimating how strong a player is, from their own games.

Capability: V1 · Screen and fit: docs/notes/experiments.e13-strength-signal.md

The whole estimator is one line of arithmetic on one feature, and that is the
result rather than a shortcut. E13 measured four candidates against 84 players'
actual ratings and cross-validated each by held-out player: **blunder rate wins**,
and adding the others buys nothing worth the complexity.

    rating ~= 2053 - 19859 * blunder_rate

**The error bar is the point, not the number.** Held-out mean absolute error is
**103 rating points** — 60 % of players land within 100 and 89 % within 200.
Anything that reports the estimate without that spread is claiming a precision
the measurement does not have, and D1 is explicit that this project must never
promise rating gains it cannot evidence.

Deterministic, no model, no engine calls of its own: blunder rate is already
counted on every observation.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.sections.base import diagnosable

# Fitted on all 84 players of the E13 corpus. Refit with
# `experiments/e13-strength-signal/run.py`, which prints these two numbers and
# the held-out error that qualifies them.
INTERCEPT = 2053.1
SLOPE = -19858.6

# Held-out mean absolute error, 5-fold by player. Reported *with* every estimate.
TYPICAL_ERROR = 103

# The blunder rates the fit was made over. Beyond them the line is extrapolating
# and says so, because a linear fit outside its range is a guess with a decimal
# point on it.
FITTED_RANGE = (0.0083, 0.0717)

# Below this the rate is too noisy to turn into a rating. One blunder in 80 moves
# and one in 90 are the same player; the arithmetic would put 250 points between
# them.
MIN_MOVES = 200


@dataclass(frozen=True)
class StrengthEstimate:
    """What the player's own moves suggest, and how far that can be trusted."""

    rating: int
    typical_error: int
    moves: int
    blunder_rate: float
    extrapolated: bool

    @property
    def range(self) -> tuple[int, int]:
        """The band most players of this measured standard actually fall in."""
        return self.rating - self.typical_error, self.rating + self.typical_error


def estimate(observations: tuple[Observation, ...], username: str) -> StrengthEstimate | None:
    """None when there are too few moves to say anything, which is a real answer."""
    mine = diagnosable(
        tuple(o for o in observations if o.mover.lower() == username.lower())
    )
    if len(mine) < MIN_MOVES:
        return None

    blunders = sum(1 for o in mine if o.label is ErrorLabel.BLUNDER)
    rate = blunders / len(mine)

    return StrengthEstimate(
        rating=round(INTERCEPT + SLOPE * rate),
        typical_error=TYPICAL_ERROR,
        moves=len(mine),
        blunder_rate=round(rate, 5),
        extrapolated=not FITTED_RANGE[0] <= rate <= FITTED_RANGE[1],
    )
