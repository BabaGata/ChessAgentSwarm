"""Does `SearxSearcher` work against a live SearxNG?

Screen: docs/notes/experiments.e50-ollama-summaries.md

[[experiments.e48-opening-agent]] shipped `SearxSearcher` with an honest caveat:
*"Untested against a live instance. No SearxNG is running here, so what is
verified is the parsing, the filtering and the failure behaviour, not the quality
of what it returns."* This removes that caveat, or fails to.

The openings asked about are ones with **no curated guide** — the case the
searcher exists for. A hand-made candidate list cannot help there by definition.

Start the instance first:
    cd searxng && docker compose up -d

Usage:
    python search_check.py [--base http://localhost:8080]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_agent import Gap, SearchUnavailable, SearxSearcher  # noqa: E402

# Families the review players reached that the library has nothing for.
UNCOVERED = (
    "Bird Opening",
    "Grob Opening",
    "Nimzo-Larsen Attack",
    "Owen Defense",
    "Alekhine Defense",
    "Benoni Defense",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8080")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    searcher = SearxSearcher(base_url=args.base)
    lines = [
        "SEARX SEARCHER AGAINST A LIVE INSTANCE",
        "=" * 78,
        "",
        "Openings with no curated guide -- the case the searcher exists for.",
        "Results are unreviewed candidates, never advice.",
        "",
    ]
    found_for = 0
    for opening in UNCOVERED:
        gap = Gap(opening=opening, games=5, share=0.30)
        lines.append("-" * 78)
        lines.append(f"{opening}")
        lines.append(f"  query: {gap.query}")
        try:
            results = searcher.search(gap)
        except SearchUnavailable as error:
            # Separated from "found nothing" on purpose (L-046).
            lines.append(f"  COULD NOT ASK -- {error}")
            print(f"  {opening}: unavailable", flush=True)
            continue
        if not results:
            lines.append("  found nothing")
        else:
            found_for += 1
            for title, url, publisher in results:
                lines.append(f"  {publisher:<26} {title[:60]}")
                lines.append(f"    {url}")
        print(f"  {opening}: {len(results)} candidates", flush=True)

    lines += [
        "=" * 78,
        f"openings with at least one candidate: {found_for} of {len(UNCOVERED)}",
        "",
        "Finding a link is not finding a guide -- E48's whole result. Whether",
        "these pages carry plan-level instruction is what the extractor and the",
        "author's review decide, not this count.",
    ]
    out = args.out / "search-check.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
