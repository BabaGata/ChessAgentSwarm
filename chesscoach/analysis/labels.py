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
INACCURACY_WP = 10.0
MISTAKE_WP = 20.0
BLUNDER_WP = 30.0

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
