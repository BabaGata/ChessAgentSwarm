"""The game corpus and its identity.

A finding is only meaningful with respect to the exact set of games that
produced it, so the corpus gets a deterministic id that is recorded in every
finding's provenance. Re-running on the same games reproduces the same id; adding
a game changes it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from chesscoach.ingest.pgn import GameRecord
from chesscoach.profile.models import CorpusRef


@dataclass(frozen=True)
class Corpus:
    """A player and the games being analysed for them."""

    username: str
    corpus_id: str
    game_ids: tuple[str, ...]
    time_controls: tuple[str, ...] = ()
    date_range: tuple[str, str] | None = None

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
        )


def build_corpus(username: str, games: tuple[GameRecord, ...] | list[GameRecord]) -> Corpus:
    """Build a corpus from the player's own games.

    Game order does not affect the id -- the same set of games is the same
    corpus however it was fetched.
    """
    own = [game for game in games if game.involves(username)]
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
    )


def _corpus_id(username: str, game_ids: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    digest.update(username.lower().encode("utf-8"))
    for game_id in game_ids:
        digest.update(b"\x00")
        digest.update(game_id.encode("utf-8"))
    return digest.hexdigest()[:32]
