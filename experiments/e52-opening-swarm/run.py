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
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    swarm = OpeningSwarm(searcher=SearxSearcher(limit=6), fetch=Fetcher(CACHE),
                         model=args.model)

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

    for opening in OPENINGS:
        lines.append("=" * 78)
        lines.append(opening)
        lines.append("")
        try:
            brief = swarm.run(opening)
        except SearchUnavailable as error:
            lines.append(f"  COULD NOT SEARCH -- {error}")
            continue
        trace = swarm.trace[-1]

        lines.append(f"  SCOUT      queries run, {trace['found']} distinct pages found")
        lines.append(f"  ASSESSOR   kept {trace['kept']}, discarded "
                     f"{trace['found'] - trace['kept']}")
        for publisher, reason in trace["discarded"]:
            lines.append(f"               - {publisher:<22}{reason[:48]}")
        lines.append(f"  READ       {len(brief.sources)} pages yielded sentences")
        for note in brief.notes[:4]:
            lines.append(f"               \"{note[:96]}\"")
        lines.append("")

        if brief.plan:
            grounded_plans += 1
            lines.append(f"  PLAN   {brief.plan}")
        elif brief.plan_grounding is not None:
            lines.append(f"  PLAN   rejected -- {brief.plan_grounding.reason[:70]}")
        else:
            lines.append("  PLAN   nothing to write from")

        if brief.watch:
            grounded_watches += 1
            lines.append(f"  WATCH  {brief.watch}")
        elif brief.watch_grounding is not None:
            lines.append(f"  WATCH  rejected -- {brief.watch_grounding.reason[:70]}")
        else:
            lines.append("  WATCH  nothing to write from")

        briefs += int(brief.accepted)
        for url in brief.sources:
            lines.append(f"  source {url}")
        lines.append("")
        print(f"  {opening}: {'brief' if brief.accepted else 'nothing'}", flush=True)

    lines += [
        "=" * 78,
        "WHAT THIS MEASURES",
        "",
        f"  openings with a usable brief   {briefs} of {len(OPENINGS)}",
        f"  PLAN halves that passed        {grounded_plans}",
        f"  WATCH halves that passed       {grounded_watches}",
        "",
        "A brief is not a good brief. Whether these read well, and whether the",
        "chess is right, is the author's judgement -- the checks only establish",
        "that nothing concrete came from outside the cited pages.",
    ]
    out = args.out / "briefs.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
