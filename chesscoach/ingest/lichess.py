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
    """
    if not perf_types:
        raise ValueError("at least one perf type is required")
    url = f"{API}/games/user/{username}?max={max_games}&{_params(perf_types)}"
    return _get(url, accept="application/x-chess-pgn").decode("utf-8", errors="replace")


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
