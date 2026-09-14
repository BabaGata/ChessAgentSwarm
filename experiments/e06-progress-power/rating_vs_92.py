"""Did the players who met their targets in the 92 % run simply get better?

The question is the author's: if ratings rose over the window, targets met
"by doing nothing" might be real progress the system could not see.

`power.py` answers it for the later deep-history run, but it cannot read the
original 32-player results: those predate the `expected` field it needs to
re-decide verdicts at another constant. This does not need to. The stored
`status` *is* the verdict that produced 92 %, so it is used as recorded, and
rating change comes from histories re-fetched for the same window by
`e05-natural-drift/refetch_controls.py`.

Usage (from the repository root):
    PYTHONPATH=. python experiments/e06-progress-power/rating_vs_92.py \\
        --results experiments/e05-natural-drift/results/results.json \\
        --histories data/raw/e05-refetch-rc
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from power import fisher_one_sided, rating_change  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--histories", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.results.read_text(encoding="utf-8"))
    rows = []
    all_changes = []
    missing = []
    for entry in data["per_player"]:
        path = args.histories / f"{entry['player']}.pgn"
        change = rating_change(path, entry["player"]) if path.exists() else None
        if change is None:
            if entry["outcomes"]:
                missing.append(entry["player"])
            continue
        all_changes.append(change)
        judged = [o for o in entry["outcomes"] if o["status"] in ("met", "not_met")]
        if judged:
            met = sum(1 for o in judged if o["status"] == "met")
            rows.append((entry["player"], change, met, len(judged)))

    print(f"promjena ranga, svi igrači s poviješću (n = {len(all_changes)}): "
          f"prosjek {statistics.mean(all_changes):+.1f}, "
          f"medijan {statistics.median(all_changes):+.1f}")
    rose = sum(1 for c in all_changes if c > 0)
    print(f"  porastao {rose}, pao ili isti {len(all_changes) - rose}")

    print(f"\nigrači s presuđenim predviđanjem (n = {len(rows)}):")
    print(f"  {'igrač':24}{'rang':>8}{'ispunjeno':>12}")
    for name, change, met, judged in sorted(rows, key=lambda r: -r[1]):
        print(f"  {name:24}{change:+8.1f}{f'{met}/{judged}':>12}")
    if missing:
        print(f"  bez povijesti: {', '.join(missing)}")

    ups = [r for r in rows if r[1] > 0]
    downs = [r for r in rows if r[1] <= 0]
    met_up, n_up = sum(r[2] for r in ups), sum(r[3] for r in ups)
    met_down, n_down = sum(r[2] for r in downs), sum(r[3] for r in downs)
    print(f"\nrang porastao: {met_up}/{n_up} ispunjeno, "
          f"prosječna promjena {statistics.mean([r[1] for r in ups]):+.1f}"
          if ups else "\nnijednom igraču s planom rang nije porastao")
    if downs:
        print(f"rang pao:      {met_down}/{n_down} ispunjeno, "
              f"prosječna promjena {statistics.mean([r[1] for r in downs]):+.1f}")
    if ups and downs:
        print(f"Fisher, jednostrani (porast ispunjava češće): "
              f"p = {fisher_one_sided(met_up, n_up, met_down, n_down):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
