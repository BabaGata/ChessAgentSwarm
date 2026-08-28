"""A local model reading search results and rewording the query.

Design: [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

The searcher cannot tell a guide from a listicle. Measured, not supposed: asked
for the Grob it returned a **Duolingo blog post** and a chess.com forum thread,
and the query that produced them is one hand-written string that has never been
varied ([[experiments.e50-ollama-summaries]]).

*"Is this a plans guide for club players, or a listicle?"* is a judgement about a
title and a domain — **language work, not chess** — which is the side of
ADR-0013's line a model is allowed on. So is proposing a different wording.

**What this cannot do is inject a false claim.** It only changes which pages
become candidates. Every page still goes through sentence selection, the
grounding check and the author's `reviewed=true`, so the worst case is that it
proposes bad pages and they are rejected — which is today's behaviour, not a
regression.

**It costs determinism, and that is paid for rather than ignored.** Acquisition
becomes non-reproducible in a way the thesis' criterion 6 cares about, so every
query tried and every verdict is recorded on `log` for the experiment to write
out. A run can then be read back even though it cannot be replayed exactly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from chesscoach import ollama
from chesscoach.opening_agent import Gap, Searcher

JUDGE = """You are choosing web pages that teach a chess opening's PLANS to a \
club player rated about 1500.

KEEP a page that looks like a guide, an article about plans and ideas, or a \
lesson on this specific opening.
REJECT a page that looks like: a list of many openings, a forum or comment \
thread, a move database or statistics page, a shop, a video, or a page about a \
different opening.

Numbered results for "{opening}":
{results}

Answer with ONLY the numbers to keep, separated by commas. No other words.
If none should be kept, answer NONE.
"""

REWORD = """A web search for chess opening guides returned poor results.

The opening is: {opening}
The search used was: {query}
{seen}
Write ONE different web search that would find a page teaching this opening's \
plans and ideas to a club player. Use different words from the search above.

Answer with ONLY the search text, on one line.
"""


@dataclass
class GuidedSearcher:
    """Wraps a searcher: the model filters the results and rewords the query.

    Implements `Searcher`, so it drops into `OpeningResourceAgent` unchanged.
    """

    inner: Searcher
    model: str = "qwen2.5:3b"
    host: str = ollama.OLLAMA_URL
    # How many rewordings to try before accepting what is there. Three searches
    # per opening is polite to the upstream engines and bounded in time.
    attempts: int = 3
    # Stop as soon as this many results survive judging.
    wanted: int = 2
    transport: object | None = None
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"guided/{getattr(self.inner, 'name', 'searcher')}"
        self.log: list[dict] = []
        self.last_answer = ""
        # How often the judge produced something no verdict could be read from.
        # Counted rather than hidden: it is the difference between "the judge
        # approved these" and "the judge did not answer".
        self.unparseable = 0

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        tried: list[str] = []
        best: list[tuple[str, str, str]] = []
        query = gap.query

        for attempt in range(self.attempts):
            tried.append(query)
            results = self.inner.search(replace(gap, query_override=query))
            kept = self._judge(gap.opening, results)
            self.log.append({
                "opening": gap.opening, "attempt": attempt, "query": query,
                "returned": len(results), "kept": len(kept),
                "answer": self.last_answer[:60],
            })
            # More survivors than any previous wording is the thing being
            # optimised, and ties keep the earlier query -- the author's.
            if len(kept) > len(best):
                best = kept
            if len(best) >= self.wanted:
                return best[: self.wanted] if self.wanted else best
            if attempt == self.attempts - 1:
                break
            reworded = self._reword(gap.opening, query, tried)
            if not reworded or reworded in tried:
                break
            query = reworded

        # Never return fewer candidates than the plain searcher would have. A
        # judge that rejects everything must not turn a working search into a
        # silent absence -- the failure L-046 keeps producing.
        if not best:
            return self.inner.search(gap)
        return best

    def _judge(self, opening: str, results) -> list[tuple[str, str, str]]:
        """Which of these look like plans guides? Titles and domains only.

        Snippets would help and are not fetched: the observed failures are
        legible from the title and the host — *"33 Chess Openings You Should
        Know"* on `blog.duolingo.com`, `chess.com/forum/view`. Stated as a limit
        rather than a design.
        """
        if not results:
            return []
        listing = "\n".join(
            f"{i}. {title[:90]}  [{publisher}]"
            for i, (title, _url, publisher) in enumerate(results)
        )
        try:
            answer = ollama.generate(
                self.model,
                JUDGE.format(opening=opening, results=listing),
                host=self.host, num_predict=40, transport=self.transport,
            )
        except ollama.OllamaUnavailable:
            # The model is an improvement, never a dependency.
            return list(results)
        self.last_answer = answer.strip()
        if "none" in answer.strip().lower()[:8]:
            return []
        chosen = ollama.indices(answer, len(results))
        if not chosen:
            # Unparseable is NOT a verdict. Keeping everything is the safe
            # fallback, and it must be visible as a fallback rather than read as
            # "the judge approved these" (L-046).
            self.unparseable += 1
            return list(results)
        return [results[i] for i in chosen]

    def _reword(self, opening: str, query: str, tried: list[str]) -> str:
        seen = ""
        if len(tried) > 1:
            seen = "Already tried:\n" + "\n".join(f"- {t}" for t in tried) + "\n"
        try:
            answer = ollama.generate(
                self.model,
                REWORD.format(opening=opening, query=query, seen=seen),
                host=self.host, num_predict=60, temperature=0.7,
                transport=self.transport,
            )
        except ollama.OllamaUnavailable:
            return ""
        return _one_line(answer)


def _one_line(answer: str) -> str:
    """The first plausible query in the answer, stripped of a model's decoration."""
    for line in answer.strip().splitlines():
        # Markers first, then quotes: stripping quotes from `- "a query"` leaves
        # the marker in front of the opening quote, which then survives.
        line = line.strip().lstrip("-*0123456789. ").strip().strip('"').strip("'").strip()
        # A model that explains itself produces a sentence, not a query.
        if 2 <= len(line.split()) <= 14 and not line.endswith((".", ":", "?")):
            return re.sub(r"\s+", " ", line)
    return ""
