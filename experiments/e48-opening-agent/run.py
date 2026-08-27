"""E48 — can the agent reproduce resources a person curated by hand?

The author: *"For test, the agent will regenerate all resources for openings that
have already been prepared and you will compare the results."*

The agent has four stages and only three can be automated, so the comparison is
in two parts and they answer different questions.

**Part 1 — validate and summarise (the automatable stages).** Take the 90 links
already curated, fetch every one, and ask: is it alive, and does the page's own
description agree with the hand-written title? This is the part that would run in
production, and it is where link rot shows up.

**Part 2 — acquire (the stage that cannot be).** Run the `WikimediaSearcher` over
the same families and put what it finds beside what a person found. It is not a
fair fight — Wikimedia is a reference and the curated links are instruction — and
the size of the gap is the point: it says what an autonomous agent costs.

Polite throughout: fetches are cached to disk and spaced, so a re-run asks only
for what it has not seen.

Usage:
    python run.py [--limit N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e47-opening-knowledge"))

from candidates import CANDIDATES  # noqa: E402

from chesscoach.opening_agent import (  # noqa: E402
    Gap,
    OpeningResourceAgent,
    SearchUnavailable,
    WikimediaSearcher,
)
from chesscoach.opening_guides import Guide  # noqa: E402

CACHE = Path(__file__).parent / "results" / "fetch-cache.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="families, 0 for all")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    families = sorted(CANDIDATES)
    if args.limit:
        families = families[: args.limit]

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text, flush=True)
        lines.append(text)

    # --- Part 1 -------------------------------------------------------------
    agent = OpeningResourceAgent(WikimediaSearcher(), cache_path=CACHE)
    alive = dead = blocked = summarised = total = 0
    dead_links: list[tuple[str, str, str]] = []
    samples: list[tuple[str, str, str]] = []

    say("PART 1 — VALIDATING THE 90 CURATED LINKS")
    say()
    for family in families:
        for title, url, publisher in CANDIDATES[family]:
            total += 1
            checked = agent.check(Guide(opening=family, title=title, url=url,
                                        publisher=publisher))
            if checked.status.startswith("HTTP 403"):
                blocked += 1
            elif checked.alive:
                alive += 1
            else:
                dead += 1
                dead_links.append((family, title, checked.status))
            if checked.summary:
                summarised += 1
                if len(samples) < 8:
                    samples.append((family, title, checked.summary))
        print(f"  {family}: done", flush=True)

    say(f"{'links checked':<34}{total:>5}")
    say(f"{'  reachable (200)':<34}{alive:>5}  ({alive/total:.0%})")
    say(f"{'  refusing a bot (403)':<34}{blocked:>5}  ({blocked/total:.0%})")
    say(f"{'  dead or unreachable':<34}{dead:>5}  ({dead/total:.0%})")
    say(f"{'  own description extracted':<34}{summarised:>5}  ({summarised/total:.0%})")

    if dead_links:
        say()
        say("DEAD OR UNREACHABLE — these would have been printed to a player:")
        for family, title, status in dead_links:
            say(f"  {status:<16}{family:<26}{title[:40]}")

    say()
    say("THE PAGE'S OWN DESCRIPTION vs THE HAND-WRITTEN TITLE")
    for family, title, summary in samples:
        say(f"\n  {family}")
        say(f"    hand : {title}")
        say(f"    page : {summary[:150]}")

    # --- Part 2 -------------------------------------------------------------
    say()
    say("=" * 78)
    say("PART 2 — WHAT THE AGENT FINDS ON ITS OWN, FOR THE SAME OPENINGS")
    say()
    say("Not a fair comparison, and that is the finding: Wikimedia is a reference")
    say("and the curated links are instruction. The gap is what an autonomous")
    say("agent costs when no free search API exists.")
    say()
    import time as _time
    found_any = unavailable = 0
    searcher = WikimediaSearcher()
    for family in families:
        try:
            results = searcher.search(Gap(opening=family, games=5, share=0.5))
        except SearchUnavailable as stop:
            unavailable += 1
            say(f"  {family:<32} COULD NOT ASK ({stop})")
            continue
        found_any += bool(results)
        _time.sleep(2.0)
        curated = ", ".join(p for _, _, p in CANDIDATES[family][:2])
        agent_found = ", ".join(p for _, _, p in results) or "nothing"
        say(f"  {family:<32} agent: {agent_found:<24} curated: {curated}")
    say()
    say(f"  families the agent found something for: {found_any}/{len(families)}")
    if unavailable:
        say(f"  families it could not even ask about: {unavailable} "
            f"— rate limited, NOT an absence")

    (args.out / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'comparison.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
