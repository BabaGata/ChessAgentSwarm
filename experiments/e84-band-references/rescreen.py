"""Does the verdict survive a correct denominator and a single band?

Note: docs/notes/experiments.e84-band-references.md

[[experiments.e83-spread-rescreen]] screened for separation on `peers-3af3206`,
which has two defects this rebuild fixes:

  1. **`allowed_motif` used the wrong denominator.** Every motif divided by the
     player's total errors, so the claim measured what share of your mistakes a
     motif punishes -- mostly a property of the positions. D2 changed it to the
     errors where the motif was actually available.
  2. **It mixed rating bands.** Players from 720 to 2006 sat in one pool, and a
     pooled null over players with genuinely different rates **inflates**
     dispersion. E83's flat verdicts survived that inflation and were therefore
     conservative; its *separating* verdicts did not, and some may be band
     effects wearing a claim's name.

Both are now fixable, so both are tested: within-band dispersion is the honest
number, and the gap between it and the pooled figure is how much of E83's
"separation" was really the rating spread.

    python rescreen.py [--old PATH] [--new PATH]
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

MIN_OPPORTUNITIES = 10
MIN_PLAYERS = 10


def cells(path: Path) -> dict[str, list[dict]]:
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def totals(rows: dict[str, list[dict]], claim: str, stratum: str | None) -> list[tuple[int, int]]:
    """Per-player (instances, opportunities), within one stratum or pooled."""
    got: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for key, contributions in rows.items():
        band, speed, name = key.split("|", 2)
        if name != claim:
            continue
        if stratum is not None and f"{band}|{speed}" != stratum:
            continue
        for row in contributions:
            got[row["player"].lower()][0] += row["instances"]
            got[row["player"].lower()][1] += row["opportunities"]
    return [(k, n) for k, n in got.values() if n >= MIN_OPPORTUNITIES]


def dispersion(obs: list[tuple[int, int]]) -> tuple[float, float, float]:
    hits, chances = sum(k for k, _ in obs), sum(n for _, n in obs)
    if not chances:
        return float("nan"), float("nan"), float("nan")
    p = hits / chances
    if p <= 0 or p >= 1 or len(obs) < 2:
        return p, float("nan"), float("nan")
    chi = sum((k - n * p) ** 2 / (n * p * (1 - p)) for k, n in obs)
    df = len(obs) - 1
    z = (math.pow(chi / df, 1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return p, chi / df, 0.5 * math.erfc(z / math.sqrt(2))


def best_within_band(rows: dict[str, list[dict]], claim: str) -> tuple[str, float, float, int]:
    """The stratum with most players, screened on its own.

    Reported rather than averaged across strata: pooling them back together is
    the very mixing this is measuring.
    """
    strata = {f"{k.split('|')[0]}|{k.split('|')[1]}" for k in rows}
    best = ("", float("nan"), float("nan"), 0)
    for stratum in sorted(strata):
        obs = totals(rows, claim, stratum)
        if len(obs) < MIN_PLAYERS or len(obs) <= best[3]:
            continue
        _, phi, tail = dispersion(obs)
        if phi == phi:
            best = (stratum, phi, tail, len(obs))
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, default=REPO / "data/raw/out/peers-3af3206.json")
    parser.add_argument("--new", type=Path, default=REPO / "data/raw/out/peers-e84.json")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    old, new = cells(args.old), cells(args.new)
    claims = sorted({k.split("|", 2)[2] for k in new})

    lines = [
        "DOES THE VERDICT SURVIVE A CORRECT DENOMINATOR AND A SINGLE BAND?",
        "=" * 100, "",
        f"  old: {args.old.name} -- band-mixed, pre-D2 denominator",
        f"  new: {args.new.name} -- three bands, motif-specific allowed_motif",
        "",
        "  'within' is the largest single stratum, screened alone. Pooling bands with",
        "  genuinely different rates inflates dispersion, so 'within' is the honest number",
        "  and pooled-minus-within is how much was really the rating spread.",
        "",
        f"  {'claim':<34}{'old':>8}{'new pooled':>12}{'within':>9}{'n':>5}  verdict",
        "  " + "-" * 96,
    ]

    changed: list[str] = []
    for claim in claims:
        old_obs = totals(old, claim, None)
        new_obs = totals(new, claim, None)
        if len(new_obs) < MIN_PLAYERS:
            continue
        # A claim the old reference never screened is **unmeasured**, not flat.
        # Folding the two together would report every newly-covered claim as
        # "recovered" -- an empty case answering like a populated one (L-046).
        screened_before = len(old_obs) >= MIN_PLAYERS
        old_phi, old_tail = (float("nan"), float("nan"))
        if screened_before:
            _, old_phi, old_tail = dispersion(old_obs)
            screened_before = old_phi == old_phi

        _, new_phi, new_tail = dispersion(new_obs)
        stratum, within_phi, within_tail, n = best_within_band(new, claim)
        if new_phi != new_phi:
            continue

        # No stratum with enough players is **unmeasured within band**, not flat.
        # The same distinction already drawn on the old side, and missing here it
        # reported claims with n=0 as having lost a separation they were never
        # re-tested for (L-046, a second time in one script).
        measurable = n >= MIN_PLAYERS and within_tail == within_tail
        is_flat = measurable and within_tail >= 0.05
        if not measurable:
            verdict, note = "too thin within band to say", ""
        elif not screened_before:
            verdict, note = ("new — " + ("flat" if is_flat else "separates")), ""
        else:
            was_flat = old_tail >= 0.05
            if was_flat and not is_flat:
                verdict, note = "RECOVERED — now separates", f"{claim}: flat -> separates"
            elif not was_flat and is_flat:
                verdict, note = "LOST — no longer separates", f"{claim}: separated -> flat"
            elif is_flat:
                verdict, note = "still flat", ""
            else:
                verdict, note = "still separates", ""
        if note:
            changed.append(note)

        lines.append(
            f"  {claim[:33]:<34}"
            f"{(f'{old_phi:.2f}' if old_phi == old_phi else '--'):>8}"
            f"{new_phi:>11.2f}x{within_phi:>8.2f}x{n:>5}  {verdict}"
        )

    lines += ["", "=" * 100, "", "  VERDICTS THAT MOVED", ""]
    lines += [f"    {c}" for c in changed] or ["    none"]
    lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "rescreen.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
