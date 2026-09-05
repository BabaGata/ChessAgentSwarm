"""Seed the tactical definitions from Lichess, where the shelf has none.

Note: docs/notes/experiments.e87-seed-lichess-themes.md

[[experiments.e86-detector-audit]] found the knowledge base unusable as a
reference — `fork`'s stored definition was a definition of a *skewer*. The cause
is not the extractor: for these concepts **the definition is not in the corpus**.
`knowledge_swarm.TERMS` says so itself — *"tactics: the web knows these, the
classical books mostly do not"* — and [[experiments.e64-chess-books]] measured
`skewer` at **zero** occurrences across the shelf. Asked for a definition the
books do not contain, a well-behaved extractor returns the nearest passage
sharing a word.

So these are seeded rather than extracted, from the source the code already
committed to. `tactics.py`:

    Motif names are the **Lichess theme keys**, which is what will let the
    detectors be validated against the CC0 puzzle database.

Definitions are quoted **verbatim** from lichess-org/lila's `puzzleTheme.xml`
(AGPL, free — C7), which is the same project whose keys the detectors use.

**Nothing here is endorsed.** `draft()` writes `reviewed=False` and refuses to
overwrite anything the author has already reviewed. Endorsement is the author's
act and this script cannot perform it.

    python seed.py [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from chesscoach.knowledge import Entry, KnowledgeBase, Source  # noqa: E402

THEMES_URL = (
    "https://raw.githubusercontent.com/lichess-org/lila/master/"
    "translation/source/puzzleTheme.xml"
)
PUBLISHER = "Lichess (lichess-org/lila), puzzle theme definitions"

# Verbatim from `puzzleTheme.xml`. The detector keys on the left are the Lichess
# theme keys, which is the whole reason this source fits.
#
# **Name and description, joined.** The file holds them as two strings, because
# the description is written to sit under a heading and so does not repeat the
# term: the fork description never says "fork", and the skewer description says
# "pin" but not "skewer". The naming gate rejected all eight when the description
# was seeded alone -- correctly, since a sentence that does not name its subject
# cannot be checked against it. Both halves are verbatim; only the colon is ours.
DEFINITIONS: dict[str, str] = {
    "fork": "Fork: A move where a piece attacks two or more opposing pieces simultaneously.",
    "pin": (
        "Pin: A tactic involving pins, where a piece is unable to move without revealing "
        "an attack on a higher value piece."
    ),
    "skewer": (
        "Skewer: A motif involving a high value piece being attacked, moving out the way, and "
        "allowing a lower value piece behind it to be captured or attacked, the "
        "inverse of a pin."
    ),
    "discoveredAttack": (
        "Discovered Attack: Moving a piece (such as a knight), that previously blocked an attack by a "
        "long range piece (such as a rook), out of the way of that piece."
    ),
    "hangingPiece": (
        "Hanging Piece: A tactic involving an opponent piece being undefended or insufficiently "
        "defended and free to capture."
    ),
    "backRankMate": (
        "Back Rank Mate: Checkmate the king on the home rank, when it is trapped there by its own pieces."
    ),
    "capturingDefender": (
        "Capturing Defender: Removing a piece that is critical to defence of another piece, allowing the "
        "now undefended piece to be captured on a following move."
    ),
    "trappedPiece": "Trapped Piece: A piece is unable to escape capture as it has limited moves.",
}

# `hangingPawn` is deliberately absent: **Lichess has no such theme.** It was
# added to this project for a measured reason -- every one of 45 reviewer notes
# mentioning a pawn was unnameable (E31) -- but it cannot be seeded from here and
# it cannot be validated against the puzzle database either. Left for the author.
NO_LICHESS_THEME = ("hangingPawn",)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--path", type=Path, default=REPO / "data" / "knowledge.json")
    args = parser.parse_args()

    base = KnowledgeBase.load(args.path)
    today = datetime.date.today().isoformat()
    source = Source(url=THEMES_URL, publisher=PUBLISHER, evidence_class="expert-consensus")

    seeded, skipped, kept_sources = [], [], 0
    for key, definition in sorted(DEFINITIONS.items()):
        existing = base.get(key)
        if existing is not None and existing.reviewed:
            skipped.append(key)  # the author's judgement outranks this
            continue

        # Any usable source already on the entry is kept alongside, not thrown
        # away: a second independent statement of the same concept is
        # corroboration, and this file is where that is recorded.
        carried = tuple(
            s for s in (existing.sources if existing else ()) if s.usable and s.url != THEMES_URL
        )
        kept_sources += len(carried)

        base.draft(Entry(
            key=key,
            definition=definition,
            quote=definition,
            sources=(source,) + carried,
            drafted_by="lichess puzzleTheme.xml (seeded verbatim, not extracted)",
            checked_on=today,
        ))
        seeded.append(key)

    print(f"seeded   {len(seeded)}: {seeded}")
    print(f"skipped  {len(skipped)} already reviewed by the author: {skipped}")
    print(f"carried  {kept_sources} pre-existing usable sources alongside")
    print(f"no Lichess theme, left alone: {list(NO_LICHESS_THEME)}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    base.save(args.path)
    print(f"\nwrote {args.path}")
    print("Every entry is reviewed=False. Endorsement is the author's act.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
