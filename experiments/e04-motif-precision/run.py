"""E04 — do the motif detectors fire sensibly on real games?

Unit tests prove each detector matches its stated definition. This asks the
different question that decides whether they may be used: how often do they fire
on real boards, and are the firings correct?

The recorded failure mode is **over-firing**. Prior art documented a skewer
detector firing 10-18x too often, and E02 found that plausible-looking detector
code fires far too readily. A base rate that looks implausible is the first
symptom, and a hand-checked sample is the confirmation.

Reads engine best-moves straight from the evaluation cache, so it needs no
engine of its own for a corpus that has already been analysed.

Usage:
    python run.py --games-dir DIR --cache CACHE.db --out DIR [--sample 24]
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import chess

from chesscoach.analysis.cache import EvalCache
from chesscoach.ingest.pgn import parse_pgn_dir
from chesscoach.tactics import Motif, detect_motifs

SEED = 20260731
DEFAULT_ENGINE = "Stockfish 18"
DEFAULT_DEPTH = 15

# Skip the opening: book moves carry little tactical information and would
# dominate the base rates.
FIRST_PLY = 8


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-dir", required=True, type=Path)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--engine", default=DEFAULT_ENGINE)
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    parser.add_argument("--sample", type=int, default=24)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    games = parse_pgn_dir(args.games_dir)
    cache = EvalCache(args.cache)

    positions = 0
    with_best = 0
    tally: Counter[str] = Counter()
    hits: list[tuple[str, str, str, str]] = []  # game, fen, move san, motif

    for game in games:
        board = chess.Board()
        for index, uci in enumerate(game.moves):
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                break

            if index >= FIRST_PLY:
                positions += 1
                cached = cache.get(board.fen(), args.engine, args.depth)
                best = _legal_best(board, cached.best_move if cached else None)
                if best is not None:
                    with_best += 1
                    for motif in detect_motifs(board, best):
                        tally[motif] += 1
                        hits.append((game.game_id, board.fen(), board.san(best), motif))

            board.push(move)

    summary = {
        "games": len(games),
        "positions_after_opening": positions,
        "positions_with_a_cached_best_move": with_best,
        "per_motif": {
            motif: {
                "fired": tally.get(motif, 0),
                "pct_of_positions": round(100 * tally.get(motif, 0) / max(1, with_best), 2),
            }
            for motif in sorted(Motif)
        },
    }
    (args.out / "counts.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    _write_sample(hits, args.out / "review_sample.md", args.sample)
    print(f"\nReview sample -> {args.out / 'review_sample.md'}")
    return 0


def _legal_best(board: chess.Board, uci: str | None) -> chess.Move | None:
    if not uci:
        return None
    move = chess.Move.from_uci(uci)
    return move if move in board.legal_moves else None


def _write_sample(hits, path: Path, size: int) -> None:
    """A stratified sample: every motif gets reviewed, not only the common ones."""
    rng = random.Random(SEED)
    by_motif: dict[str, list] = {}
    for hit in hits:
        by_motif.setdefault(hit[3], []).append(hit)

    per_motif = max(1, size // max(1, len(by_motif)))
    lines = ["# E04 motif review sample", ""]

    for motif in sorted(by_motif):
        pool = by_motif[motif]
        picked = rng.sample(pool, min(per_motif, len(pool)))
        lines.append(f"## {motif} — {len(pool)} firings, showing {len(picked)}")
        lines.append("")
        for game_id, fen, san, _ in picked:
            lines.append(f"### `{game_id}` — best move **{san}**")
            lines.append(f"- FEN: `{fen}`")
            lines.append("```")
            lines.append(str(chess.Board(fen)))
            lines.append("```")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
