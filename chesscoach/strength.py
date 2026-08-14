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
    """One speed's line, and the error that qualifies it.

    `typical_error` is what the report promises the player, so it must be the
    most pessimistic honest figure available -- and after E27 that means the
    error measured on **players the line was never fitted on**, not the
    cross-validated figure from inside the fitting corpus.
    """

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
#
# **Deliberately left uncorrected**, and it is the control that makes E29's blitz
# correction believable. Rapid's predictor is far less noisy (reliability 0.853
# against blitz's 0.641), so attenuation theory asks for only a 1.17x stretch --
# and the held-out players point the *other* way, demanding 0.63x. Applying the
# correction here degrades MAE from 79 to 111. The remedy helps exactly where the
# predictor is noisy and hurts where it is not, which is what attenuation
# predicts and a blanket "stretching helps" would not.
RAPID_FIT = _Fit(
    intercept=2053.1, slope=-19858.6, typical_error=103, fitted_range=(0.0083, 0.0717)
)

# Refit on the same 84 players' blitz games after step 5 admitted them, because
# applying a rapid line to a blitz corpus was extrapolation the report did not
# admit to (I-04).
#
# **E27 tested that line on 30 players fetched after every constant was frozen
# and it did badly** -- MAE 150 against 157 for guessing the median -- because
# blunder rate is a *noisy* measure of skill at blitz, and noise in a predictor
# shrinks an OLS slope toward zero. It ranked players well (r = +0.83) and
# compressed the scale, so strong players read as much weaker than they are.
#
# **Corrected in E29 by the standard remedy for regression dilution**: divide the
# slope by the predictor's reliability, and rotate about the fitting data's
# centroid so the line still passes through it.
#
#   reliability   0.641   split-half by game, Spearman-Brown, **fitting corpus only**
#   correction    1.56x
#
# The evidence that this was the right diagnosis is that the correction factor
# and the held-out data were computed from **different data and agree**: the 30
# held-out players independently demand a 1.48x stretch. On them the corrected
# line scores **MAE 129 against the shipped line's 149**, with the bias narrowing
# from -111 to -97 and estimates within 200 points rising from 75 % to 88 %.
#
# Still the weaker reading, and still worth saying so: 129 against 148 for
# guessing the band's median is an improvement, not a good rating estimate.
BLITZ_FIT = _Fit(
    intercept=2000.6, slope=-18791.9, typical_error=129, fitted_range=(0.0090, 0.0607)
)

# Held-out mean signed error after the correction (E29, was -88 before it): the
# estimate still reads a stranger as this many points weaker than they are.
# Reported rather than subtracted -- an offset read off the validation set is the
# fitting-to-your-test-set error the correction was careful to avoid.
BLITZ_BIAS = -97

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
