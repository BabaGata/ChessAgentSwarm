"""Do the shipped claims still separate players? Measured on 83, not 12.

Note: docs/notes/experiments.e83-spread-rescreen.md

E82's correction moved the L-024 spreads down at the shipped threshold, and
`allowed_motif` went from 1.59x to **1.34x** -- against a screen where
[[experiments.e09-square-candidates]] **rejected** `cedes_open_file` at 1.31x and
`concedes_hole` at 1.25x. A hair above a line that has killed claims before.

But E33 measures that spread over **12 players**, and p90/median over twelve is a
statistic with almost no power: p90 of twelve values is the eleventh, so one
unusual player moves it. The peer reference holds per-player rates for **83**, and
reading it costs nothing.

**No engine pass.** The reference stores instances and opportunities per player
per claim, which is exactly a rate.

    python run.py [--peers PATH] [--min-opportunities 10]
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPO = Path(__file__).resolve().parents[2]

# E09's own verdicts, which are the only calibration this screen has.
#   concedes_outpost  2.15  accepted, "highest spread in the project"
#   cedes_open_file   1.31  REJECTED
#   concedes_hole     1.25  REJECTED
REJECTED_AT = 1.31
ACCEPTED_AT = 2.15


def rates(peers: dict, claim: str, floor: int) -> dict[str, float]:
    """Per-player rate for one claim, pooled across strata. E69's function."""
    totals: dict[str, list[int]] = {}
    for key, contributions in peers["cells"].items():
        if key.split("|")[-1] != claim:
            continue
        for row in contributions:
            got = totals.setdefault(row["player"].lower(), [0, 0])
            got[0] += row["instances"]
            got[1] += row["opportunities"]
    return {p: hits / chances for p, (hits, chances) in totals.items() if chances >= floor}


def spread(values: list[float]) -> float:
    """p90 / median, the L-024 screen, computed exactly as E33 computes it."""
    values = sorted(values)
    median = statistics.median(values)
    p90 = values[min(len(values) - 1, int(0.9 * len(values)))]
    return (p90 / median) if median else float("nan")


def interval(values: list[float], draws: int = 2000, seed: int = 7) -> tuple[float, float]:
    """A bootstrap interval for the spread.

    **The point of this experiment.** A spread of 1.34 against a rejection line
    of 1.31 is a decision that only means something if the interval does not
    straddle it, and E33 reported a bare number over twelve players.
    """
    rng = random.Random(seed)
    got = []
    for _ in range(draws):
        sample = [rng.choice(values) for _ in values]
        value = spread(sample)
        if value == value:
            got.append(value)
    got.sort()
    return got[int(0.025 * len(got))], got[int(0.975 * len(got))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", type=Path,
                        default=REPO / "data/raw/out/peers-3af3206.json")
    parser.add_argument("--min-opportunities", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = json.loads(args.peers.read_text(encoding="utf-8"))
    claims = sorted({key.split("|")[-1] for key in peers["cells"]})

    lines = [
        "DO THE SHIPPED CLAIMS STILL SEPARATE PLAYERS?",
        "=" * 88, "",
        f"reference {args.peers.name}, at least {args.min_opportunities} opportunities.",
        "",
        f"E09 rejected candidates at {REJECTED_AT}x and below, and accepted its best at "
        f"{ACCEPTED_AT}x.",
        "A spread near the rejection line is only a verdict if its interval clears it.",
        "",
        f"  {'claim':<34}{'players':>8}{'spread':>9}{'95% interval':>20}  verdict",
        "  " + "-" * 84,
    ]

    rows = []
    for claim in claims:
        measured = rates(peers, claim, args.min_opportunities)
        values = [v for v in measured.values() if v > 0]
        if len(values) < 10:
            continue
        got = spread(values)
        if got != got:
            continue
        low, high = interval(values)
        rows.append((claim, len(values), got, low, high))

    for claim, n, got, low, high in sorted(rows, key=lambda r: r[2]):
        if low > REJECTED_AT:
            verdict = "separates"
        elif high < REJECTED_AT:
            verdict = "FAILS — below E09's line"
        else:
            verdict = "cannot tell — straddles the line"
        lines.append(f"  {claim[:33]:<34}{n:>8}{got:>8.2f}x"
                     f"{f'{low:.2f} - {high:.2f}':>20}  {verdict}")

    straddling = [r for r in rows if r[3] <= REJECTED_AT <= r[4]]
    failing = [r for r in rows if r[4] < REJECTED_AT]
    lines += [
        "", "=" * 88, "",
        f"  claims screened                {len(rows)}",
        f"  clear the line                 {len(rows) - len(straddling) - len(failing)}",
        f"  straddle it                    {len(straddling)}",
        f"  fall below it                  {len(failing)}",
        "",
        "  A straddling interval is not a pass. It says the sample cannot tell",
        "  this claim from one E09 threw away, which is a different statement",
        "  from either verdict and is the honest one to record.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    (args.out / "spreads.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
