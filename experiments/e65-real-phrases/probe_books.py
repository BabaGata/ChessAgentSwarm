"""Which phrases do chess writers actually use for the things we detect?

Design: docs/notes/design.knowledge-base.md

E64 found that nine of fourteen claim keys are this project's own jargon:
Capablanca has a chapter on **castling**, and nobody has written a definition of
**"late castling"** because it is not a term. So the knowledge base was asking
the literature to define words the literature has never used.

The author's fix, which is smaller than restructuring:

    "try to find on internet the actuall phrases for these concepts and for
    every concept that is being detected add multiple key words that can be used
    for searching"

**Discovered rather than asserted.** Every phrase below is a candidate; this
script counts how often each appears across 1.4 MB of Capablanca, Edward Lasker
and Staunton. A phrase the masters never write is not the phrase to search for
-- and the counts also say which of our claims the classical literature has no
word for at all, which is worth knowing before searching the web for one.

The book check is free and instant. `probe_web.py` does the second half.

    python probe_books.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.books import BookLibrary  # noqa: E402

# Candidates per claim. Mine to propose, the books' to confirm or refuse.
CANDIDATES: dict[str, tuple[str, ...]] = {
    "fork": ("fork", "forking", "double attack", "royal fork", "family fork"),
    "pin": ("pin", "pinned", "pinning", "absolute pin"),
    "skewer": ("skewer", "x-ray", "through attack"),
    "hangingPiece": ("hanging piece", "undefended piece", "loose piece", "en prise",
                     "unprotected piece"),
    "hangingPawn": ("hanging pawn", "isolated pawn", "backward pawn", "weak pawn"),
    "trappedPiece": ("trapped", "shut in", "no retreat", "hemmed in"),
    "discoveredAttack": ("discovered attack", "discovered check", "battery"),
    "capturingDefender": ("removing the defender", "capturing the defender",
                          "removing the guard", "deflection", "exchange the defender"),
    "late_castling": ("castle early", "king safety", "castling", "delay castling",
                      "safety of the king"),
    "slow_development": ("development", "develop the pieces", "loss of time",
                         "lag in development", "gain of time", "tempo"),
    "repeat_move": ("same piece twice", "moving the same piece", "loss of time",
                    "waste of time", "lost tempo"),
    "pawn_error": ("pawn moves", "too many pawn moves", "premature advance",
                   "pawn advance"),
    "allows_square": ("outpost", "weak square", "hole", "strong square"),
    "allows_pressure": ("attack on the king", "king side attack", "king safety",
                        "assault on the king"),
    "endgame_error": ("endgame", "end game", "king activity", "opposition"),
    "moved_into_attack": ("en prise", "leaving it en prise", "unprotected",
                          "attacked piece"),
    "long_think_error": ("time limit", "clock", "time trouble"),
}


def main() -> int:
    library = BookLibrary.load()
    if not len(library):
        print("no books on the shelf; run experiments/e64-books/fetch.py")
        return 1

    corpus = " ".join(library.texts.values()).lower()
    print(f"{len(library)} books, {len(corpus) // 1024} KB of chess writing")
    print()
    print("How often the masters actually use each candidate phrase.")
    print("A phrase they never write is not the phrase to search for.")
    print()

    unnamed = []
    for claim, phrases in CANDIDATES.items():
        counts = [(p, corpus.count(p.lower())) for p in phrases]
        counts.sort(key=lambda row: -row[1])
        found = [f"{p} ({n})" for p, n in counts if n]
        missing = [p for p, n in counts if not n]
        print(f"  {claim:20} {', '.join(found) if found else 'NOTHING'}")
        if missing:
            print(f"  {'':20} unused: {', '.join(missing)}")
        if not found:
            unnamed.append(claim)

    print()
    print("=" * 76)
    print("CLAIMS THE CLASSICAL LITERATURE HAS NO WORD FOR")
    print("=" * 76)
    print()
    if unnamed:
        for claim in unnamed:
            print(f"  {claim}")
        print()
        print("These need the web, or they need to point at a concept that does")
        print("have a name. A search is not going to invent the vocabulary.")
    else:
        print("  none -- every claim has at least one phrase the books use")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
