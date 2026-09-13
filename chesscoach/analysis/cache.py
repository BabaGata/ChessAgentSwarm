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

import json
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

-- MultiPV results: the engine's few best moves, in its own order.
--
-- A **second table**, not more columns on the one above. That one holds
-- 283,576 rows which must keep working, and the lines are wanted only at error
-- positions -- about 4 % of them -- so widening it would mean a migration for
-- a column null on nearly everything.
--
-- `lines_asked` is in the key because three lines and five lines are different
-- questions. Answering a request for five out of a row that stored three would
-- truncate silently, which is the one failure the completeness check exists to
-- rule out.
CREATE TABLE IF NOT EXISTS position_lines (
    fen         TEXT    NOT NULL,
    engine      TEXT    NOT NULL,
    depth       INTEGER NOT NULL,
    lines_asked INTEGER NOT NULL,
    lines_json  TEXT    NOT NULL,
    PRIMARY KEY (fen, engine, depth, lines_asked)
);
"""


@dataclass(frozen=True)
class PositionEval:
    """An engine's verdict on one position."""

    score_cp: int
    best_move: str | None = None
    is_mate: bool = False


@dataclass(frozen=True)
class Line:
    """One of the engine's candidate moves, with what it evaluates to.

    `score_cp` is from the point of view of the side to move, unlike
    `PositionEval.score_cp`, which is White-relative. The difference is
    deliberate: a candidate list is read to rank *this player's* options, and
    flipping every comparison at the call site is how a sign error gets in.
    """

    uci: str
    score_cp: int
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

    def get_lines(
        self, fen: str, engine: str, depth: int, wanted: int
    ) -> tuple[Line, ...] | None:
        """The stored candidate list, or None if this position has none deep enough.

        **A stored list of `n` answers any request for `n` or fewer**, because
        the top three of five are the top three. It cannot answer a request for
        more: the missing lines might have been the ones that mattered, and
        returning a short list as though it were complete is the truncation the
        whole design is careful about.

        `None` rather than `()`: *"never asked"* and *"the engine returned
        nothing"* are different, and only the first means run the engine.
        """
        row = self._connection.execute(
            "SELECT lines_asked, lines_json FROM position_lines"
            " WHERE fen = ? AND engine = ? AND depth = ? AND lines_asked >= ?"
            " ORDER BY lines_asked ASC LIMIT 1",
            (fen, engine, depth, wanted),
        ).fetchone()

        if row is None:
            self.misses += 1
            return None

        self.hits += 1
        _asked, payload = row
        stored = tuple(
            Line(uci=item["uci"], score_cp=item["score_cp"],
                 is_mate=bool(item.get("is_mate", False)))
            for item in json.loads(payload)
        )
        return stored[:wanted]

    def put_lines(
        self, fen: str, engine: str, depth: int, asked: int, lines: tuple[Line, ...]
    ) -> None:
        payload = json.dumps(
            [{"uci": line.uci, "score_cp": line.score_cp, "is_mate": line.is_mate}
             for line in lines]
        )
        self._connection.execute(
            "INSERT OR REPLACE INTO position_lines"
            " (fen, engine, depth, lines_asked, lines_json) VALUES (?, ?, ?, ?, ?)",
            (fen, engine, depth, asked, payload),
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
