"""E01 — Stockfish throughput and diagnosis-stability benchmark.

Answers two open questions:

  A1  How long does analysing a player's games actually take on this machine?
  A2  Does deeper analysis change the *diagnosis*, or only the evaluation?

Method
------
Every position of a game is evaluated once, from White's point of view, together
with the engine's preferred move. The loss attributed to the move actually played
is then the drop in the mover's evaluation between the position before and after
it -- one analysis per position rather than two, which is what makes whole-game
analysis affordable.

Two corrections carried over from prior art (see docs/notes/domain.prior-art.md,
lesson L-005), both of which materially change the labels:

  * Losses are measured in **win-probability points**, not centipawns. Losing
    100cp at equality decides a game; losing 100cp at +900 is irrelevant, yet a
    fixed centipawn threshold labels both identically.
  * A move that matches the engine's own first choice is recorded as zero loss,
    and evaluations are clamped before differencing. Without this, mate-delivering
    moves register as enormous *losses*, because mate is encoded as +-30000.

Parallelism: run 1 engine thread per process and many processes. Measured on this
machine, a fixed-depth search is fastest single-threaded -- extra threads widen
the search rather than reaching the target depth sooner, so cores are far better
spent on more games at once than on more threads per game.

Usage:
    python benchmark.py --games-dir DIR --engine PATH --out DIR [--phase both]
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import chess
import chess.engine
import chess.pgn

# --- Error classification -------------------------------------------------
# Thresholds are in win-probability points (0-100). Provisional project values,
# not a standard -- see open question C2, which must fix and validate them.
INACCURACY_WP = 10.0
MISTAKE_WP = 20.0
BLUNDER_WP = 30.0

# Evaluations are clamped before differencing so a forced mate cannot produce a
# meaningless loss. Stockfish encodes mate as +-30000 internally.
CLAMP_CP = 1000

HASH_MB = 256  # per engine process; kept constant so timings stay comparable


@dataclass(frozen=True)
class Config:
    """One engine configuration to benchmark."""

    name: str
    threads: int = 1
    depth: int | None = None
    movetime_ms: int | None = None

    def limit(self) -> chess.engine.Limit:
        if self.depth is not None:
            return chess.engine.Limit(depth=self.depth)
        return chess.engine.Limit(time=(self.movetime_ms or 0) / 1000.0)


@dataclass
class GameResult:
    """Per-game timing and the error labels derived from the evaluations."""

    game_id: str
    positions: int
    seconds: float
    labels: dict[str, str]


def win_probability(cp: int) -> float:
    """Lichess' centipawn -> win-percentage conversion."""
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-0.00368208 * cp)) - 1.0)


def clamp(cp: int) -> int:
    return max(-CLAMP_CP, min(CLAMP_CP, cp))


def score_to_cp(score: chess.engine.PovScore) -> int:
    """White-relative centipawns, with mates clamped to the bounds."""
    white = score.white()
    if white.is_mate():
        return CLAMP_CP if (white.mate() or 0) > 0 else -CLAMP_CP
    return clamp(white.score() or 0)


def classify(loss_wp: float) -> str | None:
    if loss_wp >= BLUNDER_WP:
        return "blunder"
    if loss_wp >= MISTAKE_WP:
        return "mistake"
    if loss_wp >= INACCURACY_WP:
        return "inaccuracy"
    return None


def load_games(games_dir: Path, limit: int) -> list[str]:
    """Return games as PGN strings so they can be shipped to worker processes."""
    games: list[str] = []
    for pgn_path in sorted(games_dir.glob("*.pgn")):
        with pgn_path.open(encoding="utf-8") as handle:
            while len(games) < limit:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                if len(list(game.mainline_moves())) < 10:
                    continue  # too short to measure anything
                games.append(str(game))
        if len(games) >= limit:
            break
    return games


def analyse_one_game(task: tuple[str, str, Config]) -> GameResult:
    """Worker entry point: analyse a single game with its own engine process."""
    engine_path, pgn_text, config = task
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return GameResult(game_id="?", positions=0, seconds=0.0, labels={})

    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    try:
        engine.configure({"Threads": config.threads, "Hash": HASH_MB})
        board = game.board()
        limit = config.limit()
        labels: dict[str, str] = {}
        positions = 0

        start = time.perf_counter()
        info = engine.analyse(board, limit)
        prev_cp = score_to_cp(info["score"])
        prev_best = info.get("pv", [None])[0]
        positions += 1

        for ply, move in enumerate(game.mainline_moves()):
            mover_is_white = board.turn == chess.WHITE
            played_best = move == prev_best
            board.push(move)
            info = engine.analyse(board, limit)
            cur_cp = score_to_cp(info["score"])
            positions += 1

            if not played_best:
                # From the mover's point of view: White wants the score to rise.
                before_wp = win_probability(prev_cp if mover_is_white else -prev_cp)
                after_wp = win_probability(cur_cp if mover_is_white else -cur_cp)
                label = classify(max(0.0, before_wp - after_wp))
                if label:
                    # Must match `chesscoach.phrasing.move_number`. Not imported because these
                    # two predate the package and depend on nothing in it; the arithmetic is
                    # inlined instead. `ply // 2 + 1` -- what was here -- puts every Black move
                    # one too high, and it spread to four experiments by being copied (L-044).
                    labels[f"{'W' if mover_is_white else 'B'}{(ply + 1) // 2}"] = label

            prev_cp = cur_cp
            prev_best = info.get("pv", [None])[0]

        seconds = time.perf_counter() - start
    finally:
        engine.quit()

    return GameResult(
        game_id=game.headers.get("GameId", game.headers.get("Site", "?")),
        positions=positions,
        seconds=seconds,
        labels=labels,
    )


def run_config(
    engine_path: str, games: list[str], config: Config, workers: int
) -> tuple[list[GameResult], dict[str, float]]:
    """Analyse every game under one configuration, across `workers` processes."""
    tasks = [(engine_path, pgn, config) for pgn in games]
    wall_start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(analyse_one_game, tasks))
    wall_seconds = time.perf_counter() - wall_start

    engine_seconds = sum(r.seconds for r in results)
    positions = sum(r.positions for r in results)
    summary = {
        "threads_per_engine": config.threads,
        "workers": workers,
        "games": len(results),
        "positions": positions,
        "engine_seconds_total": round(engine_seconds, 2),
        "wall_seconds": round(wall_seconds, 2),
        "seconds_per_position": round(engine_seconds / max(1, positions), 4),
        "wall_seconds_per_game": round(wall_seconds / max(1, len(results)), 2),
        "projected_wall_seconds_50_games": round(wall_seconds / max(1, len(results)) * 50, 1),
    }
    return results, summary


def compare_labels(cheap: list[GameResult], rich: list[GameResult]) -> dict[str, object]:
    """How much does the *diagnosis* change between two settings? (A2)"""
    agree = disagree = only_cheap = only_rich = 0
    blunder_cheap = blunder_rich = blunder_both = 0

    for a, b in zip(cheap, rich):
        for key in set(a.labels) | set(b.labels):
            label_a, label_b = a.labels.get(key), b.labels.get(key)
            if label_a and label_b:
                agree += label_a == label_b
                disagree += label_a != label_b
            elif label_a:
                only_cheap += 1
            else:
                only_rich += 1
            blunder_cheap += label_a == "blunder"
            blunder_rich += label_b == "blunder"
            blunder_both += label_a == "blunder" and label_b == "blunder"

    total = agree + disagree + only_cheap + only_rich
    union = blunder_cheap + blunder_rich - blunder_both
    return {
        "labelled_moves_total": total,
        "same_label": agree,
        "different_label": disagree,
        "only_in_cheap": only_cheap,
        "only_in_rich": only_rich,
        "exact_agreement_pct": round(100 * agree / max(1, total), 1),
        "blunders_cheap": blunder_cheap,
        "blunders_rich": blunder_rich,
        "blunders_in_both": blunder_both,
        "blunder_agreement_pct": round(100 * blunder_both / max(1, union), 1),
    }


THROUGHPUT_CONFIGS = [
    Config("depth12_t1", depth=12),
    Config("depth15_t1", depth=15),
    Config("depth18_t1", depth=18),
    Config("depth20_t1", depth=20),
    Config("movetime50_t1", movetime_ms=50),
    Config("movetime200_t1", movetime_ms=200),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-dir", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--phase", choices=["throughput", "stability", "both"], default="both")
    parser.add_argument("--throughput-games", type=int, default=10)
    parser.add_argument("--stability-games", type=int, default=30)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {
        "engine": args.engine,
        "hash_mb_per_process": HASH_MB,
        "workers": args.workers,
        "thresholds_win_pct": {
            "inaccuracy": INACCURACY_WP,
            "mistake": MISTAKE_WP,
            "blunder": BLUNDER_WP,
        },
    }

    if args.phase in ("throughput", "both"):
        games = load_games(args.games_dir, args.throughput_games)
        print(f"A1 throughput: {len(games)} games, {args.workers} workers\n", flush=True)
        summaries: dict[str, object] = {}
        for config in THROUGHPUT_CONFIGS:
            _, summary = run_config(args.engine, games, config, args.workers)
            summaries[config.name] = summary
            print(f"  {config.name:16} {summary}", flush=True)
            (args.out / "throughput_v2.json").write_text(
                json.dumps(summaries, indent=2), encoding="utf-8"
            )
        results["throughput"] = summaries

    if args.phase in ("stability", "both"):
        games = load_games(args.games_dir, args.stability_games)
        print(f"\nA2 stability: {len(games)} games", flush=True)
        # Depth 18 is the reference rather than 20: measured wall time at depth 20
        # is dominated by whichever single game is longest (see results/README),
        # which makes it an impractical baseline for a 30-game comparison.
        pairs = [
            (Config("depth12_t1", depth=12), Config("depth18_t1", depth=18)),
            (Config("depth15_t1", depth=15), Config("depth18_t1", depth=18)),
            (Config("movetime100_t1", movetime_ms=100), Config("depth18_t1", depth=18)),
        ]
        cache: dict[str, list[GameResult]] = {}
        comparisons: dict[str, object] = {}
        for cheap_cfg, rich_cfg in pairs:
            for cfg in (cheap_cfg, rich_cfg):
                if cfg.name not in cache:
                    print(f"  analysing at {cfg.name}", flush=True)
                    cache[cfg.name], _ = run_config(args.engine, games, cfg, args.workers)
            comparison = compare_labels(cache[cheap_cfg.name], cache[rich_cfg.name])
            comparisons[f"{cheap_cfg.name}_vs_{rich_cfg.name}"] = comparison
            print(f"  {cheap_cfg.name} vs {rich_cfg.name}: {comparison}", flush=True)
        results["stability"] = comparisons

        (args.out / "labels_sample.json").write_text(
            json.dumps(
                {name: [asdict(r) for r in res[:3]] for name, res in cache.items()}, indent=2
            ),
            encoding="utf-8",
        )

    (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWritten to {args.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
