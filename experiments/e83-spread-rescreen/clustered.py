"""Bracket the dispersion between two nulls, because moves are not independent.

Opportunities inside one game are correlated -- the same opponent, the same
position type, the same clock. Pearson dispersion assumes independent trials, so
it is **inflated**, and "separates" is the optimistic verdict.

The inflation is bounded. If outcomes within a game were *perfectly* correlated,
a game would carry the information of one trial, and dispersion would inflate by
exactly the mean opportunities-per-game. Dividing by that gives the floor: the
value that survives even the worst clustering the data admits.

  floor > 1   -- separates players under any clustering. Certain.
  ceiling < 1 -- does not separate even assuming independence. Certain.
  spanning 1  -- depends on how correlated moves within a game really are.
"""
from __future__ import annotations
import json
from pathlib import Path
from overdispersion import counts, dispersion, peers

def games(claim: str, floor: int = 10):
    totals: dict[str, list[int]] = {}
    for key, rows in peers["cells"].items():
        if key.split("|")[-1] != claim:
            continue
        for row in rows:
            got = totals.setdefault(row["player"].lower(), [0, 0, 0])
            got[0] += row["instances"]
            got[1] += row["opportunities"]
            got[2] += row["games_with_data"]
    kept = [v for v in totals.values() if v[1] >= floor]
    chances = sum(v[1] for v in kept)
    played = sum(v[2] for v in kept)
    return (chances / played) if played else float("nan")

rows = []
for claim in sorted({k.split("|")[-1] for k in peers["cells"]}):
    obs = counts(claim)
    if len(obs) < 10:
        continue
    _, phi, tail = dispersion(obs)
    if phi != phi:
        continue
    per_game = games(claim)
    # Clustering can only *shrink* effective sample size. Where a claim
    # offers fewer than one opportunity per game there is nothing within a
    # game to correlate, so the design effect floors at 1 -- dividing by a
    # value below 1 would inflate the bound it is supposed to lower.
    design = max(1.0, per_game)
    rows.append((claim, phi, phi / design, per_game, tail))

print("DOES IT STILL SEPARATE IF EVERY MOVE IN A GAME IS THE SAME MOVE?\n" + "=" * 92)
print(f"\n  {'claim':<34}{'per game':>10}{'floor':>9}{'ceiling':>10}  verdict")
print("  " + "-" * 88)
certain = flat = span = 0
for claim, phi, low, per_game, tail in sorted(rows, key=lambda r: -r[2]):
    # Significance first (L-055). A floor above 1.0 is only a point estimate;
    # asking it before the p-value let four claims with dispersion of 1.04-1.37
    # and p of 0.09-0.38 be reported as separating under any clustering.
    if tail >= 0.05:
        verdict, flat = "DOES NOT separate, even independent", flat + 1
    elif low > 1.0:
        verdict, certain = "separates under any clustering", certain + 1
    else:
        verdict, span = "depends on clustering", span + 1
    print(f"  {claim[:33]:<34}{per_game:>10.1f}{low:>8.2f}x{phi:>9.2f}x  {verdict}")

print("\n" + "=" * 92)
print(f"\n  separate under any clustering    {certain}")
print(f"  depend on clustering             {span}")
print(f"  do not separate at all           {flat}")
print("\n  The last group is the robust finding: it fails against the *optimistic*")
print("  null, so no correction can rescue it.\n")
