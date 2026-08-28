"""Is every concrete thing this text says actually in its source?

Design: [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

A local model rewriting quoted sentences into natural prose is only acceptable if
the rewrite can be **checked**. This module is that check, and it is deliberately
deterministic: a second model grading the first would move the trust problem
rather than solve it.

Two tests, aimed at two different failure modes.

**Ungrounded moves.** Every square (`e4`) and every move (`Nf3`, `O-O`, `exd5`)
in the output must appear in the source. This is the highest-risk hallucination
and the most checkable: a model told to summarise the Pirc will happily write
*"break with c5"* when the page said *"break with e5"*, and that single character
is the difference between advice and misinformation.

**Novelty.** The share of content words in the output that never appear in the
source. A rewrite reuses its source's vocabulary; a model drawing on its own
chess training brings in words the page never used. This catches the softer
failure — whole ideas arriving from nowhere — where the move check cannot.

**What neither catches, stated plainly:** a sentence built entirely from the
source's own vocabulary that changes who does what. Swapping the colours —
*"White aims to undermine the center… while Black allows the pressure"* — passes
both tests against a page saying the opposite, because every word and every
square is the source's and only the roles moved.

Straightforward negation is not caught either. For a while it was, because
*"avoid"* and *"never"* are words a page recommending a break does not use — but
that was luck, not design, and correcting the inflection comparison ("aim" must
match "aiming") lowered novelty everywhere and removed the accident. Recorded
rather than mourned: nothing here understands a sentence, and a check that only
worked by coincidence was never coverage.

That residue is why the output still sits behind `reviewed=true` and why the
evidence class says `composed`, not `sourced`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A square, and a move in standard algebraic notation. Castling included because
# "O-O" is a concrete claim about what to do.
_SQUARE = re.compile(r"\b[a-h][1-8]\b")
_MOVE = re.compile(
    r"\b(?:[KQRBN][a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|"
    r"[a-h]x[a-h][1-8](?:=[QRBN])?[+#]?|O-O(?:-O)?)\b"
)

# Words carrying no claim, so their absence from the source means nothing. Kept
# short on purpose: an over-long list would let real vocabulary through as
# "common".
_STOPWORDS = frozenset("""
a an the and or but if then than that this these those there here
is are was were be been being am do does did done
to of in on at by for with from into onto over under after before
you your yours it its he she they them their his her
can could should would may might must will shall
not no nor so as such very more most much many few less least
one two three both all any each other another same
i we us our me my mine while when where which who whom whose what how why
up down out off again once about between against during through
also just only even still yet already
""".split())

# Above this share of never-seen content words, the model is writing rather than
# rewriting. Calibrated in [[experiments.e50-ollama-summaries]] against real
# output from two models, not chosen.
MAX_NOVELTY = 0.45


@dataclass(frozen=True)
class Grounding:
    """The verdict, and enough detail to argue with it."""

    grounded: bool
    ungrounded_moves: tuple[str, ...]
    novelty: float
    novel_words: tuple[str, ...]

    @property
    def reason(self) -> str:
        """Why it failed, in one line, or empty when it passed."""
        if self.ungrounded_moves:
            return "names moves not in the source: " + ", ".join(self.ungrounded_moves)
        if self.novelty > MAX_NOVELTY:
            return (f"novelty {self.novelty:.0%} over {MAX_NOVELTY:.0%}: "
                    + ", ".join(self.novel_words[:8]))
        return ""


def moves_in(text: str) -> tuple[str, ...]:
    """Every square and move named, in order, without duplicates."""
    found = _MOVE.findall(text) + _SQUARE.findall(text)
    seen: list[str] = []
    for token in found:
        if token not in seen:
            seen.append(token)
    return tuple(seen)


def content_words(text: str) -> tuple[str, ...]:
    """Lower-cased words that carry a claim."""
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]*", text.lower())
    return tuple(w for w in words if w not in _STOPWORDS and len(w) > 2)


def check(text: str, source: str) -> Grounding:
    """Is everything concrete in `text` present in `source`?

    Comparison is case-insensitive for words and **case-sensitive for moves**,
    because `Be4` and `be4` are a bishop move and a square, and conflating them
    would let a hallucinated piece move pass as a mentioned square.
    """
    source_moves = set(moves_in(source))
    ungrounded = tuple(m for m in moves_in(text) if m not in source_moves)

    source_words = set(content_words(source))
    used = content_words(text)
    novel = tuple(w for w in used if not _is_known(w, source_words))
    novelty = len(novel) / len(used) if used else 0.0

    return Grounding(
        grounded=not ungrounded and novelty <= MAX_NOVELTY,
        ungrounded_moves=ungrounded,
        novelty=novelty,
        novel_words=novel,
    )


# British and American spellings of the same word are not new content. Kept
# short and explicit rather than reaching for a stemmer: these are the ones that
# actually occur on chess pages.
_SPELLINGS = {
    "centre": "center", "centres": "centers", "central": "central",
    "defence": "defense", "defences": "defenses",
    "colour": "color", "coloured": "colored",
    "manoeuvre": "maneuver", "manoeuvres": "maneuvers",
    "counterattack": "counter", "flank": "flank",
}

# Shortest word for which a prefix relationship is evidence rather than an
# accident. Below this, "aim" would ground itself on "aimless".
_MIN_STEM = 3


def _normalise(word: str) -> str:
    return _SPELLINGS.get(word, word)


def _is_known(word: str, source_words: set[str]) -> bool:
    """Is this word the source's, allowing for inflection and spelling?

    A rewrite is allowed to say "developing" where the source said "development",
    or the checker forbids rewriting. The comparison runs **both ways** -- an
    earlier version stemmed both sides to five characters, which failed on the
    pair it most needed to handle: "aim" stems to "aim" and "aiming" to "aimin",
    so a model told to say what a player aims for was marked as inventing the
    word.
    """
    word = _normalise(word)
    if word in source_words:
        return True
    for other in source_words:
        other = _normalise(other)
        if word == other:
            return True
        if len(word) >= _MIN_STEM and other.startswith(word):
            return True
        if len(other) >= _MIN_STEM and word.startswith(other):
            return True
    return False
