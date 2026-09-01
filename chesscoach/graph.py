"""The graph knowledge base: connection, schema, and the stage-1 loader.

Design: docs/notes/design.graph-knowledge-base.md

**Neo4j is a derived index, never the source of truth.** Every node here is built
from a file this repository versions or from the code itself, so the database can
be wiped and rebuilt and nothing is lost. That is what makes the review gate
survivable: knowledge cannot be authored *in* the database, because the loader is
the only writer and it only reads files.

Two consequences run through this module:

* **loading is idempotent** -- `MERGE`, never `CREATE`, so running the loader
  twice leaves what running it once left, and rebuilding is an ordinary
  operation rather than a careful one;
* **the address is configuration** -- the engine is already a path argument and
  Ollama's host is already a parameter, and Neo4j joins them, so the topology is
  a deployment choice rather than something the code believes.

Stage 1 loads only what needs no sourcing: the rules of chess, generated from
`python-chess`, and the Lichess speeds, read from the classifier that decides
them. Concepts, passages and corroboration come later and under a different
evidence rule.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import TracebackType

from chesscoach.chess_rules import movement_rules, outcome_rules, time_control_rules

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "chesscoach"
DEFAULT_DATABASE = "neo4j"


class GraphUnavailable(RuntimeError):
    """The database could not be reached.

    **Raised, never swallowed into an empty result.** A knowledge base that
    answers "I found nothing" when it is simply not running is the empty case
    answering exactly like a populated one, which is the failure this project has
    recorded eight times (L-046). A caller that wants to degrade gracefully
    catches this; nothing may confuse it with silence.
    """


@dataclass(frozen=True)
class Settings:
    """Where the graph lives and who we are to it."""

    uri: str = DEFAULT_URI
    user: str = DEFAULT_USER
    # `repr=False`: a connection failure prints its settings, and a password in
    # a log is a password in a bug report.
    password: str = field(default=DEFAULT_PASSWORD, repr=False)
    database: str = DEFAULT_DATABASE


def settings_from_env(environ: dict[str, str] | None = None) -> Settings:
    """Read the address from the environment, falling back to the local container."""
    source = os.environ if environ is None else environ
    return Settings(
        uri=source.get("NEO4J_URI", DEFAULT_URI),
        user=source.get("NEO4J_USER", DEFAULT_USER),
        password=source.get("NEO4J_PASSWORD", DEFAULT_PASSWORD),
        database=source.get("NEO4J_DATABASE", DEFAULT_DATABASE),
    )


# Uniqueness, so a second load updates a node rather than adding a twin. These
# are what make `MERGE` idempotent in practice as well as in intent.
_CONSTRAINTS = (
    "CREATE CONSTRAINT rule_name IF NOT EXISTS "
    "FOR (r:Rule) REQUIRE r.name IS UNIQUE",
    "CREATE CONSTRAINT timecontrol_name IF NOT EXISTS "
    "FOR (t:TimeControl) REQUIRE t.name IS UNIQUE",
    "CREATE CONSTRAINT concept_name IF NOT EXISTS "
    "FOR (c:Concept) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT claim_key IF NOT EXISTS "
    "FOR (c:Claim) REQUIRE c.key IS UNIQUE",
    "CREATE CONSTRAINT opening_pgn IF NOT EXISTS "
    "FOR (o:Opening) REQUIRE o.pgn IS UNIQUE",
    "CREATE CONSTRAINT source_id IF NOT EXISTS "
    "FOR (s:Source) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT passage_id IF NOT EXISTS "
    "FOR (p:Passage) REQUIRE p.id IS UNIQUE",
)


class GraphStore:
    """A connection to the graph, and the only thing that writes to it."""

    def __init__(self, driver, database: str) -> None:
        self._driver = driver
        self._database = database

    @classmethod
    def connect(cls, settings: Settings | None = None) -> GraphStore:
        """Open a verified connection, or raise `GraphUnavailable`.

        The connectivity check is not optional politeness: the driver connects
        lazily, so without it the first real query fails somewhere far from the
        cause, and "the container is not running" reads as a query bug.
        """
        settings = settings or settings_from_env()
        try:
            from neo4j import GraphDatabase
            from neo4j.exceptions import Neo4jError, ServiceUnavailable
        except ImportError as error:  # pragma: no cover - dependency missing
            raise GraphUnavailable(f"the neo4j driver is not installed: {error}") from error

        try:
            driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))
            driver.verify_connectivity()
        except (ServiceUnavailable, Neo4jError, OSError, ValueError) as error:
            raise GraphUnavailable(f"{settings.uri}: {error}") from error
        return cls(driver, settings.database)

    def close(self) -> None:
        self._driver.close()

    def __enter__(self) -> GraphStore:
        return self

    def __exit__(self, kind: type[BaseException] | None, value: BaseException | None,
                 traceback: TracebackType | None) -> None:
        self.close()

    def _run(self, query: str, **parameters):
        with self._driver.session(database=self._database) as session:
            return list(session.run(query, **parameters))

    def ensure_schema(self) -> None:
        """Apply the uniqueness constraints. Safe to run repeatedly."""
        for statement in _CONSTRAINTS:
            self._run(statement)

    def load_rules(self) -> int:
        """Load the rules layer: movement, outcomes, and the Lichess speeds.

        Everything written here is generated or read from code, so this loader
        needs no review gate. It is stage 1 precisely because of that.
        """
        written = 0

        for rule in movement_rules():
            self._run(
                "MERGE (r:Rule {name: $name}) "
                "SET r.kind = 'movement', r.piece = $piece, r.symbol = $symbol, "
                "    r.statement = $statement, r.special = $special, "
                "    r.attacks_from_centre = $attacks, r.provenance = $provenance, "
                "    r.servable = true",
                name=f"how the {rule.piece} moves", piece=rule.piece,
                symbol=rule.symbol, statement=rule.description,
                special=rule.special, attacks=list(rule.attacks_from_centre),
                provenance=rule.generated_by,
            )
            written += 1

        for rule in outcome_rules():
            self._run(
                "MERGE (r:Rule {name: $name}) "
                "SET r.kind = 'outcome', r.statement = $statement, "
                "    r.provenance = $provenance, r.servable = true",
                name=rule.name, statement=rule.statement,
                provenance=rule.implemented_by,
            )
            written += 1

        for rule in time_control_rules():
            self._run(
                "MERGE (t:TimeControl {name: $name}) "
                "SET t.statement = $statement, t.upper_seconds = $upper, "
                "    t.examples = $examples, t.provenance = $provenance, "
                "    t.servable = true",
                name=rule.name, statement=rule.statement,
                upper=rule.upper_seconds, examples=list(rule.examples),
                provenance=rule.implemented_by,
            )
            written += 1

        return written

    def counts(self) -> dict[str, int]:
        """How many nodes of each label. The cheapest check that a load worked."""
        rows = self._run(
            "MATCH (n) UNWIND labels(n) AS label "
            "RETURN label, count(*) AS n ORDER BY label"
        )
        return {row["label"]: row["n"] for row in rows}

    def rule_about(self, subject: str) -> dict | None:
        """One rule, by piece or by name, or None.

        **None rather than a guess.** A knowledge base that returns its nearest
        node for an unknown subject is how a small model ends up confidently
        answering a question nobody has the answer to.
        """
        rows = self._run(
            "MATCH (r:Rule) "
            "WHERE r.servable AND (toLower(r.piece) = toLower($subject) "
            "                      OR toLower(r.name) = toLower($subject)) "
            "RETURN r LIMIT 1",
            subject=subject,
        )
        return dict(rows[0]["r"]) if rows else None

    def wipe(self) -> None:
        """Delete every node. Safe because nothing is authored here.

        The loader rebuilds from files, so this is an ordinary operation rather
        than a destructive one -- which is the practical benefit of the
        derived-index decision.
        """
        self._run("MATCH (n) DETACH DELETE n")
