"""Assessor and Compiler on pages already fetched, with no live search.

Screen: docs/notes/experiments.e52-opening-swarm.md

Every upstream engine SearxNG queries is rate-limited after a day of runs --
brave and google cse "Suspended: too many requests", startpage "CAPTCHA" -- so a
live run reports zero pages and says nothing about the swarm. `SearxSearcher`
now raises on that rather than returning empty (L-046, fifth instance), and this
exercises the two agents that changed against the page cache instead.

**What this can show:** whether the Assessor keeps useful sentences from real
article text, and whether the Compiler's bullets survive their own checks.

**What it cannot show:** anything about the Scout, the skip list in action, or
how the pipeline behaves on an opening nobody has fetched pages for.

Usage:
    python offline.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_swarm import Assessor, Candidate, Compiler  # noqa: E402
from chesscoach.skiplist import domain_of  # noqa: E402

CACHE = Path(__file__).parent / "results" / "pages.json"

# Which cached pages belong to which opening, by a word in the URL. Crude and
# adequate: the cache was built one opening at a time.
OPENINGS = {
    "Pirc Defense": ("pirc",),
    "London System": ("london",),
    "French Defense": ("french",),
    "Bird Opening": ("bird",),
    "Owen Defense": ("owen",),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not CACHE.exists():
        print(f"no page cache at {CACHE}; run run.py first when search is available")
        return 1
    pages: dict[str, str] = json.loads(CACHE.read_text(encoding="utf-8"))

    assessor = Assessor(model=args.model)
    compiler = Compiler(model=args.model)

    lines = [
        f"ASSESSOR AND COMPILER, OFFLINE  model={args.model}",
        "=" * 78,
        "",
        "Live search is rate-limited, so these run against pages already",
        "fetched. Nothing here says anything about the Scout or the skip list.",
        "",
        "Every kept sentence is verbatim from the page. Every bullet is checked",
        "against those sentences and dropped on its own if it fails.",
        "",
    ]
    kept_plans = kept_watches = briefs = 0

    for opening, needles in OPENINGS.items():
        urls = [u for u in pages if any(n in u.lower() for n in needles) and pages[u]]
        if not urls:
            continue
        lines.append("=" * 78)
        lines.append(f"{opening}   ({len(urls)} cached pages)")
        lines.append("")

        notes: list[str] = []
        for url in urls[:5]:
            candidate = Candidate(title=url[:60], url=url, publisher=domain_of(url))
            reading = assessor.read(opening, candidate, pages[url])
            mark = f"{len(reading.sentences)} kept" if reading.useful else (
                f"not an article -> skip as {reading.skip_reason}"
                if reading.skip_reason else "nothing usable"
            )
            lines.append(f"  ASSESSOR  {candidate.publisher:<26}{mark}")
            for sentence in reading.sentences:
                lines.append(f"              \"{sentence[:88]}\"")
            notes += list(reading.sentences)
        lines.append("")

        if not notes:
            lines.append("  (no sentences approved, so the Compiler is not called)")
            lines.append("")
            print(f"  {opening}: nothing", flush=True)
            continue

        brief = compiler.compile(opening, tuple(notes))
        for point in brief.plans:
            lines.append(f"  - PLAN   {point}")
        for point in brief.watches:
            lines.append(f"  - WATCH  {point}")
        for point in brief.dropped:
            lines.append(f"    dropped ({point.kind}) -- {point.dropped_for[:60]}")
        lines.append("")
        kept_plans += len(brief.plans)
        kept_watches += len(brief.watches)
        briefs += int(brief.accepted)
        print(f"  {opening}: {len(brief.plans)} plan, {len(brief.watches)} watch",
              flush=True)

    lines += [
        "=" * 78,
        "WHAT THIS MEASURES",
        "",
        f"  openings with a usable brief   {briefs}",
        f"  plan points kept               {kept_plans}",
        f"  opponent points kept           {kept_watches}",
        "",
        "Points passing their checks is not points being right. Whether the",
        "chess holds is the author's judgement and has not happened.",
    ]
    out = args.out / "offline.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
