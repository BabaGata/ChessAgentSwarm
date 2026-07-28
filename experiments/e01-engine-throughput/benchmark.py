"""E01 — Stockfish throughput and diagnosis-stability benchmark.

Answers two open questions:

  A1  How long does analysing a player's games actually take on this machine?
  A2  Does deeper analysis change the *diagnosis*, or only the evaluation?

Method
------
Every position of a game is evaluated once, from White's point of view. The
centipawn loss of a move is then the drop in the mover's evaluation between the
position before and after it -- one analysis per position rather than two, which
is what makes whole-game analysis affordable at all.

Phase "throughput": a small set of games analysed under several engine
configurations, measuring seconds per position and per game.

Phase "stability": the same games analysed at a cheap and an expensive setting,
comparing the resulting *error labels* rather than the raw evaluations. If the
labels agree, the cheap setting is the correct one to use forever.

Usage:
    python benchmark.py --games-dir DIR --engine PATH --out DIR [--phase both]
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.engine
import chess.pgn

# Provisional error thresholds in centipawns. Lichess classifies on win-probability
# deltas instead; these are simpler and adequate for a stability comparison, but
# they are a project decision, not a standard -- see open question C2.
INACCURACY_CP = 50
MISTAKE_CP = 100
BLUNDER_CP = 250

# Evaluations are clamped before differencing so that a forced mate does not
# produce a meaningless six-figure centipawn loss.
CLAMP_CP = 1000

HASH_MB = 512  # held constant across configurations so timings stay comparable


@dataclass(frozen=True)
class Config:
    """One engine configuration to benchmark."""

    name: str
    threads: int
    depth: int | None = None
    movetime_ms: int | None = None

    def limit(self) -> chess.engine.Limit:
        if self.depth is not None:
            return chess.engine.Limit(depth=self.depth)
        return chess.engine.Limit(time=self.movetime_ms / 1000.0)


@dataclass
class GameAnalysis:
    """Per-position evaluations and the error labels derived from them."""

    game_id: str
    scores_cp: list[int] = field(default_factory=list)
    positions: int = 0
    seconds: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)


def load_games(games_dir: Path, limit: int) -> list[chess.pgn.Game]:
    games: list[chess.pgn.Game] = []
    for pgn_path in sorted(games_dir.glob("*.pgn")):
        with pgn_path.open(encoding="utf-8") as handle:
            while len(games) < limit:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                if len(list(game.mainline_moves())) < 10:
                    continue  # not enough of a game to measure anything
                games.append(game)
        if len(games) >= limit:
            break
    return games


def clamp(cp: int) -> int:
    return max(-CLAMP_CP, min(CLAMP_CP, cp))


def score_to_cp(score: chess.engine.PovScore) -> int:
    """White-relative centipawns, with mates clamped to the bounds."""
    white = score.white()
    if white.is_mate():
        mate_in = white.mate() or 0
        return CLAMP_CP if mate_in > 0 else -CLAMP_CP
    return clamp(white.score() or 0)


def classify(loss_cp: int) -> str | None:
    if loss_cp >= BLUNDER_CP:
        return "blunder"
    if loss_cp >= MISTAKE_CP:
        return "mistake"
    if loss_cp >= INACCURACY_CP:
        return "inaccuracy"
    return None


def analyse_game(
    engine: chess.engine.SimpleEngine, game: chess.pgn.Game, config: Config
) -> GameAnalysis:
    """Evaluate every position of one game and label the moves."""
    result = GameAnalysis(game_id=game.headers.get("GameId", game.headers.get("Site", "?")))
    board = game.board()
    limit = config.limit()

    start = time.perf_counter()
    info = engine.analyse(board, limit)
    result.scores_cp.append(score_to_cp(info["score"]))
    result.positions += 1

    for ply, move in enumerate(game.mainline_moves()):
        mover_is_white = board.turn == chess.WHITE
        board.push(move)
        info = engine.analyse(board, limit)
        result.scores_cp.append(score_to_cp(info["score"]))
        result.positions += 1

        before, after = result.scores_cp[-2], result.scores_cp[-1]
        # Loss from the mover's point of view: White wants the score to rise.
        loss = (before - after) if mover_is_white else (after - before)
        label = classify(max(0, loss))
        if label:
            side = "W" if mover_is_white else "B"
            result.labels[f"{side}{ply // 2 + 1}"] = label

    result.seconds = time.perf_counter() - start
    return result


def run_config(
    engine_path: str, games: list[chess.pgn.Game], config: Config
) -> tuple[list[GameAnalysis], dict[str, float]]:
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    try:
        engine.configure({"Threads": config.threads, "Hash": HASH_MB})
        analyses = []
        for index, game in enumerate(games, start=1):
            analysis = analyse_game(engine, game, config)
            analyses.append(analysis)
            print(
                f"    game {index}/{len(games)}: {analysis.positions} positions "
                f"in {analysis.seconds:.1f}s",
                flush=True,
            )
    finally:
        engine.quit()

    total_seconds = sum(a.seconds for a in analyses)
    total_positions = sum(a.positions for a in analyses)
    summary = {
        "games": len(analyses),
        "positions": total_positions,
        "total_seconds": round(total_seconds, 2),
        "seconds_per_position": round(total_seconds / max(1, total_positions), 4),
        "seconds_per_game": round(total_seconds / max(1, len(analyses)), 2),
        "projected_seconds_50_games": round(total_seconds / max(1, len(analyses)) * 50, 1),
    }
    return analyses, summary


def compare_labels(cheap: list[GameAnalysis], rich: list[GameAnalysis]) -> dict[str, object]:
    """How much does the *diagnosis* change between two settings? (A2)"""
    agree = disagree = only_cheap = only_rich = 0
    blunder_cheap = blunder_rich = blunder_both = 0

    for a, b in zip(cheap, rich):
        keys = set(a.labels) | set(b.labels)
        for key in keys:
            label_a, label_b = a.labels.get(key), b.labels.get(key)
            if label_a and label_b:
                agree += label_a == label_b
                disagree += label_a != label_b
            elif label_a:
                only_cheap += 1
            else:
                only_rich += 1
            if label_a == "blunder":
                blunder_cheap += 1
            if label_b == "blunder":
                blunder_rich += 1
            if label_a == "blunder" and label_b == "blunder":
                blunder_both += 1

    total = agree + disagree + only_cheap + only_rich
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
        "blunder_jaccard_pct": round(
            100 * blunder_both / max(1, blunder_cheap + blunder_rich - blunder_both), 1
        ),
    }


THROUGHPUT_CONFIGS = [
    Config("depth15_t1", threads=1, depth=15),
    Config("depth15_t4", threads=4, depth=15),
    Config("depth15_t16", threads=16, depth=15),
    Config("depth18_t16", threads=16, depth=18),
    Config("depth20_t16", threads=16, depth=20),
    Config("movetime50_t4", threads=4, movetime_ms=50),
    Config("movetime100_t4", threads=4, movetime_ms=100),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-dir", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--phase", choices=["throughput", "stability", "both"], default="both")
    parser.add_argument("--throughput-games", type=int, default=5)
    parser.add_argument("--stability-games", type=int, default=20)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {"hash_mb": HASH_MB, "engine": args.engine}

    if args.phase in ("throughput", "both"):
        games = load_games(args.games_dir, args.throughput_games)
        print(f"A1 throughput: {len(games)} games\n", flush=True)
        summaries = {}
        for config in THROUGHPUT_CONFIGS:
            print(f"  config {config.name}", flush=True)
            _, summary = run_config(args.engine, games, config)
            summaries[config.name] = summary
            print(f"  -> {summary}\n", flush=True)
            (args.out / "throughput.json").write_text(
                json.dumps(summaries, indent=2), encoding="utf-8"
            )
        results["throughput"] = summaries

    if args.phase in ("stability", "both"):
        games = load_games(args.games_dir, args.stability_games)
        print(f"\nA2 stability: {len(games)} games", flush=True)
        cheap_cfg = Config("depth15_t16", threads=16, depth=15)
        rich_cfg = Config("depth20_t16", threads=16, depth=20)

        print(f"  analysing at {cheap_cfg.name}", flush=True)
        cheap, cheap_summary = run_config(args.engine, games, cheap_cfg)
        print(f"  analysing at {rich_cfg.name}", flush=True)
        rich, rich_summary = run_config(args.engine, games, rich_cfg)

        results["stability"] = {
            "cheap": {"config": cheap_cfg.name, **cheap_summary},
            "rich": {"config": rich_cfg.name, **rich_summary},
            "comparison": compare_labels(cheap, rich),
        }
        print(json.dumps(results["stability"], indent=2), flush=True)

    (args.out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWritten to {args.out / 'results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
