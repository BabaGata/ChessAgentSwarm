"""Is JSON good enough for the opening book, or is it a future problem?

Screen: docs/notes/experiments.e53-storage.md

Three questions, all answerable by measurement rather than by preference:

  **load**    how long does the book take to open, and how much memory?
  **query**   does storing it as JSON slow the theory check at all?
  **extend**  what does adding one opening cost, which is what happens every
              time a new player brings a line nobody has recorded?

The third is the one that decides whether the format becomes a problem later,
because appending to a JSON document means rewriting it.

Usage:
    python book_cost.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import DEFAULT_BOOK, OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    size = DEFAULT_BOOK.stat().st_size

    tracemalloc.start()
    started = time.perf_counter()
    book = OpeningBook.load()
    load_seconds = time.perf_counter() - started
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Query: walking real games is what the theory check actually does.
    games = []
    for path in sorted(GAMES.glob("*.pgn"))[:6]:
        games += load_games(path)[:20]
    started = time.perf_counter()
    walked = [book.walk(list(g.moves)) for g in games]
    walk_seconds = time.perf_counter() - started

    # Extend: one new opening, as when a player brings a line nobody recorded.
    payload = json.loads(DEFAULT_BOOK.read_text(encoding="utf-8"))
    started = time.perf_counter()
    payload["openings"].append(
        {"eco": "A00", "name": "Test Opening", "epd": "x", "plies": 1, "pgn": "1. a3"}
    )
    scratch = args.out / "book-rewrite.json"
    scratch.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    extend_seconds = time.perf_counter() - started
    scratch.unlink()

    # For scale: what a per-player accumulation would look like after a year.
    per_walk_us = 1e6 * walk_seconds / max(len(walked), 1)

    lines = [
        "IS JSON GOOD ENOUGH FOR THE OPENING BOOK?",
        "=" * 74,
        "",
        f"  file size                        {size / 1e6:>8.2f} MB",
        f"  named lines                      {len(book):>8}",
        f"  positions in theory              {book.positions_in_theory:>8}",
        "",
        "LOAD -- paid once per process",
        f"  parse + index                    {load_seconds:>8.2f} s",
        f"  peak memory while loading        {peak / 1e6:>8.1f} MB",
        "",
        "QUERY -- what the theory check does per game",
        f"  games walked                     {len(walked):>8}",
        f"  total                            {walk_seconds:>8.3f} s",
        f"  per game                         {per_walk_us:>8.0f} us",
        "",
        "EXTEND -- adding one opening rewrites the whole document",
        f"  read + append + write            {extend_seconds:>8.3f} s",
        "",
        "=" * 74,
        "The query number is the one that matters for the thesis: a walk is a",
        "dict lookup, and the storage format has already been paid for by then.",
    ]
    text = "\n".join(lines)
    print(text)
    (args.out / "book-cost.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
