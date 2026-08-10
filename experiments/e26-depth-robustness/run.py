"""E26 — do the findings survive a deeper engine?

Every claim in this project rests on **depth 15** calling a move an error. E01
established at the very beginning that labels shift with depth, and that fact was
used to key the evaluation cache and then never followed up: nothing has ever
asked whether a deeper engine agrees with the diagnoses the swarm ships.

This is the closest thing to [[vision]]'s success criterion 2 — *the weaknesses
the swarm names match those an independent analysis identifies* — that can be run
without a human. The independent analysis is the same engine given far more time,
which is a weaker check than a strong player and a real one.

**Sampled, not exhaustive, and that is a design choice rather than a shortcut.**
Re-analysing one player's whole corpus at depth 22 costs ~53 minutes; the same
budget spent on sampled moves from *thirty* players buys a far better estimate of
the thing being asked, because the quantity of interest is a proportion. Precision
comes from the number of moves, and breadth comes from spreading them.

Each sampled move is re-labelled exactly as production would: evaluate the
position before, evaluate it after the move played, and run the same
`move_loss_wp` and `classify`. What changes is only the depth.

Deeper is not truth. Depth 22 is better evidence than depth 15 and still an
engine at a fixed depth; where they disagree this says the label is **fragile**,
not that it is wrong.

Usage:
    python run.py --pgn DIR --blitz DIR --engine PATH --cache DB
                  [--players 30] [--per-player 40] [--deep 22]
"""

from __future__ import annotations

import argparse
import collections
import random
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.labels import classify, move_loss_wp  # noqa: E402
from chesscoach.analysis.parallel import _evaluate_with_engines  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

SHALLOW = 15
RAPID_GAMES = 24
SEED = 20260808


def after_fen(fen_before: str, uci: str) -> str | None:
    board = chess.Board(fen_before)
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        return None
    board.push(move)
    return board.fen()


def relabel(before, after, mover_is_white: bool, played_best: bool):
    loss = move_loss_wp(
        before_cp=before.score_cp,
        after_cp=after.score_cp,
        mover_is_white=mover_is_white,
        played_best=played_best,
    )
    return loss, classify(loss)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--blitz", type=Path, default=None)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--players", type=int, default=30)
    parser.add_argument("--per-player", type=int, default=40)
    parser.add_argument("--deep", type=int, default=22)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    rng = random.Random(SEED)
    paths = sorted(args.pgn.glob("*.pgn"))[: args.players]
    sampled = []

    print(f"sampling up to {args.per_player} moves from each of {len(paths)} players "
          f"at depth {SHALLOW}\n", flush=True)

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

            # Depth 15 is already cached from every earlier run, so this pass is
            # free; only the deep evaluations below are paid for.
            observed = analyse_corpus(corpus, games, session.analyser)
            mine = diagnosable(
                tuple(o for o in observed if o.mover.lower() == player.lower())
            )
            if not mine:
                continue
            chosen = rng.sample(list(mine), min(args.per_player, len(mine)))
            sampled.extend((player, o) for o in chosen)
            print(f"  {index:>3}/{len(paths)} {player}: {len(chosen)} of {len(mine)} moves",
                  flush=True)

    # Positions to evaluate deep: each move needs the position before and after.
    wanted: dict[str, None] = {}
    usable = []
    for player, o in sampled:
        landing = after_fen(o.fen_before, o.move_played)
        if landing is None:
            continue
        usable.append((player, o, landing))
        wanted[o.fen_before] = None
        wanted[landing] = None

    fens = list(wanted)
    print(f"\n{len(usable)} moves, {len(fens)} distinct positions to evaluate at "
          f"depth {args.deep}", flush=True)
    started = time.perf_counter()
    deep = _evaluate_with_engines(fens, args.engine, args.deep, workers=args.workers)
    print(f"  done in {(time.perf_counter() - started) / 60:.1f} min", flush=True)

    pairs: collections.Counter = collections.Counter()
    best_same = 0
    loss_shift = []

    for _player, o, landing in usable:
        before, after = deep.get(o.fen_before), deep.get(landing)
        if before is None or after is None:
            continue
        played_best = before.best_move == o.move_played
        loss, label = relabel(before, after, o.mover_is_white, played_best)

        pairs[(o.label.value if o.label else "clean", label.value if label else "clean")] += 1
        best_same += before.best_move == o.best_move
        loss_shift.append((o.loss_wp, loss))

    total = sum(pairs.values())
    if not total:
        print("nothing comparable")
        return 1

    print(f"\n{'=' * 72}")
    print(f"{total} of players' own diagnosable moves, depth {SHALLOW} against "
          f"depth {args.deep}\n")

    errors = sum(n for (a, _), n in pairs.items() if a != "clean")
    kept = sum(n for (a, b), n in pairs.items() if a != "clean" and b != "clean")
    identical = sum(n for (a, b), n in pairs.items() if a == b)
    invented = sum(n for (a, b), n in pairs.items() if a == "clean" and b != "clean")
    clean = total - errors

    print(f"  called an error at {SHALLOW}            {errors}")
    print(f"  still an error at {args.deep}              {kept}   "
          f"({kept / max(1, errors):.0%})   <- every finding rests on this")
    print(f"  exactly the same label               {identical / total:.0%} of all moves")
    print(f"  clean at {SHALLOW}, an error at {args.deep}   {invented}   "
          f"({invented / max(1, clean):.1%} of clean moves)")

    for kind in ("blunder", "mistake", "inaccuracy"):
        at15 = sum(n for (a, _), n in pairs.items() if a == kind)
        same = sum(n for (a, b), n in pairs.items() if a == kind and b == kind)
        any_error = sum(n for (a, b), n in pairs.items() if a == kind and b != "clean")
        if at15:
            print(f"\n  {kind}s at {SHALLOW}: {at15}")
            print(f"    still a {kind}          {same / at15:.0%}")
            print(f"    still an error at all   {any_error / at15:.0%}")

    print(f"\n  the better move the player was shown is still best   "
          f"{best_same / total:.0%}")

    # What the rates would do: the same transition matrix, read as a multiplier.
    implied = (kept + invented) / max(1, errors)
    print(f"\n  implied error-rate ratio at {args.deep}    {implied:.2f}")
    print("  Near 1 means a claim's rate -- and so the comparison against peers that")
    print("  makes it a finding -- does not depend on the depth it was measured at.")

    print(f"\n  where they disagree, by depth-{SHALLOW} label:")
    for (a, b), n in sorted(pairs.items(), key=lambda kv: -kv[1]):
        if a != b:
            print(f"    {a:<12} -> {b:<12} {n:>5}   ({n / total:.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
