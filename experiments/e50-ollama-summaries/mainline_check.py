"""Which rows carry a family's own bare name, and do they form a chain?

`_pick_main_line` takes the DEEPEST row named plainly for the family, on the
argument that a player asking what the Pirc is wants three moves rather than one.
That was measured on six families where those rows form a progressive chain.

The Indian Defense breaks it: the deepest plainly-named row is
`1. d4 Nf6 2. c4 e6 3. Qb3`, an obscure sideline presented as the main line. The
question is whether the rule needs the rows to be a chain, and how often they are.

Usage:
    python mainline_check.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook  # noqa: E402

FAMILIES = (
    "Indian Defense", "Pirc Defense", "Sicilian Defense", "French Defense",
    "Italian Game", "Queen's Pawn Game", "Caro-Kann Defense", "English Opening",
    "Scandinavian Defense", "King's Pawn Game", "Vienna Game", "Hungarian Opening",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load()
    out = ["ROWS NAMED PLAINLY FOR THE FAMILY", "=" * 78, "",
           "A chain means each row extends the one before it, so the deepest is a",
           "continuation of the main line rather than a different line entirely.", ""]

    for family in FAMILIES:
        exact = [o for o in book.lines_for(family) if o.name.strip() == family]
        chained = all(
            later.pgn.startswith(earlier.pgn)
            for earlier, later in zip(exact, exact[1:])
        )
        from chesscoach.opening_resource import _pick_main_line
        chosen = _pick_main_line(book.lines_for(family), family)
        out.append("-" * 78)
        out.append(f"{family}   {len(exact)} rows   chain={chained}")
        for opening in exact:
            mark = "  <-- CHOSEN" if chosen and opening.pgn == chosen.pgn else ""
            out.append(f"   {opening.plies:>2} plies  {opening.pgn}{mark}")

    text = "\n".join(out)
    print(text)
    (args.out / "mainline-check.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
