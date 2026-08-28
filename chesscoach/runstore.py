"""What each agent in the swarm did, kept so it can be asked about later.

Design: [[decisions.0016-a-run-store-for-the-swarm]]

Before this, a run cost five fetches and ten model calls and left nothing behind
but a text file written by an experiment script. Running the same opening again
paid the whole bill again, and questions like *"which sites have ever yielded a
usable sentence"* or *"what does the Compiler get dropped for most"* could only be
answered by grepping reports.

**SQLite, from the standard library.** No server, no dependency, one file that
travels with the repository — which matters for an examiner reproducing this
(C1, C7). Readability was explicitly not the priority; being able to ask
questions was, and `dump_run.py` turns any run back into the same text report.

**Written as the run proceeds, not at the end.** Each page is committed when it
is read, so a crash or a rate limit halfway through leaves everything collected
up to that point — which is the failure that actually happens here, given how
often the search engines suspend themselves. A run that never finished is
visible as one with no `finished_at`, rather than as an absence.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path("data/runs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS run (
    id          INTEGER PRIMARY KEY,
    opening     TEXT    NOT NULL,
    model       TEXT    NOT NULL,
    searcher    TEXT    NOT NULL DEFAULT '',
    started_at  TEXT    NOT NULL,
    -- NULL means the run did not finish. Kept rather than deleted: a run that
    -- died halfway still holds everything it had collected.
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS page (
    id          INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES run(id) ON DELETE CASCADE,
    url         TEXT    NOT NULL,
    publisher   TEXT    NOT NULL,
    title       TEXT    NOT NULL DEFAULT '',
    -- 'read', 'skipped' (never fetched), or 'unusable' (fetched, no article).
    outcome     TEXT    NOT NULL,
    skip_reason TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS note (
    id       INTEGER PRIMARY KEY,
    run_id   INTEGER NOT NULL REFERENCES run(id) ON DELETE CASCADE,
    page_id  INTEGER REFERENCES page(id) ON DELETE CASCADE,
    ordinal  INTEGER NOT NULL,
    sentence TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS point (
    id          INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES run(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL,
    ordinal     INTEGER NOT NULL,
    text        TEXT    NOT NULL,
    kept        INTEGER NOT NULL,
    dropped_for TEXT    NOT NULL DEFAULT '',
    novelty     REAL
);

CREATE INDEX IF NOT EXISTS run_opening   ON run(opening, started_at);
CREATE INDEX IF NOT EXISTS page_run      ON page(run_id);
CREATE INDEX IF NOT EXISTS page_domain   ON page(publisher, outcome);
CREATE INDEX IF NOT EXISTS note_run      ON note(run_id);
CREATE INDEX IF NOT EXISTS point_run     ON point(run_id, kind);
CREATE INDEX IF NOT EXISTS point_dropped ON point(kept, dropped_for);
"""


@dataclass(frozen=True)
class RunRow:
    id: int
    opening: str
    model: str
    started_at: str
    finished_at: str | None
    pages: int
    notes: int
    points_kept: int

    @property
    def finished(self) -> bool:
        return self.finished_at is not None


class RunStore:
    """Everything the swarm did, one SQLite file."""

    def __init__(self, path: Path | str = DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        # Write-ahead logging so a reader (dump_run.py) never blocks a running
        # swarm, and a crash leaves a consistent file rather than a truncated one.
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> RunStore:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # --- writing, as the run proceeds ---------------------------------------

    def start_run(self, opening: str, model: str, searcher: str = "") -> int:
        cursor = self._db.execute(
            "INSERT INTO run (opening, model, searcher, started_at) VALUES (?,?,?,?)",
            (opening, model, searcher, _now()),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def record_page(self, run_id: int, url: str, publisher: str, outcome: str,
                    title: str = "", skip_reason: str = "") -> int:
        cursor = self._db.execute(
            "INSERT INTO page (run_id, url, publisher, title, outcome, skip_reason)"
            " VALUES (?,?,?,?,?,?)",
            (run_id, url, publisher, title, outcome, skip_reason),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def record_notes(self, run_id: int, page_id: int | None, sentences) -> None:
        self._db.executemany(
            "INSERT INTO note (run_id, page_id, ordinal, sentence) VALUES (?,?,?,?)",
            [(run_id, page_id, i, s) for i, s in enumerate(sentences)],
        )
        self._db.commit()

    def record_points(self, run_id: int, points) -> None:
        self._db.executemany(
            "INSERT INTO point (run_id, kind, ordinal, text, kept, dropped_for,"
            " novelty) VALUES (?,?,?,?,?,?,?)",
            [
                (run_id, p.kind, i, p.text, int(p.kept), p.dropped_for,
                 None if p.grounding is None else p.grounding.novelty)
                for i, p in enumerate(points)
            ],
        )
        self._db.commit()

    def finish_run(self, run_id: int) -> None:
        self._db.execute("UPDATE run SET finished_at = ? WHERE id = ?",
                         (_now(), run_id))
        self._db.commit()

    # --- asking questions ---------------------------------------------------

    def runs(self, opening: str | None = None, limit: int = 20) -> list[RunRow]:
        """Most recent first, with the counts a reader wants before drilling in."""
        sql = """
            SELECT r.id, r.opening, r.model, r.started_at, r.finished_at,
                   (SELECT COUNT(*) FROM page  p WHERE p.run_id = r.id) AS pages,
                   (SELECT COUNT(*) FROM note  n WHERE n.run_id = r.id) AS notes,
                   (SELECT COUNT(*) FROM point t WHERE t.run_id = r.id AND t.kept)
                       AS points_kept
            FROM run r
        """
        params: list = []
        if opening:
            sql += " WHERE r.opening = ?"
            params.append(opening)
        sql += " ORDER BY r.started_at DESC, r.id DESC LIMIT ?"
        params.append(limit)
        return [RunRow(**dict(row)) for row in self._db.execute(sql, params)]

    def latest(self, opening: str) -> RunRow | None:
        found = self.runs(opening=opening, limit=1)
        return found[0] if found else None

    def pages(self, run_id: int) -> list[sqlite3.Row]:
        return list(self._db.execute(
            "SELECT * FROM page WHERE run_id = ? ORDER BY id", (run_id,)))

    def notes(self, run_id: int) -> list[sqlite3.Row]:
        return list(self._db.execute(
            "SELECT n.*, p.publisher FROM note n LEFT JOIN page p ON p.id = n.page_id"
            " WHERE n.run_id = ? ORDER BY n.id", (run_id,)))

    def points(self, run_id: int) -> list[sqlite3.Row]:
        return list(self._db.execute(
            "SELECT * FROM point WHERE run_id = ? ORDER BY id", (run_id,)))

    def drop_reasons(self, limit: int = 20) -> list[sqlite3.Row]:
        """Why points are lost, across every run. The question tuning needs."""
        return list(self._db.execute(
            "SELECT dropped_for, COUNT(*) AS n FROM point"
            " WHERE NOT kept AND dropped_for <> ''"
            " GROUP BY dropped_for ORDER BY n DESC LIMIT ?", (limit,)))

    def productive_domains(self, limit: int = 20) -> list[sqlite3.Row]:
        """Which publishers actually yield notes, across every run."""
        return list(self._db.execute(
            """
            SELECT p.publisher,
                   COUNT(DISTINCT p.id) AS pages,
                   COUNT(n.id)          AS notes
            FROM page p LEFT JOIN note n ON n.page_id = p.id
            GROUP BY p.publisher
            ORDER BY notes DESC, pages DESC
            LIMIT ?
            """, (limit,)))

    def unfinished(self) -> list[RunRow]:
        return [r for r in self.runs(limit=1000) if not r.finished]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
