"""E45 — what the increment correction does to the population rates.

D16: `Observation.seconds_spent` was `clock_before - clock_after`, and `%clk` is
written *after* the increment is credited, so the stored value was `spent - i`.
14.7 % of the peer corpus carries an increment, so every population rate that
depends on thinking time was measured slightly wrong.

The claim at risk is the largest number this project has produced:
`instant_move_error` at **16.1 wp/game**, the most expensive weakness measured
and the headline of the band note ([[experiments.e25-shared-weaknesses]]). The
bug inflates exactly that claim, by counting considered moves on increment games
as instant ones.

This compares the reference built before the fix with the one built after, on
the same corpus, same engine, same depth — so the only difference is the
correction.

Usage:
    python compare_references.py --before OLD.json --after NEW.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# The claims that depend on the clock at all. Everything else should be
# identical, and is checked to be, because a difference there would mean the
# rebuild changed something this fix has no business changing.
CLOCK_CLAIMS = ("instant_move_error", "long_think_error", "time_pressure_error")


def cells(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("cells", payload)


def summarise(cell: dict) -> tuple[float, float]:
    """Population rate and cost per game for one (band, speed, claim)."""
    contributions = cell if isinstance(cell, list) else cell.get("contributions", [])
    instances = sum(c.get("instances", 0) for c in contributions)
    opportunities = sum(c.get("opportunities", 0) for c in contributions)
    cost = sum(c.get("cost_wp", 0.0) or 0.0 for c in contributions)
    games = sum(c.get("games_with_data", 0) for c in contributions)
    return (
        instances / opportunities if opportunities else 0.0,
        cost / games if games else 0.0,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    args = parser.parse_args()

    before, after = cells(args.before), cells(args.after)

    print("CLOCK-DEPENDENT CLAIMS — before and after the increment correction")
    print(f"{'cell':<52}{'rate before':>12}{'rate after':>11}"
          f"{'cost before':>13}{'cost after':>11}")
    print("-" * 99)
    moved = 0
    for key in sorted(set(before) | set(after)):
        if not any(claim in key for claim in CLOCK_CLAIMS):
            continue
        if key not in before or key not in after:
            print(f"{key:<52}  {'(only in one reference)':>44}")
            continue
        r0, c0 = summarise(before[key])
        r1, c1 = summarise(after[key])
        if abs(r0 - r1) < 1e-9 and abs(c0 - c1) < 1e-9:
            continue
        moved += 1
        print(f"{key:<52}{r0:>11.2%}{r1:>11.2%}{c0:>13.2f}{c1:>11.2f}")

    print(f"\n  clock-dependent cells that moved: {moved}")

    unrelated = 0
    for key in sorted(set(before) & set(after)):
        if any(claim in key for claim in CLOCK_CLAIMS):
            continue
        r0, _ = summarise(before[key])
        r1, _ = summarise(after[key])
        if abs(r0 - r1) > 1e-9:
            unrelated += 1
            if unrelated <= 8:
                print(f"  UNEXPECTED move in a clock-free claim: {key} "
                      f"{r0:.2%} -> {r1:.2%}")
    print(f"  clock-FREE cells that moved (should be 0): {unrelated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
