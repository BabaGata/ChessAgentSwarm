"""Position evaluation cache, keyed by (position, engine, depth).

Depth belongs in the key rather than in a column. E01 measured that error labels
differ substantially between analysis depths, so treating evaluations from
different depths as interchangeable is a correctness bug -- and a key prevents it
structurally, where a convention would only prevent it while everyone remembers.

Positions recur across a player's games and heavily across players in the
opening, so the cache gets cheaper the more it is used.
See docs/notes/decisions.0007-storage-sqlite-cache-json-profile.md.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

_SCHEMA = """
CREATE TABLE IF NOT EXISTS position_eval (
    fen        TEXT    NOT NULL,
    engine     TEXT    NOT NULL,
    depth      INTEGER NOT NULL,
    score_cp   INTEGER NOT NULL,
    best_move  TEXT,
    is_mate    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (fen, engine, depth)
);
"""


@dataclass(frozen=True)
class PositionEval:
    """An engine's verdict on one position."""

    score_cp: int
    best_move: str | None = None
    is_mate: bool = False


class EvalCache:
    """SQLite-backed store for position evaluations.

    Usable as a context manager. Counts hits and misses so the cost saving is
    measurable rather than assumed.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path))
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.executescript(_SCHEMA)
        self.hits = 0
        self.misses = 0

    def get(self, fen: str, engine: str, depth: int) -> PositionEval | None:
        row = self._connection.execute(
            "SELECT score_cp, best_move, is_mate FROM position_eval"
            " WHERE fen = ? AND engine = ? AND depth = ?",
            (fen, engine, depth),
        ).fetchone()

        if row is None:
            self.misses += 1
            return None

        self.hits += 1
        score_cp, best_move, is_mate = row
        return PositionEval(score_cp=score_cp, best_move=best_move, is_mate=bool(is_mate))

    def put(self, fen: str, engine: str, depth: int, evaluation: PositionEval) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO position_eval"
            " (fen, engine, depth, score_cp, best_move, is_mate) VALUES (?, ?, ?, ?, ?, ?)",
            (
                fen,
                engine,
                depth,
                evaluation.score_cp,
                evaluation.best_move,
                int(evaluation.is_mate),
            ),
        )

    def size(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM position_eval").fetchone()[0]

    def commit(self) -> None:
        self._connection.commit()

    def close(self) -> None:
        self._connection.commit()
        self._connection.close()

    def __enter__(self) -> EvalCache:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
