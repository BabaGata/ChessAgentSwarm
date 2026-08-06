"""Fetch the blitz games the swarm has never looked at.

The same players as the rapid histories, so the screen compares a player against
themselves rather than against a different population. Public games and public
usernames only (R-10); nothing here stores anything beyond the PGN.

Polite by construction: one request per player, sequential, with the module's own
back-off on 429.

Usage:
    python fetch_blitz.py --players DIR --out DIR [--games 40]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.ingest.lichess import LichessUnavailable, fetch_games_pgn  # noqa: E402

# A courtesy pause on top of the API's own limits -- this is a free public
# service and a thesis has no claim on it.
PAUSE_S = 1.5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", required=True, type=Path,
                        help="directory of rapid PGNs, one per player")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--games", type=int, default=40)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    names = [p.stem for p in sorted(args.players.glob("*.pgn"))]
    print(f"{len(names)} players, up to {args.games} blitz games each\n", flush=True)

    fetched = skipped = failed = 0
    for index, name in enumerate(names, start=1):
        target = args.out / f"{name}.pgn"
        if target.exists():
            skipped += 1
            continue
        try:
            pgn = fetch_games_pgn(name, args.games, perf_types=("blitz",))
        except LichessUnavailable as error:
            print(f"  {index:>3}/{len(names)} {name}: {error}", flush=True)
            failed += 1
            continue

        target.write_text(pgn, encoding="utf-8")
        games = pgn.count("[Event ")
        fetched += 1
        print(f"  {index:>3}/{len(names)} {name}: {games} games", flush=True)
        time.sleep(PAUSE_S)

    print(f"\nfetched {fetched}, already present {skipped}, failed {failed}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
