"""Building the directory of games that a reference population is made from.

`build-peer-reference` reads a directory of `<username>.pgn` files and turns them
into the band rates every finding in this project is judged against. Until now
nothing in the product produced that directory -- it came from
`experiments/e01-engine-throughput/fetch_games.py` -- so a third party following
the vault could not reach step one. That is vision success criterion 6, which was
asserted in the scorecard and not met.

**What a reader reproduces is the procedure, not the sample.** Discovery reads
arena standings, and today's arenas are not the ones this project's reference was
built from. A reader gets a different 80-odd players from the same band, and the
population *rates* should agree; the usernames will not. Stating that is the
difference between a reproducible method and an unreproducible result.

Public games and public usernames only (R-10). Nothing here is stored beyond the
PGN files the caller asked for.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from chesscoach.ingest.lichess import (
    DIAGNOSTIC_PERF_TYPES,
    LichessUnavailable,
    fetch_games_pgn,
    find_candidate_players,
)

# A courtesy pause between players, on top of the API's own limits.
PAUSE_S = 1.5

# Below this a player contributes few moves and a very noisy rate, and every
# condition they are thin on widens the band interval for everyone. A reference
# is better without them than with them.
MIN_GAMES = 15

# The band filter, the exclusions and MIN_GAMES each thin the candidate list, so
# asking for exactly the number of players wanted returns fewer nearly always.
CANDIDATE_MULTIPLE = 4


@dataclass(frozen=True)
class Fetched:
    username: str
    rating: int
    n_games: int
    path: Path


def fetch_population(
    out: Path,
    *,
    players: int,
    games: int,
    band: tuple[int, int],
    speed: str | None = None,
    exclude: tuple[Path, ...] = (),
    progress=None,
) -> list[Fetched]:
    """Fetch up to `players` players in `band`, one PGN file each.

    `speed` fetches a single stratum. Give it whenever the directory is destined
    for `build-peer-reference`, because that command **labels** every game in a
    directory with its `--time-control` rather than reading each game's own. A
    mixed directory built as `rapid` files blitz games under rapid, and then a
    blitz-heavy player meets a reference with no blitz stratum: `_mixed` returns
    None for every claim, and the peer comparison and band notes disappear from
    a report that otherwise still renders. Silent, and total.

    `exclude` names directories whose players must not be fetched. That exists so
    a held-out set stays held out: E27's value was entirely that its thirty
    players had touched nothing this project was built on, and a later rebuild of
    the reference could quietly spend them.

    Players already present in `out` are skipped rather than refetched, so the
    command can be re-run to top a corpus up, and usernames are compared
    case-insensitively -- Lichess treats `Alice` and `alice` as one account and
    two files would weight them double.
    """
    out.mkdir(parents=True, exist_ok=True)
    seen = {path.stem.lower() for path in out.glob("*.pgn")}
    for directory in exclude:
        seen |= {path.stem.lower() for path in Path(directory).glob("*.pgn")}

    perf_types = (speed,) if speed else DIAGNOSTIC_PERF_TYPES
    low, high = band
    candidates = find_candidate_players(low, high, players * CANDIDATE_MULTIPLE)
    fresh = [(name, rating) for name, rating in candidates if name.lower() not in seen]
    _say(progress, f"{len(candidates)} candidates in {low}-{high}, {len(fresh)} of them new")

    written: list[Fetched] = []
    for name, rating in fresh:
        if len(written) >= players:
            break
        try:
            pgn = fetch_games_pgn(name, games, perf_types=perf_types)
        except LichessUnavailable as error:
            _say(progress, f"  {name}: {error}")
            continue

        n_games = pgn.count("[Event ")
        if n_games < MIN_GAMES:
            _say(progress, f"  {name}: only {n_games} games, skipped")
            time.sleep(PAUSE_S)
            continue

        path = out / f"{name}.pgn"
        path.write_text(pgn, encoding="utf-8")
        written.append(Fetched(username=name, rating=rating, n_games=n_games, path=path))
        _say(progress, f"  {len(written):>3}/{players} {name} ({rating}): {n_games} games")
        time.sleep(PAUSE_S)

    return written


def _say(progress, line: str) -> None:
    if progress is not None:
        progress(line)
