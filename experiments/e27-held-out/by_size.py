"""Is the held-out coverage gap generalisation, or just smaller corpora?

`compare.py` put held-out coverage at the 5th percentile of resampled in-sample
draws — borderline — while the held-out players carry a median of 54 games
against 70. Coverage rises with games (E12, E21), so the two explanations are
tangled and the difference means nothing until they are separated.

Matched on corpus size: coverage within game-count buckets, and a like-for-like
comparison over the overlapping range only.

Usage:
    python by_size.py --held-out DIR --in-sample DIR
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

BUCKETS = ((0, 40), (40, 60), (60, 80), (80, 1000))


def load(directory: Path):
    rows = []
    for path in sorted(directory.glob("*.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        steps = (profile.get("plan") or {}).get("steps", [])
        rows.append((profile["corpus"]["n_games"], bool(steps)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out", required=True, type=Path)
    parser.add_argument("--in-sample", required=True, type=Path)
    args = parser.parse_args()

    held, inside = load(args.held_out), load(args.in_sample)

    print(f"{'games':<12}{'held out':>22}{'in sample':>22}")
    for low, high in BUCKETS:
        h = [spoke for games, spoke in held if low <= games < high]
        i = [spoke for games, spoke in inside if low <= games < high]
        label = f"{low}-{high if high < 1000 else '+'}"
        h_txt = f"{sum(h)}/{len(h)} ({sum(h) / len(h):.0%})" if h else "-"
        i_txt = f"{sum(i)}/{len(i)} ({sum(i) / len(i):.0%})" if i else "-"
        print(f"{label:<12}{h_txt:>22}{i_txt:>22}")

    # The overlapping range, where both sets have players and the comparison is
    # not extrapolating past one of them.
    low = max(min(g for g, _ in held), min(g for g, _ in inside))
    high = min(max(g for g, _ in held), max(g for g, _ in inside))
    h = [spoke for games, spoke in held if low <= games <= high]
    i = [spoke for games, spoke in inside if low <= games <= high]

    print(f"\nover the overlapping range, {low}-{high} games:")
    print(f"  held out   {sum(h)}/{len(h)}  {sum(h) / len(h):.0%}"
          f"   median {statistics.median(g for g, _ in held if low <= g <= high):.0f} games")
    print(f"  in sample  {sum(i)}/{len(i)}  {sum(i) / len(i):.0%}"
          f"   median {statistics.median(g for g, _ in inside if low <= g <= high):.0f} games")

    # Fisher exact, hand-written as elsewhere in this project: does the
    # difference survive at all once size is matched?
    from math import comb

    a, b = sum(h), len(h) - sum(h)
    c, d = sum(i), len(i) - sum(i)
    total = a + b + c + d

    def probability(x: int) -> float:
        return comb(a + b, x) * comb(c + d, a + c - x) / comb(total, a + c)

    observed = probability(a)
    tail = sum(
        probability(x)
        for x in range(max(0, a + c - (c + d)), min(a + b, a + c) + 1)
        if probability(x) <= observed + 1e-12
    )
    print(f"\n  Fisher exact, two-tailed: p = {tail:.3f}")
    print("  Above 0.05 means the coverage difference is explained by corpus size")
    print("  rather than by the players being new.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
