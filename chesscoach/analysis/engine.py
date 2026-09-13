"""Stockfish, driven through python-chess, behind the cache.

Settings follow E01's measurements: depth 15 for routine analysis, and **one
thread per engine**. Extra threads made fixed-depth search slower, because they
widen the search rather than reaching the target depth sooner; cores are far
better spent on more positions at once.

The cache sits in front of the engine rather than beside it, so callers cannot
accidentally bypass it and lose reproducibility.
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType

import chess
import chess.engine

from chesscoach.analysis.cache import EvalCache, Line, PositionEval
from chesscoach.analysis.labels import CLAMP_CP

DEFAULT_DEPTH = 15
DEFAULT_HASH_MB = 256
DEFAULT_THREADS = 1


def to_position_eval(info: dict) -> PositionEval:
    """Convert an engine info dict into a White-relative, clamped evaluation.

    Kept separate from the engine so it can be tested without one — and because
    the mate case is exactly where the arithmetic goes wrong if it is not:
    Stockfish encodes mate as roughly +-30000, which turns a mate-delivering
    move into an enormous apparent *loss* unless it is clamped (lesson L-005).
    """
    score = info["score"].white()
    principal_variation = info.get("pv") or []
    best_move = principal_variation[0].uci() if principal_variation else None

    if score.is_mate():
        mate_in = score.mate() or 0
        return PositionEval(
            score_cp=CLAMP_CP if mate_in > 0 else -CLAMP_CP,
            best_move=best_move,
            is_mate=True,
        )

    raw = score.score() or 0
    return PositionEval(
        score_cp=max(-CLAMP_CP, min(CLAMP_CP, raw)), best_move=best_move, is_mate=False
    )


class StockfishAnalyser:
    """Evaluates positions at a fixed depth, caching every result.

    Depth is fixed for the analyser's lifetime on purpose: it is part of the
    cache key and of every finding's provenance, and mixing depths within one
    analysis is the error the design is built to make impossible.
    """

    def __init__(
        self,
        engine_path: Path | str,
        depth: int = DEFAULT_DEPTH,
        cache: EvalCache | None = None,
        hash_mb: int = DEFAULT_HASH_MB,
        threads: int = DEFAULT_THREADS,
    ) -> None:
        if depth <= 0:
            raise ValueError(f"depth must be positive, got {depth}")

        self.depth = depth
        self.cache = cache
        self._engine = chess.engine.SimpleEngine.popen_uci(str(engine_path))
        self._engine.configure({"Threads": threads, "Hash": hash_mb})
        self._limit = chess.engine.Limit(depth=depth)
        self.engine_name = self._engine.id.get("name", "unknown engine")

    def analyse(self, board: chess.Board) -> PositionEval:
        """Evaluate a position, consulting the cache first."""
        fen = board.fen()
        if self.cache is not None:
            cached = self.cache.get(fen, self.engine_name, self.depth)
            if cached is not None:
                return cached

        evaluation = self._analyse_uncached(board)
        if self.cache is not None:
            self.cache.put(fen, self.engine_name, self.depth, evaluation)
        return evaluation

    def _analyse_uncached(self, board: chess.Board) -> PositionEval:
        return to_position_eval(self._engine.analyse(board, self._limit))

    def lines(self, board: chess.Board, wanted: int) -> tuple[Line, ...]:
        """The engine's `wanted` best moves here, in its own order, cached.

        **Scores are from the side to move**, unlike `PositionEval.score_cp`
        which is White-relative. A candidate list is read to rank *this
        player's* options, and flipping the comparison at every call site is how
        a sign error gets in.

        Mate is clamped the same way `to_position_eval` clamps it, and for the
        same reason: Stockfish encodes it near +-30000, which turns the move
        that delivers it into an enormous apparent loss (L-005).

        The cache is asked with the same `(fen, engine, depth)` key plus the
        number of lines, because three lines and five are different questions.
        """
        fen = board.fen()
        if self.cache is not None:
            stored = self.cache.get_lines(fen, self.engine_name, self.depth, wanted)
            if stored is not None:
                return stored

        infos = self._engine.analyse(board, self._limit, multipv=wanted)
        if isinstance(infos, dict):  # an engine may collapse a single-PV result
            infos = [infos]

        found = []
        for info in infos:
            variation = info.get("pv") or []
            if not variation:
                continue
            score = info["score"].pov(board.turn)
            if score.is_mate():
                ahead = (score.mate() or 0) > 0
                found.append(Line(uci=variation[0].uci(),
                                  score_cp=CLAMP_CP if ahead else -CLAMP_CP,
                                  is_mate=True))
            else:
                raw = score.score() or 0
                found.append(Line(uci=variation[0].uci(),
                                  score_cp=max(-CLAMP_CP, min(CLAMP_CP, raw)),
                                  is_mate=False))

        lines = tuple(found)
        if self.cache is not None:
            self.cache.put_lines(fen, self.engine_name, self.depth, wanted, lines)
        return lines

    def close(self) -> None:
        self._engine.quit()

    def __enter__(self) -> StockfishAnalyser:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
