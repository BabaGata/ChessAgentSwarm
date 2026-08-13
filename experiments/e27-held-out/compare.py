"""E27 — does the swarm behave the same on players it was never built on?

Every threshold, screened claim and constant was chosen while looking at the same
84 players the swarm is then run on. Leave-one-out removes a player from their
*own* peer rate; it does nothing about the fact that **what to measure** was
selected on this sample.

Two things have to be controlled for before any difference means anything:

  sample size   30 players and 84 players cannot produce the same number of
                distinct claim kinds, however similar the systems are. So the
                in-sample figure is recomputed on **random 30-player subsets**,
                giving a distribution rather than a single number to compare
                against.

  corpus size   coverage rises with games. The held-out players were fetched as
                production fetches (60 pooled games); the in-sample set is 24
                rapid plus whatever blitz existed. Reported side by side rather
                than assumed equal.

Usage:
    python compare.py --held-out DIR --in-sample DIR [--draws 2000]
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

SEED = 20260810


def load(directory: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*.json"))]


def advised_kinds(profile: dict) -> list[str]:
    by_id = {f["id"]: f for f in profile.get("findings", [])}
    steps = (profile.get("plan") or {}).get("steps", [])
    return [
        f"{by_id[s['finding_id']]['claim']['kind']}.{by_id[s['finding_id']]['claim']['subject']}"
        for s in steps
        if s["finding_id"] in by_id
    ]


def measure(profiles: list[dict]) -> tuple[float, int, float]:
    """Coverage, distinct claim kinds, and mean pairwise overlap."""
    advice = [advised_kinds(p) for p in profiles]
    spoken = [a for a in advice if a]
    coverage = len(spoken) / len(profiles) if profiles else 0.0
    kinds = len({k for a in advice for k in a})

    overlaps = []
    for i in range(len(spoken)):
        for j in range(i + 1, len(spoken)):
            a, b = set(spoken[i]), set(spoken[j])
            overlaps.append(len(a & b) / len(a | b) if a | b else 0.0)
    return coverage, kinds, statistics.mean(overlaps) if overlaps else 0.0


def games_of(profile: dict) -> int:
    return profile["corpus"]["n_games"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out", required=True, type=Path)
    parser.add_argument("--in-sample", required=True, type=Path)
    parser.add_argument("--draws", type=int, default=2000)
    args = parser.parse_args()

    held = load(args.held_out)
    inside = load(args.in_sample)
    rng = random.Random(SEED)

    h_cov, h_kinds, h_overlap = measure(held)
    i_cov, i_kinds, i_overlap = measure(inside)

    print(f"{len(held)} held-out players against {len(inside)} in-sample\n")
    print(f"{'':<26}{'held out':>12}{'in sample':>12}")
    print(f"{'players':<26}{len(held):>12}{len(inside):>12}")
    print(f"{'median games each':<26}"
          f"{statistics.median(games_of(p) for p in held):>12.0f}"
          f"{statistics.median(games_of(p) for p in inside):>12.0f}")
    print(f"{'advised':<26}{h_cov:>11.0%}{i_cov:>12.0%}")
    print(f"{'distinct claim kinds':<26}{h_kinds:>12}{i_kinds:>12}")
    print(f"{'mean pairwise overlap':<26}{h_overlap:>12.2f}{i_overlap:>12.2f}")

    # The like-for-like comparison: what would the in-sample set look like if it
    # were only as large as the held-out one?
    n = len(held)
    coverages, kind_counts, overlaps = [], [], []
    for _ in range(args.draws):
        subset = rng.sample(inside, n)
        c, k, o = measure(subset)
        coverages.append(c)
        kind_counts.append(k)
        overlaps.append(o)

    def where(value: float, draws: list[float]) -> float:
        """Share of subsets at or below the held-out value."""
        return sum(1 for d in draws if d <= value) / len(draws)

    print(f"\nin-sample resampled to {n} players, {args.draws} draws")
    print(f"{'':<26}{'median':>10}{'5th':>8}{'95th':>8}{'held out':>10}{'pctile':>9}")
    for name, value, draws, fmt in (
        ("advised", h_cov, coverages, "{:.0%}"),
        ("distinct claim kinds", float(h_kinds), [float(k) for k in kind_counts], "{:.0f}"),
        ("mean pairwise overlap", h_overlap, overlaps, "{:.2f}"),
    ):
        ordered = sorted(draws)
        print(f"{name:<26}"
              f"{fmt.format(statistics.median(ordered)):>10}"
              f"{fmt.format(ordered[len(ordered) // 20]):>8}"
              f"{fmt.format(ordered[19 * len(ordered) // 20]):>8}"
              f"{fmt.format(value):>10}"
              f"{where(value, draws):>8.0%}")

    print("\n  A held-out value inside the 5th-95th band is a system that behaves the same")
    print("  on strangers. Outside it is in-sample optimism, and the size of the gap is")
    print("  how much of the reported performance was selection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
