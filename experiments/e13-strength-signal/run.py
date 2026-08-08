"""E13 — can playing strength be estimated from a player's own games?

V1 is the last vision capability at flat zero that a game record could support,
and [[evaluation]]'s A2 makes it self-validating: estimate strength with the
rating hidden, then compare against the rating the player actually has.

Screened before building, as every section since S6 has been (L-023).

**Range restriction was the thing to check first, and it turned out not to
apply.** The worry was that every player was selected for sitting inside
1400-1800, leaving too little rating variance to predict. In fact the band filter
was applied to *arena standings at discovery*, and the ratings on the games
themselves run **789 to 2129** with a standard deviation of 233. The spread is
still printed first, because it is what decides whether the correlations mean
anything.

Candidate features, all from observations that already exist:

    mean_loss_wp      average win probability given away per move
    error_rate        share of moves labelled inaccuracy or worse
    blunder_rate      share labelled blunder
    best_move_rate    share where the player found the engine's move

Usage:
    python run.py --pgn DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.labels import ErrorLabel  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import GameRecord, parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

FEATURES = ("mean_loss_wp", "error_rate", "blunder_rate", "best_move_rate")

MIN_MOVES = 200
MIN_RATED_GAMES = 10


def player_rating(games: tuple[GameRecord, ...], player: str) -> float | None:
    """The player's own Elo, averaged over the games that carry one."""
    ratings = [
        game.white_elo if game.player_is_white(player) else game.black_elo
        for game in games
        if (game.white_elo if game.player_is_white(player) else game.black_elo)
    ]
    if len(ratings) < MIN_RATED_GAMES:
        return None
    return statistics.mean(ratings)


def features(observations, player: str) -> dict[str, float] | None:
    mine = diagnosable(
        tuple(o for o in observations if o.mover.lower() == player.lower())
    )
    if len(mine) < MIN_MOVES:
        return None

    total = len(mine)
    return {
        "mean_loss_wp": statistics.mean(o.loss_wp for o in mine),
        "error_rate": sum(1 for o in mine if o.label is not None) / total,
        "blunder_rate": sum(1 for o in mine if o.label is ErrorLabel.BLUNDER) / total,
        "best_move_rate": sum(1 for o in mine if o.played_best) / total,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument(
        "--fit",
        choices=FEATURES,
        default=None,
        help="print the full-sample fit for this feature instead of the best one",
    )
    args = parser.parse_args()

    rows: list[tuple[str, float, dict[str, float]]] = []
    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"screening {len(paths)} players at depth {args.depth}\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            games = parse_pgn_file(path)
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            rating = player_rating(games, path.stem)
            if rating is None:
                print(f"  {index:>2}/{len(paths)} {path.stem}: no ratings", flush=True)
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            measured = features(observations, path.stem)
            if measured is None:
                print(f"  {index:>2}/{len(paths)} {path.stem}: too few moves", flush=True)
                continue
            rows.append((path.stem, rating, measured))
            print(f"  {index:>2}/{len(paths)} {path.stem}: {rating:.0f}", flush=True)

    if len(rows) < 10:
        print("\ntoo few players to say anything")
        return 1

    ratings = [r for _, r, _ in rows]
    print(f"\n{len(rows)} players")
    print(f"rating   median {statistics.median(ratings):.0f}  "
          f"min {min(ratings):.0f}  max {max(ratings):.0f}  "
          f"sd {statistics.stdev(ratings):.0f}")
    print(
        "  Spread is what makes the correlations readable. The band filter was applied\n"
        "  to arena standings at discovery, not to these games, so the sample is far\n"
        "  wider than 1400-1800 and the correlations are not attenuated by restriction."
    )

    print(f"\n{'feature':<16} {'median':>9} {'sd':>9} {'corr with rating':>18}")
    for name in FEATURES:
        values = [f[name] for _, _, f in rows]
        r = statistics.correlation(values, ratings)
        print(f"{name:<16} {statistics.median(values):>9.4f} "
              f"{statistics.stdev(values):>9.4f} {r:>18.3f}")

    _fit_and_evaluate(rows, wanted=args.fit)
    return 0


# --- turning a correlation into an estimator --------------------------------


def _fold_of(player: str, folds: int) -> int:
    """Split by a stable hash of the name, so folds do not track fetch order."""
    return sum(player.encode("utf-8")) % folds


def _ols1(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Slope and intercept, by hand — one feature needs no linear algebra."""
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    variance = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / variance
    return slope, mean_y - slope * mean_x


def _fit_and_evaluate(rows, folds: int = 5, wanted: str | None = None) -> None:
    """Cross-validated, because an in-sample fit is not an estimator.

    L-018 is the reason this is not optional: a constant read off the same data
    it is scored against looked five times better than it was, and the same trap
    is waiting for any regression.
    """
    print(f"\n{folds}-fold cross-validation, split by player\n")
    print(f"  {'feature':<16} {'held-out MAE':>13} {'within 100':>11} {'within 200':>11}")

    baseline = statistics.mean(abs(r - statistics.median([x for _, x, _ in rows]))
                               for _, r, _ in rows)

    for name in FEATURES:
        errors: list[float] = []
        for fold in range(folds):
            train = [(r, f[name]) for p, r, f in rows if _fold_of(p, folds) != fold]
            test = [(r, f[name]) for p, r, f in rows if _fold_of(p, folds) == fold]
            if len(train) < 5 or not test:
                continue
            slope, intercept = _ols1([x for _, x in train], [r for r, _ in train])
            errors += [abs(intercept + slope * x - r) for r, x in test]

        if not errors:
            continue
        mae = statistics.mean(errors)
        print(f"  {name:<16} {mae:>13.0f} "
              f"{sum(1 for e in errors if e <= 100) / len(errors):>10.0%} "
              f"{sum(1 for e in errors if e <= 200) / len(errors):>10.0%}")

    print(f"\n  {'guess the median':<16} {baseline:>13.0f}")
    print("  Any feature that does not beat this is not an estimator, whatever its"
          "\n  correlation looks like.")

    # Coefficients for whatever ships: fitted on everything, since the
    # cross-validation above is what establishes the error, not the fit.
    #
    # `wanted` lets a caller ask for a *named* feature rather than the winner.
    # Refitting for blitz needed exactly that: `blunder_rate` and `mean_loss_wp`
    # finish within noise of each other there, and matching the feature the rapid
    # model already ships is worth more than three points of MAE.
    if wanted:
        best = wanted
    else:
        best = min(
            FEATURES,
            key=lambda name: statistics.mean(
                abs(
                    _ols1(
                        [f[name] for _, _, f in rows], [r for _, r, _ in rows]
                    )[1]
                    + _ols1([f[name] for _, _, f in rows], [r for _, r, _ in rows])[0] * f[name]
                    - r
                )
                for _, r, f in rows
            ),
        )
    xs = [f[best] for _, _, f in rows]
    slope, intercept = _ols1(xs, [r for _, r, _ in rows])
    residuals = sorted(abs(intercept + slope * x - r) for (_, r, _), x in zip(rows, xs))
    print(
        f"\nfull-sample fit on {best}:"
        f"\n  rating = {intercept:.1f} + {slope:.1f} * {best}"
        f"\n  fitted on {len(rows)} players, "
        f"{best} ranging {min(xs):.4f} to {max(xs):.4f}"
        f"\n  in-sample MAE {statistics.mean(residuals):.0f}"
        f" (the held-out figure above is the honest one)"
    )


if __name__ == "__main__":
    raise SystemExit(main())
