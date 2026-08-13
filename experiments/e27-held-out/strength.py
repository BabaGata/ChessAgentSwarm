"""Does the rating estimate hold on players it was never fitted on?

V1's lines were fitted on the 84-player corpus and cross-validated **by fold
within it** — held-out players, but held out of a set that was itself the only
data ever looked at. E13 reported ±103 rapid and ±123 blitz on that basis.

These 30 players were fetched after every constant in the system was frozen, and
their ratings are sitting in their own game headers. That makes this the one
capability with a genuine external check available for free, and the closest the
project gets to [[vision]]'s success criterion 1 on strangers.

Usage:
    python strength.py --pgn DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.speed import speed_class  # noqa: E402
from chesscoach.strength import estimate  # noqa: E402

MIN_RATED_GAMES = 10


def own_rating(games, player: str, speed: str | None) -> float | None:
    """The player's own Elo, at one speed, from the games that carry one.

    Matched to the speed the estimate is for: comparing a blitz estimate against
    a rating averaged over rapid games would measure the speed gap (~80 points,
    E19) rather than the estimator.
    """
    ratings = [
        game.white_elo if game.player_is_white(player) else game.black_elo
        for game in games
        if (speed is None or speed_class(game.time_control) == speed)
        and (game.white_elo if game.player_is_white(player) else game.black_elo)
    ]
    return statistics.mean(ratings) if len(ratings) >= MIN_RATED_GAMES else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    args = parser.parse_args()

    rows = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(args.pgn.glob("*.pgn")):
            player = path.stem
            games = [g for g in parse_pgn_file(path) if g.involves(player)]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue

            observed = analyse_corpus(corpus, games, session.analyser)
            speeds = {g.game_id: speed_class(g.time_control) for g in games}
            measured = estimate(observed, player, speeds)
            if measured is None:
                print(f"  {player}: no estimate (too few moves at one speed)", flush=True)
                continue

            actual = own_rating(games, player, measured.speed)
            if actual is None:
                print(f"  {player}: no {measured.speed} rating to check against", flush=True)
                continue

            error = measured.rating - actual
            rows.append((player, measured.speed, measured.rating, actual, error,
                         measured.typical_error, measured.extrapolated))
            print(f"  {player:<22} {measured.speed:<9} est {measured.rating:>5}  "
                  f"actual {actual:>6.0f}  error {error:>+6.0f}", flush=True)

    if not rows:
        print("\nno players could be checked")
        return 1

    errors = [abs(e) for *_, e, _, _ in rows]
    signed = [e for *_, e, _, _ in rows]
    claimed = statistics.mean(t for *_, t, _ in rows)

    print(f"\n{'=' * 66}")
    print(f"{len(rows)} held-out players, none of them in the fitting corpus\n")
    print(f"  mean absolute error        {statistics.mean(errors):>6.0f}")
    print(f"  median absolute error      {statistics.median(errors):>6.0f}")
    print(f"  claimed typical error      {claimed:>6.0f}   <- what the report promises")
    print(f"  within 100                 {sum(1 for e in errors if e <= 100) / len(errors):>6.0%}")
    print(f"  within 200                 {sum(1 for e in errors if e <= 200) / len(errors):>6.0%}")
    print(f"\n  mean signed error          {statistics.mean(signed):>+6.0f}   "
          "<- bias: negative means the swarm reads players as weaker than they are")

    baseline = statistics.median(a for *_, a, _, _, _ in rows)
    naive = statistics.mean(abs(a - baseline) for *_, a, _, _, _ in rows)
    print(f"  guessing the median ({baseline:.0f})  {naive:>6.0f}   <- the bar to beat")

    by_speed: dict[str, list[float]] = {}
    for _p, speed, _e, _a, error, _t, _x in rows:
        by_speed.setdefault(speed, []).append(abs(error))
    print()
    for speed, values in sorted(by_speed.items()):
        print(f"  {speed:<10} {len(values):>3} players, MAE {statistics.mean(values):>5.0f}")

    extrapolated = sum(1 for *_, x in rows if x)
    if extrapolated:
        print(f"\n  {extrapolated} estimates were outside the fitted blunder-rate range "
              "and said so")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
