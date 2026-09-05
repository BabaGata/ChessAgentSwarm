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
from chesscoach.domains import (
    CLAIM_DOMAINS,
    DOMAINS,
    EVIDENCE_CLASS,
    PREREQUISITES,
    SOURCE,
    UNMAPPED_ON_PURPOSE,
)
from chesscoach.embedding import DIMENSIONS, embed, embed_all

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
    "CREATE CONSTRAINT domain_key IF NOT EXISTS "
    "FOR (d:Domain) REQUIRE d.key IS UNIQUE",
)


@dataclass(frozen=True)
class Definition:
    """One knowledge-base entry, in the shape the graph stores."""

    key: str
    text: str
    publisher: str
    url: str
    # **Endorsed by the author**, which is what a player may be shown. Loading is
    # not endorsing: an unreviewed entry is still written, so the author can
    # retrieve and inspect it, and `servable` is what keeps it out of a report.
    servable: bool

    @property
    def locator(self) -> str:
        """Traceable to the claim it defines, as a passage is to its book."""
        return f"definition://{self.key}"


def definitions_to_load(base) -> tuple[Definition, ...]:
    """The entries worth putting in the graph, in a stable order.

    `complete` is the gate -- a definition **and** a usable source -- which is
    hard rule 7 read exactly as `Entry` already reads it. An entry with a fine
    sentence and no source is refused here for the same reason it is refused a
    player.
    """
    found = []
    for key in sorted(base.entries):
        entry = base.entries[key]
        if not entry.complete:
            continue
        source = next((s for s in entry.sources if s.usable), None)
        found.append(Definition(
            key=key,
            text=entry.definition,
            publisher=source.publisher if source else "",
            url=source.url if source else "",
            servable=entry.reviewed,
        ))
    return tuple(found)

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

    def _retrievable(self, label: str, node_id: str, text: str) -> None:
        """Give a node the shared label and an embedding, so search reaches it."""
        vector = embed(text)
        self._run(
            f"MATCH (n:{label} {{name: $name}}) "
            "SET n:Knowledge, n.id = $id, n.text = $text "
            "WITH n CALL db.create.setNodeVectorProperty(n, 'embedding', $vector)",
            name=node_id.split("://", 1)[1], id=node_id, text=text, vector=vector,
        )

    def load_definitions(self, base=None) -> int:
        """Put the knowledge base into the graph, so retrieval can reach it.

        Before this, `answer()` searched 1,159 book passages and 12 generated
        rules while the definitions sat in `knowledge.json`, which the retriever
        never reads -- asked *"what is a fork"* it returned an ASCII board
        diagram. Two stores, one of them invisible.

        **Loading is not endorsing.** An entry is written when it is `complete`
        and marked `servable` only when the author has reviewed it, so an
        unreviewed definition is retrievable for inspection and still refused to
        a player by the rule that already governs that.
        """
        if base is None:
            from chesscoach.knowledge import KnowledgeBase

            base = KnowledgeBase.load()

        written = 0
        for definition in definitions_to_load(base):
            self._run(
                "MERGE (d:Definition {name: $name}) "
                "SET d.claim = $claim, d.statement = $statement, "
                "    d.publisher = $publisher, d.url = $url, d.servable = $servable",
                name=definition.key, claim=definition.key, statement=definition.text,
                publisher=definition.publisher, url=definition.url,
                servable=definition.servable,
            )
            self._retrievable("Definition", definition.locator, definition.text)
            written += 1
        return written

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
            self._retrievable(
                "Rule", f"rule://how the {rule.piece} moves",
                f"How the {rule.piece} moves. {rule.description} {rule.special}".strip())
            written += 1

        for rule in outcome_rules():
            self._run(
                "MERGE (r:Rule {name: $name}) "
                "SET r.kind = 'outcome', r.statement = $statement, "
                "    r.provenance = $provenance, r.servable = true",
                name=rule.name, statement=rule.statement,
                provenance=rule.implemented_by,
            )
            self._retrievable("Rule", f"rule://{rule.name}",
                              f"{rule.name}. {rule.statement}")
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
            self._retrievable("TimeControl", f"rule://{rule.name}", rule.statement)
            written += 1

        return written

    # How many passages to embed per request. One at a time is a minute of
    # round trips for the current shelf; all 607 at once is a single request
    # large enough that a failure costs the whole run.
    EMBED_BATCH = 32

    def ensure_vector_index(self) -> None:
        """The index that makes "passages near this question" a query.

        Verified on `neo4j:5-community` 5.26.30 before the design relied on it,
        so the vector half needs no second database.
        """
        # Indexed on the shared `:Knowledge` label, so one query reaches
        # rules and book passages alike. The alternative was a keyword gate in
        # front of retrieval, and the one I wrote answered "what is a backward
        # pawn?" with the rule for how a pawn *moves* -- it matched on the last
        # word of the question. Similarity is a better judge of what a question
        # is about than the last noun in it.
        self._run(
            "CREATE VECTOR INDEX knowledge_embedding IF NOT EXISTS "
            "FOR (k:Knowledge) ON (k.embedding) "
            "OPTIONS {indexConfig: {`vector.dimensions`: $dimensions, "
            "`vector.similarity_function`: 'cosine'}}",
            dimensions=DIMENSIONS,
        )

    def load_passages(self, library, embedder=embed_all) -> int:
        """Every passage on the shelf, with its vector and its citation.

        **No claims are extracted here and that is the stage.** A passage is the
        book's own words, keyed by the `book://slug#index` locator that
        `BookLibrary.all_passages` decides -- so anything retrieved can be quoted
        and attributed, and nothing has been interpreted yet.

        Passages already carrying an embedding are skipped, which makes a second
        run cheap rather than another pass over the whole shelf.
        """
        pending = [
            (book, locator, text)
            for book, locator, text in library.all_passages()
            if text.strip()
        ]
        if not pending:
            return 0

        known = {
            row["id"] for row in self._run(
                "MATCH (p:Passage) WHERE p.embedding IS NOT NULL RETURN p.id AS id")
        }
        pending = [row for row in pending if row[1] not in known]

        for book in {b.slug: b for b, _, _ in pending}.values():
            self._run(
                "MERGE (s:Source {id: $id}) "
                "SET s.title = $title, s.author = $author, s.year = $year, "
                "    s.evidence_class = $evidence_class, "
                # Lineage, not file. Corroboration counts independent voices,
                # and pre-1929 chess books copy each other, so a count over
                # files would measure ancestry rather than agreement.
                #
                # **The author alone, not author-and-year.** A first version
                # keyed on both, which made Edward Lasker's *Chess Strategy*
                # (1915) and *Chess and Checkers* (1918) two independent
                # sources — one man agreeing with himself, counted as
                # corroboration. That is precisely the error this field exists
                # to prevent, arriving through the field itself.
                "    s.lineage = $lineage",
                id=book.slug, title=book.title, author=book.author,
                year=book.year, evidence_class=book.evidence_class,
                lineage=book.author,
            )

        written = 0
        for start in range(0, len(pending), self.EMBED_BATCH):
            batch = pending[start:start + self.EMBED_BATCH]
            vectors = embedder([text for _, _, text in batch])
            for (book, locator, text), vector in zip(batch, vectors):
                self._run(
                    "MERGE (p:Passage {id: $id}) "
                    "SET p:Knowledge, p.text = $text, p.book = $book "
                    "WITH p CALL db.create.setNodeVectorProperty(p, 'embedding', $vector) "
                    "WITH p MATCH (s:Source {id: $book}) MERGE (p)-[:FROM]->(s)",
                    id=locator, text=text, book=book.slug, vector=vector,
                )
                written += 1
        return written

    def search(self, question: str, k: int = 4) -> list[dict]:
        """The passages nearest a question, with what a citation needs.

        Returns the book's own text and its locator, never a summary: at this
        stage the base has read nothing and interpreted nothing, and an answer
        built on this quotes a book or it says nothing.
        """
        vector = embed(question)
        # Over-fetched, because the two kinds of knowledge are wildly unequal in
        # number -- 12 generated rules against 1,159 book passages -- and the
        # rules are short, focused statements that embed strongly for any
        # definitional question. Asked "what is a backward pawn?", the top three
        # were all rules and the answer became a refusal, from a shelf that
        # discusses backward pawns in four voices.
        rows = self._run(
            "CALL db.index.vector.queryNodes('knowledge_embedding', $wide, $vector) "
            "YIELD node, score "
            "OPTIONAL MATCH (node)-[:FROM]->(s:Source) "
            "RETURN node.id AS locator, node.text AS text, score, "
            "       coalesce(s.title, node.kind) AS title, "
            "       coalesce(s.author, node.provenance) AS author, "
            "       coalesce(s.year, '') AS year, "
            # Lineage and embedding, because corroboration is a question about
            # independent voices agreeing and neither can be answered from an
            # author's display name alone.
            "       coalesce(s.lineage, '') AS lineage, "
            "       node.embedding AS embedding, "
            "       'Rule' IN labels(node) OR 'TimeControl' IN labels(node) "
            "         AS generated",
            wide=max(k * 6, 12), vector=vector,
        )
        found = [dict(row) for row in rows]

        # At most half the answer's material may be generated rules, so the
        # books are always heard from when they have anything to say. The cap
        # is a floor on book coverage rather than a preference between them.
        allowed = max(1, k // 2)
        kept: list[dict] = []
        generated = 0
        for row in found:
            if row.get("generated"):
                if generated >= allowed:
                    continue
                generated += 1
            kept.append(row)
            if len(kept) == k:
                break
        return kept

    def load_domains(self) -> int:
        """The ten knowledge domains, what gates what, and where claims land.

        Stage 4 of [[design.graph-knowledge-base]], and the structure
        `chesscoach/arbiter.py` has had a hole for since it was written: it
        refused to rank on prerequisites because *"inventing one would be
        fabricated pedagogy"*. The order exists, sourced, in
        `domain.chess-concepts` § C -- it had simply never been written where
        code could read it.

        **The absent edges are the point.** K9 and K10 are cross-cutting and are
        ordered against nothing, five claim kinds are deliberately unmapped
        because their domain depends on *why* the player did the thing, and each
        of those carries the reason. A graph that answered every question would
        be claiming far more than the note supports.
        """
        written = 0
        for domain in DOMAINS:
            self._run(
                "MERGE (d:Domain {key: $key}) "
                "SET d.name = $name, d.covers = $covers, "
                "    d.source = $source, d.evidence_class = $evidence",
                key=domain.key, name=domain.name, covers=domain.covers,
                source=SOURCE, evidence=EVIDENCE_CLASS,
            )
            written += 1

        for gate, gated in PREREQUISITES:
            self._run(
                "MATCH (a:Domain {key: $gate}), (b:Domain {key: $gated}) "
                "MERGE (a)-[r:PREREQUISITE_OF]->(b) SET r.source = $source",
                gate=gate, gated=gated, source=SOURCE,
            )
            written += 1

        for kind, key in CLAIM_DOMAINS.items():
            self._run(
                "MERGE (c:Claim {key: $kind}) SET c.kind = $kind "
                "WITH c MATCH (d:Domain {key: $domain}) "
                "MERGE (c)-[:BELONGS_TO]->(d)",
                kind=kind, domain=key,
            )
            written += 1

        # Stored **with the reason**, so "nobody decided" and "there is nothing
        # to decide" cannot be confused later by anyone reading the graph.
        for kind, reason in UNMAPPED_ON_PURPOSE.items():
            self._run(
                "MERGE (c:Claim {key: $kind}) "
                "SET c.kind = $kind, c.unmapped_because = $reason",
                kind=kind, reason=reason,
            )
            written += 1

        return written

    def prerequisites_of(self, key: str) -> list[str]:
        """Every domain that gates this one, directly or through a chain."""
        rows = self._run(
            "MATCH (d:Domain {key: $key}) "
            "MATCH (gate:Domain)-[:PREREQUISITE_OF*]->(d) "
            "RETURN DISTINCT gate.key AS key ORDER BY key",
            key=key,
        )
        return [row["key"] for row in rows]

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
