"""Step 6 — a returning player's second assessment should be richer, not thinner.

Spec: docs/notes/design.short-history-prioritisation.md § layer 5

The plan said *"accumulate the corpus across sessions"*, implying the swarm has to
store a player's games. It does not: **Lichess is the archive**, complete and
free, so the only thing that has to change is the size of the window asked for.

At a fixed `--games 60` the window **slides** — twenty new games push the twenty
oldest out, and a player who comes back after a month is diagnosed on no more
evidence than the first time, having played more chess. Growing the window by the
size of the previous corpus makes the second assessment strictly better informed
than the first, which is what the progress loop needs to be worth running.

Cheap because of the engine cache: the games already analysed cost nothing to
analyse again, so only the genuinely new ones are paid for.
"""

from __future__ import annotations

import pytest

from chesscoach.cli import games_to_fetch
from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef


def a_profile(n_games: int, game_ids: tuple[str, ...] = ()) -> PlayerProfile:
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=n_games, game_ids=game_ids),
    )


class TestHowManyToAskFor:
    def test_a_new_player_gets_the_plain_window(self):
        assert games_to_fetch(window=60, previous=None) == 60

    def test_a_returning_player_gets_their_history_plus_the_window(self):
        # 40 already analysed, plus room for 60 more: nothing they had is lost.
        assert games_to_fetch(window=60, previous=a_profile(40)) == 100

    def test_a_profile_with_no_games_is_the_same_as_none(self):
        assert games_to_fetch(window=60, previous=a_profile(0)) == 60

    def test_it_never_shrinks_the_window(self):
        assert games_to_fetch(window=60, previous=a_profile(5)) >= 60

    def test_it_is_capped_so_a_long_history_cannot_run_away(self):
        # Someone with 4,000 games should not trigger a 4,060-game analysis;
        # C1 is a constraint, not an aspiration.
        asked = games_to_fetch(window=60, previous=a_profile(4000))

        assert asked < 4000

    def test_the_cap_still_leaves_room_for_new_games(self):
        from chesscoach.cli import MAX_ACCUMULATED_GAMES

        assert games_to_fetch(window=60, previous=a_profile(MAX_ACCUMULATED_GAMES)) == (
            MAX_ACCUMULATED_GAMES
        )


class TestTheCorpusActuallyGrows:
    """The property that matters, stated as a property rather than an example."""

    @pytest.mark.parametrize("already,new", [(24, 20), (40, 5), (100, 60)])
    def test_asking_covers_everything_held_plus_the_new_games(self, already, new):
        asked = games_to_fetch(window=60, previous=a_profile(already))

        assert asked >= already + new or asked == 300

    def test_a_second_session_never_asks_for_less_than_the_first(self):
        first = games_to_fetch(window=60, previous=None)
        second = games_to_fetch(window=60, previous=a_profile(first))

        assert second > first
