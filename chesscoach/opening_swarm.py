"""Three agents that turn an opening name into a brief a player can act on.

Design: [[decisions.0014-three-agents-for-the-opening-brief]]

    SCOUT      writes search queries and casts a wide net.     judges nothing
    ASSESSOR   reads what came back and discards the unusable. writes nothing
    COMPILER   writes the player's brief from what survived.   searches nothing

Each has one job, one prompt stating its role, and a failure mode it must not
have. The separation is not decoration: an agent that both searched and judged
would have no reason to discard its own results, and one that both judged and
wrote could quietly replace a weak source with its own knowledge.

**Every chess claim still traces to a fetched page.** The Compiler works only
from sentences the Assessor kept, which are verbatim from those pages, and its
output is checked against them by `grounding.check` before anyone sees it. That
is what keeps a swarm of language models inside R-03: the models decide *which
text* and *which words*, never *what is true about chess*.

**The brief has two halves because a plan is only half of what a player needs.**
The author asked for *"a short description of the plan for the player and what
should be careful as a response of the opponent"* — so `PLAN` and `WATCH` are
produced and checked separately, and a brief can keep one and lose the other.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from chesscoach import ollama
from chesscoach.grounding import Grounding, check, content_words
from chesscoach.opening_agent import Gap
from chesscoach.plan_selector import LlmSelector

MODEL = "qwen2.5:3b"

# Above this share of shared content words, WATCH is the PLAN said again rather
# than a different claim. Measured on a real run: the Pirc brief's WATCH was its
# PLAN with the colour flipped -- "Black will aim to control the center with
# pawns on d6 and c6" against "Control the center with pawns on d6 and c6" --
# and it passed the grounding check, because every word was the source's. The
# checker cannot see a restatement; this can.
MAX_RESTATEMENT = 0.60

# The brief has two halves, so the search needs two angles. Measured: with only
# the plans query, **0 of 6** WATCH halves survived -- every one was either the
# PLAN restated or invented and caught, because no retrieved sentence described
# what the other side does. A missing half of the brief was a missing half of
# the search.
OPPONENT_QUERY = "how to play against the {opening} main responses"

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
- vary the angle between queries: one about plans, one about the middlegame, \
one about what each side wants
- a query is not a title and not a sentence

Opening: {opening}
{tried}
Write {count} different search queries, one per line. Nothing else.
"""

# --- the Assessor ------------------------------------------------------------

ASSESSOR = """You are the ASSESSOR in a chess coaching system.

YOUR ROLE
The Scout found these pages. You decide which are worth reading for a club \
player rated about 1500 who wants to learn what to AIM FOR in this opening. \
A later agent writes the player's brief using only what you keep, so what you \
discard is gone — but discarding everything leaves the player with nothing.

KEEP a page that explains ideas, plans, typical structures, pawn breaks, or \
what each side is trying to do.
DISCARD a page that is: a list of many different openings, a forum or comment \
thread, a move database or statistics table, a shop or product listing, a \
video, or clearly about a different opening.

WHEN UNSURE, KEEP. Everything you keep is reviewed by a person before any \
player sees it, so a mediocre page costs little and a discarded good page is \
lost.

Pages found for "{opening}":
{results}

Answer one line per page, in order, exactly like this:
<number> KEEP <short reason>
<number> DISCARD <short reason>
"""

# --- the Compiler ------------------------------------------------------------

COMPILER = """You are the COMPILER in a chess coaching system.

YOUR ROLE
You write the short brief a player reads before studying this opening. You work \
ONLY from the notes below, which were taken from pages the Assessor approved. \
You must NOT add chess knowledge of your own: a check compares your text against \
these notes and throws away anything naming a square, a move or an idea they do \
not contain.

Do not change who does what. If a note says White does something, do not write \
that Black does it.

WRITE EXACTLY TWO PARTS, using these labels:

PLAN: two short sentences on what the player should aim for in this opening.
WATCH: one or two short sentences on what the opponent will try, and what the \
player should be ready for.

Plain words only. No term a 1500 would have to look up. No move numbers. No \
preamble, no headings beyond the two labels.

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
class Verdict:
    """One page, judged, with the Assessor's reason kept for the author."""

    candidate: Candidate
    keep: bool
    reason: str


@dataclass(frozen=True)
class Brief:
    """What a player would read, and everything needed to argue with it."""

    opening: str
    plan: str
    watch: str
    sources: tuple[str, ...]
    plan_grounding: Grounding | None = None
    watch_grounding: Grounding | None = None
    notes: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        """At least one half survived its check."""
        return bool(self.plan or self.watch)


@dataclass
class Scout:
    """Writes queries and runs them. Judges nothing."""

    searcher: object
    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    queries: int = 3
    transport: object | None = None
    name: str = "scout"

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
        """Every distinct page the proposed queries turn up, deduplicated by URL.

        The Scout's own default query runs first and always: a model that writes
        three bad queries must not be able to make the search worse than not
        having asked it.
        """
        gap = Gap(opening=opening, games=0, share=0.0)
        queries = [gap.query, OPPONENT_QUERY.format(opening=opening)]
        try:
            queries += [q for q in self.propose(opening) if q not in queries]
        except ollama.OllamaUnavailable:
            pass

        found: dict[str, Candidate] = {}
        for query in queries:
            asked = Gap(opening=opening, games=0, share=0.0, query_override=query)
            for row in _detailed(self.searcher, asked):
                title, url, publisher, snippet = row
                found.setdefault(url, Candidate(title, url, publisher, snippet))
        return list(found.values())


@dataclass
class Assessor:
    """Reads what the Scout brought and discards the unusable. Writes nothing."""

    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    transport: object | None = None
    name: str = "assessor"

    def assess(self, opening: str, candidates: list[Candidate]) -> list[Verdict]:
        if not candidates:
            return []
        listing = "\n".join(
            f"{i}. {c.title[:90]}  [{c.publisher}]\n   {c.snippet[:220]}"
            for i, c in enumerate(candidates)
        )
        try:
            answer = ollama.generate(
                self.model,
                ASSESSOR.format(opening=opening, results=listing),
                host=self.host, num_predict=60 * len(candidates),
                transport=self.transport,
            )
        except ollama.OllamaUnavailable:
            # Unjudged, not approved -- and said so in the reason, because a
            # blank verdict reading as approval is how this goes wrong.
            return [Verdict(c, True, "not assessed: model unavailable")
                    for c in candidates]
        return _verdicts(answer, candidates)


@dataclass
class Compiler:
    """Writes the brief from what survived. Searches nothing, adds nothing."""

    model: str = MODEL
    host: str = ollama.OLLAMA_URL
    transport: object | None = None
    name: str = field(default="compiler")

    def compile(self, opening: str, notes: tuple[str, ...]) -> Brief:
        if not notes:
            # Nothing approved means nothing to say. Asking the model anyway is
            # asking it what it believes about the opening, which is refused.
            return Brief(opening=opening, plan="", watch="", sources=())

        answer = ollama.generate(
            self.model,
            COMPILER.format(opening=opening, notes="\n".join(f"- {n}" for n in notes)),
            host=self.host, num_predict=300, transport=self.transport,
        )
        plan, watch = _two_parts(answer)
        # "none" is the Compiler declining, which the prompt asks for when the
        # notes do not cover what the opponent does. Silence is a real answer
        # and must not be checked as if it were a claim.
        if watch.strip().lower().rstrip(".") == "none":
            watch = ""
        source = " ".join(notes)

        # Checked separately: a good plan should not be thrown away because the
        # opponent half wandered, and vice versa.
        plan_grounding = check(plan, source) if plan else None
        # A WATCH that merely repeats the PLAN tells the player nothing about
        # the opponent, which is the half of the brief it exists to supply.
        if watch and plan and _restates(watch, plan):
            watch = ""
        watch_grounding = check(watch, source) if watch else None
        return Brief(
            opening=opening,
            plan=plan if plan_grounding and plan_grounding.grounded else "",
            watch=watch if watch_grounding and watch_grounding.grounded else "",
            sources=(),
            plan_grounding=plan_grounding,
            watch_grounding=watch_grounding,
            notes=notes,
        )


@dataclass
class OpeningSwarm:
    """Scout -> Assessor -> read the kept pages -> Compiler."""

    searcher: object
    fetch: object
    model: str = MODEL
    # How many approved pages to read. Each costs a fetch and a selection call.
    # Raised from 3 after a real run: the Compiler was given ONE sentence and
    # filled the rest from its own knowledge, which the checker then rejected --
    # a safe failure that still leaves the player with nothing. Note supply, not
    # the checker, was the binding constraint.
    read: int = 5
    transport: object | None = None

    def __post_init__(self) -> None:
        self.scout = Scout(searcher=self.searcher, model=self.model,
                           transport=self.transport)
        self.assessor = Assessor(model=self.model, transport=self.transport)
        self.compiler = Compiler(model=self.model, transport=self.transport)
        self.selector = LlmSelector(model=self.model, transport=self.transport)
        self.trace: list[dict] = []

    def run(self, opening: str) -> Brief:
        candidates = self.scout.find(opening)
        verdicts = self.assessor.assess(opening, candidates)
        kept = [v for v in verdicts if v.keep]
        self.trace.append({
            "opening": opening, "found": len(candidates), "kept": len(kept),
            "discarded": [(v.candidate.publisher, v.reason)
                          for v in verdicts if not v.keep],
        })

        notes: list[str] = []
        sources: list[str] = []
        for verdict in kept[: self.read]:
            body = self.fetch(verdict.candidate.url)
            if not body:
                continue
            picked = self.selector.select(opening, body, limit=3)
            if picked:
                notes += list(picked)
                sources.append(verdict.candidate.url)

        brief = self.compiler.compile(opening, tuple(notes))
        return Brief(
            opening=brief.opening, plan=brief.plan, watch=brief.watch,
            sources=tuple(sources), plan_grounding=brief.plan_grounding,
            watch_grounding=brief.watch_grounding, notes=brief.notes,
        )


# --- reading what the agents say ---------------------------------------------


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
        if not (2 <= len(line.split()) <= 8):
            continue
        if line.endswith((".", ":", "?")):
            continue
        if line not in out:
            out.append(line)
        if len(out) >= limit:
            break
    return out


_VERDICT = re.compile(r"^\s*(\d+)\D{0,4}\b(KEEP|DISCARD)\b[:\s-]*(.*)$", re.I)


def _verdicts(answer: str, candidates: list[Candidate]) -> list[Verdict]:
    """One verdict per candidate, defaulting to KEEP for anything unjudged.

    The default is not neutrality. A page the Assessor never mentioned has not
    been rejected, and treating silence as rejection is how a parse failure
    becomes an empty report (L-046).
    """
    said: dict[int, tuple[bool, str]] = {}
    for line in answer.splitlines():
        match = _VERDICT.match(line)
        if not match:
            continue
        index = int(match.group(1))
        if 0 <= index < len(candidates):
            said[index] = (match.group(2).upper() == "KEEP",
                           match.group(3).strip()[:80])
    return [
        Verdict(c, *said.get(i, (True, "not judged"))) for i, c in enumerate(candidates)
    ]


def _two_parts(answer: str) -> tuple[str, str]:
    """The PLAN and WATCH halves, or blanks if the labels never appeared."""
    text = answer.strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    plan = watch = ""
    match = re.search(r"PLAN\s*:?\s*(.+?)(?=WATCH\s*:|$)", text, re.I | re.S)
    if match:
        plan = _tidy(match.group(1))
    match = re.search(r"WATCH\s*:?\s*(.+)$", text, re.I | re.S)
    if match:
        watch = _tidy(match.group(1))
    return plan, watch


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip().strip("*").strip()
    return text


def _restates(watch: str, plan: str) -> bool:
    """Is this the plan said again, rather than something about the opponent?

    The denominator is the **shorter** of the two. Dividing by the WATCH's own
    length lets a model escape by padding: the real Pirc failure shared 6 words
    with a 12-word WATCH (50 %, allowed) and those 6 were 75 % of the entire
    PLAN, which is what "it said the same thing again" actually looks like.
    """
    watch_words = set(content_words(watch))
    plan_words = set(content_words(plan))
    if not watch_words or not plan_words:
        return False
    shared = watch_words & plan_words
    return len(shared) / min(len(watch_words), len(plan_words)) > MAX_RESTATEMENT
