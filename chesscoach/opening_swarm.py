"""Three agents that turn an opening name into a brief a player can act on.

Design: [[decisions.0014-three-agents-for-the-opening-brief]], revised by
[[decisions.0015-a-learned-skip-list-and-a-bullet-brief]].

    SCOUT      searches, and never fetches what the skip list already refuses
    ASSESSOR   reads the TEXT, keeps the sentences that matter, and adds
               unusable sites to the skip list
    COMPILER   turns what survived into bullet points

Each has one job, one prompt stating its role, and a failure mode it must not
have. The separation is load-bearing: an agent that both searched and judged
would have no reason to discard its own results, and one that both judged and
wrote could quietly replace a weak source with its own knowledge.

**The Assessor works on sentences, not on titles.** The first design had it
judging search results from a title and a domain: that measured 10/12 against a
person, rejected genuine guides, and spent a model call to conclude that TikTok
hosts videos. The cheap permanent judgement is now a **deterministic skip list**
the Assessor maintains, and the model's attention goes where only a reader helps
— deciding which of a page's sentences say something a player can use.

**The brief is bullet points, not prose.** Each point is checked on its own, so
one bad point is dropped instead of a whole paragraph, and the agent that finally
speaks to the player joins the points into sentences alongside everything else it
knows about that player.

**Every chess claim still traces to a fetched page.** The Compiler works only
from sentences the Assessor kept, which are verbatim, and every bullet is checked
by `grounding.check` before it survives. The models decide *which text* and
*which words*, never *what is true about chess*.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from chesscoach import ollama
from chesscoach.grounding import Grounding, check, overlap
from chesscoach.opening_agent import Gap
from chesscoach.opening_plans import (
    MAX_WORDS,
    MIN_WORDS,
    is_usable_note,
    names_a_target,
    text_blocks,
)
from chesscoach.runstore import RunStore
from chesscoach.skiplist import REASONS, SkipList, domain_of

MODEL = "qwen2.5:3b"

# Above this share of shared content words, a WATCH point is a PLAN point said
# again. Measured on a real run: the Pirc brief's opponent half was its plan with
# the colour flipped and passed the grounding check, because every word was the
# source's. The checker cannot see a restatement; this can.
MAX_RESTATEMENT = 0.60

# The brief has two halves, so the search needs two angles.
OPPONENT_QUERY = "how to play against the {opening} main responses"

# Sentences offered in ONE question. Measured, not guessed: handed 50 numbered
# sentences, qwen2.5:3b answered NONE on four pages of six; at 25 it answers with
# indices. So a long article is asked about in chunks rather than truncated, and
# the whole page is read instead of its first fifty sentences.
CHUNK = 25

# Sentences taken from any one chunk, and from any one page. The page cap bounds
# cost; the chunk cap stops one dense paragraph filling the brief.
PER_CHUNK = 4
PER_PAGE = 6

# A page with fewer readable words than this is not an article: a video page, a
# paywall, or a fetch that returned a shell.
MIN_PAGE_WORDS = 120


# --- the Scout ---------------------------------------------------------------

SCOUT = """You are the SCOUT in a chess coaching system.

YOUR ROLE
You find web pages that teach the PLANS of a chess opening to a club player \
rated about 1500. You do NOT judge whether a page is good — a different agent \
does that, and it can only judge what you bring it. Your job is to cast a wide \
net with well-formed queries.

HOW TO WRITE A SEARCH QUERY
- 3 to 6 words, lowercase, no punctuation, no colons
- name the opening, then words like: plans, ideas, strategy, middlegame, \
typical plans, how to play
- vary the angle: one about the player's plans, one about the middlegame, one \
about what the opponent does
- a query is not a title and not a sentence

Opening: {opening}
{tried}
Write {count} different search queries, one per line. Nothing else.
"""

# --- the Assessor ------------------------------------------------------------

ASSESSOR = """You are the ASSESSOR in a chess coaching system.

YOUR ROLE
You read one web page and pick the sentences that carry the most information about how this opening is played. A later agent turns what you pick into a short brief for the player, so **more material is better than less** — you are choosing the richest sentences, not deciding whether the page is good enough.

Do NOT reject a sentence for being hard to read or for using a term a beginner would not know. The next agent rewrites it in plain words, and it cannot rewrite what you did not pass on.

The most informative sentences say:
- what a side aims for, or the plan
- where the pieces belong, or which pawn break to play
- what the OPPONENT does, and what to be ready for
- what kind of position each side is trying to reach

A sentence carries no information about how the opening is PLAYED if it is:
- a win rate, a rating, or how often a move is chosen
- who has played the opening, or when it was invented
- a comment someone left, or a list of tags
Never pick one of those, however confident it sounds.

Sentences from a page about the {opening}:
{sentences}

Pick the {limit} most informative, best first, and answer with ONLY their numbers separated by commas.
Answer NONE only if the page is not about chess at all.
"""

UNUSABLE = """You are the ASSESSOR in a chess coaching system.

This page could not be read as an article. Say what kind of site it is, so the \
system stops fetching pages from it.

Site: {domain}
Title: {title}
What was found: {found}

Answer with ONE word from this list: {reasons}
If it looks like an ordinary article that simply failed to load, answer NONE.
"""

# --- the Compiler ------------------------------------------------------------

COMPILER = """You are the COMPILER in a chess coaching system.

YOUR ROLE
You turn approved notes into short bullet points. Another agent joins your \
points into sentences for the player later, so do NOT write paragraphs, \
introductions or conclusions — only the points.

You work ONLY from the notes below. You must NOT add chess knowledge of your \
own: a check compares each point against these notes and throws away any point \
naming a square, a move or an idea they do not contain.

Do not change who does what. If a note says White does something, do not write \
that Black does it.

Write up to {plans} points on what the player should aim for, then up to \
{watches} points on what the opponent will try. Use exactly these labels:

PLAN: <one short point>
WATCH: <one short point>

One line each. No move numbers.

EVERY point must name a square, a pawn or a piece move — d4, e5, c5, Nf3, the
e1-h4 diagonal. A point like "develop in harmony and prepare for counterplay"
names nothing a player can do and is worthless; "develop the light-squared bishop
to d3 or e2" is a point. If a note is too vague to anchor to a square, leave it
out rather than repeating its vague words.

The notes are written for stronger players and may use terms a club player would \
have to look up — "Maroczy bind", "prophylaxis", "minority attack". Do not \
repeat those terms. Say what they MEAN in plain words, using the rest of the \
note to work out what is happening on the board. Making the notes understandable \
is your job; nobody after you will do it.

If the notes say nothing about what the opponent does, write no WATCH lines at \
all — that is correct, not a failure.

Notes about the {opening}:
{notes}
"""


@dataclass(frozen=True)
class Candidate:
    title: str
    url: str
    publisher: str
    snippet: str = ""


@dataclass(frozen=True)
class Reading:
    """What the Assessor made of one page."""

    candidate: Candidate
    sentences: tuple[str, ...]
    # Set only when the page was not an article, and names why the domain should
    # be skipped from now on.
    skip_reason: str = ""

    @property
    def useful(self) -> bool:
        return bool(self.sentences)


@dataclass(frozen=True)
class Point:
    """One bullet, and whether it survived its own check."""

    text: str
    kind: str  # "plan" or "watch"
    grounding: Grounding | None = None
    dropped_for: str = ""

    @property
    def kept(self) -> bool:
        return not self.dropped_for


@dataclass(frozen=True)
class Brief:
    """What a player would be told, as points, with everything to argue with."""

    opening: str
    points: tuple[Point, ...] = ()
    sources: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def of(self, kind: str) -> tuple[str, ...]:
        return tuple(p.text for p in self.points if p.kind == kind and p.kept)

    @property
    def plans(self) -> tuple[str, ...]:
        return self.of("plan")

    @property
    def watches(self) -> tuple[str, ...]:
        return self.of("watch")

    @property
    def dropped(self) -> tuple[Point, ...]:
        return tuple(p for p in self.points if not p.kept)

    @property
    def accepted(self) -> bool:
        """A brief with no plan points is not a brief. WATCH is a bonus."""
        return bool(self.plans)


@dataclass
class Scout:
    """Searches and hands over candidates. Judges nothing, fetches nothing."""

    searcher: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    queries: int = 3
    transport: object | None = None
    name: str = "scout"

    def __post_init__(self) -> None:
        self.skipped: list[str] = []

    def propose(self, opening: str, tried: tuple[str, ...] = ()) -> list[str]:
        seen = ("Already tried, do not repeat:\n"
                + "\n".join(f"- {t}" for t in tried) + "\n") if tried else ""
        answer = ollama.generate(
            self.model,
            SCOUT.format(opening=opening, tried=seen, count=self.queries),
            host=self.host, num_predict=120, temperature=0.7,
            transport=self.transport,
        )
        return _queries(answer, self.queries)

    def find(self, opening: str) -> list[Candidate]:
        """Distinct pages worth fetching, with skipped domains never returned.

        The two default queries run first and always: a model that writes bad
        queries must not be able to make the search worse than not asking it.
        """
        queries = [
            Gap(opening=opening, games=0, share=0.0).query,
            OPPONENT_QUERY.format(opening=opening),
        ]
        try:
            queries += [q for q in self.propose(opening) if q not in queries]
        except ollama.OllamaUnavailable:
            pass

        found: dict[str, Candidate] = {}
        self.skipped = []
        for query in queries:
            asked = Gap(opening=opening, games=0, share=0.0, query_override=query)
            for title, url, publisher, snippet in _detailed(self.searcher, asked):
                if self.skiplist.skips(url):
                    self.skipped.append(publisher)
                    continue
                found.setdefault(url, Candidate(title, url, publisher, snippet))
        return list(found.values())


@dataclass
class Assessor:
    """Reads a page's text and keeps what matters. Writes no prose.

    Its second job is maintenance: a page that is not an article at all puts its
    **domain** on the skip list, so the Scout stops bringing it back and no model
    call is ever spent on that site again.
    """

    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    keep: int = PER_PAGE
    transport: object | None = None
    name: str = "assessor"

    def read(self, opening: str, candidate: Candidate, body: str) -> Reading:
        sentences = self.candidates(body)
        if len(_words(body)) < MIN_PAGE_WORDS or not sentences:
            return Reading(candidate, (), self.classify(candidate, body))

        kept: list[str] = []
        for start in range(0, len(sentences), CHUNK):
            kept += self._pick(opening, sentences[start:start + CHUNK])
            if len(kept) >= self.keep:
                break
        return Reading(candidate, tuple(kept[: self.keep]))

    def _pick(self, opening: str, chunk: list[str]) -> list[str]:
        """The most informative few from one chunk, chosen by index."""
        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(chunk))
        answer = ollama.generate(
            self.model,
            ASSESSOR.format(opening=opening, sentences=numbered, limit=PER_CHUNK),
            host=self.host, num_predict=40, transport=self.transport,
        )
        if "none" in answer.strip().lower()[:8]:
            return []
        # Indices, never text -- so a kept sentence is the page's own words by
        # construction and cannot be something the model composed. The veto is
        # `is_usable_note`, which refuses advertising, study advice and annotated
        # variations but **not** hard vocabulary: judging readability here would
        # starve the agent whose job is to make things readable.
        chosen = ollama.indices(answer, len(chunk))[:PER_CHUNK]
        return [chunk[i] for i in chosen if is_usable_note(chunk[i])]

    def classify(self, candidate: Candidate, body: str) -> str:
        """What kind of site is this, given it is not an article?

        Only ever asked about a page that already failed to yield readable prose,
        so the model never gets the chance to condemn a site it merely disliked.
        """
        found = f"{len(_words(body))} words of readable text"
        try:
            answer = ollama.generate(
                self.model,
                UNUSABLE.format(domain=domain_of(candidate.url),
                                title=candidate.title[:90], found=found,
                                reasons=", ".join(REASONS)),
                host=self.host, num_predict=10, transport=self.transport,
            )
        except ollama.OllamaUnavailable:
            return ""
        first = answer.strip().lower().split()
        word = first[0].strip(".,:*") if first else ""
        return word if word in REASONS else ""

    def candidates(self, body: str) -> list[str]:
        """Sentences worth offering: plausible length, real punctuation."""
        found: list[str] = []
        for block in text_blocks(body):
            fragments = _SPLIT.split(block)
            for sentence in fragments:
                sentence = sentence.strip()
                if not (MIN_WORDS <= len(sentence.split()) <= MAX_WORDS):
                    continue
                # A whole block with no full stop is a list item or a heading,
                # and chess guides put plans in bullet lists -- "King safety:
                # often castle queenside in sharp lines". Requiring terminal
                # punctuation dropped every one of them.
                if not sentence.endswith((".", "!")) and len(fragments) > 1:
                    continue
                found.append(sentence)
        return found


@dataclass
class Compiler:
    """Turns approved notes into bullet points. Searches nothing, adds nothing."""

    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    plans: int = 3
    watches: int = 2
    transport: object | None = None
    name: str = "compiler"

    def compile(self, opening: str, notes: tuple[str, ...]) -> Brief:
        if not notes:
            # Nothing approved means nothing to say. Asking anyway is asking the
            # model what it believes about the opening, which is refused.
            return Brief(opening=opening)

        answer = ollama.generate(
            self.model,
            COMPILER.format(opening=opening, plans=self.plans,
                            watches=self.watches,
                            notes="\n".join(f"- {n}" for n in notes)),
            host=self.host, num_predict=320, transport=self.transport,
        )
        source = " ".join(notes)
        points: list[Point] = []
        kept_plans: list[str] = []
        kept_watches: list[str] = []

        for kind, text in _bullets(answer):
            grounding = check(text, source)
            dropped = "" if grounding.grounded else grounding.reason
            # A point that repeats one already kept spends a line of the brief
            # saying nothing new. Real output gave three plan points that were
            # "challenge White's pawn structure" three ways; and a WATCH point
            # repeating a PLAN point says nothing about the opponent at all,
            # which is the only reason that half exists.
            if not dropped and _restates(text, kept_plans + kept_watches):
                dropped = "repeats a point already made"
            # A point must name something a player can find on the board. The
            # author, on real output: *"vague words like harmony and counterplay
            # when there is nowhere stated what counterplay is not valuable at
            # all."* A square is not required -- a file, a diagonal or a named
            # piece is equally locatable, and "take the d file while watching
            # Black's light-squared bishop" is a real point. What is refused is
            # the generic noun: "pieces", "the center", "pawn structure".
            if not dropped and not names_a_target(text):
                dropped = "names nothing on the board"
            points.append(Point(text, kind, grounding, dropped))
            if not dropped:
                (kept_plans if kind == "plan" else kept_watches).append(text)

        return Brief(opening=opening, points=tuple(points), notes=notes)


@dataclass
class OpeningSwarm:
    """Scout -> Assessor (per page) -> Compiler, with the skip list learned."""

    searcher: object
    fetch: object
    skiplist: SkipList = field(default_factory=SkipList.seeded)
    model: str = MODEL
    # How many surviving pages to read. Each costs a fetch and a model call.
    read: int = 5
    # Optional: with none supplied the swarm behaves exactly as before and
    # persists nothing, which keeps the tests fast and the class usable alone.
    store: RunStore | None = None
    transport: object | None = None

    def __post_init__(self) -> None:
        self.scout = Scout(searcher=self.searcher, skiplist=self.skiplist,
                           model=self.model, transport=self.transport)
        self.assessor = Assessor(model=self.model, transport=self.transport)
        self.compiler = Compiler(model=self.model, transport=self.transport)
        self.trace: list[dict] = []

    def run(self, opening: str) -> Brief:
        # Opened BEFORE the search, and every page committed as it is handled,
        # so a rate limit or a crash leaves everything collected up to that
        # point. Opening it after `find` was the first version and it was wrong
        # for the reason this store exists: a search that failed left no row at
        # all, so the commonest failure here was invisible rather than visible
        # as a run with no pages.
        run_id = None
        if self.store is not None:
            run_id = self.store.start_run(
                opening, self.model,
                searcher=getattr(self.searcher, "name", type(self.searcher).__name__),
            )

        candidates = self.scout.find(opening)
        if run_id is not None:
            for publisher in dict.fromkeys(self.scout.skipped):
                self.store.record_page(run_id, "", publisher, "skipped")

        notes: list[str] = []
        sources: list[str] = []
        learned: list[tuple[str, str]] = []
        for candidate in candidates[: self.read]:
            body = self.fetch(candidate.url) or ""
            reading = self.assessor.read(opening, candidate, body)
            if reading.skip_reason:
                before = len(self.skiplist)
                self.skiplist = self.skiplist.add(
                    candidate.url, reading.skip_reason, "assessor", _today()
                )
                if len(self.skiplist) > before:
                    learned.append((domain_of(candidate.url), reading.skip_reason))
            if reading.useful:
                notes += list(reading.sentences)
                sources.append(candidate.url)
                # Guard 3: a site that has helped can never be skipped later.
                self.skiplist = self.skiplist.mark_useful(candidate.url)

            if run_id is not None:
                page_id = self.store.record_page(
                    run_id, candidate.url, candidate.publisher,
                    "read" if reading.useful
                    else ("unusable" if reading.skip_reason else "nothing"),
                    title=candidate.title, skip_reason=reading.skip_reason,
                )
                if reading.sentences:
                    self.store.record_notes(run_id, page_id, reading.sentences)

        brief = self.compiler.compile(opening, tuple(notes))
        if run_id is not None:
            # Dropped points are stored too: why the swarm rejects things is the
            # question tuning needs, and it is invisible in the brief itself.
            self.store.record_points(run_id, brief.points)
            self.store.finish_run(run_id)

        self.trace.append({
            "opening": opening,
            "run_id": run_id,
            "found": len(candidates),
            "skipped_before_fetch": list(self.scout.skipped),
            "read": min(len(candidates), self.read),
            "yielded": len(sources),
            "learned": learned,
        })
        # Keep the Scout's view of the list current within a run.
        self.scout.skiplist = self.skiplist
        return Brief(opening=brief.opening, points=brief.points,
                     sources=tuple(sources), notes=brief.notes)


# --- reading what the agents say ---------------------------------------------

_SPLIT = re.compile(r"(?<=[.!?])\s+")
_BULLET = re.compile(r"^\s*[-*]?\s*(PLAN|WATCH)\s*:?\s*(.+?)\s*$", re.I)


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def _words(text: str) -> list[str]:
    return " ".join(text_blocks(text)).split()


def _detailed(searcher, gap):
    """Snippets when the searcher has them, blanks when it does not."""
    getter = getattr(searcher, "search_detailed", None)
    if getter is not None:
        return getter(gap)
    return [(t, u, p, "") for t, u, p in searcher.search(gap)]


def _queries(answer: str, limit: int) -> list[str]:
    """Query lines from the Scout, with its decoration removed."""
    out: list[str] = []
    for line in answer.strip().splitlines():
        line = line.strip().lstrip("-*0123456789. ").strip().strip('"').strip("'")
        line = re.sub(r"\s+", " ", line).strip()
        # A model explaining itself writes a sentence; a query is short and bare.
        if not (2 <= len(line.split()) <= 8) or line.endswith((".", ":", "?")):
            continue
        if line not in out:
            out.append(line)
        if len(out) >= limit:
            break
    return out


def _bullets(answer: str) -> list[tuple[str, str]]:
    """(kind, text) for every labelled line, ignoring everything else."""
    text = answer.strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = _BULLET.match(line)
        if not match:
            continue
        point = re.sub(r"\s+", " ", match.group(2)).strip().strip("*").strip()
        if len(point.split()) >= 4:
            out.append((match.group(1).lower(), point))
    return out


def _restates(point: str, already: list[str]) -> bool:
    """Is this point one already made, in different words?

    Uses the same inflection-tolerant comparison as the grounding check: exact
    string matching read "Black stays flexible and breaks against d4" and "Black
    will stay flexible and will break against d4" as 60 % alike, just under the
    threshold, when they are one sentence written twice.
    """
    return any(overlap(point, made) > MAX_RESTATEMENT for made in already)
