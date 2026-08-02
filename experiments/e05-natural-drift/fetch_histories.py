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
from fetch_games import fetch_games_pgn, find_candidate_players  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.ingest.pgn import parse_pgn_text  # noqa: E402

# Lichess asks for restraint; the fetcher already backs off on 429.
PAUSE_BETWEEN_PLAYERS_S = 2.0

# A history is only useful if the earlier half alone clears the confidence gate,
# which needs 20+ games with data. Below this there is no point analysing it.
MIN_USABLE_GAMES = 40


def collect_players(args) -> list[str]:
    """Players we already have, plus more discovered from recent arenas."""
    known = [path.stem for path in sorted(args.players_dir.glob("*.pgn"))] if args.players_dir else []
    if not args.discover:
        return known

    seen = {name.lower() for name in known}
    print(f"discovering players rated {args.band[0]}-{args.band[1]}...", flush=True)
    found = find_candidate_players(args.band[0], args.band[1], args.discover)
    fresh = [name for name, _ in found if name.lower() not in seen]
    print(f"  {len(known)} known, {len(fresh)} new\n", flush=True)
    return known + fresh


def already_deep_enough(path: Path, wanted: int) -> bool:
    """A shallow history from an earlier run is refetched rather than kept."""
    if not path.exists():
        return False
    return len(parse_pgn_text(path.read_text(encoding="utf-8"))) >= wanted * 0.8


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--players-dir", type=Path, default=None, help="one PGN per player")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--games", type=int, default=150)
    parser.add_argument("--discover", type=int, default=0, help="how many players to look for")
    parser.add_argument("--band", nargs=2, type=int, default=[1400, 1800])
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    players = collect_players(args)
    print(f"{len(players)} players, up to {args.games} games each\n")

    kept = 0
    for index, player in enumerate(players, start=1):
        target = args.out / f"{player}.pgn"
        label = f"  {index:>3}/{len(players)} {player}"

        if already_deep_enough(target, args.games):
            print(f"{label}: already deep enough")
            kept += 1
            continue

        try:
            pgn = fetch_games_pgn(player, args.games)
        except Exception as error:  # noqa: BLE001 - one player must not end the run
            print(f"{label}: FAILED — {error}", flush=True)
            continue

        games = parse_pgn_text(pgn)
        if len(games) < MIN_USABLE_GAMES:
            print(f"{label}: only {len(games)} games, skipped", flush=True)
            time.sleep(PAUSE_BETWEEN_PLAYERS_S)
            continue

        target.write_text(pgn, encoding="utf-8")
        kept += 1
        print(f"{label}: {len(games)} games", flush=True)
        time.sleep(PAUSE_BETWEEN_PLAYERS_S)

    print(f"\nusable histories: {kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
