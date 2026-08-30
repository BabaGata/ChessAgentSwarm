"""Download the public-domain chess books the knowledge base reads.

Design: docs/notes/design.knowledge-base.md
Evidence: docs/notes/experiments.e64-chess-books.md

Three Project Gutenberg texts, out of copyright. Free in the way C7 means it:
no key, no rate limit, no signup an examiner cannot reproduce. Downloaded once
and read from disk forever, so the shelf is not in the repository -- 1.4 MB that
is reproducible from three ids.

    python experiments/e64-books/fetch.py
"""

from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.books import DEFAULT_SHELF, SHELF  # noqa: E402
from chesscoach.opening_agent import AGENT  # noqa: E402

# Gutenberg ids, from the Gutendex records rather than from memory.
IDS = {
    "capablanca-chess-fundamentals": 33870,
    "edward-lasker-chess-strategy": 5614,
    "staunton-blue-book-of-chess": 16377,
}


def main() -> int:
    DEFAULT_SHELF.mkdir(parents=True, exist_ok=True)
    for book in SHELF:
        target = DEFAULT_SHELF / f"{book.slug}.txt"
        if target.exists():
            print(f"  {book.slug}: already here, {target.stat().st_size // 1024} KB")
            continue
        gid = IDS[book.slug]
        # Two layouts, because Gutenberg uses both and which one a book has is
        # not predictable from its id.
        for url in (f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
                    f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt"):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": AGENT})
                with urllib.request.urlopen(request, timeout=60) as response:
                    body = response.read().decode("utf-8", "replace")
            except Exception as exc:
                print(f"    {type(exc).__name__} on {url.rsplit('/', 1)[-1]}")
                continue
            target.write_text(body, encoding="utf-8")
            print(f"  {book.slug}: {len(body) // 1024} KB")
            break
        else:
            print(f"  {book.slug}: COULD NOT DOWNLOAD")
        time.sleep(2)

    print(f"\nshelf: {DEFAULT_SHELF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
