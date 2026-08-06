"""The game corpus and its identity.

A finding is only meaningful with respect to the exact set of games that
produced it, so the corpus gets a deterministic id that is recorded in every
finding's provenance. Re-running on the same games reproduces the same id; adding
a game changes it.

This is also where games that should never be diagnosed are dropped, and the
reasons counted. Excluding here rather than at parse time keeps the decision
**auditable** -- the profile records how many games were set aside and why, so a
player who brought 24 games and was analysed on 21 can be told that (C5).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from chesscoach.ingest.pgn import GameRecord
from chesscoach.profile.models import CorpusRef

# The player halved their own clock for an extra arena point. Their errors there
# are a self-inflicted time handicap, and S2's whole subject is time pressure --
# so these games do not merely add noise, they bias the signal the swarm is most
# confident about. 8.0% of the measured corpus.
BERSERKED = "berserked"

# Nobody made a chess decision worth diagnosing. 2.2%.
ABANDONED = "abandoned"

_ABANDONED_TERMINATION = "abandoned"


@dataclass(frozen=True)
class Corpus:
    """A player and the games being analysed for them."""

    username: str
    corpus_id: str
    game_ids: tuple[str, ...]
    time_controls: tuple[str, ...] = ()
    date_range: tuple[str, str] | None = None
    # (reason, count) for games set aside, in a stable order.
    excluded: tuple[tuple[str, int], ...] = ()

    @property
    def n_games(self) -> int:
        return len(self.game_ids)

    def to_ref(self) -> CorpusRef:
        return CorpusRef(
            corpus_id=self.corpus_id,
            n_games=self.n_games,
            time_controls=self.time_controls,
            date_range=self.date_range,
            # Recorded so a later progress check knows which games are new.
            game_ids=self.game_ids,
            excluded=self.excluded,
        )


def exclusion_reason(game: GameRecord, username: str) -> str | None:
    """Why this game must not be diagnosed, or None if it is fine.

    One reason per game even when a game fails both tests -- the count is of
    games set aside, not of objections raised.
    """
    if (game.termination or "").strip().lower() == _ABANDONED_TERMINATION:
        return ABANDONED
    if game.berserked_by(username):
        return BERSERKED
    return None


def build_corpus(username: str, games: tuple[GameRecord, ...] | list[GameRecord]) -> Corpus:
    """Build a corpus from the player's own games, minus the undiagnosable ones.

    Game order does not affect the id -- the same set of games is the same
    corpus however it was fetched.
    """
    own = []
    dropped: dict[str, int] = {}
    for game in games:
        if not game.involves(username):
            continue
        reason = exclusion_reason(game, username)
        if reason is None:
            own.append(game)
        else:
            dropped[reason] = dropped.get(reason, 0) + 1

    game_ids = tuple(sorted(game.game_id for game in own))

    time_controls = tuple(sorted({g.time_control for g in own if g.time_control}))
    dates = sorted(g.date for g in own if g.date)
    date_range = (dates[0], dates[-1]) if dates else None

    return Corpus(
        username=username,
        corpus_id=_corpus_id(username, game_ids),
        game_ids=game_ids,
        time_controls=time_controls,
        date_range=date_range,
        excluded=tuple(sorted(dropped.items())),
    )


def _corpus_id(username: str, game_ids: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(username.lower().encode("utf-8"))
    for game_id in game_ids:
        digest.update(b"\x00")
        digest.update(game_id.encode("utf-8"))
    return digest.hexdigest()[:32]
