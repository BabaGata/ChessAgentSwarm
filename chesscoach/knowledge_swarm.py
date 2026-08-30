"""Scout → Assessor → Compiler, pointed at a detected claim instead of an opening.

Design: docs/notes/design.knowledge-base.md (Option C)

The author chose the swarm to draft the knowledge base and asked that LLM agents
be used as far as they go. This reuses the three agents rather than growing a
fourth: **the `Assessor` is used unchanged** — its prompt takes a topic string,
and a claim name is as good a topic as an opening name — and only the queries
and the final assembly are new.

**The strongest guarantee here is that the definition is not written by a
model.** It is a sentence from the retrieved page, chosen **by index**, exactly
the trick that keeps the Assessor's kept notes verbatim. The model chooses
*which* sentence defines the thing; it never composes the sentence. So the one
field the detector review will be compared against is the source's own words.

What the model does write — `why` and `practice` — is grounded against the kept
notes and dropped when it is not, and `practice` is dropped entirely when
nothing supports it. [[capacity.knowledge]] records that the expertise research
found training-method evidence thin and coaching's value contested, so inventing
practice advice would contradict the project's own knowledge base and produce
exactly the unfalsifiable coaching CLAUDE.md forbids.

**`not_this` is never written here.** The web's definition of a fork is *"one
piece attacks two pieces at once"*, which is precisely what the broken detector
implemented. That field is the author's.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chesscoach import ollama
from chesscoach.grounding import check
from chesscoach.knowledge import Entry, Source
from chesscoach.opening_agent import Gap, SearchUnavailable
from chesscoach.opening_swarm import (
    MODEL,
    Assessor,
    Candidate,
    _detailed,
    _restates,
    _today,
)
from chesscoach.skiplist import SkipList

# How a claim key is said out loud. Only the ones whose names do not survive a
# mechanical de-underscoring: "late_castling" reads fine, "hangingPawn" does not.
TOPICS = {
    "fork": "fork tactic in chess",
    "pin": "pin tactic in chess",
    "skewer": "skewer tactic in chess",
    "hangingPiece": "hanging piece in chess",
    "hangingPawn": "hanging pawn in chess",
    "discoveredAttack": "discovered attack in chess",
    "trappedPiece": "trapped piece in chess",
    "capturingDefender": "capturing the defender in chess",
    "backRankMate": "back rank mate in chess",
    "slow_development": "slow development in the chess opening",
    "late_castling": "castling late in the chess opening",
    "repeat_move": "moving the same piece twice in the chess opening",
    "pawn_error": "pawn moves instead of developing in the chess opening",
    "endgame_error": "endgame technique in chess",
    "moved_into_attack": "moving a piece where it can be attacked in chess",
    "concedes_weakness": "creating a pawn weakness in chess",
    "allows_square": "allowing an outpost square in chess",
    "allows_pressure": "allowing pressure against the king in chess",
}

COMPILER_SCHEMA = ollama.schema_of(
    definition={"type": "integer"},
    why={"type": "string"},
    practice=ollama.array_of("string"),
)

COMPILER = """You are the COMPILER in a chess coaching system.

You are writing one encyclopedia entry about: {topic}

These numbered sentences were taken from real chess pages. They are the ONLY
material you may use. You may not add chess knowledge of your own.

{notes}

Answer as JSON with three fields:

"definition": the NUMBER of the single sentence that says what {topic} actually
is. Choose a number from the list. Do not write a sentence.
If NONE of the sentences says what {topic} is, answer -1. Most pages are about
something else, so -1 is the right answer more often than not. Do not pick the
closest sentence -- a sentence about a different subject is worse than none.

"why": one sentence on what it costs a player who gets this wrong, using only
what the sentences above say. If the sentences do not say, answer "".

"practice": up to {practice} short suggestions for how to practise this, each
supported by the sentences above. If the sentences suggest none, answer with an
empty list. Do not invent training advice."""


def topic_for(key: str) -> str:
    """A searchable phrase for a claim key."""
    if key in TOPICS:
        return TOPICS[key]
    return key.replace("_", " ") + " in chess"


@dataclass
class KnowledgeScout:
    """Finds pages that explain a claim. Judges nothing, fetches nothing.

    Three fixed queries rather than model-written ones. The opening Scout asks a
    model for queries because opening names are many and their phrasings vary;
    a claim has one name and three obvious questions about it, and a generated
    query here could only be worse than the obvious one.
    """

    searcher: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    name: str = "knowledge-scout"

    def __post_init__(self) -> None:
        self.skipped: list[str] = []

    def queries(self, topic: str) -> list[str]:
        return [
            f"what is a {topic}",
            f"why {topic} matters",
            f"how to practise {topic}",
        ]

    def find(self, key: str) -> list[Candidate]:
        topic = topic_for(key)
        found: dict[str, Candidate] = {}
        self.skipped = []
        failures = 0
        for query in self.queries(topic):
            asked = Gap(opening=key, games=0, share=0.0, query_override=query)
            try:
                results = _detailed(self.searcher, asked)
            except SearchUnavailable:
                failures += 1
                continue
            for title, url, publisher, snippet in results:
                if self.skiplist.skips(url):
                    self.skipped.append(publisher)
                    continue
                found.setdefault(url, Candidate(title, url, publisher, snippet))
        # Every query failing is "we could not ask", which must not be returned
        # as "nothing was found" -- L-046, six instances in this project.
        if failures == len(self.queries(topic)) and not found:
            raise SearchUnavailable(f"every query for {key!r} failed")
        return list(found.values())


@dataclass
class KnowledgeCompiler:
    """Assembles one entry. Chooses a definition, writes at most two fields."""

    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    practice: int = 2
    transport: object | None = None
    name: str = "knowledge-compiler"

    def compile(self, key: str, notes: tuple[str, ...],
                sources: tuple[Source, ...]) -> Entry:
        if not notes:
            # Nothing kept means nothing to say. Asking anyway is asking the
            # model what it believes about forks, which is the whole thing R-03
            # forbids.
            return Entry(key=key, drafted_by=self.model, checked_on=_today())

        topic = topic_for(key)
        numbered = "\n".join(f"{i}. {n}" for i, n in enumerate(notes))
        answer = ollama.generate(
            self.model,
            COMPILER.format(topic=topic, notes=numbered, practice=self.practice),
            host=self.host, num_predict=260, schema=COMPILER_SCHEMA,
            transport=self.transport,
        )
        data = ollama.as_json(answer)

        quote = self._quote(data, notes)
        source_text = " ".join(notes)
        why = self._grounded(str((data or {}).get("why", "")).strip(), source_text)
        practice = tuple(
            p for p in ollama.strings(data, "practice")[: self.practice]
            if self._grounded(p, source_text) and not _restates(p, [why] if why else [])
        )

        return Entry(
            key=key,
            # The retrieved sentence IS the definition. A model-written
            # paraphrase is where the precision goes, and precision is the one
            # thing the detector review needs from this field.
            definition=quote,
            quote=quote,
            sources=sources,
            why=why,
            practice=practice,
            drafted_by=self.model,
            checked_on=_today(),
        )

    @staticmethod
    def _quote(data: dict | None, notes: tuple[str, ...]) -> str:
        """The chosen sentence, verbatim, or nothing.

By index, so the definition is the page's own words by construction and
        cannot be something the model composed. Two answers are refused rather
        than repaired, on `ollama.ints`'s contract: an index **outside the list**
        is a hallucination rather than a near miss, and **prose in an integer
        field** is the model ignoring the one instruction that matters here.
        Clamping either would silently pick a sentence nobody chose.

        **-1 means no sentence defines the topic, and it is the important
        answer.** The first live run drafted a "definition" of castling that read
        *"There are two possible moves that place a pawn in the centre of the
        board"* -- a real sentence, verbatim from a real page, about something
        else entirely. Choosing by index guarantees provenance; it cannot
        guarantee relevance, and without a way to say "none of these" the model
        must return the least-bad sentence. A plausible wrong answer where
        "nothing found" was the truth is L-046 with the failure moved from the
        pipeline into the content.
        """
        if not data:
            return ""
        chosen = data.get("definition")
        if isinstance(chosen, bool) or not isinstance(chosen, int):
            return ""
        return notes[chosen] if 0 <= chosen < len(notes) else ""

    @staticmethod
    def _grounded(text: str, source: str) -> str:
        """Model prose, or nothing if the notes do not support it."""
        if not text:
            return ""
        return text if check(text, source).grounded else ""


@dataclass
class KnowledgeSwarm:
    """Scout → Assessor (per page) → Compiler, for one detected claim."""

    searcher: object
    fetch: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    model: str = MODEL
    read: int = 4
    transport: object | None = None

    def __post_init__(self) -> None:
        self.scout = KnowledgeScout(self.searcher, self.skiplist)
        self.assessor = Assessor(model=self.model, transport=self.transport)
        self.compiler = KnowledgeCompiler(model=self.model,
                                          transport=self.transport)

    def draft(self, key: str) -> Entry:
        """One unreviewed entry for one claim.

        Never returns a reviewed entry, and cannot: `Entry` defaults to
        `reviewed=False` and nothing here sets it. Endorsement is the author's
        act alone.
        """
        candidates = self.scout.find(key)
        topic = topic_for(key)

        notes: list[str] = []
        sources: list[Source] = []
        for candidate in candidates[: self.read]:
            body = self._body(candidate)
            if not body:
                continue
            reading = self.assessor.read(topic, candidate, body)
            if reading.skip_reason:
                # A page that is not an article puts its DOMAIN on the skip
                # list, so no model call is ever spent on that site again.
                self.skiplist = self.skiplist.add(
                    candidate.url, reading.skip_reason, "assessor", _today()
                )
            if not reading.useful:
                continue
            notes += list(reading.sentences)
            # A site that has helped can never be skipped later -- the guard
            # that stops the list eating its own sources.
            self.skiplist = self.skiplist.mark_useful(candidate.url)
            sources.append(Source(url=candidate.url, publisher=candidate.publisher,
                                  evidence_class="single-expert"))

        return self.compiler.compile(key, tuple(notes), tuple(sources))

    def _body(self, candidate: Candidate) -> str:
        try:
            return self.fetch(candidate.url) or ""
        except Exception:
            # A page that will not load is one page, not a failed run.
            return ""
