"""Error classification for played moves.

Two decisions here were bought with measurements rather than taste, and both are
recorded in docs/notes/learning.lessons.md:

  * losses are measured in **win-probability points**, not centipawns (L-005).
    Losing 100cp at equality can decide a game; losing 100cp at +900 is
    irrelevant, yet a fixed centipawn threshold labels both the same;
  * a move matching the engine's own choice scores **zero** loss, and
    evaluations are clamped before differencing. Without this, mate-delivering
    moves register as enormous losses, because mate is encoded as +-30000.
"""

from __future__ import annotations

import math
from enum import Enum

# Evaluations are clamped before differencing so a forced mate cannot produce a
# meaningless loss.
CLAMP_CP = 1000

# Thresholds in win-probability points. Provisional project values, not a
# standard -- see docs/notes/architecture.confidence.md.
#
# Lowered from 10.0 on 2026-08-16, screened in [[experiments.e33-error-threshold]]
# across four values on twelve players. What it buys, measured against a strong
# club player's own game-by-game annotation of 106 moves:
#
#                       moves called    reviewer notes   reviewer notes
#     INACCURACY_WP        an error         DETECTED          NAMED
#             10.0            9.0 %            58 %            28 %
#              5.0           19.2 %            78 %            38 %
#              3.0           27.8 %            89 %            42 %
#
# The expected failure -- claims flooding with cheap errors until they stop
# separating players -- did not occur: at 5.0 four of five watched claims reach
# their *best* p90/median spread of any threshold tested. 3.0 buys 11 more points
# of detection for a quarter of all moves being errors and the sharpest dilution
# of cost per error, so 5.0 is where the evidence stops rather than where it runs
# out.
#
# The reviewer's median noticed mistake cost 8.9 wp. A floor above that was
# discarding most of what a strong player sees, by construction.
INACCURACY_WP = 5.0

# Scaled with the floor rather than left at 20 so the bands stay evenly spaced;
# this is the value E33 screened. The boundary is close to **cosmetic**: every
# measurement in the swarm turns on `label is not None`, and only the printed
# word changes here.
MISTAKE_WP = 17.5
BLUNDER_WP = 30.0

# What `INACCURACY_WP` was when the progress check's no-change constant was
# fitted. E05 measured `NO_CHANGE_RATIO = 0.58` from 57 predictions across 84
# players, cross-validated at 2 and 5 folds -- all of it at a 10 wp floor.
#
# Change the floor and that constant describes a different quantity: rates are
# built from different moves, and the regression it corrects for has a different
# size. The refit needs the 84-player corpus, which is deliberately not committed
# (data is regenerable), so it is **outstanding** rather than done.
#
# This constant exists so the gap cannot be forgotten: `progress.py` states it in
# its own output rather than quietly reporting a verdict calibrated for a floor
# the analysis no longer uses.
NO_CHANGE_RATIO_FITTED_AT_WP = 10.0


def calibration_is_stale() -> bool:
    """Is the progress check's constant fitted for the floor now in use?"""
    return INACCURACY_WP != NO_CHANGE_RATIO_FITTED_AT_WP

# Lichess' centipawn -> win-percentage conversion constant.
_WP_SCALE = 0.00368208


class ErrorLabel(str, Enum):
    """How costly a move was, relative to what was available."""

    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"


def win_probability(cp: int | float) -> float:
    """Expected score, 0-100, for the side the evaluation favours."""
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-_WP_SCALE * cp)) - 1.0)


def clamp_cp(cp: int) -> int:
    """Bound an evaluation so mate scores cannot dominate arithmetic."""
    return max(-CLAMP_CP, min(CLAMP_CP, cp))


def classify(loss_wp: float) -> ErrorLabel | None:
    """Label a loss, or None when the move was good enough."""
    if loss_wp >= BLUNDER_WP:
        return ErrorLabel.BLUNDER
    if loss_wp >= MISTAKE_WP:
        return ErrorLabel.MISTAKE
    if loss_wp >= INACCURACY_WP:
        return ErrorLabel.INACCURACY
    return None


def move_loss_wp(
    *, before_cp: int, after_cp: int, mover_is_white: bool, played_best: bool
) -> float:
    """Win-probability points the mover gave away by playing this move.

    Evaluations are White-relative; the loss is computed from the mover's point
    of view. A move that improves the position is not a loss.
    """
    if played_best:
        return 0.0

    before, after = clamp_cp(before_cp), clamp_cp(after_cp)
    if not mover_is_white:
        before, after = -before, -after

    return max(0.0, win_probability(before) - win_probability(after))
