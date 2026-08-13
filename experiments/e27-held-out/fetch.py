"""E27 — fetch players who played no part in building any of this.

Every threshold, screened claim and constant in the swarm was chosen while
looking at the same 84 players it is then run on: `FOCUS_MARGIN`, the five
band-note claims, the section screens (E09, E11, E14, E25), the strength fits,
the peer reference itself. Leave-one-out removes a player from their *own* peer
rate; it does nothing about the fact that **what to measure** was selected on
this sample.

This project has been caught by in-sample optimism twice — E03's effect reversed
on held-out players (L-008), and E05's constant looked five times better than it
was until it was cross-validated (L-018). The whole pipeline has never been run
on strangers.

Fetched exactly as production would: `fetch_games_pgn` with the shipped
`DIAGNOSTIC_PERF_TYPES`, so rapid, classical and blitz arrive pooled in one file
like a real new user's corpus. Public games and public usernames only (R-10).

Usage:
    python fetch.py --out DIR --exclude DIR [--players 30] [--games 60]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e01-engine-throughput"))

from fetch_games import find_candidate_players  # noqa: E402

from chesscoach.ingest.lichess import LichessUnavailable, fetch_games_pgn  # noqa: E402

PAUSE_S = 1.5

# The corpus needs enough games to be worth diagnosing at all; below this the
# swarm would be silent for reasons that say nothing about generalisation.
MIN_GAMES = 15


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--exclude", type=Path, default=None,
                        help="a directory of PGNs whose players are already used")
    parser.add_argument("--players", type=int, default=30)
    parser.add_argument("--games", type=int, default=60)
    parser.add_argument("--band", nargs=2, type=int, default=[1400, 1800])
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    seen = {p.stem.lower() for p in args.exclude.glob("*.pgn")} if args.exclude else set()
    seen |= {p.stem.lower() for p in args.out.glob("*.pgn")}
    print(f"{len(seen)} usernames already used or fetched\n", flush=True)

    low, high = args.band
    # Ask for more than needed: the band filter and the overlap with the existing
    # corpus both thin the list.
    candidates = find_candidate_players(low, high, args.players * 4)
    fresh = [(name, rating) for name, rating in candidates if name.lower() not in seen]
    print(f"{len(candidates)} candidates in {low}-{high}, {len(fresh)} of them new\n",
          flush=True)

    kept = 0
    for name, rating in fresh:
        if kept >= args.players:
            break
        try:
            pgn = fetch_games_pgn(name, args.games)
        except LichessUnavailable as error:
            print(f"  {name}: {error}", flush=True)
            continue

        games = pgn.count("[Event ")
        if games < MIN_GAMES:
            print(f"  {name}: only {games} games, skipped", flush=True)
            time.sleep(PAUSE_S)
            continue

        (args.out / f"{name}.pgn").write_text(pgn, encoding="utf-8")
        kept += 1
        print(f"  {kept:>3}/{args.players} {name} ({rating}): {games} games", flush=True)
        time.sleep(PAUSE_S)

    print(f"\n{kept} players written to {args.out}")
    return 0 if kept else 1


if __name__ == "__main__":
    raise SystemExit(main())
