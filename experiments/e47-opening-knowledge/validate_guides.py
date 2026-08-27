"""Check every link in the guide library, and stamp what was found.

Screen: docs/notes/experiments.e48-opening-agent.md, which fetched the 90 curated
links and found one already dead — Owen Defense, HTTP 410 — sitting in the library
ready to be printed to a player.

**A maintenance pass, run deliberately, never during a report.** `for_opening`
reads a local file; this is what puts the truth in that file. Fetches are cached
and spaced, so a re-run costs almost nothing and a first run is polite.

`alive=False` is the only state that hides a link. Never-checked stays visible:
the author approved it by opening it, so absence of a check is not evidence of
death (L-046).

Usage:
    python validate_guides.py [--library data/openings/guides.json] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_agent import OpeningResourceAgent, WorklistSearcher  # noqa: E402
from chesscoach.opening_guides import DEFAULT_LIBRARY, GuideLibrary  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "e48-opening-agent" / "results" / "fetch-cache.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    library = GuideLibrary.load(args.library)
    print(f"{len(library)} links, {len(library.unchecked)} never checked")

    # The searcher is unused here — validation never acquires — so the worklist
    # one is passed to make that explicit rather than reaching for the network.
    agent = OpeningResourceAgent(WorklistSearcher(), cache_path=CACHE)
    checked = library.validated(agent, today=date.today().isoformat())

    print(f"\n{'reachable':<24}{len(checked) - len(checked.dead):>5}")
    print(f"{'confirmed dead':<24}{len(checked.dead):>5}")
    if checked.dead:
        print("\nthese are now hidden from players:")
        for guide in checked.dead:
            print(f"  {guide.opening:<26}{guide.title[:44]}")
            print(f"    {guide.url}")

    gained = sum(1 for g in checked._guides if g.summary)
    print(f"\n{'with a page description':<24}{gained:>5}")

    if args.dry_run:
        print("\ndry run — nothing written")
        return 0

    checked.save(args.library)
    print(f"\nstamped and written to {args.library}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
