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
DEFAULT_FOLDS = 2


def load_predictions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        {"player": player["player"], **outcome}
        for player in data["per_player"]
        for outcome in player["outcomes"]
        if outcome.get("after") is not None and outcome.get("expected")
    ]


def fold_of(player: str, folds: int) -> int:
    return sum(player.encode("utf-8")) % folds


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


def cross_validate(predictions: list[dict], quantile: float, folds: int) -> dict:
    """Fit the ratio on every fold but one, score it on the one held out."""
    grouped = {
        fold: [p for p in predictions if fold_of(p["player"], folds) == fold]
        for fold in range(folds)
    }

    fitted, out_of_sample = [], []
    for fold in range(folds):
        train = [p for f, members in grouped.items() if f != fold for p in members]
        test = grouped[fold]
        if not train or not test:
            continue
        ratio = fit_ratio(train, quantile)
        fitted.append(ratio)
        out_of_sample.append((*met_share(test, ratio), ratio))

    met = sum(m for m, _, _ in out_of_sample)
    total = sum(n for _, n, _ in out_of_sample)
    return {
        "grouped": grouped,
        "fitted": fitted,
        "per_fold": out_of_sample,
        "met": met,
        "total": total,
        "met_share": met / total if total else None,
        "spread": max(fitted) - min(fitted) if fitted else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--quantile", type=float, default=0.2)
    parser.add_argument("--folds", type=int, default=DEFAULT_FOLDS)
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="report the whole quantile/false-positive trade-off instead of one point",
    )
    args = parser.parse_args()

    predictions = load_predictions(args.results)
    players = len({p["player"] for p in predictions})
    print(f"{len(predictions)} usable predictions from {players} players\n")

    if args.sweep:
        return _sweep(predictions, args.folds)

    result = cross_validate(predictions, args.quantile, args.folds)
    for fold, members in result["grouped"].items():
        print(f"  fold {fold}: {len(members)} predictions, "
              f"{len({p['player'] for p in members})} players")

    print(f"\nfitting at the {args.quantile:.0%} quantile of after/expected\n")
    for met, total, ratio in result["per_fold"]:
        print(f"  fit on the other folds -> ratio {ratio:.3f} | "
              f"OUT-OF-SAMPLE {met}/{total} met")

    print("\n" + "=" * 56)
    if result["total"]:
        print(f"out-of-sample met by doing nothing   {result['met']}/{result['total']} "
              f"({100 * result['met_share']:.0f}%)")
    if result["fitted"]:
        print(f"fitted ratios                        "
              f"{', '.join(f'{r:.3f}' for r in result['fitted'])}")
        print(f"suggested constant (mean)            {statistics.mean(result['fitted']):.3f}")

    all_ratios = sorted(p["after"] / p["expected"] for p in predictions)
    print(f"\nafter/expected across everything     median {statistics.median(all_ratios):.2f}, "
          f"min {all_ratios[0]:.2f}, max {all_ratios[-1]:.2f}")
    return 0


def _sweep(predictions: list[dict], folds: int) -> int:
    """The trade-off curve: a stricter target buys fewer false successes.

    Spread is the gap between the ratios the folds fit independently. Where it
    is wide the constant is not being estimated, only guessed at.
    """
    print(f"{folds}-fold cross-validation\n")
    print("  quantile   constant   spread   out-of-sample met by doing nothing")
    for percent in range(5, 55, 5):
        result = cross_validate(predictions, percent / 100, folds)
        if not result["total"]:
            continue
        print(
            f"  {percent:>6}%     {statistics.mean(result['fitted']):.3f}    "
            f"{result['spread']:.3f}    {result['met']:>3}/{result['total']} "
            f"({100 * result['met_share']:>3.0f}%)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
