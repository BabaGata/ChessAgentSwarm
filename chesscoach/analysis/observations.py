"""The typed output of the analysis core.

An Observation is one move, measured. Section agents read observations and emit
Findings; nothing else in the system reads raw games. Every observation carries
its own provenance, because evaluations from different depths are not
comparable (E01) and merging them silently is the bug that would follow.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.analysis.labels import ErrorLabel


@dataclass(frozen=True)
class Observation:
    """One played move, with what the engine thought before and after."""

    game_id: str
    ply: int
    mover: str
    mover_is_white: bool
    fen_before: str
    move_played: str
    best_move: str | None
    score_cp_before: int
    score_cp_after: int
    loss_wp: float
    label: ErrorLabel | None
    phase: str
    played_best: bool
    clock_before: float | None
    clock_after: float | None
    engine: str
    depth: int
    # Seconds credited after each move. Needed because `%clk` is written *after*
    # the increment lands, so a bare difference of readings is not what the
    # player spent (D16).
    increment: float = 0.0
    # Who the player was up against, and when. Carried so a citation can be
    # checked: a bare game id sends the reader hunting, and the report is
    # supposed to be evidence rather than a puzzle (D18).
    opponent: str = ""
    played_on: str | None = None

    @property
    def is_error(self) -> bool:
        return self.label is not None

    @property
    def seconds_spent(self) -> float | None:
        """Time taken on this move, when both clock readings are available.

        The increment is added back because `%clk` records the clock **after** it
        is credited: with an increment `i` the reading falls by `spent - i`, so
        the bare difference understates thinking time by exactly `i`. Uncorrected,
        a 3.5 s move on a 180+2 game reads as 1.5 s and counts as instant
        (D16, [[experiments.e44-clock-on-noted-moves]]). 14.7 % of the peer
        corpus carries an increment, so this is a population-level error rather
        than an edge case.
        """
        if self.clock_before is None or self.clock_after is None:
            return None
        return max(0.0, self.clock_before - self.clock_after + self.increment)
