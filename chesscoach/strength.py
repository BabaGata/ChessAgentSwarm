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

@dataclass(frozen=True)
class _Fit:
    """One speed's line, and the held-out error that qualifies it."""

    intercept: float
    slope: float
    typical_error: int
    fitted_range: tuple[float, float]

    def rating(self, blunder_rate: float) -> int:
        return round(self.intercept + self.slope * blunder_rate)

    def extrapolating(self, blunder_rate: float) -> bool:
        low, high = self.fitted_range
        return not low <= blunder_rate <= high


# Fitted on the 84-player E13 corpus, whose games were rapid and classical, so
# the same line serves both. Refit with `experiments/e13-strength-signal/run.py`.
RAPID_FIT = _Fit(
    intercept=2053.1, slope=-19858.6, typical_error=103, fitted_range=(0.0083, 0.0717)
)

# Refit on the same 84 players' blitz games after step 5 admitted them, because
# applying a rapid line to a blitz corpus was extrapolation the report did not
# admit to (I-04). **Blitz is genuinely harder to read**: held-out error 123
# against rapid's 103, and the line is much flatter -- blunder rate discriminates
# less when everyone is rushing. Still well clear of the 141 that guessing the
# median scores, which is the bar a feature has to beat to be an estimator at all.
BLITZ_FIT = _Fit(
    intercept=1841.3, slope=-12045.1, typical_error=123, fitted_range=(0.0090, 0.0607)
)

# Speeds with a fit. Bullet has none and is not fetched; if one ever arrives, no
# estimate is the honest answer rather than the nearest line.
FITS: dict[str, _Fit] = {
    "classical": RAPID_FIT,
    "rapid": RAPID_FIT,
    "blitz": BLITZ_FIT,
}

# Below this the rate is too noisy to turn into a rating. One blunder in 80 moves
# and one in 90 are the same player; the arithmetic would put 250 points between
# them. Counted **within one speed**, not across the corpus -- see `estimate`.
MIN_MOVES = 200


@dataclass(frozen=True)
class StrengthEstimate:
    """What the player's own moves suggest, and how far that can be trusted."""

    rating: int
    typical_error: int
    moves: int
    blunder_rate: float
    extrapolated: bool
    speed: str

    @property
    def range(self) -> tuple[int, int]:
        """The band most players of this measured standard actually fall in."""
        return self.rating - self.typical_error, self.rating + self.typical_error


def estimate(
    observations: tuple[Observation, ...],
    username: str,
    speeds: dict[str, str] | None = None,
) -> StrengthEstimate | None:
    """The player's standard **at one speed**, or None if no speed carries enough.

    `speeds` maps game id to speed class. Without it every move is treated as
    rapid, which is what the corpus was before step 5 pooled the speeds.

    **Deliberately one speed rather than a blend.** A player with half their
    games at each has *two* ratings roughly 80 points apart (E19), so a blended
    number estimates a quantity that does not exist. The dominant speed is used
    and named, and `MIN_MOVES` applies within it -- which is stricter than
    before, and silences a genuinely mixed player with a thin corpus rather than
    handing them an average of two scales.
    """
    mine = diagnosable(
        tuple(o for o in observations if o.mover.lower() == username.lower())
    )
    if not mine:
        return None

    by_speed: dict[str, list[Observation]] = {}
    for observation in mine:
        speed = (speeds or {}).get(observation.game_id, "rapid")
        if speed in FITS:
            by_speed.setdefault(speed, []).append(observation)
    if not by_speed:
        return None

    speed, moves = max(by_speed.items(), key=lambda pair: (len(pair[1]), pair[0]))
    if len(moves) < MIN_MOVES:
        return None

    fit = FITS[speed]
    rate = sum(1 for o in moves if o.label is ErrorLabel.BLUNDER) / len(moves)

    return StrengthEstimate(
        rating=fit.rating(rate),
        typical_error=fit.typical_error,
        moves=len(moves),
        blunder_rate=round(rate, 5),
        extrapolated=fit.extrapolating(rate),
        speed=speed,
    )
