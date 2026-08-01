"""Fetch deeper histories so each player can be split into before and after.

E05 needs two periods per player: enough games in the earlier one for a plan to
clear the confidence gate, and enough in the later one to check it. Lichess
returns newest first, so the split is by date.

Usage:
    python fetch_histories.py --players-dir DIR --out DIR [--games 60]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e01-engine-throughput"))
from fetch_games import fetch_games_pgn  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.ingest.pgn import parse_pgn_text  # noqa: E402

# Lichess asks for restraint; the fetcher already backs off on 429.
PAUSE_BETWEEN_PLAYERS_S = 2.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--players-dir", required=True, type=Path, help="one PGN per player")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--games", type=int, default=60)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    players = [path.stem for path in sorted(args.players_dir.glob("*.pgn"))]
    print(f"{len(players)} players, up to {args.games} games each")

    kept = 0
    for index, player in enumerate(players, start=1):
        target = args.out / f"{player}.pgn"
        if target.exists():
            print(f"  {index:>2}/{len(players)} {player}: already have it")
            kept += 1
            continue

        try:
            pgn = fetch_games_pgn(player, args.games)
        except Exception as error:  # noqa: BLE001 - one player must not end the run
            print(f"  {index:>2}/{len(players)} {player}: FAILED — {error}")
            continue

        games = parse_pgn_text(pgn)
        if len(games) < 20:
            print(f"  {index:>2}/{len(players)} {player}: only {len(games)} games, skipped")
            continue

        target.write_text(pgn, encoding="utf-8")
        kept += 1
        print(f"  {index:>2}/{len(players)} {player}: {len(games)} games")
        time.sleep(PAUSE_BETWEEN_PLAYERS_S)

    print(f"\nusable histories: {kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
