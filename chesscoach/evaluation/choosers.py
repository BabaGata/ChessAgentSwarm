"""Move choosers for planted-weakness generation.

Kept apart from `planted` so the generator itself has no engine dependency and
stays testable with a scripted stub.

The inferior move is chosen as a random legal move that is *not* among the
engine's top choices, rather than as the engine's Nth-best. Nth-best moves are
often nearly as good, which would plant a weakness too subtle to be found; the
point of an evaluation set is that the planted flaw is genuinely there.
"""

from __future__ import annotations

import random
from pathlib import Path
from types import TracebackType

import chess
import chess.engine

# Deliberately shallow: generation plays both sides for many games, and the
# baseline only has to be reasonable, not strong.
DEFAULT_DEPTH = 8

# How many of the engine's preferred moves are excluded when picking a bad one.
AVOID_TOP_N = 3


class EngineMoveChooser:
    """Plays the engine's move, or a deliberately poor legal alternative."""

    def __init__(
        self,
        engine_path: Path | str,
        depth: int = DEFAULT_DEPTH,
        avoid_top_n: int = AVOID_TOP_N,
        threads: int = 1,
        hash_mb: int = 128,
    ) -> None:
        self._engine = chess.engine.SimpleEngine.popen_uci(str(engine_path))
        self._engine.configure({"Threads": threads, "Hash": hash_mb})
        self._limit = chess.engine.Limit(depth=depth)
        self.avoid_top_n = avoid_top_n

    def best(self, board: chess.Board) -> chess.Move:
        info = self._engine.analyse(board, self._limit)
        principal_variation = info.get("pv") or []
        if principal_variation:
            return principal_variation[0]
        return next(iter(board.legal_moves))

    def inferior(self, board: chess.Board, rng: random.Random) -> chess.Move:
        """A legal move the engine did not rank highly."""
        legal = sorted(board.legal_moves, key=lambda move: move.uci())
        if len(legal) == 1:
            return legal[0]

        preferred = self._top_moves(board)
        candidates = [move for move in legal if move not in preferred] or [
            move for move in legal if move != (preferred[0] if preferred else None)
        ]
        return rng.choice(candidates or legal)

    def _top_moves(self, board: chess.Board) -> list[chess.Move]:
        infos = self._engine.analyse(board, self._limit, multipv=self.avoid_top_n)
        if isinstance(infos, dict):  # some engines collapse a single-PV result
            infos = [infos]
        moves = []
        for info in infos:
            principal_variation = info.get("pv") or []
            if principal_variation:
                moves.append(principal_variation[0])
        return moves

    def close(self) -> None:
        self._engine.quit()

    def __enter__(self) -> EngineMoveChooser:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
