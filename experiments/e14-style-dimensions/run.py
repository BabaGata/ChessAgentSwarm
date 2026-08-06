"""E14 — is there any style to measure, or only strength wearing a label?

V3 is the last vision capability at zero. `domain.coaching` § 6 is unusually
directive about how to approach it: **measured tendencies plus measured
performance, not a personality label**, and treat the whole idea with suspicion.

So a candidate style dimension has to clear **two** bars, not one:

  * **it varies between players** (L-023) — otherwise there is no dimension;
  * **it is uncorrelated with rating** (L-025) — otherwise it is not style, it is
    strength under a friendlier name, and the swarm already measures strength to
    ±103 points.

The second bar is the one that matters here and the one this project has been
caught by before: S7's `missed_quiet` spread handsomely and turned out to be the
error rate. A "tendency" that rises with rating is the same failure with the word
"style" attached, and it is exactly what a personality label would paper over.

Candidates, all cheap board or clock properties of the player's own moves:

    capture_share    how much of their play is captures
    check_share      how much is checks
    queenless_share  how much they play with the queens off
    material_at_20   non-pawn pieces still on at move 20 — open versus closed
    game_length      how long their games run
    seconds_per_move pace, which is the only temperament signal available

Usage:
    python run.py --pgn DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import GameRecord, parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

CANDIDATES = (
    "capture_share",
    "check_share",
    "queenless_share",
    "material_at_20",
    "game_length",
    "seconds_per_move",
)

MIN_MOVES = 200
MIN_RATED_GAMES = 10

# A dimension is only style if it survives both. The rating bar is deliberately
# strict: at |r| above this the "tendency" is mostly telling us how strong the
# player is, which the swarm already knows far more precisely.
MIN_SPREAD = 1.35
MAX_RATING_CORR = 0.35


def _queens_off(fen: str) -> bool:
    board = chess.Board(fen)
    return not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(
        chess.QUEEN, chess.BLACK
    )


def player_rating(games: tuple[GameRecord, ...], player: str) -> float | None:
    ratings = [
        game.white_elo if game.player_is_white(player) else game.black_elo
        for game in games
        if (game.white_elo if game.player_is_white(player) else game.black_elo)
    ]
    return statistics.mean(ratings) if len(ratings) >= MIN_RATED_GAMES else None


def tendencies(observations, games, player: str) -> dict[str, float] | None:
    mine = diagnosable(
        tuple(o for o in observations if o.mover.lower() == player.lower())
    )
    if len(mine) < MIN_MOVES:
        return None

    captures = checks = queenless = 0
    material = []
    for observation in mine:
        board = chess.Board(observation.fen_before)
        try:
            move = chess.Move.from_uci(observation.move_played)
        except ValueError:
            continue
        if move not in board.legal_moves:
            continue
        captures += board.is_capture(move)
        checks += board.gives_check(move)
        queenless += not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(
            chess.QUEEN, chess.BLACK
        )
        if observation.ply == 40:
            material.append(
                sum(
                    len(board.pieces(piece, colour))
                    for piece in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
                    for colour in (chess.WHITE, chess.BLACK)
                )
            )

    seconds = [o.seconds_spent for o in mine if o.seconds_spent is not None]
    lengths = [len(g.moves) for g in games]

    # The performance half: do they actually play better where they prefer to be?
    off = [o for o in mine if _queens_off(o.fen_before)]
    on = [o for o in mine if not _queens_off(o.fen_before)]
    fit = None
    if len(off) >= 50 and len(on) >= 50:
        with_queens = sum(1 for o in on if o.label is not None) / len(on)
        without = sum(1 for o in off if o.label is not None) / len(off)
        fit = without / with_queens if with_queens else None

    return {
        "queenless_fit": fit or 0.0,
        "capture_share": captures / len(mine),
        "check_share": checks / len(mine),
        "queenless_share": queenless / len(mine),
        "material_at_20": statistics.mean(material) if material else 0.0,
        "game_length": statistics.mean(lengths) if lengths else 0.0,
        "seconds_per_move": statistics.mean(seconds) if seconds else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    args = parser.parse_args()

    rows: list[tuple[float, dict[str, float]]] = []
    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"screening {len(paths)} players at depth {args.depth}\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            games = parse_pgn_file(path)
            corpus = build_corpus(path.stem, games)
            rating = player_rating(games, path.stem) if corpus.n_games else None
            if rating is None:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            measured = tendencies(observations, games, path.stem)
            if measured is None:
                continue
            rows.append((rating, measured))
            print(f"  {index:>2}/{len(paths)} {path.stem}", flush=True)

    if len(rows) < 20:
        print("\ntoo few players")
        return 1

    ratings = [r for r, _ in rows]
    print(f"\n{len(rows)} players, ratings {min(ratings):.0f}-{max(ratings):.0f}\n")
    print(f"{'dimension':<18} {'median':>9} {'p90/med':>9} {'corr rating':>12}  verdict")

    for name in CANDIDATES:
        values = [f[name] for _, f in rows]
        if not any(values):
            continue
        ordered = sorted(values)
        median = statistics.median(ordered)
        spread = ordered[int(0.90 * (len(ordered) - 1))] / median if median else float("inf")
        r = statistics.correlation(values, ratings)

        if spread < MIN_SPREAD:
            verdict = "too uniform"
        elif abs(r) > MAX_RATING_CORR:
            verdict = "**strength, not style**"
        else:
            verdict = "style"
        print(f"{name:<18} {median:>9.3f} {spread:>9.2f} {r:>12.3f}  {verdict}")

    print(
        f"\nBars: spread >= {MIN_SPREAD} and |corr with rating| <= {MAX_RATING_CORR}."
        "\nA dimension that rises with rating is strength wearing a friendlier name,"
        "\nand the swarm already measures strength to +/-103 points (E13)."
    )

    fits = [f["queenless_fit"] for _, f in rows if f.get("queenless_fit")]
    if len(fits) >= 20:
        ordered = sorted(fits)
        median = statistics.median(ordered)
        p10 = ordered[int(0.10 * (len(ordered) - 1))]
        p90 = ordered[int(0.90 * (len(ordered) - 1))]
        print(
            "\nThe other half of domain.coaching section 6 — does the tendency suit them?"
            "\nqueenless_fit = error rate with queens off / error rate with queens on:"
            f"\n  n={len(fits)}  median {median:.2f}  p10 {p10:.2f}  p90 {p90:.2f}  "
            f"spread {p90 / median:.2f}"
            "\n  Below 1 means they really are better there; above 1 means the preference"
            "\n  does not pay. A spread near 1 would mean players do not differ, and the"
            "\n  fit half would have nothing to say."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
