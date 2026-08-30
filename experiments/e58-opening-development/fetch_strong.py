"""Games by players who know the openings, for the expectation to be built from.

Design: docs/notes/design.opening-development-signals.md

The author's correction, after E58 derived its norms from the review corpus:

    "I don't want this to be built by peer reference but by better players who
    usually know the opening. The comparison will later been done with peers for
    how regularly they develop later than expected."

That is a different and better reference. A 1600-rated corpus tells you what
1600s do, and E58 showed it disagreeing with the author's own sense of when the
Ruy Lopez castles. Players who know the opening are the ones whose timing *is*
the opening's timing -- so the expectation comes from them, and peers are asked
only how often a player misses it.

**Source and reproducibility.** Players come from the public rapid leaderboard,
which is a stable public list rather than a band this script chose, so the
selection cannot be tuned toward a wanted answer. The snapshot is written into
the manifest because the leaderboard moves daily. Public usernames and public
rated games only (R-10).

    python experiments/e58-opening-development/fetch_strong.py --players 200 --games 60
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
POLITE_GAP_S = 2

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "corpus-strong"


def _get(url: str, accept: str = "application/json") -> bytes:
    """GET with the documented 429 back-off. Raises on anything else.

    Lifted from `experiments/e01-engine-throughput/fetch_games.py`, which has
    been fetching against this API since M4 -- a second implementation of the
    back-off would be a second thing to get wrong.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRIES - 1:
                print(f"  429 received; backing off {RATE_LIMIT_BACKOFF_S}s", flush=True)
                time.sleep(RATE_LIMIT_BACKOFF_S)
                continue
            raise
    raise RuntimeError(f"exhausted retries for {url}")


def leaderboard(count: int) -> list[tuple[str, int]]:
    """The public rapid leaderboard, strongest first."""
    data = json.loads(_get(f"{API}/player/top/{count}/rapid"))
    return [(u["username"], u["perfs"]["rapid"]["rating"]) for u in data["users"]]


def games_for(username: str, max_games: int) -> str:
    """A player's rated rapid games as PGN.

    No clocks, evals or accuracy: development timing needs the moves and nothing
    else, and asking for the rest would multiply the download for data that goes
    straight in the bin.
    """
    params = (
        f"max={max_games}"
        "&perfType=rapid"
        "&rated=true"
        "&opening=true"
    )
    return _get(
        f"{API}/games/user/{username}?{params}", accept="application/x-chess-pgn"
    ).decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", type=int, default=200)
    parser.add_argument("--games", type=int, default=60)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Reading the top {args.players} rapid players...", flush=True)
    players = leaderboard(args.players)
    if not players:
        print("leaderboard returned nothing", file=sys.stderr)
        return 1
    print(f"  ratings {players[-1][1]}-{players[0][1]}", flush=True)

    manifest: list[dict[str, object]] = []
    total = 0
    for index, (name, rating) in enumerate(players, 1):
        path = args.out / f"{name}.pgn"
        if path.exists():
            # Resumable: a run interrupted at player 140 should not re-download
            # the first 139, and re-running must not double the corpus.
            continue
        try:
            pgn = games_for(name, args.games)
        except urllib.error.HTTPError as exc:
            print(f"  {name}: HTTP {exc.code}, skipped", flush=True)
            continue
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"  {name}: {type(exc).__name__}, skipped", flush=True)
            continue

        count = pgn.count("[Event ")
        if count == 0:
            print(f"  {name}: no games", flush=True)
            continue
        path.write_text(pgn, encoding="utf-8")
        manifest.append({"player": name, "rating": rating, "games": count})
        total += count
        print(f"  [{index}/{len(players)}] {name} ({rating}): {count} games",
              flush=True)
        time.sleep(POLITE_GAP_S)

    (args.out / "manifest.json").write_text(
        json.dumps(
            {
                "source": "lichess rapid leaderboard",
                "fetched_players": len(manifest),
                "total_games": total,
                "rating_range": [players[-1][1], players[0][1]],
                "players": manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{total} games from {len(manifest)} players -> {args.out}")
    return 0 if total else 1


if __name__ == "__main__":
    raise SystemExit(main())
