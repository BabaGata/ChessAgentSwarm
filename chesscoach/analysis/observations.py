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

    @property
    def is_error(self) -> bool:
        return self.label is not None

    @property
    def seconds_spent(self) -> float | None:
        """Time taken on this move, when both clock readings are available."""
        if self.clock_before is None or self.clock_after is None:
            return None
        return max(0.0, self.clock_before - self.clock_after)
