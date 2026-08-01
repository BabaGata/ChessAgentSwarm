"""Two-fold cross-validation of the target rule's calibration constant.

The 8 % figure E05 reported was fitted on the same predictions it was tested
against, which makes it optimistic. This fits the constant on one half of the
players and evaluates it on the other, then swaps.

No re-analysis is needed. A prediction's before/after rates and its no-change
estimate do not depend on the target rule -- only the verdict does -- so the
whole cross-validation is arithmetic over the recorded results.

Usage:
    python calibrate.py --results results/results.json [--quantile 0.2]
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

# Players are split by a stable hash of their name rather than by file order, so
# the folds do not track when they were fetched.
FOLDS = 2


def load_predictions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {"player": player["player"], **outcome}
        for player in data["per_player"]
        for outcome in player["outcomes"]
        if outcome.get("after") is not None and outcome.get("expected")
    ]


def fold_of(player: str) -> int:
    return sum(player.encode("utf-8")) % FOLDS


def fit_ratio(predictions: list[dict], quantile: float) -> float | None:
    """The quantile of observed after/expected — what doing nothing achieves."""
    ratios = sorted(p["after"] / p["expected"] for p in predictions)
    if not ratios:
        return None
    index = max(0, min(len(ratios) - 1, int(round(quantile * (len(ratios) - 1)))))
    return ratios[index]


def met_share(predictions: list[dict], ratio: float) -> tuple[int, int]:
    met = sum(1 for p in predictions if p["after"] <= p["expected"] * ratio)
    return met, len(predictions)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--quantile", type=float, default=0.2)
    args = parser.parse_args()

    predictions = load_predictions(args.results)
    print(f"{len(predictions)} usable predictions from "
          f"{len({p['player'] for p in predictions})} players\n")

    folds = {fold: [p for p in predictions if fold_of(p["player"]) == fold] for fold in range(FOLDS)}
    for fold, members in folds.items():
        print(f"  fold {fold}: {len(members)} predictions, "
              f"{len({p['player'] for p in members})} players")

    print(f"\nfitting at the {args.quantile:.0%} quantile of after/expected\n")

    fitted, out_of_sample = [], []
    for fold in range(FOLDS):
        train = [p for f, members in folds.items() if f != fold for p in members]
        test = folds[fold]
        if not train or not test:
            print(f"  fold {fold}: too small to evaluate")
            continue

        ratio = fit_ratio(train, args.quantile)
        in_met, in_total = met_share(train, ratio)
        out_met, out_total = met_share(test, ratio)
        fitted.append(ratio)
        out_of_sample.append((out_met, out_total))

        print(
            f"  fit on the other fold -> ratio {ratio:.3f} | "
            f"in-sample {in_met}/{in_total} met | "
            f"OUT-OF-SAMPLE {out_met}/{out_total} met"
        )

    total_met = sum(met for met, _ in out_of_sample)
    total = sum(count for _, count in out_of_sample)
    print("\n" + "=" * 56)
    if total:
        print(f"out-of-sample met by doing nothing   {total_met}/{total} "
              f"({100 * total_met / total:.0f}%)")
    if fitted:
        print(f"fitted ratios                        {', '.join(f'{r:.3f}' for r in fitted)}")
        print(f"suggested constant (mean)            {statistics.mean(fitted):.3f}")

    all_ratios = sorted(p["after"] / p["expected"] for p in predictions)
    print(f"\nafter/expected across everything     median {statistics.median(all_ratios):.2f}, "
          f"min {all_ratios[0]:.2f}, max {all_ratios[-1]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
