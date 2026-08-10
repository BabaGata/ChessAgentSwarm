"""E26b — does the move the player was shown still beat the move they played?

E26 found that 90 % of moves called an error at depth 15 are still errors at
depth 22, and that the alternative the report offers is still the engine's **top
choice** only 78 % of the time. That 78 % is easy to overread. The report does
not claim the shown move is optimal; it claims it was better than what happened:

    For example game 3YS085d3, move 40, you played f6e6 (h3e6 was better)

So the bar that matters is the weaker one, and it is the one E26 did not measure.
A shown move that has slipped from first to second best is still sound advice. A
shown move that is **worse than the move played** is a defect in the report.

Only two positions per move are needed — after the played move and after the
shown one — because depth 22's own favourite is irrelevant to this question.
Evaluations are cached to disk so any further follow-up is free.

The sample is identical to E26 by construction: same seed, same player order,
same per-player count.

Usage:
    python better_move.py --pgn DIR --blitz DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.labels import clamp_cp, win_probability  # noqa: E402
from chesscoach.analysis.parallel import _evaluate_with_engines  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

SHALLOW = 15
RAPID_GAMES = 24
SEED = 20260808

# Below this the two moves are the same move as far as a player is concerned.
NEGLIGIBLE_WP = 1.0


def after_fen(fen_before: str, uci: str) -> str | None:
    board = chess.Board(fen_before)
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    if move not in board.legal_moves:
        return None
    board.push(move)
    return board.fen()


def mover_wp(score_cp: int, mover_is_white: bool) -> float:
    """Win probability from the mover's point of view, clamped as production does."""
    cp = clamp_cp(score_cp)
    return win_probability(cp if mover_is_white else -cp)


def main() -> int:
    import random

    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--blitz", type=Path, default=None)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--players", type=int, default=30)
    parser.add_argument("--per-player", type=int, default=40)
    parser.add_argument("--deep", type=int, default=22)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--evals", type=Path, default=None, help="where to cache deep evals")
    args = parser.parse_args()

    rng = random.Random(SEED)
    paths = sorted(args.pgn.glob("*.pgn"))[: args.players]
    sampled = []

    with engine_session(args.engine, SHALLOW, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            player = path.stem
            games = sorted(
                (g for g in parse_pgn_file(path) if g.involves(player)),
                key=lambda g: (g.date or "", g.game_id),
            )[-RAPID_GAMES:]
            if args.blitz and (extra := args.blitz / f"{player}.pgn").exists():
                games = games + [g for g in parse_pgn_file(extra) if g.involves(player)]

            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            observed = analyse_corpus(corpus, games, session.analyser)
            mine = diagnosable(
                tuple(o for o in observed if o.mover.lower() == player.lower())
            )
            if not mine:
                continue
            sampled.extend(rng.sample(list(mine), min(args.per_player, len(mine))))
            print(f"  {index:>3}/{len(paths)} {player}", flush=True)

    # Only moves the report would actually comment on: an error, with an
    # alternative to offer, and the two genuinely different.
    cases = []
    wanted: dict[str, None] = {}
    for o in sampled:
        if o.label is None or not o.best_move or o.best_move == o.move_played:
            continue
        played = after_fen(o.fen_before, o.move_played)
        shown = after_fen(o.fen_before, o.best_move)
        if played is None or shown is None:
            continue
        cases.append((o, played, shown))
        wanted[played] = None
        wanted[shown] = None

    fens = list(wanted)
    print(f"\n{len(cases)} error moves with an alternative shown, "
          f"{len(fens)} positions at depth {args.deep}", flush=True)

    started = time.perf_counter()
    deep = _evaluate_with_engines(fens, args.engine, args.deep, workers=args.workers)
    print(f"  done in {(time.perf_counter() - started) / 60:.1f} min", flush=True)

    if args.evals:
        args.evals.write_text(
            json.dumps({fen: e.score_cp for fen, e in deep.items()}), encoding="utf-8"
        )

    better = worse = same = 0
    margins = []
    regressions = []

    for o, played, shown in cases:
        a, b = deep.get(played), deep.get(shown)
        if a is None or b is None:
            continue
        gained = mover_wp(b.score_cp, o.mover_is_white) - mover_wp(a.score_cp, o.mover_is_white)
        margins.append(gained)
        if gained > NEGLIGIBLE_WP:
            better += 1
        elif gained < -NEGLIGIBLE_WP:
            worse += 1
            regressions.append((gained, o))
        else:
            same += 1

    total = better + worse + same
    if not total:
        print("nothing comparable")
        return 1

    print(f"\n{'=' * 72}")
    print(f"{total} moves where the report said 'X was better', judged at depth "
          f"{args.deep}\n")
    print(f"  the shown move is still better        {better:>5}   {better / total:.0%}")
    print(f"  the two are within {NEGLIGIBLE_WP:.0f} point         {same:>5}   {same / total:.0%}")
    print(f"  **the shown move is worse**           {worse:>5}   {worse / total:.0%}")

    ordered = sorted(margins)
    print(f"\n  win probability the shown move gains, per move")
    print(f"    median {statistics.median(ordered):>6.1f}   "
          f"p10 {ordered[len(ordered) // 10]:>6.1f}   "
          f"p90 {ordered[9 * len(ordered) // 10]:>6.1f}")

    if regressions:
        print(f"\n  worst regressions (shown move loses more than the played one):")
        for gained, o in sorted(regressions)[:5]:
            print(f"    {gained:>6.1f} wp   game {o.game_id} ply {o.ply}   "
                  f"played {o.move_played}, shown {o.best_move}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
