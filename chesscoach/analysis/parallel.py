"""Pre-evaluating a whole corpus of positions in parallel.

E01 measured the two facts that dictate this design:

  * at a **fixed depth** a single engine thread is fastest per position -- extra
    threads widen the search rather than reaching depth sooner;
  * parallelising **per game** leaves wall time hostage to the longest game,
    which is exactly how one 182-position game once held nineteen cores idle.

So positions are collected across the entire corpus, deduplicated, evaluated
across many single-threaded engines, and written to the cache in one pass. The
ordinary sequential analysis then runs on cache hits alone, unchanged.

Deduplication is worth more than it looks: openings repeat heavily both within
one player's games and across players, so a corpus of many players costs far
less than the sum of its parts.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Callable, Iterable, Sequence

import chess
import chess.engine

from chesscoach.analysis.cache import EvalCache, PositionEval
from chesscoach.analysis.engine import to_position_eval
from chesscoach.ingest.pgn import GameRecord

# Positions per worker per chunk. A new ProcessPoolExecutor is built for every
# chunk, and on Windows that spawns rather than forks -- each child re-imports
# the module and launches its own Stockfish. Measured on a 14-core laptop, one
# pool costs on the order of ten seconds, so the figure that matters is how many
# positions each worker gets before the pool is torn down.
#
# The old CHUNK_SIZE was a flat 250, which with 18 workers gave each one **14
# positions** before paying for a fresh pool -- so a 240,000-position corpus paid
# for ~960 pools. Sizing per worker instead keeps the amortisation constant as
# the machine changes.
POSITIONS_PER_WORKER = 400

# Floor for tiny corpora, where one pool is the whole job anyway.
MIN_CHUNK_SIZE = 250


def collect_positions(games: Iterable[GameRecord]) -> tuple[str, ...]:
    """Every distinct position the corpus visits, in a stable order.

    A malformed continuation ends that game's walk rather than raising: the rest
    of the corpus is still worth evaluating.
    """
    seen: dict[str, None] = {}

    for game in games:
        board = chess.Board()
        seen.setdefault(board.fen(), None)
        for uci in game.moves:
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                break
            board.push(move)
            seen.setdefault(board.fen(), None)

    return tuple(seen)


def prefetch(
    games: Sequence[GameRecord],
    cache: EvalCache,
    engine: str | Path,
    depth: int,
    workers: int | None = None,
    evaluate_batch: Callable[..., dict[str, PositionEval]] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> int:
    """Evaluate every uncached position in the corpus. Returns how many were new."""
    positions = collect_positions(games)
    if not positions:
        return 0

    engine_name = _engine_name(engine, evaluate_batch)
    missing = [fen for fen in positions if cache.get(fen, engine_name, depth) is None]
    if not missing:
        return 0

    evaluate = evaluate_batch or _evaluate_with_engines
    workers = workers or max(1, (os.cpu_count() or 4) - 2)
    chunk_size = max(MIN_CHUNK_SIZE, workers * POSITIONS_PER_WORKER)
    chunks = [missing[i : i + chunk_size] for i in range(0, len(missing), chunk_size)]

    done = 0
    for chunk in chunks:
        for fen, evaluation in evaluate(chunk, engine, depth, workers=workers).items():
            cache.put(fen, engine_name, depth, evaluation)
        done += len(chunk)
        if progress is not None:
            progress(done, len(missing))

    cache.commit()
    return len(missing)


def _engine_name(engine: str | Path, evaluate_batch: Callable | None) -> str:
    """The cache key's engine field, which must match what the analyser will use."""
    if evaluate_batch is not None:
        return str(engine)
    return _probe_engine_name(engine)


def _probe_engine_name(engine_path: str | Path) -> str:
    """Ask the engine what it calls itself, so cache keys line up exactly."""
    process = chess.engine.SimpleEngine.popen_uci(str(engine_path))
    try:
        return process.id.get("name", "unknown engine")
    finally:
        process.quit()


def _evaluate_with_engines(
    fens: Sequence[str], engine: str | Path, depth: int, workers: int = 4
) -> dict[str, PositionEval]:
    """Evaluate a chunk across a pool of single-threaded engines."""
    per_worker = max(1, len(fens) // workers + 1)
    tasks = [
        (str(engine), depth, fens[i : i + per_worker]) for i in range(0, len(fens), per_worker)
    ]

    results: dict[str, PositionEval] = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for batch in pool.map(_evaluate_task, tasks):
            results.update(batch)
    return results


def _evaluate_task(task: tuple[str, int, Sequence[str]]) -> dict[str, PositionEval]:
    """Worker entry point: one engine, one thread, many positions."""
    engine_path, depth, fens = task
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    try:
        engine.configure({"Threads": 1, "Hash": 128})
        limit = chess.engine.Limit(depth=depth)
        return {
            fen: to_position_eval(engine.analyse(chess.Board(fen), limit)) for fen in fens
        }
    finally:
        engine.quit()
