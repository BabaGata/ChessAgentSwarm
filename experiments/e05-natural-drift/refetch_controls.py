"""Re-fetch the histories of the exact players E05 measured.

E05's PGN histories are no longer on disk, so the 92 % headline cannot be
broken down by rating change — the question being whether the players who met
their targets are the ones whose rating rose. `fetch_histories.py` discovers
*new* players in the band; this fetches the *same* ones, by name, out of
`results.json`.

The game-export endpoint rate-limits by IP and answers 429 to a whole burst;
waiting the documented minute clears it, and the fetcher does that. (curl
reported the same refusal as a 404 page, which cost an afternoon.) A personal
access token raises the limit if it keeps recurring; no scope is needed for
public games: https://lichess.org/account/oauth/token.

Usage:
    python refetch_controls.py --results results/results.json \\
        --out ../../data/raw/e05-refetch

Then, to answer the question the thesis leaves open:

    python ../e06-progress-power/power.py --results results/results.json \\
        --histories ../../data/raw/e05-refetch --ratio 0.34

0.34 is the constant that produced the 92 %. Running it at the current constant
as well shows whether the split by rating change depends on the target rule.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

EXPORT = "https://lichess.org/api/games/user/{name}"
# Same selection as e01 fetch_games.py, which built the E05 histories: rapid
# and classical together. Rapid alone drops games a player had in classical and
# so shifts the window (levit79 fell from 60 games to 18).
QUERY = ("max={games}&perfType=rapid,classical&rated=true&clocks=false"
         "&evals=false&opening=true")

# E05's results were committed on 2026-08-01, and its histories were the newest
# 60 rapid games at that moment. The API returns newest first, so without an
# upper bound a re-fetch today measures a later period than the experiment did.
E05_UNTIL = "2026-08-01"
PAUSE_S = 3.0  # Lichess asks for restraint; the export endpoint is the costly one
BACKOFF_S = 65.0  # their documented answer to a 429 is to wait a full minute
ATTEMPTS = 4


def end_of_day_ms(day: str) -> int:
    """Epoch milliseconds for the last moment of `day`, UTC."""
    from datetime import datetime, timedelta, timezone
    start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int((start + timedelta(days=1)).timestamp() * 1000) - 1


def fetch(name: str, games: int, token: str | None,
          until: str | None = None) -> str:
    """One player's games, waiting out a rate limit rather than giving up.

    The export endpoint answers 429 for a whole IP, not per user, so a burst
    fails every request in it. Retrying immediately makes that worse; waiting
    the documented minute is the only thing that works.
    """
    url = EXPORT.format(name=name) + "?" + QUERY.format(games=games)
    if until:
        url += f"&until={end_of_day_ms(until)}"
    for attempt in range(1, ATTEMPTS + 1):
        request = urllib.request.Request(
            url, headers={"Accept": "application/x-chess-pgn"})
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == ATTEMPTS:
                raise
            print(f'      429, čekam {BACKOFF_S:.0f} s '
                  f'(pokušaj {attempt}/{ATTEMPTS})', flush=True)
            time.sleep(BACKOFF_S)
    raise RuntimeError('unreachable')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path,
                        help="E05 results.json, for the player names")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--games", type=int, default=60,
                        help="E05 used the newest 60 rapid games")
    parser.add_argument("--until", default=E05_UNTIL,
                        help="last day of games to include, YYYY-MM-DD")
    parser.add_argument("--token", default=None,
                        help="Lichess personal access token, if anonymous "
                             "export is refused")
    args = parser.parse_args()

    names = [entry["player"] for entry in
             json.loads(args.results.read_text(encoding="utf-8"))["per_player"]]
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{len(names)} igrača iz {args.results}, partije do {args.until}")

    fetched, skipped, failed = 0, 0, []
    for index, name in enumerate(names, start=1):
        target = args.out / f"{name}.pgn"
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue
        try:
            pgn = fetch(name, args.games, args.token, args.until)
        except urllib.error.HTTPError as error:
            failed.append(f"{name}: HTTP {error.code}")
            print(f"  [{index}/{len(names)}] {name}: HTTP {error.code}")
            time.sleep(PAUSE_S)
            continue
        except urllib.error.URLError as error:
            failed.append(f"{name}: {error.reason}")
            print(f"  [{index}/{len(names)}] {name}: {error.reason}")
            time.sleep(PAUSE_S)
            continue

        target.write_text(pgn, encoding="utf-8")
        fetched += 1
        print(f"  [{index}/{len(names)}] {name}: "
              f"{pgn.count('[Event ')} partija")
        time.sleep(PAUSE_S)

    print(f"\npreuzeto {fetched}, preskočeno {skipped}, neuspjelo "
          f"{len(failed)}")
    for line in failed:
        print(f"  {line}")
    if fetched == 0 and failed and all("404" in line for line in failed):
        print("\nSvi zahtjevi vraćaju 404. Ostale putanje API-ja rade, pa je "
              "riječ o izvozu partija:\nprobaj s --token.")
    return 1 if fetched == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
