"""Are the development claims three claims, or one wearing three names?

Design: docs/notes/design.opening-development-signals.md

The design note committed to this before the claims shipped:

    "But whether all four survive is not an argument to win -- it is a number to
    measure... If two exceed |r| > 0.85 across the review corpus, they are one
    signal with two names and only the more actionable one ships."

E59 checked `slow_development` against `late_castling` alone and found r = 0.68.
The rest of the screen was never run, and the detectors have been corrected five
times since, so even that number is stale.

**No engine pass.** The peer reference stores per-player instances and
opportunities for every claim, which is exactly a per-player rate -- so the
screen reads the artefact that already exists rather than recomputing it, and it
is current by construction because the reference was rebuilt at HEAD.

    python run.py [--peers PATH] [--min-opportunities 10]
"""

from __future__ import annotations

import argparse
import json
import statistics
from itertools import combinations
from pathlib import Path

DEFAULT_PEERS = (
    Path(__file__).resolve().parents[2] / "data" / "raw" / "out" / "peers-3af3206.json"
)

# The development claims, plus the ones they might merely be restating.
DEVELOPMENT = ("slow_development.book", "late_castling.book", "repeat_move.any",
               "pawn_error.any")
COMPARISONS = ("early_error.any.own", "endgame_error.any.own")

# The design note's ceiling. Above this, two claims are one signal with two
# names and only the more actionable ships.
CEILING = 0.85


def rates(peers: dict, claim: str, floor: int) -> dict[str, float]:
    """Per-player rate for one claim, pooled across strata."""
    totals: dict[str, list[int]] = {}
    for key, contributions in peers["cells"].items():
        if key.split("|")[-1] != claim:
            continue
        for row in contributions:
            got = totals.setdefault(row["player"].lower(), [0, 0])
            got[0] += row["instances"]
            got[1] += row["opportunities"]
    return {
        player: hits / chances
        for player, (hits, chances) in totals.items()
        if chances >= floor
    }


def correlation(left: dict[str, float], right: dict[str, float]) -> tuple[float, int]:
    """Pearson r over the players both claims measured, and how many that was."""
    shared = sorted(set(left) & set(right))
    if len(shared) < 3:
        return float("nan"), len(shared)
    a = [left[p] for p in shared]
    b = [right[p] for p in shared]
    if len(set(a)) < 2 or len(set(b)) < 2:
        return float("nan"), len(shared)
    return statistics.correlation(a, b), len(shared)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", type=Path, default=DEFAULT_PEERS)
    parser.add_argument("--min-opportunities", type=int, default=10)
    args = parser.parse_args()

    peers = json.loads(args.peers.read_text(encoding="utf-8"))
    measured = {
        claim: rates(peers, claim, args.min_opportunities)
        for claim in DEVELOPMENT + COMPARISONS
    }

    print("ARE THE DEVELOPMENT CLAIMS ONE SIGNAL OR SEVERAL?")
    print("=" * 76)
    print()
    print(f"reference   {args.peers.name}")
    print(f"players     at least {args.min_opportunities} opportunities on a claim")
    print()
    for claim in DEVELOPMENT + COMPARISONS:
        found = measured[claim]
        if found:
            print(f"  {claim:26} {len(found):3} players, "
                  f"median rate {statistics.median(found.values()):.0%}")
        else:
            print(f"  {claim:26}   0 players")

    print()
    print("=" * 76)
    print(f"THE DEVELOPMENT CLAIMS AGAINST EACH OTHER   (ceiling |r| > {CEILING})")
    print("=" * 76)
    print()
    print(f"{'pair':<48}{'r':>8}{'players':>9}   verdict")
    print("-" * 74)
    duplicates = []
    for left, right in combinations(DEVELOPMENT, 2):
        r, n = correlation(measured[left], measured[right])
        if r != r:  # nan
            print(f"{left + ' / ' + right:<48}{'--':>8}{n:>9}   too few players")
            continue
        same = abs(r) > CEILING
        duplicates.append((left, right)) if same else None
        print(f"{left + ' / ' + right:<48}{r:>8.2f}{n:>9}   "
              f"{'ONE SIGNAL, TWO NAMES' if same else 'distinct'}")

    print()
    print("=" * 76)
    print("AND AGAINST THE CLAIMS THEY MIGHT BE RESTATING")
    print("=" * 76)
    print()
    print("A development claim that tracks the general opening error rate is not")
    print("telling anyone anything new -- that is what closed a section slot in")
    print("E10 at +0.917.")
    print()
    print(f"{'pair':<48}{'r':>8}{'players':>9}")
    print("-" * 65)
    for claim in DEVELOPMENT:
        for against in COMPARISONS:
            r, n = correlation(measured[claim], measured[against])
            shown = "--" if r != r else f"{r:.2f}"
            print(f"{claim + ' / ' + against:<48}{shown:>8}{n:>9}")

    print()
    if duplicates:
        print("DUPLICATES FOUND:")
        for left, right in duplicates:
            print(f"  {left} and {right} are one signal. Only the more")
            print("  actionable of the two should ship.")
    else:
        print("No pair exceeds the ceiling: every development claim carries")
        print("something the others do not, and all may ship.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
