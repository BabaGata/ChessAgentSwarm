"""Download the CC0 opening book and build the position-keyed store.

Source: https://github.com/lichess-org/chess-openings — **CC0 public domain**, so
unencumbered, unlike the Wikibooks ideas layer that follows it.

The five TSVs carry `eco`, `name`, `pgn`. The `epd` column exists only in a
`dist/` build that is **not on master**, so the position key is computed here
with python-chess instead — which removes a dependency rather than adding one.

Data is not committed, as with the corpora: this regenerates it in under a
second.

Usage:
    python fetch_book.py [--out data/openings/book.json]
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import DEFAULT_BOOK, OpeningBook  # noqa: E402

BASE = "https://raw.githubusercontent.com/lichess-org/chess-openings/master/"
VOLUMES = "abcde"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_BOOK)
    args = parser.parse_args()

    rows: list[list[str]] = []
    for volume in VOLUMES:
        url = f"{BASE}{volume}.tsv"
        with urllib.request.urlopen(url, timeout=60) as response:
            text = response.read().decode("utf-8")
        lines = text.splitlines()[1:]
        volume_rows = [line.split("\t") for line in lines if line.strip()]
        rows += [r for r in volume_rows if len(r) >= 3]
        print(f"  {volume}.tsv: {len(volume_rows)} lines", flush=True)

    book = OpeningBook.from_rows((r[0], r[1], r[2]) for r in rows)
    book.save(args.out)
    print(f"\n{len(rows)} lines downloaded, {len(book)} positions kept "
          f"({len(rows) - len(book)} duplicates or unreplayable)")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
