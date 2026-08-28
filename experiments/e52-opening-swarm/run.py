"""Scout -> Assessor -> Compiler, run end to end on real openings.

Screen: docs/notes/experiments.e52-opening-swarm.md

Three agents with three roles, each doing only its own job:

    SCOUT      writes queries, casts a wide net    judges nothing
    ASSESSOR   discards what is unusable           writes nothing
    COMPILER   writes the brief from what survived searches nothing

The openings are ones with **no curated guide**, so nothing here is being
re-derived from material a person already chose — the swarm starts from a name.

What is measured: pages found, pages discarded (with the Assessor's reasons),
sentences that survived, and whether each half of the brief passed its grounding
check. The brief itself is printed in full, because whether it reads well is the
author's judgement and no count substitutes for it.

Needs SearxNG and Ollama:
    cd ../e50-ollama-summaries/searxng && docker compose up -d

Usage:
    python run.py [--model qwen2.5:3b]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_agent import SearchUnavailable, SearxSearcher  # noqa: E402
from chesscoach.opening_swarm import OpeningSwarm  # noqa: E402
from chesscoach.runstore import RunStore  # noqa: E402
from chesscoach.skiplist import DEFAULT_PATH, SkipList  # noqa: E402

CACHE = Path(__file__).parent / "results" / "pages.json"
AGENT = "ChessAgentSwarm/0.1 (thesis research; opening brief)"

# Two groups on purpose. An all-zero run on obscure openings cannot distinguish
# "the swarm does not work" from "these openings have no good pages", so the
# second group is openings the author has already seen good material for.
UNCOVERED = ("Bird Opening", "Grob Opening", "Owen Defense")
WELL_COVERED = ("Pirc Defense", "London System", "French Defense")
OPENINGS = UNCOVERED + WELL_COVERED


class Fetcher:
    """Fetches a page once and remembers it, so a re-run costs nothing."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._cache: dict[str, str] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    def __call__(self, url: str) -> str:
        if url in self._cache:
            return self._cache[url]
        try:
            request = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(400_000).decode("utf-8", "replace")
        except Exception:
            body = ""
        self._cache[url] = body
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache), encoding="utf-8")
        time.sleep(1.5)
        return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--store", type=Path, default=None,
                        help="SQLite file to record every agent's output into")
    parser.add_argument("--only", default=None,
                        help="one opening, for a paced live confirmation")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # The skip list persists between runs, so a later run does less work than an
    # earlier one -- that is the point of it being learned rather than fixed.
    skiplist = SkipList.load(DEFAULT_PATH)
    store = RunStore(args.store) if args.store else None
    swarm = OpeningSwarm(searcher=SearxSearcher(limit=6), fetch=Fetcher(CACHE),
                         skiplist=skiplist, model=args.model, store=store)

    openings = (args.only,) if args.only else OPENINGS
    lines = [
        f"THE OPENING SWARM  model={args.model}",
        "=" * 78,
        "",
        "SCOUT writes queries. ASSESSOR discards. COMPILER writes the brief.",
        "Every sentence the Compiler works from is verbatim from a page the",
        "Assessor kept, and both halves of the brief are checked against them.",
        "",
        "NOT ENDORSED: no source here is reviewed=true.",
        "",
    ]
    briefs = grounded_plans = grounded_watches = 0

    for opening in openings:
        lines.append("=" * 78)
        lines.append(opening)
        lines.append("")
        try:
            brief = swarm.run(opening)
        except SearchUnavailable as error:
            lines.append(f"  COULD NOT SEARCH -- {error}")
            continue
        trace = swarm.trace[-1]

        lines.append(f"  SCOUT      {trace['found']} pages to read; "
                     f"{len(trace['skipped_before_fetch'])} skipped before fetching"
                     + (f" ({', '.join(sorted(set(trace['skipped_before_fetch'])))})"
                        if trace["skipped_before_fetch"] else ""))
        lines.append(f"  ASSESSOR   read {trace['read']}, "
                     f"{trace['yielded']} yielded usable sentences")
        for domain, reason in trace["learned"]:
            lines.append(f"               learned to skip {domain} ({reason})")
        for note in brief.notes[:5]:
            lines.append(f"               \"{note[:92]}\"")
        lines.append("")

        for point in brief.plans:
            lines.append(f"  - PLAN   {point}")
        for point in brief.watches:
            lines.append(f"  - WATCH  {point}")
        for point in brief.dropped:
            lines.append(f"    dropped ({point.kind}) -- {point.dropped_for[:62]}")
        if not brief.points:
            lines.append("  (no points -- nothing approved to write from)")
        grounded_plans += len(brief.plans)
        grounded_watches += len(brief.watches)

        briefs += int(brief.accepted)
        for url in brief.sources:
            lines.append(f"  source {url}")
        lines.append("")
        print(f"  {opening}: {'brief' if brief.accepted else 'nothing'}", flush=True)

    lines += [
        "=" * 78,
        "WHAT THIS MEASURES",
        "",
        f"  openings with a usable brief   {briefs} of {len(openings)}",
        f"  plan points kept               {grounded_plans}",
        f"  opponent points kept           {grounded_watches}",
        f"  sites on the skip list         {len(swarm.skiplist)} "
        f"({len(swarm.skiplist.learned)} learned)",
        "",
        "A brief is not a good brief. Whether these read well, and whether the",
        "chess is right, is the author's judgement -- the checks only establish",
        "that nothing concrete came from outside the cited pages.",
    ]
    swarm.skiplist.save(DEFAULT_PATH)
    if store is not None:
        store.close()
    out = args.out / "briefs.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
