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

# Resolved from this file, never from the working directory. A relative
# default silenced five claims for as long as they had existed (I-09),
# because every script in this repository runs from its own folder.
_DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_PATH = _DATA / "runs.db"

TABLES = """
CREATE TABLE IF NOT EXISTS run (
    id          INTEGER PRIMARY KEY,
    opening     TEXT    NOT NULL,
    model       TEXT    NOT NULL,
    searcher    TEXT    NOT NULL DEFAULT '',
    started_at  TEXT    NOT NULL,
    -- NULL means the run did not finish. Kept rather than deleted: a run that
    -- died halfway still holds everything it had collected.
    finished_at TEXT,
    -- Set when a person has been through this run, whatever they decided.
    -- **This is not the gate** -- `point.approved` is. A run reviewed with
    -- nothing approved is a real and useful outcome, and it must be
    -- distinguishable from a run nobody has opened.
    --
    -- The column is named `approved` for the same reason it is not renamed: the
    -- store migrates additively, and a history is not worth rewriting over a
    -- word. `RunRow.reviewed` is what the code reads it as.
    approved    INTEGER NOT NULL DEFAULT 0,
    approved_at TEXT
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
    novelty     REAL,
    -- **The gate.** A brief is approved point by point, because a run of five
    -- points routinely has four worth showing and one that is not, and
    -- all-or-nothing forced the author to discard the four to be rid of the one.
    approved    INTEGER NOT NULL DEFAULT 0
);

"""

# Columns added after the first version. `CREATE TABLE IF NOT EXISTS` does
# nothing to a table that already exists, so a store written last week would
# raise "no such column: approved" on the index below -- which is exactly what
# happened. The point of this file is that it accumulates, so it has to survive
# its own schema growing.
ADDED_COLUMNS = (
    ("run", "approved", "INTEGER NOT NULL DEFAULT 0"),
    ("run", "approved_at", "TEXT"),
    ("page", "title", "TEXT NOT NULL DEFAULT ''"),
    ("point", "approved", "INTEGER NOT NULL DEFAULT 0"),
)

INDEXES = """
CREATE INDEX IF NOT EXISTS run_opening   ON run(opening, started_at);
CREATE INDEX IF NOT EXISTS run_approved  ON run(opening, approved, started_at);
CREATE INDEX IF NOT EXISTS page_run      ON page(run_id);
CREATE INDEX IF NOT EXISTS page_domain   ON page(publisher, outcome);
CREATE INDEX IF NOT EXISTS note_run      ON note(run_id);
CREATE INDEX IF NOT EXISTS point_run     ON point(run_id, kind);
CREATE INDEX IF NOT EXISTS point_dropped ON point(kept, dropped_for);
CREATE INDEX IF NOT EXISTS point_approved ON point(run_id, approved);
"""


@dataclass(frozen=True)
class StoredBrief:
    """An approved brief, in the shape a report wants to print."""

    run_id: int
    opening: str
    model: str
    made_on: str
    plans: tuple[str, ...]
    watches: tuple[str, ...]
    sources: tuple[str, ...]

    @property
    def has_points(self) -> bool:
        return bool(self.plans or self.watches)


@dataclass(frozen=True)
class RunRow:
    id: int
    opening: str
    model: str
    started_at: str
    finished_at: str | None
    approved: int
    pages: int
    notes: int
    points_kept: int
    points_approved: int

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    @property
    def reviewed(self) -> bool:
        """Has a person been through this run? Not the same as showing anything."""
        return bool(self.approved)

    @property
    def shows_anything(self) -> bool:
        return self.points_approved > 0


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
        self._db.executescript(TABLES)
        self._migrate()
        self._db.executescript(INDEXES)
        self._db.commit()

    def _migrate(self) -> None:
        """Add columns an older store is missing, leaving its rows alone.

        Only ever additive. A store is a history; dropping or rewriting a column
        would lose the record it exists to keep, so a change that cannot be
        expressed as an added column needs a new table rather than an edit here.
        """
        for table, column, definition in ADDED_COLUMNS:
            existing = {
                row["name"] for row in self._db.execute(f"PRAGMA table_info({table})")
            }
            if existing and column not in existing:
                self._db.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                )

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


    # --- approval, and what a report may read --------------------------------

    def kept_points(self, run_id: int) -> list[sqlite3.Row]:
        """The points a person can choose between, in the order they are shown.

        Only points that survived their own checks: a dropped point is not a
        candidate for approval, so numbering them would invite approving one.
        """
        return list(self._db.execute(
            "SELECT * FROM point WHERE run_id = ? AND kept ORDER BY id", (run_id,)))

    def approve(self, run_id: int, choices=None) -> int:
        """Approve some of a run's points, or all of them.

        `choices` are **1-based positions among the kept points**, as printed by
        `dump_run.py --run N`. One-based because a person is reading a numbered
        list, and only over the kept points because the dropped ones are not on
        offer. Returns how many points were approved.

        An out-of-range choice is ignored rather than raised: this is a person
        typing numbers, and losing the whole command to one typo would be worse
        than silently approving the four that were right.
        """
        points = self.kept_points(run_id)
        if choices is None:
            wanted = points
        else:
            wanted = [points[i - 1] for i in choices if 1 <= i <= len(points)]

        self._db.executemany(
            "UPDATE point SET approved = 1 WHERE id = ?",
            [(p["id"],) for p in wanted],
        )
        self._mark_reviewed(run_id)
        self._db.commit()
        return len(wanted)

    def withdraw(self, run_id: int, choices=None) -> int:
        """Stop showing some points, or all of them. Nothing is deleted."""
        points = self.kept_points(run_id)
        if choices is None:
            wanted = points
        else:
            wanted = [points[i - 1] for i in choices if 1 <= i <= len(points)]

        self._db.executemany(
            "UPDATE point SET approved = 0 WHERE id = ?",
            [(p["id"],) for p in wanted],
        )
        self._db.commit()
        return len(wanted)

    def mark_reviewed(self, run_id: int) -> None:
        """A person read this run and approved nothing. A real outcome.

        Without it, a run judged worthless would stay on the pending list for
        ever and be read again every time.
        """
        self._mark_reviewed(run_id)
        self._db.commit()

    def _mark_reviewed(self, run_id: int) -> None:
        self._db.execute(
            "UPDATE run SET approved = 1, approved_at = ? WHERE id = ?",
            (_now(), run_id),
        )

    def pending(self, limit: int = 20) -> list[RunRow]:
        """Finished runs with points, that nobody has been through yet."""
        return [
            r for r in self.runs(limit=1000)
            if r.finished and not r.reviewed and r.points_kept
        ][:limit]

    def approved_brief(self, opening: str) -> StoredBrief | None:
        """The newest approved brief for this opening, or nothing.

        **Only points a person approved are returned**, one by one. A run where
        four points were approved and one was not shows four; a run where the
        author approved nothing is not a brief at all and returns nothing, the
        same silence the guide library gives for an unreviewed link.

        There is deliberately no age limit. What goes stale is a *link*, and the
        guide library already checks liveness separately; the plans of the Pirc
        do not expire on a calendar. A better model or a dead source is a reason
        to re-run and re-approve, and the calendar is not.
        """
        row = self._db.execute(
            "SELECT r.id, r.model, r.started_at FROM run r"
            " WHERE r.opening = ? AND r.finished_at IS NOT NULL"
            "   AND EXISTS (SELECT 1 FROM point p"
            "               WHERE p.run_id = r.id AND p.approved)"
            " ORDER BY r.started_at DESC, r.id DESC LIMIT 1",
            (opening,),
        ).fetchone()
        if row is None:
            return None

        points = [p for p in self.points(row["id"]) if p["approved"]]
        sources = [
            p["url"] for p in self.pages(row["id"])
            if p["outcome"] == "read" and p["url"]
        ]
        return StoredBrief(
            run_id=row["id"],
            opening=opening,
            model=row["model"],
            made_on=row["started_at"][:10],
            plans=tuple(p["text"] for p in points if p["kind"] == "plan"),
            watches=tuple(p["text"] for p in points if p["kind"] == "watch"),
            sources=tuple(dict.fromkeys(sources)),
        )

    # --- asking questions ---------------------------------------------------

    def runs(self, opening: str | None = None, limit: int = 20) -> list[RunRow]:
        """Most recent first, with the counts a reader wants before drilling in."""
        sql = """
            SELECT r.id, r.opening, r.model, r.started_at, r.finished_at,
                   r.approved,
                   (SELECT COUNT(*) FROM page  p WHERE p.run_id = r.id) AS pages,
                   (SELECT COUNT(*) FROM note  n WHERE n.run_id = r.id) AS notes,
                   (SELECT COUNT(*) FROM point t WHERE t.run_id = r.id AND t.kept)
                       AS points_kept,
                   (SELECT COUNT(*) FROM point t
                     WHERE t.run_id = r.id AND t.approved) AS points_approved
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
