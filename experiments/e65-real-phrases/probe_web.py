"""Which candidate phrases actually retrieve chess pages?

Design: docs/notes/design.knowledge-base.md

`probe_books.py` asked 1.4 MB of Capablanca, Lasker and Staunton which phrases
they use. This asks the web the complementary question, because the two sources
fail in opposite places: the books have no word for a skewer or an outpost
because those terms postdate them, and the web has plenty.

**A phrase earns its place by returning chess**, not by sounding right. The
measure is how many results come back and how many of their titles mention
chess -- a phrase that returns twenty pages about something else is worse than
one that returns three about the right thing.

    python probe_web.py [--phrases "skewer chess,outpost chess"]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SEARX = "http://localhost:8080/search"
SPACING = 6.0

# The gaps the books left. Each line is one claim and the phrasings worth trying
# for it, including the ones the classical literature has no word for at all.
GAPS: dict[str, tuple[str, ...]] = {
    "capturingDefender": ("removing the defender chess", "removing the guard chess",
                          "deflection chess tactic", "undermining chess tactic"),
    "skewer": ("skewer chess tactic", "x-ray attack chess"),
    "allows_square": ("outpost chess", "weak square chess", "hole chess position"),
    "fork": ("fork chess tactic", "double attack chess"),
    "trappedPiece": ("trapped piece chess", "piece with no squares chess"),
}


def ask(query: str) -> tuple[int, int]:
    """Results returned, and how many name chess in their title."""
    url = f"{SEARX}?{urllib.parse.urlencode({'q': query, 'format': 'json'})}"
    try:
        with urllib.request.urlopen(url, timeout=40) as response:
            payload = json.load(response)
    except Exception:
        return -1, -1
    results = payload.get("results", [])
    chessy = sum(1 for r in results if "chess" in (r.get("title") or "").lower())
    return len(results), chessy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phrases", default="")
    args = parser.parse_args()

    if args.phrases:
        plan = {"ad hoc": tuple(p.strip() for p in args.phrases.split(",") if p.strip())}
    else:
        plan = GAPS

    print("WHICH PHRASES RETURN CHESS?")
    print("=" * 74)
    print()
    print(f"{'phrase':<36}{'results':>9}{'chess titles':>14}")
    print("-" * 60)
    for claim, phrases in plan.items():
        print(f"{claim}")
        for phrase in phrases:
            total, chessy = ask(phrase)
            if total < 0:
                print(f"  {phrase:<34}{'FAILED':>9}")
            else:
                print(f"  {phrase:<34}{total:>9}{chessy:>14}")
            time.sleep(SPACING)
        print()
    print("A phrase returning pages that do not name chess is not a chess phrase,")
    print("however right it sounds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
