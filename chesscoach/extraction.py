"""Does this passage actually describe the concept, or merely sit near it?

Design: docs/notes/design.graph-knowledge-base.md § "Extraction: select, never
compose"

**Why this exists at all.** A first run of stage 3 skipped it and corroborated
19 concepts of 19 at every threshold from 0.50 to 0.80 -- including `skewer`,
which E64 measured as appearing **zero times** across the shelf. The method was
circular: retrieve passages similar to a query, then measure that they are
similar to each other. Every page of chess prose passes a test like that.

So similarity finds candidates and **judgement decides**. The judgement is made
the way this project already knows is safe: the model **picks a sentence by
index** and may answer `-1`. It never writes one. E63 recorded what happens
without the refusal option -- the model returns the least-bad sentence rather
than none, and a definition of castling arrives that is really about pawns.

The stored result is therefore a **verbatim sentence from a real book**, with the
locator that finds it again. The label may be wrong and can be checked; the text
cannot be invented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chesscoach import ollama

# A sentence worth judging: long enough to define something, short enough to be
# one claim. The same shape `books._SENTENCE` uses for prose detection.
_SENTENCE = re.compile(r"[^.!?]{40,400}[.!?]")

# Fewer than this and the model is choosing from almost nothing; many more and a
# 3.8B model loses track of the numbering, which E63 saw as HTTP 500s on long
# prompts.
MAX_SENTENCES = 14

JUDGE_SCHEMA = ollama.schema_of(sentence={"type": "integer"})

JUDGE = """You are checking whether a passage from a chess book explains a term.

TERM: {concept}

Below are numbered sentences from one passage of one book.

{sentences}

Pick the ONE sentence that passes this test:

    A player who did not know what "{concept}" means could read this sentence
    alone and afterwards know what it means.

That is the whole test. A sentence fails it if it uses the term while
explaining something else, describes one position where it happened, gives moves
without saying what they illustrate, or is part of a board diagram.

If no sentence passes, answer -1.

Answer with a number only."""


@dataclass(frozen=True)
class Extraction:
    """One sentence a book uses to explain a concept."""

    concept: str
    locator: str
    lineage: str
    sentence: str


def sentences_of(passage: str) -> list[str]:
    """The passage's own sentences, trimmed to what a model can number reliably."""
    found = [" ".join(m.group(0).split()) for m in _SENTENCE.finditer(passage)]
    return found[:MAX_SENTENCES]


def mentions(concept: str, passage: str, phrases=()) -> bool:
    """Does the passage use the concept at all, in any of its real phrasings?

    **The deterministic half of the gate, and it does most of the work.** Asked
    on its own, `phi4-mini:3.8b` kept 4 candidate passages of 4 for "skewer" --
    a term E64 measured as appearing **zero times** on the original shelf -- one
    of them a board diagram. A model asked "is this about X" will find a way to
    say yes.

    A passage that never uses the word, in any wording writers actually use,
    cannot be explaining it. The phrasings come from `TERMS`, measured in E65
    against these books rather than guessed: "outpost" scores 0 where "hole"
    scores 50.
    """
    from chesscoach.knowledge_swarm import _names

    # `_names` is the project's existing answer to "does this text mention the
    # thing it is supposed to define", and it already subtracts the generic
    # vocabulary -- which is the step two wrong versions of this function were
    # missing. Matching whole search phrases refused every `pin` passage, and
    # matching their content words accepted every `skewer` passage because
    # "chess" was among them.
    return _names(passage, concept)


def describes(
    concept: str,
    passage: str,
    phrases=(),
    model: str = "qwen3:8b",
    host: str = ollama.OLLAMA_URL,
    transport=None,
) -> str | None:
    """The sentence that explains `concept`, or None.

    Two gates, cheap one first. The passage must **use** the term, and then a
    sentence in it must **teach** the term. Neither alone is enough: the first
    passes any page that mentions the word, and the second, on the evidence,
    passes almost anything.

    **None is the expected answer.** Most passages near a term do not define it,
    and a gate that rarely refuses is not a gate -- it is the circular method
    this module was written to replace.
    """
    if not mentions(concept, passage, phrases):
        return None
    options = sentences_of(passage)
    if not options:
        return None

    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(options))
    try:
        reply = ollama.generate(
            model,
            JUDGE.format(concept=concept, sentences=numbered),
            host=host, num_predict=12, temperature=0.0,
            schema=JUDGE_SCHEMA, transport=transport,
        )
    except ollama.OllamaUnavailable:
        # Raised upward would be defensible; returning None here would make an
        # unreachable model look exactly like a passage that explains nothing,
        # so it is re-raised rather than swallowed.
        raise

    chosen = _index_of(reply)
    if chosen is None or not 0 <= chosen < len(options):
        return None
    return options[chosen]


def _index_of(reply: str) -> int | None:
    """The integer the model answered with, or None.

    Structured output should make this a formality, and it is not: a small model
    asked for an integer will sometimes wrap it in prose or JSON anyway.
    """
    if not reply:
        return None
    try:
        import json

        payload = json.loads(reply)
        if isinstance(payload, dict) and "sentence" in payload:
            return int(payload["sentence"])
        if isinstance(payload, int):
            return payload
    except (ValueError, TypeError):
        pass
    found = re.search(r"-?\d+", reply)
    return int(found.group(0)) if found else None
