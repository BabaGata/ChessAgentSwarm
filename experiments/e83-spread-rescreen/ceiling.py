"""Is p90/median measuring discrimination, or is it measuring the base rate?

A rate cannot exceed 1.0, so p90/median is **bounded above by 1/median**. A claim
firing on 90 % of its opportunities cannot score above 1.11 however cleanly it
separates players. E09 compared `concedes_outpost` (median rate 0.0077, ceiling
130x) against candidates with far commoner rates and called the losers
undiscriminating -- so the question is whether the screen ranked claims by how
well they separate players or merely by how rare they are.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
from run import rates, spread, interval, REJECTED_AT

REPO = Path(__file__).resolve().parents[2]
peers = json.loads((REPO / "data/raw/out/peers-3af3206.json").read_text(encoding="utf-8"))

rows = []
for claim in sorted({k.split("|")[-1] for k in peers["cells"]}):
    values = [v for v in rates(peers, claim, 10).values() if v > 0]
    if len(values) < 10:
        continue
    got = spread(values)
    if got != got:
        continue
    median = statistics.median(values)
    rows.append((claim, median, 1.0 / median, got, got / (1.0 / median)))

print("HOW MUCH OF THE SPREAD WAS AVAILABLE TO BE SCORED?\n" + "=" * 92)
print(f"\n  {'claim':<34}{'median':>9}{'ceiling':>10}{'spread':>9}{'% of ceiling':>14}")
print("  " + "-" * 88)
for claim, median, ceiling, got, used in sorted(rows, key=lambda r: r[2]):
    flag = "  <-- ceiling below E09's line" if ceiling < REJECTED_AT else ""
    print(f"  {claim[:33]:<34}{median:>9.3f}{ceiling:>9.2f}x{got:>8.2f}x{used:>13.0%}{flag}")

corr = statistics.correlation([r[1] for r in rows], [r[3] for r in rows])
capped = [r for r in rows if r[2] < REJECTED_AT]
print("\n" + "=" * 92)
print(f"\n  correlation, median rate vs spread    {corr:+.2f}")
print(f"  claims whose ceiling is below 1.31x   {len(capped)}")
for r in capped:
    print(f"      {r[0]:<36} ceiling {r[2]:.2f}x -- could never have passed")
print("\n  A claim cannot score above its ceiling. Where the ceiling sits below the")
print("  rejection line, a 'fails to discriminate' verdict was arithmetic, not evidence.\n")
