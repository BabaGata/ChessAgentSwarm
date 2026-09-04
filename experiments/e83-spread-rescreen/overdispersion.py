"""A discrimination screen that does not reward rarity.

p90/median is bounded by 1/median, so it scores a claim partly on how rare it is
(r = -0.53 here). E09's accept/reject column is perfectly rank-ordered by base
rate. "Percent of ceiling" exposes that but is no more principled.

The scale-free question is the one the screen always meant to ask: **do players
differ by more than sampling noise alone would produce?** Under a null where every
player shares one rate p, each player's count is binomial(n_i, p). Pearson's
dispersion -- observed variance over binomial variance -- is 1.0 when players are
interchangeable and rises with real separation, at any base rate.

It also fixes a second flaw p90/median never handled: a player with 11
opportunities and one with 900 count equally in a percentile, though one is
almost all noise. Dispersion weights by n_i.
"""
from __future__ import annotations
import json, math, statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
peers = json.loads((REPO / "data/raw/out/peers-3af3206.json").read_text(encoding="utf-8"))


def counts(claim: str, floor: int = 10) -> list[tuple[int, int]]:
    totals: dict[str, list[int]] = {}
    for key, rows in peers["cells"].items():
        if key.split("|")[-1] != claim:
            continue
        for row in rows:
            got = totals.setdefault(row["player"].lower(), [0, 0])
            got[0] += row["instances"]
            got[1] += row["opportunities"]
    return [(k, n) for k, n in totals.values() if n >= floor]


def dispersion(obs: list[tuple[int, int]]) -> tuple[float, float, float]:
    """Pearson chi-square over df, and a normal-approximation p-value."""
    hits, chances = sum(k for k, _ in obs), sum(n for _, n in obs)
    p = hits / chances
    if p <= 0 or p >= 1:
        return float("nan"), float("nan"), float("nan")
    chi = sum((k - n * p) ** 2 / (n * p * (1 - p)) for k, n in obs)
    df = len(obs) - 1
    # Wilson-Hilferty: chi2/df is approximately normal with these moments.
    z = (math.pow(chi / df, 1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    tail = 0.5 * math.erfc(z / math.sqrt(2))
    return p, chi / df, tail


def screen():
    rows = []
    for claim in sorted({k.split("|")[-1] for k in peers["cells"]}):
        obs = counts(claim)
        if len(obs) < 10:
            continue
        p, phi, tail = dispersion(obs)
        if phi != phi:
            continue
        rows.append((claim, len(obs), p, phi, tail))

    print("DO PLAYERS DIFFER BY MORE THAN SAMPLING NOISE?\n" + "=" * 92)
    print("\n  Dispersion 1.0 = players are interchangeable. Higher = real separation.")
    print("  Scale-free: a common claim and a rare one are judged on the same axis.\n")
    print(f"  {'claim':<34}{'players':>8}{'rate':>8}{'dispersion':>12}{'p':>11}")
    print("  " + "-" * 88)
    for claim, n, p, phi, tail in sorted(rows, key=lambda r: -r[3]):
        mark = "" if tail < 0.001 else ("  weak" if tail < 0.05 else "  NOT SEPARATED")
        print(f"  {claim[:33]:<34}{n:>8}{p:>8.3f}{phi:>11.2f}x{tail:>11.1e}{mark}")

    flat = [r for r in rows if r[4] >= 0.05]
    print("\n" + "=" * 92)
    print(f"\n  claims screened          {len(rows)}")
    print(f"  separate players         {len([r for r in rows if r[4] < 0.001])}")
    print(f"  weakly                   {len([r for r in rows if 0.001 <= r[4] < 0.05])}")
    print(f"  do NOT separate          {len(flat)}")
    for r in flat:
        print(f"      {r[0]}")
    corr = statistics.correlation([r[2] for r in rows], [r[3] for r in rows])
    print(f"\n  correlation, base rate vs dispersion   {corr:+.2f}   (p90/median gave -0.53)\n")


if __name__ == "__main__":
    screen()
