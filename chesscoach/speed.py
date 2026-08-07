"""Which speed a game was played at.

Lichess classifies by **estimated duration** -- the starting clock plus forty
increments -- rather than by the starting clock alone, so 3+2 is blitz and 5+5 is
rapid. Reimplemented here rather than read from the API because the swarm works
from PGN, where only the `TimeControl` tag survives.

Why the swarm needs the answer at all: [[experiments.e19-blitz-stratum]] found
blitz predicts a player's rapid behaviour as well as rapid predicts itself, so
the evidence pools -- but rates still may not be **compared** across speeds
(E01), so every comparison must know which speed it is looking at.
"""

from __future__ import annotations

ULTRA_BULLET = "ultraBullet"
BULLET = "bullet"
BLITZ = "blitz"
RAPID = "rapid"
CLASSICAL = "classical"

# Upper bounds on estimated duration, in seconds, in Lichess's own order.
_BOUNDS: tuple[tuple[float, str], ...] = (
    (30, ULTRA_BULLET),
    (180, BULLET),
    (480, BLITZ),
    (1500, RAPID),
)

# How many increments a game is assumed to last, which is Lichess's convention
# rather than a measurement.
_ASSUMED_MOVES = 40


def estimated_seconds(time_control: str | None) -> float | None:
    """Starting clock plus forty increments, or None if the tag is unreadable.

    Correspondence and unlimited games carry no usable control, and a game the
    swarm cannot place has no speed rather than a guessed one.
    """
    if not time_control or "+" not in time_control:
        return None
    initial, _, increment = time_control.partition("+")
    try:
        return float(initial) + _ASSUMED_MOVES * float(increment)
    except ValueError:
        return None


def speed_class(time_control: str | None) -> str | None:
    """The speed a game belongs to, or None when the control cannot be read."""
    seconds = estimated_seconds(time_control)
    if seconds is None:
        return None
    for bound, name in _BOUNDS:
        if seconds < bound:
            return name
    return CLASSICAL
