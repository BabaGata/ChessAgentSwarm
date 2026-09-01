"""Which concepts the shelf actually agrees about.

Design: docs/notes/design.graph-knowledge-base.md § "The evidence rule"

The author's rule, which replaces one endorsement per entry with one rule
endorsed once:

    "count how many sources have mentioned some concept and described it in a
    similar way and then take what has been mentioned several times as a
    confirmed knowledge"

Three things make that a measurement rather than a vote.

**Lineage, not file.** Pre-1929 chess books copy each other, and one author with
two books is one voice. `Source.lineage` is the author, and the count is over
distinct lineages -- otherwise the number measures ancestry.

**Agreement is checked, not assumed.** Two passages both mentioning "backward
pawn" are not two descriptions of it. Agreement is embedding similarity between
the passages that describe it, so the same idea in different words counts and two
unrelated remarks do not.

**Verbatim agreement is a warning, not a confirmation.** Near-identical phrasing
between two books is the signature of copying. It is reported as a shared-ancestor
flag, because it is *paraphrase* agreement that carries evidence.

**Nothing here decides what is true.** A corroborated concept is one the
literature describes consistently, and that is what the base may say: "Capablanca,
Staunton and Philidor describe it this way", with the passages. Said as truth it
would be folklore with a citation count attached.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Above this, two passages are saying the same thing in their own words.
# Calibrated in E79 rather than chosen: swept against pairs the author can read.
AGREEMENT = 0.60

# Above this, two passages are not agreeing -- one is copying the other, or both
# copy a third. Reported rather than counted.
SHARED_ANCESTOR = 0.95

# How many independent lineages must describe a concept before the base will
# serve it. Two is the minimum that can mean anything; the sweep says what each
# setting buys.
MIN_LINEAGES = 2


@dataclass(frozen=True)
class Attestation:
    """One passage that describes a concept, and whose voice it is."""

    concept: str
    locator: str
    lineage: str
    text: str
    similarity: float = 0.0


@dataclass(frozen=True)
class Corroboration:
    """What the shelf says about one concept, and how independently."""

    concept: str
    attestations: tuple[Attestation, ...] = ()
    # Pairs whose wording is close enough to suggest one copied the other.
    shared_ancestors: tuple[tuple[str, str], ...] = ()

    @property
    def lineages(self) -> tuple[str, ...]:
        return tuple(sorted({a.lineage for a in self.attestations}))

    @property
    def independent(self) -> int:
        """Distinct voices, which is the number the rule is about."""
        return len(self.lineages)

    def servable(self, minimum: int = MIN_LINEAGES) -> bool:
        """Enough independent voices, agreeing in their own words.

        A concept below the bar is **stored and not served**, and the count of
        those is the honest measure of what a free shelf supports.
        """
        return self.independent >= minimum

    @property
    def attribution(self) -> str:
        """What the base is allowed to say: who describes it, not that it is so."""
        voices = self.lineages
        if not voices:
            return ""
        if len(voices) == 1:
            return f"{voices[0]} describes it this way"
        return f"{', '.join(voices[:-1])} and {voices[-1]} describe it this way"


def cosine(left, right) -> float:
    """Similarity of two embeddings, 0 when either has no magnitude."""
    dot = sum(a * b for a, b in zip(left, right))
    size = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / size if size else 0.0


def corroborate(
    concept: str,
    candidates: list[Attestation],
    vectors: dict[str, list[float]],
    agreement: float = AGREEMENT,
    shared_ancestor: float = SHARED_ANCESTOR,
) -> Corroboration:
    """Keep the passages that agree with at least one other **voice**.

    A passage agreeing only with another book by the same author is not
    corroborated: that is the lineage rule applied to the agreement step as well
    as to the count, and without it one author's two books would confirm each
    other.
    """
    kept: list[Attestation] = []
    flags: list[tuple[str, str]] = []

    for first in candidates:
        best = 0.0
        for second in candidates:
            if first.locator == second.locator or first.lineage == second.lineage:
                continue
            score = cosine(vectors.get(first.locator, []), vectors.get(second.locator, []))
            if score >= shared_ancestor:
                pair = tuple(sorted((first.locator, second.locator)))
                if pair not in flags:
                    flags.append(pair)  # type: ignore[arg-type]
            best = max(best, score)
        if best >= agreement:
            kept.append(Attestation(concept, first.locator, first.lineage,
                                    first.text, round(best, 4)))

    return Corroboration(
        concept=concept,
        attestations=tuple(sorted(kept, key=lambda a: (-a.similarity, a.locator))),
        shared_ancestors=tuple(flags),
    )
