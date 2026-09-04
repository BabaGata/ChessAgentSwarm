"""Answering a player's chess question from the shelf, or refusing to.

Design: docs/notes/design.graph-knowledge-base.md

The author's goal for the whole graph:

    "I want the ollama agent to be able to have normal conversation with the
    player if the player asks it some questions about chess, so that it is not
    only able to give to the player the generated review but also to discuss it
    with the player."

This is that path, and it holds one line that everything else in the project
already holds: **the answer says who says a thing, never that it is so.**

    "Capablanca and Staunton describe it this way: ..."      allowed
    "A backward pawn is one that ..."                        not allowed

The second is a chess claim this project cannot support, and it is what R-03
forbids -- a model's own words wearing the authority of a knowledge base. The
first is a claim about the literature, it is checkable against the locators, and
it is what V8 and C5 already require of every finding in a report.

**Refusal is a real outcome.** With nothing retrieved, or nothing from two
independent voices, the honest answer is that the shelf does not cover it. E79
measured 5 concepts of 19 in exactly that state, and `skewer` is not on these
books at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chesscoach import ollama
from chesscoach.corroboration import Attestation, corroborate

# How many passages to put in front of the model. Enough to answer from, few
# enough that a 3.8B model does not lose the question.
PASSAGES = 3

# Below this many independent voices, the answer is offered as one book's view
# rather than as something the literature agrees on.
CORROBORATED = 2

PROMPT = """You are a chess coach talking to a club player rated about 1500.

Answer the question using ONLY the reference material below. Do not add chess
knowledge of your own, even if you are confident it is correct.

If the material does not answer the question, say exactly:
    The books I have do not cover that.

Write at most four sentences. Do not name the books; that is added separately.

Reference material:
{context}

Question: {question}
"""

REFUSAL = "The books I have do not cover that."


@dataclass(frozen=True)
class Answer:
    """What the coach says, and everything needed to check it."""

    text: str
    question: str
    locators: tuple[str, ...] = ()
    voices: tuple[str, ...] = ()
    grounded: bool = True
    # True when part of the answer came from the generated rules layer, which is
    # computed rather than quoted and needs no corroboration.
    computed: bool = False
    # How many independent lineages actually **agree**, by E79's rule. Distinct
    # from `len(voices)`, which is only how many were read.
    agreeing: int = 0

    @property
    def corroborated(self) -> bool:
        """Do at least two independent authors **agree**?

        Not how many were read. E79's rule: distinct lineages whose passages
        resemble each other closely enough to be the same idea, and not so
        closely as to be one copying the other.
        """
        return self.agreeing >= CORROBORATED

    @property
    def attribution(self) -> str:
        """Who says it. **Never that it is true.**"""
        if not self.voices:
            return ""  # computed answers are labelled separately
        if len(self.voices) == 1:
            return f"{self.voices[0]} describes it this way"
        return (f"{', '.join(self.voices[:-1])} and {self.voices[-1]} "
                f"describe it this way")

    def rendered(self) -> str:
        """The answer as a player reads it, attribution and citations included."""
        if not self.grounded:
            return self.text
        lines = [self.text, ""]
        if self.attribution:
            lines.append(f"— {self.attribution}.")
        if self.computed:
            # Said whenever any of the material was generated, because which
            # source the model leaned on is not knowable from here -- and the
            # "rapid" answer came from the computed rule while carrying a
            # book beside it, so a hedge about a lone author would have been
            # about the wrong thing entirely.
            lines.append("— part of this is computed from the rules of chess "
                         "rather than quoted from a book.")
        elif len(self.voices) == 1:
            # Said out loud rather than left to the reader to notice. One book
            # is one opinion, however eminent its author. **Not said when the
            # answer is computed**: arithmetic does not need a second opinion.
            lines.append("  Only one of the books on the shelf discusses this, "
                         "so take it as one author's view.")
        elif len(self.voices) > 1 and not self.corroborated:
            # Several books were read and their descriptions do not resemble
            # each other. That is worth saying: the citations are real and the
            # agreement they imply is not.
            lines.append("  These books were read for this answer but do not "
                         "agree closely on it, so treat it with care.")
        for locator in self.locators:
            lines.append(f"  {locator}")
        return "\n".join(lines)


def answer(
    question: str,
    store,
    model: str = "phi4-mini:3.8b",
    passages: int = PASSAGES,
    host: str = ollama.OLLAMA_URL,
    transport=None,
) -> Answer:
    """Answer from the shelf, or say the shelf does not cover it.

    `store` is a `GraphStore`. It is passed in rather than opened here because
    an unreachable database must not be indistinguishable from a question with
    no answer -- the caller decides what to do about that, and `GraphStore`
    raises rather than returning nothing.
    """
    hits = store.search(question, k=passages)
    if not hits:
        return Answer(REFUSAL, question, grounded=False)

    context = "\n\n".join(
        f"[{hit['locator']}] {' '.join(hit['text'].split())}" for hit in hits)
    said = ollama.generate(
        model, PROMPT.format(context=context, question=question),
        host=host, num_predict=260, temperature=0.2, transport=transport,
    ).strip()

    if not said or REFUSAL.lower() in said.lower():
        # The model's own refusal is kept, and the citations dropped with it:
        # naming books beside "I cannot answer" implies they were consulted and
        # found wanting on this point, which is more than was established.
        return Answer(REFUSAL, question, grounded=False)

    # **Voices are corroborated, not counted.** A first version listed the
    # distinct authors among the retrieved passages and called that
    # corroboration -- "three passages I read happened to be by different
    # people", which two books can satisfy while saying unrelated things. E79
    # built the actual rule and the answer path shipped without it.
    #
    # **Generated rules are not voices.** `python-chess: Board.attacks(d4)` is
    # computation, and calling it an author produced "python-chess describes it
    # this way" followed by a warning that only one author discusses it -- a
    # hedge about scholarly consensus attached to arithmetic.
    computed = any(hit.get("generated") for hit in hits)
    quoted = [hit for hit in hits if not hit.get("generated")]

    candidates = [
        Attestation(question, hit["locator"],
                    hit.get("lineage") or hit.get("author") or "",
                    " ".join(hit["text"].split()))
        for hit in quoted
    ]
    vectors = {hit["locator"]: hit.get("embedding") or [] for hit in quoted}
    agreed = corroborate(question, candidates, vectors)

    # Everyone whose passage was read is still named -- they are cited, and
    # hiding a source because it disagreed would be the opposite of honest.
    # `corroborated` is what the agreement check decides.
    named: list[str] = []
    for hit in quoted:
        who = hit.get("author") or ""
        if who and who not in named:
            named.append(who)

    return Answer(
        text=said,
        question=question,
        locators=tuple(hit["locator"] for hit in hits),
        voices=tuple(named),
        computed=computed,
        agreeing=agreed.independent,
    )
