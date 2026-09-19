"""Answering the player's questions after the report.

Design: docs/notes/design.narrated-session.md

Two places an answer may come from, tried in order, and nothing else:

  1. **The report.** The model is given the player's report and the question, and
     either answers from it or says the report does not cover it. The answer is
     checked exactly as the summary is (`narrator.verdict`): no move, square or
     number the report does not contain, and not too much vocabulary of its own.
  2. **The books.** A question the report does not cover -- *"what is a pin?"* --
     goes to the book knowledge graph through `answering.answer`, which quotes and
     names its sources (E79's rules, unchanged).

If neither can answer, the player is told so in a fixed sentence. **The model is
never asked what it believes about chess**: that is R-03, and a conversation is
where a model's confident nonsense is most convincing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from chesscoach import answering, ollama
from chesscoach.narrator import MODEL, verdict

# A question asking what a chess idea *is*. Answered only from the books, never
# from the report: E92 asked "What is a pin?" and the model answered from the
# report with a wrong definition that passed the check at 42 % novelty, the same
# as a good answer. Novelty cannot separate them, so the route does. English and
# Croatian, since the author's players ask in both.
_CONCEPT = re.compile(
    r"^\s*(what\s+is|what's|whats|what\s+are|what\s+does\s+.+\s+mean|define|"
    r"explain\s+what|meaning\s+of|"
    r"što\s+je|sto\s+je|što\s+su|sto\s+su|što\s+znači|sto\s+znaci|objasni\s+što|"
    r"objasni\s+sto)\b",
    re.IGNORECASE,
)

# The model's way of saying "not from this report". Checked case-insensitively.
NOT_COVERED = "NOT_IN_REPORT"

REFUSAL = ("I can answer from your report and from the chess books I have, and "
           "neither covers that.")

UNAVAILABLE = ("I cannot answer questions right now, because the local model is "
               "not running. Everything above stands as it is.")

PROMPT = """You are a chess coach. Below is a report measured from the player's own games.

Answer the player's question using ONLY the report. Speak to them as "you", in at most three
sentences, and copy any number exactly as the report gives it.
Do not explain what a chess idea is or how to play in general; that is not in the report.
If the report does not answer the question, reply with exactly: {not_covered}

Report:
{report}

Question: {question}
"""


class Source(Enum):
    REPORT = "report"
    BOOKS = "books"
    REFUSED = "refused"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Reply:
    """What to tell the player, and where it came from."""

    text: str
    source: Source
    reason: str = ""


def answer_followup(question: str, report: str, *, store=None, model: str = MODEL,
                    book_model: str = "phi4-mini:3.8b", host: str = ollama.OLLAMA_URL,
                    transport=None) -> Reply:
    """Answer from the report, else from the books, else refuse."""
    if is_concept_question(question):
        return _from_books(question, store, book_model, host, transport)
    try:
        said = ollama.generate(
            model, PROMPT.format(report=report, question=question, not_covered=NOT_COVERED),
            host=host, num_predict=220, temperature=0.2, transport=transport,
        ).strip()
    except ollama.OllamaUnavailable as error:
        return Reply(UNAVAILABLE, Source.UNAVAILABLE, str(error))

    if said and NOT_COVERED.lower() not in said.lower():
        reason = verdict(said, report)
        if not reason:
            return Reply(said, Source.REPORT)
        # An answer that failed the check is not passed on, and not retried
        # against the books: the question was about the report.
        return Reply(REFUSAL, Source.REFUSED, reason)

    return _from_books(question, store, book_model, host, transport)


def is_concept_question(question: str) -> bool:
    """Does it ask what a chess idea is, rather than something about this player?"""
    return bool(_CONCEPT.search(question or ""))


def _from_books(question, store, model, host, transport) -> Reply:
    if store is None:
        return Reply(REFUSAL, Source.REFUSED, "no book store")
    try:
        found = answering.answer(question, store, model=model, host=host, transport=transport)
    except ollama.OllamaUnavailable as error:
        return Reply(UNAVAILABLE, Source.UNAVAILABLE, str(error))
    except RuntimeError as error:  # GraphUnavailable is a RuntimeError
        return Reply(REFUSAL, Source.REFUSED, f"book store unavailable ({error})")
    if not found.grounded:
        return Reply(REFUSAL, Source.REFUSED, "the books do not cover it")
    return Reply(found.rendered(), Source.BOOKS)
