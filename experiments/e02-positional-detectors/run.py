"""Run the E02 positional detectors over real games and sample for manual review.

Unit tests prove the detectors match their stated definitions. This script asks
the different question that matters: do they fire *sensibly and at a plausible
rate* on real games from the target band?

Two outputs:
  * counts -- how often each feature appears, per position and per game;
  * a review file -- randomly sampled detections with the board drawn out, so a
    human can check each one and the precision can be stated honestly rather
    than assumed.

Usage:
    python run.py --games-dir DIR --out DIR [--sample 15]
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import chess
import chess.pgn

from detectors import DETECTORS, Feature

# Skip the opening: before this many full moves, structures have not formed and
# every game looks the same. Sample every Nth ply after that so consecutive,
# nearly identical positions do not dominate.
FIRST_MOVE = 12
PLY_STRIDE = 4

SEED = 20260728  # fixed so the review sample is reproducible


def iter_sampled_positions(games_dir: Path):
    """Yield (game_id, ply, board) for sampled positions of every game."""
    for pgn_path in sorted(games_dir.glob("*.pgn")):
        with pgn_path.open(encoding="utf-8") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                game_id = game.headers.get("GameId", game.headers.get("Site", "?"))
                board = game.board()
                for ply, move in enumerate(game.mainline_moves(), start=1):
                    board.push(move)
                    if ply < FIRST_MOVE * 2 or ply % PLY_STRIDE:
                        continue
                    yield game_id, ply, board.copy()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--sample", type=int, default=15)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    detections: Counter[str] = Counter()
    positions_with: Counter[str] = Counter()
    games_with: dict[str, set[str]] = {name: set() for name in DETECTORS}
    all_hits: list[tuple[str, int, str, Feature]] = []
    positions = 0
    games: set[str] = set()

    for game_id, ply, board in iter_sampled_positions(args.games_dir):
        positions += 1
        games.add(game_id)
        for name, detector in DETECTORS.items():
            hits: list[Feature] = []
            for color in (chess.WHITE, chess.BLACK):
                hits.extend(detector(board, color))
            if hits:
                positions_with[name] += 1
                games_with[name].add(game_id)
            detections[name] += len(hits)
            for hit in hits:
                all_hits.append((game_id, ply, board.fen(), hit))

    summary = {
        "positions_sampled": positions,
        "games": len(games),
        "per_feature": {
            name: {
                "detections": detections[name],
                "positions_with": positions_with[name],
                "pct_of_positions": round(100 * positions_with[name] / max(1, positions), 1),
                "games_with": len(games_with[name]),
                "pct_of_games": round(100 * len(games_with[name]) / max(1, len(games)), 1),
            }
            for name in DETECTORS
        },
    }
    (args.out / "counts.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))

    # Stratified review sample: take an equal share from each feature so rare
    # features are still reviewed, rather than being swamped by common ones.
    rng = random.Random(SEED)
    lines: list[str] = ["# E02 review sample", ""]
    per_feature = max(1, args.sample // len(DETECTORS))
    for name in DETECTORS:
        pool = [h for h in all_hits if h[3].name.startswith(name.split("_")[0])] or [
            h for h in all_hits if name.split("_")[0] in h[3].name
        ]
        picked = rng.sample(pool, min(per_feature, len(pool)))
        lines.append(f"## {name} ({len(pool)} detections, showing {len(picked)})")
        lines.append("")
        for game_id, ply, fen, feature in picked:
            board = chess.Board(fen)
            lines.append(f"### {feature}")
            lines.append(f"- game `{game_id}`, ply {ply}, move {ply // 2 + 1}")
            lines.append(f"- FEN: `{fen}`")
            lines.append("```")
            lines.append(str(board))
            lines.append("```")
            lines.append("")

    (args.out / "review_sample.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReview sample -> {args.out / 'review_sample.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
