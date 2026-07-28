"""Fetch a sample of real games from the Lichess API for experiment E01.

Also serves as the practical verification of open question E1 (the Lichess API
parameter names, which were taken from a third-party documentation mirror).

Player selection: pick a finished arena tournament, read its standings, and take
players whose rating sits in the target band. This avoids hard-coding a username
and keeps the sample reproducible in shape, if not in exact content.

Usage:
    python fetch_games.py --out <dir> [--band 1400 1800] [--games 50]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://lichess.org/api"
UA = "ChessAgentSwarm-thesis-research (educational; contact via github)"

# Lichess asks clients to back off a full minute on HTTP 429.
RATE_LIMIT_BACKOFF_S = 60
MAX_RETRIES = 3


def _get(url: str, accept: str = "application/json") -> bytes:
    """GET with the documented 429 back-off. Raises on anything else."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRIES - 1:
                print(f"  429 received; backing off {RATE_LIMIT_BACKOFF_S}s", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_S)
                continue
            raise
    raise RuntimeError(f"exhausted retries for {url}")


def find_candidate_players(low: int, high: int, wanted: int) -> list[tuple[str, int]]:
    """Read finished arena standings and return (username, rating) inside the band."""
    tournaments = json.loads(_get(f"{API}/tournament"))
    finished = tournaments.get("finished", []) + tournaments.get("started", [])
    if not finished:
        raise RuntimeError("no tournaments returned by /api/tournament")

    found: list[tuple[str, int]] = []
    for tour in finished:
        if len(found) >= wanted:
            break
        tid = tour["id"]
        try:
            standings = json.loads(_get(f"{API}/tournament/{tid}?page=1"))
        except urllib.error.HTTPError as exc:
            print(f"  skipping tournament {tid}: HTTP {exc.code}", flush=True)
            continue
        for player in standings.get("standing", {}).get("players", []):
            rating = player.get("rating")
            name = player.get("name")
            if rating and name and low <= rating <= high:
                found.append((name, rating))
                if len(found) >= wanted:
                    break
        time.sleep(1)  # be polite between tournament calls
    return found


def fetch_games_pgn(username: str, max_games: int) -> str:
    """Export a user's games as PGN with clocks, openings and phase divisions.

    The query parameters here are exactly open question E1: if the response
    carries %clk comments, an Opening tag and division data, the parameter names
    from the third-party mirror are confirmed against the live API.
    """
    params = (
        f"max={max_games}"
        "&perfType=rapid,classical"
        "&rated=true"
        "&clocks=true"
        "&opening=true"
        "&division=true"
        "&evals=true"
        "&accuracy=true"
    )
    return _get(f"{API}/games/user/{username}?{params}", accept="application/x-chess-pgn").decode(
        "utf-8", errors="replace"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--band", nargs=2, type=int, default=[1400, 1800])
    parser.add_argument("--games", type=int, default=50)
    parser.add_argument("--players", type=int, default=6)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    low, high = args.band

    print(f"Finding players rated {low}-{high} from recent arenas...", flush=True)
    players = find_candidate_players(low, high, args.players)
    if not players:
        print("No players found in band.", file=sys.stderr)
        return 1
    print(f"  candidates: {players}", flush=True)

    total_games = 0
    manifest: list[dict[str, object]] = []
    for name, rating in players:
        if total_games >= args.games:
            break
        want = min(args.games - total_games, 20)
        print(f"Fetching up to {want} games for {name} ({rating})...", flush=True)
        pgn = fetch_games_pgn(name, want)
        count = pgn.count("[Event ")
        if count == 0:
            print("  no games returned; skipping", flush=True)
            continue
        path = args.out / f"{name}.pgn"
        path.write_text(pgn, encoding="utf-8")
        manifest.append({"player": name, "rating": rating, "games": count, "file": path.name})
        total_games += count
        print(f"  got {count} games -> {path.name}", flush=True)
        time.sleep(2)

    (args.out / "manifest.json").write_text(
        json.dumps({"band": [low, high], "total_games": total_games, "sources": manifest}, indent=2),
        encoding="utf-8",
    )
    print(f"\nTotal games fetched: {total_games}")
    return 0 if total_games else 1


if __name__ == "__main__":
    raise SystemExit(main())
