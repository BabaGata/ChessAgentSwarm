"""Build the full opening resource for every family the review players play.

Screen: docs/notes/experiments.e49-opening-resources.md

The author approved one entry — FreeChessTrainer's Pirc page — and asked for the
same shape everywhere: *"the main lines to be fetched with maybe a few variants.
Short summary or description of the information about the plans and a link for
further references."*

So this produces exactly that, one family at a time, and the number that decides
whether the approach works is **how many candidate pages yield a plan sentence at
all**. E48 established that the agent can always find a *link*; the open question
is whether a link carries anything a 1500 can act on. A page that yields nothing
is the honest answer to that for that page, and is counted rather than patched.

**Only the quotes are cached, never the pages.** Caching HTML would put a
copy of ninety copyrighted articles in the repository, which is the thing the
whole design exists to avoid. The cost is that changing the selection rules
means re-fetching; the fetches are spaced and the cache makes a re-run free.

Usage:
    python build_resources.py [--families 12] [--refetch]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e47-opening-knowledge"))

from candidates import CANDIDATES  # noqa: E402

from chesscoach.opening_guides import DEFAULT_LIBRARY, GuideLibrary  # noqa: E402
from chesscoach.opening_plans import MAX_QUOTES, plan_quotes  # noqa: E402
from chesscoach.opening_resource import build_resource  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
QUOTE_CACHE = Path(__file__).parent / "results" / "quotes.json"
AGENT = "ChessAgentSwarm/0.1 (thesis research; opening plan extraction)"
POLITE_SECONDS = 1.5


def quotes_for(url: str, cache: dict, refetch: bool) -> dict:
    """Plan sentences from one page, fetched once and remembered."""
    if url in cache and not refetch:
        return cache[url]
    try:
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(400_000).decode("utf-8", "replace")
        entry = {"status": str(response.status),
                 "quotes": list(plan_quotes(body, limit=MAX_QUOTES))}
    except urllib.error.HTTPError as error:
        # A refusal is not an absence of plans (L-046) -- kept apart so the
        # denominator counts pages actually read.
        entry = {"status": f"HTTP {error.code}", "quotes": []}
    except Exception as error:
        entry = {"status": type(error).__name__, "quotes": []}
    cache[url] = entry
    QUOTE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUOTE_CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    time.sleep(POLITE_SECONDS)
    return entry


def repertoires(book: OpeningBook) -> tuple[Counter, dict[str, list[str]]]:
    """What the review players actually play, family and subline both."""
    families: Counter = Counter()
    lines: dict[str, list[str]] = {}
    for path in sorted(ROOT.glob("games/*.pgn")):
        for game in load_games(path)[:20]:
            walk = book.walk(list(game.moves))
            if not walk.opening:
                continue
            family = walk.opening.name.split(":")[0].strip()
            families[family] += 1
            lines.setdefault(family, []).append(walk.opening.name)
    return families, lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", type=int, default=12)
    parser.add_argument("--refetch", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load()
    library = GuideLibrary.load(DEFAULT_LIBRARY)
    families, reached = repertoires(book)
    cache = json.loads(QUOTE_CACHE.read_text(encoding="utf-8")) if QUOTE_CACHE.exists() else {}

    # Candidate keys may name a SUBLINE now ("Indian Defense: Accelerated
    # London System"), so a family is covered when any key falls inside it.
    by_family: dict[str, list] = {}
    for key, entries in CANDIDATES.items():
        by_family.setdefault(key.split(":")[0].strip(), []).extend(entries)

    wanted = [f for f, _ in families.most_common() if f in by_family][: args.families]

    lines = [
        "OPENING RESOURCES — moves, quoted plans, and a link",
        "=" * 78,
        "",
        "The shape the author approved on the Pirc entry, built for every family.",
        "",
        "Every sentence below is QUOTED VERBATIM from the page credited beside it.",
        "Nothing here is written by the system. Move lists are from",
        "lichess-org/chess-openings (CC0). Variants are ordered by how often these",
        "players actually reached them.",
        "",
        "NOT ENDORSED: no page here is reviewed=true, so none of it reaches a",
        "player yet. This is the material for that review.",
        "",
    ]

    pages_read = pages_with_plans = 0
    families_with_plans = 0

    for family in wanted:
        resource = build_resource(family, book, library, reached=reached.get(family, []))
        lines.append("-" * 78)
        lines.append(f"{family}  —  {families[family]} games")
        lines.append("")

        if resource.main_line:
            lines.append(f"  MAIN LINE   {resource.main_line.moves}")
        for variant in resource.variants:
            played = f"{variant.games} games" if variant.games else "not played"
            lines.append(f"    {variant.variation[:34]:<36}{variant.moves[:44]:<46}{played}")
        lines.append("")

        found_here = False
        for title, url, publisher in by_family[family]:
            entry = quotes_for(url, cache, args.refetch)
            if entry["status"].startswith("HTTP") or not entry["status"].isdigit():
                lines.append(f"  [{publisher}] not read — {entry['status']}")
                continue
            pages_read += 1
            if not entry["quotes"]:
                lines.append(f"  [{publisher}] read, no plan sentence found")
                continue
            pages_with_plans += 1
            found_here = True
            lines.append(f"  PLANS, quoted from {publisher}:")
            for quote in entry["quotes"]:
                lines.append(f'    "{quote}"')
            lines.append(f"    further reading: {url}")
        families_with_plans += int(found_here)
        lines.append("")
        print(f"  {family}: done", flush=True)

    lines += [
        "=" * 78,
        "WHAT THIS MEASURES",
        "",
        f"  pages read                        {pages_read:>4}",
        f"  pages yielding a plan sentence    {pages_with_plans:>4}"
        f"  ({100 * pages_with_plans / pages_read:.0f} %)" if pages_read else "",
        f"  families with at least one        {families_with_plans:>4} of {len(wanted)}",
        "",
        "A page yielding nothing is a finding, not a failure of the extractor:",
        "a reference article explains what an opening IS and never what to aim",
        "for, which is exactly the distinction E48 could not measure.",
    ]

    out = args.out / "resources.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
