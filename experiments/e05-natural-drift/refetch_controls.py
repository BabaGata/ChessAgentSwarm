"""Re-fetch the histories of the exact players E05 measured.

E05's PGN histories are no longer on disk, so the 92 % headline cannot be
broken down by rating change — the question being whether the players who met
their targets are the ones whose rating rose. `fetch_histories.py` discovers
*new* players in the band; this fetches the *same* ones, by name, out of
`results.json`.

Lichess's game-export endpoint refuses anonymous requests from some networks
(other endpoints answer, that one returns 404), so pass a personal access token
if the plain run fails. Any token works; no scope is needed for public games.
Create one at https://lichess.org/account/oauth/token.

Usage:
    python refetch_controls.py --results results/results.json --out histories
    python refetch_controls.py ... --token lip_xxxxxxxx

Then, to answer the question the thesis leaves open:

    python ../e06-progress-power/power.py \\
        --results results/results.json --histories histories --ratio 0.34

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
QUERY = ("max={games}&perfType=rapid&rated=true&clocks=false"
         "&evals=false&opening=true")
PAUSE_S = 2.0  # Lichess asks for restraint; the export endpoint is the costly one


def fetch(name: str, games: int, token: str | None) -> str:
    request = urllib.request.Request(
        EXPORT.format(name=name) + "?" + QUERY.format(games=games),
        headers={"Accept": "application/x-chess-pgn"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path,
                        help="E05 results.json, for the player names")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--games", type=int, default=150)
    parser.add_argument("--token", default=None,
                        help="Lichess personal access token, if anonymous "
                             "export is refused")
    args = parser.parse_args()

    names = [entry["player"] for entry in
             json.loads(args.results.read_text(encoding="utf-8"))["per_player"]]
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{len(names)} igrača iz {args.results}")

    fetched, skipped, failed = 0, 0, []
    for index, name in enumerate(names, start=1):
        target = args.out / f"{name}.pgn"
        if target.exists() and target.stat().st_size > 0:
            skipped += 1
            continue
        try:
            pgn = fetch(name, args.games, args.token)
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
    if failed and all("404" in line for line in failed):
        print("\nSvi zahtjevi vraćaju 404. Ostale putanje API-ja rade, pa je "
              "riječ o izvozu partija:\nprobaj s --token.")
    return 1 if fetched == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
