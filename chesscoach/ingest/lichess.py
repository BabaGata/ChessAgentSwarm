"""Fetching a player's games from Lichess.

Promoted out of `experiments/e01-engine-throughput/fetch_games.py`, which is where
it was written to verify the API parameters (question E1) and where it stayed for
far too long: without it in the product, using the swarm meant running a script
from an experiments directory before you could run the swarm at all.

Public games and public usernames only (R-10). Nothing here stores anything.

The query parameters are the ones E1 confirmed against the live API:
`clocks=true` yields the `%clk` comments S2 depends on, `opening=true` yields the
ECO and Opening tags. `evals=true` is asked for and mostly not answered — Lichess
only holds evaluations for games a user chose to analyse, which for ordinary
amateur games is rare, and that is why this project runs its own engine.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

API = "https://lichess.org/api"

# Lichess asks that clients identify themselves, and asks for a full minute's
# back-off on 429. Both are their documented terms, and a coaching tool that
# hammers a free public API does not deserve one.
USER_AGENT = "ChessAgentSwarm-thesis-research (educational; contact via github)"
RATE_LIMIT_BACKOFF_S = 60
MAX_RETRIES = 3
REQUEST_TIMEOUT_S = 120

# Between arena standings pages while discovering players. Not a rate-limit
# response -- a courtesy, since discovery walks many tournaments in a row.
TOURNAMENT_PAUSE_S = 1.0

# What the swarm diagnoses on.
#
# Blitz was excluded until E19, on the grounds that error rates are not
# comparable across time controls (E01, `domain.signals`). That reasoning was
# right about **comparison** and was being used to justify **discarding**, which
# cost a median 82 % of a player's games.
#
# E19 measured the difference: blitz predicts a player's rapid behaviour as well
# as rapid predicts itself -- 93 % of the reliability ceiling -- so the evidence
# is about the same player. It is now pooled, while the *baseline* stays
# per-speed and is rebuilt for each player's own mix (`SectionContext._mixed`),
# so E01's rule is kept rather than overruled. On a 24-game history this took the
# swarm from advising 50 % of players to **79 %**, with overlap unchanged.
#
# **Bullet is still excluded, and deliberately.** E19 tested blitz and nothing
# faster. Somewhere below blitz "the same player, hurrying" becomes a different
# game, and that boundary is unmeasured -- so it stays where the evidence stops.
DIAGNOSTIC_PERF_TYPES = ("rapid", "classical", "blitz")

PGN_PARAMS = "rated=true&clocks=true&opening=true&division=true"


def _params(perf_types: tuple[str, ...]) -> str:
    return f"perfType={','.join(perf_types)}&{PGN_PARAMS}"


class LichessUnavailable(RuntimeError):
    """The API could not be reached, or refused. Distinct from "no games"."""


def fetch_games_pgn(
    username: str, max_games: int, perf_types: tuple[str, ...] = DIAGNOSTIC_PERF_TYPES
) -> str:
    """A player's most recent rated games at the given speeds, as PGN.

    The default is what the swarm diagnoses on; anything else is a caller
    deliberately asking for a different stratum, never a blend. Mixing speeds
    into one corpus is the thing `DIAGNOSTIC_PERF_TYPES` exists to prevent.

    **`max_games` is a floor, not a ceiling.** Measured against the live API on
    2026-08-14: asking 20 returns 24, asking 25 returns 36, asking 40 returns 48,
    and the same counts come back for every user, so the export rounds up to an
    internal batch rather than counting a player's games. The surplus games are
    **distinct** -- checked by game id, no repeats -- so the only consequence is
    that a corpus is sometimes a little larger than requested, and the counts
    this project quotes are the ones actually analysed. Multiples of 12 come back
    exactly, which is why 24, 60 and 300 never showed it.
    """
    if not perf_types:
        raise ValueError("at least one perf type is required")
    url = f"{API}/games/user/{username}?max={max_games}&{_params(perf_types)}"
    return _get(url, accept="application/x-chess-pgn").decode("utf-8", errors="replace")


def find_candidate_players(
    low: int, high: int, wanted: int
) -> list[tuple[str, int]]:
    """Players inside a rating band, read from finished arena standings.

    Promoted out of `experiments/e01-engine-throughput/` because
    `build-peer-reference` needs a corpus and nothing in the product produced
    one -- so a third party reproducing this from the vault (success criterion 6)
    stopped at the first step. The same complaint that produced `coach`, one
    level further back.

    **Reproducible in shape rather than in content.** The tournaments finishing
    today are not the ones that finished when this project's reference was built,
    so a reader gets a different sample of the same population. That is the
    honest guarantee and the reason population *rates* are what this project
    compares against, never individual players.

    A tournament that cannot be read is skipped rather than fatal: one bad id out
    of several is no reason to return nothing. No tournaments at all **is**
    fatal, because silence would look like "the band is empty" and the caller
    would go on to build a corpus of nobody.
    """
    payload = json.loads(_get(f"{API}/tournament"))
    ids = [
        tour["id"]
        for key in ("finished", "started")
        for tour in payload.get(key, [])
        if tour.get("id")
    ]
    if not ids:
        raise LichessUnavailable("no tournaments returned by /api/tournament")

    found: list[tuple[str, int]] = []
    seen: set[str] = set()
    for tournament in ids:
        if len(found) >= wanted:
            break
        try:
            standings = json.loads(_get(f"{API}/tournament/{tournament}?page=1"))
        except LichessUnavailable:
            continue

        for player in standings.get("standing", {}).get("players", []):
            name, rating = player.get("name"), player.get("rating")
            # Arena regulars appear in many tournaments, and a player counted
            # twice would carry double weight in every population rate.
            if not name or not rating or name.lower() in seen:
                continue
            if low <= rating <= high:
                found.append((name, rating))
                seen.add(name.lower())
                if len(found) >= wanted:
                    break
        time.sleep(TOURNAMENT_PAUSE_S)

    return found


def _get(url: str, accept: str = "application/json") -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": accept}
    )
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_BACKOFF_S)
                continue
            if error.code == 404:
                raise LichessUnavailable(f"no such user: {url}") from error
            raise LichessUnavailable(f"HTTP {error.code} from Lichess") from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise LichessUnavailable(f"could not reach Lichess: {error}") from error
    raise LichessUnavailable(f"gave up after {MAX_RETRIES} attempts: {url}")
