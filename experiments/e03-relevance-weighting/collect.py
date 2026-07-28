"""Collect per-move records pairing positional features with error outcomes (E03).

E02 showed positional features are detectable but that presence alone is not a
coaching signal: isolated pawns occur in 96% of games. Open question C6 asks how
a detected feature is weighted for relevance.

This script builds the evidence needed to answer it. For every position it
records which features are present -- split into the mover's own features and
the opponent's -- and whether the move actually played was an error. The
relevance question then becomes measurable: does the presence of a feature shift
the probability that this player errs?

Output: one JSON record per move, consumed by relevance.py.

Usage:
    python collect.py --games-dir DIR --engine PATH --out records.jsonl
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import chess
import chess.engine
import chess.pgn

# The detectors live in the E02 experiment; import them rather than duplicating,
# so a change to a definition cannot silently diverge between experiments.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "e02-positional-detectors"))
from detectors import DETECTORS  # noqa: E402

# Matches E01's working setting: depth 15 routine analysis, single-threaded
# engines across many processes.
DEPTH = 15
HASH_MB = 256
CLAMP_CP = 1000

# Win-probability thresholds, as in E01.
INACCURACY_WP = 10.0
MISTAKE_WP = 20.0
BLUNDER_WP = 30.0

# Skip the first moves: opening play is book-driven and structures have not formed.
FIRST_PLY = 16


def win_probability(cp: int) -> float:
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * cp)) - 1.0)


def score_to_cp(score: chess.engine.PovScore) -> int:
    white = score.white()
    if white.is_mate():
        return CLAMP_CP if (white.mate() or 0) > 0 else -CLAMP_CP
    return max(-CLAMP_CP, min(CLAMP_CP, white.score() or 0))


def classify(loss_wp: float) -> str | None:
    if loss_wp >= BLUNDER_WP:
        return "blunder"
    if loss_wp >= MISTAKE_WP:
        return "mistake"
    if loss_wp >= INACCURACY_WP:
        return "inaccuracy"
    return None


def phase_of(board: chess.Board) -> str:
    """Coarse phase by remaining material, used as a confound check."""
    pieces = sum(
        len(board.pieces(pt, color))
        for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
        for color in (chess.WHITE, chess.BLACK)
    )
    if pieces >= 10:
        return "opening_middlegame"
    if pieces >= 5:
        return "late_middlegame"
    return "endgame"


def features_for(board: chess.Board, mover: chess.Color) -> list[str]:
    """Feature names tagged by owner, from the mover's point of view.

    `own_backward_pawn` is a weakness the mover carries; `opp_outpost` is one
    they have conceded. The distinction matters: a coach's advice differs
    entirely between the two.
    """
    names: list[str] = []
    for key, detector in DETECTORS.items():
        if detector(board, mover):
            names.append(f"own_{key}")
        if detector(board, not mover):
            names.append(f"opp_{key}")
    return names


def process_game(task: tuple[str, str, str]) -> list[dict[str, object]]:
    """Analyse one game and emit a record per move played after FIRST_PLY."""
    engine_path, pgn_text, source_player = task
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return []

    white = game.headers.get("White", "?")
    black = game.headers.get("Black", "?")
    game_id = game.headers.get("GameId", game.headers.get("Site", "?"))

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    records: list[dict[str, object]] = []
    try:
        engine.configure({"Threads": 1, "Hash": HASH_MB})
        limit = chess.engine.Limit(depth=DEPTH)
        board = game.board()

        info = engine.analyse(board, limit)
        prev_cp = score_to_cp(info["score"])
        prev_best = info.get("pv", [None])[0]

        for ply, move in enumerate(game.mainline_moves(), start=1):
            mover = board.turn
            mover_name = white if mover == chess.WHITE else black
            played_best = move == prev_best
            feats = features_for(board, mover) if ply >= FIRST_PLY else []
            phase = phase_of(board)

            board.push(move)
            info = engine.analyse(board, limit)
            cur_cp = score_to_cp(info["score"])

            if ply >= FIRST_PLY:
                if played_best:
                    loss = 0.0
                else:
                    before = win_probability(prev_cp if mover == chess.WHITE else -prev_cp)
                    after = win_probability(cur_cp if mover == chess.WHITE else -cur_cp)
                    loss = max(0.0, before - after)
                records.append(
                    {
                        "game_id": game_id,
                        "source_player": source_player,
                        "mover": mover_name,
                        "ply": ply,
                        "phase": phase,
                        "features": feats,
                        "loss_wp": round(loss, 2),
                        "label": classify(loss),
                    }
                )

            prev_cp = cur_cp
            prev_best = info.get("pv", [None])[0]
    finally:
        engine.quit()
    return records


def load_tasks(games_dir: Path, engine: str) -> list[tuple[str, str, str]]:
    tasks = []
    for pgn_path in sorted(games_dir.glob("*.pgn")):
        source_player = pgn_path.stem
        with pgn_path.open(encoding="utf-8") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                if len(list(game.mainline_moves())) < FIRST_PLY + 6:
                    continue
                tasks.append((engine, str(game), source_player))
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-dir", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = parser.parse_args()

    tasks = load_tasks(args.games_dir, args.engine)
    print(f"analysing {len(tasks)} games at depth {DEPTH} on {args.workers} workers", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.out.open("w", encoding="utf-8") as sink:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for done, records in enumerate(pool.map(process_game, tasks), start=1):
                for record in records:
                    sink.write(json.dumps(record) + "\n")
                    written += 1
                if done % 10 == 0:
                    print(f"  {done}/{len(tasks)} games, {written} records", flush=True)

    print(f"wrote {written} records -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
