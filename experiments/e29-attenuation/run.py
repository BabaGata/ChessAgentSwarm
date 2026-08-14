"""E29 — correct the blitz rating line for regression dilution.

[[experiments.e27-held-out]] found V1's blitz line failing on strangers: MAE 150
against 157 for guessing the band's median, with a systematic **-88** bias. The
diagnosis was **slope attenuation** — it ranks players well (r = +0.83) and
compresses the scale, estimates spreading 115 points where the players spread
210, so strong players read as much weaker than they are.

That has a standard cause and a standard fix. When the predictor is measured
with error, OLS shrinks the slope toward zero in proportion to that error:

    slope_observed  =  slope_true  x  lambda,    lambda = reliability of the predictor

so the corrected slope is `slope_observed / lambda`. Blunder rate at blitz is a
noisy measure of skill — that is precisely what makes blitz hard to read — and
E27's attenuation analysis independently asked for a stretch of about **1.5x**.

**The separation that makes this legitimate.** E27 could have produced a
correction directly by regressing actual on estimated over the 30 held-out
players. That would be fitting the model to the set that measures it, which is
L-018 exactly. So:

    lambda      estimated on the **84-player fitting corpus**, by split-half
                reliability with the Spearman-Brown correction. No held-out
                rating is touched.

    validation  on the **30 held-out players**, whose ratings have never been
                used to fit anything.

If a correction derived only from the fitting corpus's internal consistency
recovers the ~1.5x that the held-out data independently demands, the diagnosis
was right. If it does not, it was not, and the line stays as it is.

Rapid runs as a control: E27 measured its slope(actual ~ estimate) at 0.83, so a
reliability-based correction should barely move it.

Usage:
    python run.py --blitz DIR --rapid DIR --held-out DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.labels import ErrorLabel  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402
from chesscoach.speed import speed_class  # noqa: E402
from chesscoach.strength import BLITZ_FIT, RAPID_FIT  # noqa: E402

SEED = 20260814
MIN_MOVES = 200
MIN_RATED_GAMES = 10
# Each half of a split must still carry enough moves to be a measurement rather
# than noise; otherwise the split-half correlation measures the split.
MIN_HALF_MOVES = 80


def blunder_rate(moves) -> float | None:
    if len(moves) < 1:
        return None
    return sum(1 for o in moves if o.label is ErrorLabel.BLUNDER) / len(moves)


def own_rating(games, player: str) -> float | None:
    ratings = [
        g.white_elo if g.player_is_white(player) else g.black_elo
        for g in games
        if (g.white_elo if g.player_is_white(player) else g.black_elo)
    ]
    return statistics.mean(ratings) if len(ratings) >= MIN_RATED_GAMES else None


def ols(xs, ys) -> tuple[float, float]:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    variance = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / variance
    return slope, my - slope * mx


def collect(directory: Path, session, player_speed: str | None, rng):
    """Per player: blunder rate, the two half-corpus rates, rating, move count."""
    rows = []
    for path in sorted(directory.glob("*.pgn")):
        player = path.stem
        games = [g for g in parse_pgn_file(path) if g.involves(player)]
        if player_speed:
            games = [g for g in games if speed_class(g.time_control) == player_speed]
        corpus = build_corpus(player, games)
        if corpus.n_games == 0:
            continue

        rating = own_rating(games, player)
        if rating is None:
            continue

        observed = analyse_corpus(corpus, games, session.analyser)
        mine = diagnosable(
            tuple(o for o in observed if o.mover.lower() == player.lower())
        )
        if len(mine) < MIN_MOVES:
            continue

        # Split by GAME, not by move: moves within a game are not independent,
        # and splitting by move would report a reliability the corpus does not
        # have.
        ids = sorted({o.game_id for o in mine})
        rng.shuffle(ids)
        left = set(ids[: len(ids) // 2])
        a = [o for o in mine if o.game_id in left]
        b = [o for o in mine if o.game_id not in left]
        if len(a) < MIN_HALF_MOVES or len(b) < MIN_HALF_MOVES:
            continue

        rows.append({
            "player": player,
            "rating": rating,
            "rate": blunder_rate(mine),
            "half_a": blunder_rate(a),
            "half_b": blunder_rate(b),
            "moves": len(mine),
        })
    return rows


def report(label: str, fit, rows, held, args) -> None:
    print(f"\n{'=' * 74}\n{label.upper()}\n")

    # --- reliability, from the fitting corpus only --------------------------
    r = statistics.correlation([x["half_a"] for x in rows], [x["half_b"] for x in rows])
    # Spearman-Brown: the split-half correlation measures a half-length
    # instrument, and the estimate uses the whole corpus.
    lam = 2 * r / (1 + r) if r > -1 else float("nan")
    print(f"  fitting corpus            {len(rows)} players")
    print(f"  split-half correlation    {r:+.3f}")
    print(f"  reliability (Spearman-Brown) {lam:.3f}")
    print(f"  implied correction        {1 / lam:.2f}x   <- from internal consistency alone")

    slope, intercept = ols([x["rate"] for x in rows], [x["rating"] for x in rows])
    print(f"\n  refitted here             rating = {intercept:.1f} + {slope:.1f} * rate")
    print(f"  shipped                   rating = {fit.intercept:.1f} + {fit.slope:.1f} * rate")

    corrected_slope = slope / lam
    mean_rate = statistics.mean(x["rate"] for x in rows)
    mean_rating = statistics.mean(x["rating"] for x in rows)
    # Rotate about the centroid: the correction is to the slope, and the line
    # must still pass through the data's centre of mass.
    corrected_intercept = mean_rating - corrected_slope * mean_rate
    print(f"  corrected                 rating = {corrected_intercept:.1f} + "
          f"{corrected_slope:.1f} * rate")

    if not held:
        print("\n  no held-out players at this speed to validate on")
        return

    # --- validation, on players whose ratings fitted nothing ----------------
    def errors(a: float, b: float):
        return [abs(a + b * x["rate"] - x["rating"]) for x in held]

    def signed(a: float, b: float):
        return [a + b * x["rate"] - x["rating"] for x in held]

    median_rating = statistics.median(x["rating"] for x in held)
    naive = statistics.mean(abs(x["rating"] - median_rating) for x in held)

    print(f"\n  held out                  {len(held)} players, ratings "
          f"{min(x['rating'] for x in held):.0f}-{max(x['rating'] for x in held):.0f}")
    print(f"\n  {'line':<26}{'MAE':>7}{'bias':>8}{'<=100':>8}{'<=200':>8}")
    for name, a, b in (
        ("shipped", fit.intercept, fit.slope),
        ("corrected", corrected_intercept, corrected_slope),
    ):
        e = errors(a, b)
        print(f"  {name:<26}{statistics.mean(e):>7.0f}{statistics.mean(signed(a, b)):>+8.0f}"
              f"{sum(1 for x in e if x <= 100) / len(e):>7.0%}"
              f"{sum(1 for x in e if x <= 200) / len(e):>7.0%}")
    print(f"  {'guessing the median':<26}{naive:>7.0f}")

    # Does the correction match what the held-out data independently asks for?
    est = [fit.intercept + fit.slope * x["rate"] for x in held]
    act = [x["rating"] for x in held]
    demanded, _ = ols(est, act)
    print(f"\n  stretch the held-out data demands   {demanded:.2f}x")
    print(f"  stretch the reliability supplies    {1 / lam:.2f}x")
    print("  These are computed from different data. Agreement is the evidence that")
    print("  attenuation was the right diagnosis; disagreement means it was not.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blitz", required=True, type=Path)
    parser.add_argument("--rapid", required=True, type=Path)
    parser.add_argument("--held-out", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    args = parser.parse_args()

    with engine_session(args.engine, args.depth, args.cache) as session:
        print("reading the fitting corpus...", flush=True)
        blitz_fit_rows = collect(args.blitz, session, "blitz", random.Random(SEED))
        rapid_fit_rows = collect(args.rapid, session, "rapid", random.Random(SEED))
        print("reading the held-out players...", flush=True)
        held_blitz = collect(args.held_out, session, "blitz", random.Random(SEED))
        held_rapid = collect(args.held_out, session, "rapid", random.Random(SEED))

    report("blitz", BLITZ_FIT, blitz_fit_rows, held_blitz, args)
    report("rapid (control)", RAPID_FIT, rapid_fit_rows, held_rapid, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
