"""Which of a page's sentences say what to aim for.

Design: [[decisions.0012-quote-the-plans-rather-than-write-them]] §, and
[[experiments.e51-llm-selection-and-search]] for the measurement.

Two implementations of one job, so which ships is an empirical question rather
than a preference — the shape `classifiers.py` and `opening_summary.py` both use.

  `RegexSelector`  eight hand-written filters. Cost nothing, run offline, and
                   were built by reading real output: six of the eight exist
                   because a specific bad sentence shipped.
  `LlmSelector`    a local model reads the page's sentences and picks. Removes
                   the brittleness, and costs a model call and determinism.

**The model answers with indices, never with text.** That is the whole safety
argument: what comes back is a set of numbers into a list this module built from
the page, so every selected sentence is verbatim by construction and there is no
opportunity to smuggle an invented sentence into the material a later grounding
check will treat as ground truth. Out-of-range numbers are dropped rather than
clamped, and a sentence is re-verified against the page before it is returned.

That matters more than it looks. [[experiments.e50-ollama-summaries]] measured
what happens when the source the checker compares against grows: false-claim pass
rate goes **3 % → 76 %** when the whole page stands in for the extracted quotes.
The selection step is not only a filter on what the model reads — it is what
makes the check on what the model writes mean anything. So selection may become a
model's job, but its output must stay small and stay the page's own words.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from chesscoach import ollama
from chesscoach.opening_plans import (
    MAX_QUOTES,
    MAX_WORDS,
    MIN_WORDS,
    is_admissible,
    is_plan_sentence,
    plan_quotes,
    text_blocks,
)

# Indices only, so prose can never be read as a selection.
SELECT_SCHEMA = ollama.schema_of(keep=ollama.array_of("integer"))

PROMPT = """Below are numbered sentences from a web page about the {opening}.

Pick the {limit} sentences that best tell a club player rated about 1500 WHAT TO \
AIM FOR in this opening — the plans, the pawn breaks, where the pieces belong.

Reject a sentence if it:
- describes what happened in one game instead of what to aim for
- uses a term a 1500 would have to look up
- advertises a course, a book or a website
- is about studying the opening rather than playing it

Answer with the numbers of the sentences you picked, in the "keep" field.
If none of them say what to aim for, keep nothing.

{sentences}
"""


class Selector(Protocol):
    name: str

    def select(self, opening: str, body: str, limit: int = 2) -> tuple[str, ...]:
        ...


@dataclass(frozen=True)
class RegexSelector:
    """The eight filters, as a real implementation rather than a special case."""

    name: str = "regex"

    def select(self, opening: str, body: str, limit: int = 2) -> tuple[str, ...]:
        return plan_quotes(body, limit=limit)


@dataclass
class LlmSelector:
    """A local model choosing from the page's own sentences, by index."""

    model: str = "qwen2.5:3b"
    host: str = ollama.OLLAMA_URL
    # How many sentences to offer. A whole article does not fit a 3B model's
    # useful context, and the ones a plan could be in are a small minority, so
    # the obvious length and shape filters run first. This is a **cheaper**
    # prefilter than RegexSelector's, deliberately: it drops fragments and
    # paragraph-length runs and leaves every judgement of content to the model.
    offered: int = 60
    # Keep the non-PLAN filters as a veto over the model's choice. Measured: the
    # model finds real plan sentences the `PLAN` pattern misses, and also picks
    # marketing ("Highlighted course The High Pressure Alapin Sicilian"), trivia
    # ("...is Gata Kamsky") and annotated variations ("Nxe5 6.d4 with a fork").
    # So it replaces the recall-limiting half of the rules and not the
    # precision-preserving half ([[experiments.e51-llm-selection-and-search]]).
    veto: bool = True
    transport: object | None = None
    name: str = field(init=False)

    def __post_init__(self) -> None:
        self.name = f"llm/{self.model}"

    def select(self, opening: str, body: str, limit: int = 2) -> tuple[str, ...]:
        limit = min(limit, MAX_QUOTES)
        candidates = self.candidates(body)
        if not candidates:
            return ()

        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(candidates))
        answer = ollama.generate(
            self.model,
            PROMPT.format(opening=opening, limit=limit, sentences=numbered),
            host=self.host,
            num_predict=60,
            schema=SELECT_SCHEMA,
            transport=self.transport,
        )
        data = ollama.as_json(answer)
        if data is not None:
            chosen = ollama.ints(data, "keep", len(candidates))[:limit]
        elif "none" in answer.strip().lower()[:8]:
            return ()
        else:
            chosen = ollama.indices(answer, len(candidates))[:limit]
        # Re-verified against the page even though indexing already guarantees
        # it. The guarantee is one refactor away from being untrue, and the
        # thing it protects -- that a checker's ground truth is really the
        # page's -- is worth a redundant comparison.
        flat = _flatten(body)
        kept = [candidates[i] for i in chosen if _flatten(candidates[i]) in flat]
        if self.veto:
            kept = [s for s in kept if is_admissible(s)]
        return tuple(kept)

    def candidates(self, body: str) -> list[str]:
        """Sentences worth offering: plausible length, not an analysis dump."""
        found: list[str] = []
        for block in text_blocks(body):
            for sentence in _SPLIT.split(block):
                sentence = sentence.strip()
                words = len(sentence.split())
                if words < MIN_WORDS or words > MAX_WORDS:
                    continue
                if not sentence.endswith((".", "!")):
                    continue
                found.append(sentence)
                if len(found) >= self.offered:
                    return found
        return found


def _flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Re-exported so a caller comparing the two selectors can ask the regex question
# of a model's answer -- "would the filters have kept this?" -- which is what
# makes the disagreement between them readable rather than just countable.
__all__ = ["LlmSelector", "RegexSelector", "Selector", "is_plan_sentence"]
