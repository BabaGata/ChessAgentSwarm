"""You score worse in this opening than in your others.

Design: docs/notes/design.detectors-name-consequences.md § 1b, from the author:

    "Early error should be totally reformatted as opening error, meaning player
    knowing less number of an opening moves than peers and losing more often when
    playing some opening then another. Keep track that main openings of the
    players would be played much more often then other openings by the same
    player."

That last sentence is the whole difficulty and most of these tests. A player has
two or three mainstays and a long tail played once or twice -- measured on the
review twelve, a **median of 2 games per opening and 46 % played exactly once**
([[experiments.e73-opening-scores]]). Ranking raw scores across that tail names
the noise every time, because one loss in a one-game opening is a 0 % score.

Two rules keep the tail out: a floor on games before an opening may be compared
at all, and non-overlapping Wilson intervals before a difference is claimed.

The comparison is against **the player's own other openings**, never a
population. Scoring badly in the Caro-Kann relative to 1400-1800 players is a
statement about the Caro-Kann; scoring badly in it relative to everything else
*you* play is a statement about your preparation, and only the second is
actionable.
"""

from __future__ import annotations

import pytest

from chesscoach.opening_scores import MIN_GAMES, score_of, weak_openings


def game(player: str, family: str, result: str, as_white: bool = True):
    class _Game:
        pass

    g = _Game()
    g.white = player if as_white else "opponent"
    g.black = "opponent" if as_white else player
    g.result = result
    g.opening = family
    g.moves = ()
    return g


def played(player: str, family: str, wins: int, draws: int, losses: int, as_white=True):
    return ([game(player, family, "1-0" if as_white else "0-1", as_white)] * wins
            + [game(player, family, "1/2-1/2", as_white)] * draws
            + [game(player, family, "0-1" if as_white else "1-0", as_white)] * losses)


class TestScoreOf:
    def test_a_win_as_white(self):
        assert score_of(game("p", "X", "1-0", as_white=True), "p") == 1.0

    def test_a_win_as_black(self):
        assert score_of(game("p", "X", "0-1", as_white=False), "p") == 1.0

    def test_a_loss_is_scored_from_the_players_side(self):
        assert score_of(game("p", "X", "0-1", as_white=True), "p") == 0.0
        assert score_of(game("p", "X", "1-0", as_white=False), "p") == 0.0

    def test_a_draw_is_a_half(self):
        assert score_of(game("p", "X", "1/2-1/2"), "p") == 0.5

    def test_an_undecided_game_has_no_score(self):
        # "*" is an abandoned or ongoing game. Scoring it zero would count a game
        # nobody lost as a loss.
        assert score_of(game("p", "X", "*"), "p") is None

    def test_a_game_the_player_is_not_in_has_no_score(self):
        assert score_of(game("someone-else", "X", "1-0"), "p") is None


class TestWeakOpenings:
    def test_a_clearly_worse_opening_is_named(self):
        # The shape of the real finding: bernes scores 29 % over 19 Caro-Kann
        # games against 60 % over 39 of everything else.
        games = played("p", "Caro-Kann", wins=2, draws=1, losses=16)
        games += played("p", "Italian", wins=24, draws=0, losses=16)

        found = weak_openings(games, "p")

        assert [w.family for w in found] == ["Caro-Kann"]
        assert found[0].games == 19
        assert found[0].score < found[0].rest_score

    def test_an_opening_below_the_floor_is_not_compared(self):
        # Three losses in three games is a 0 % score whose interval genuinely
        # separates -- and it is exactly the tail the author's caveat excludes.
        games = played("p", "Rare Line", wins=0, draws=0, losses=MIN_GAMES - 1)
        games += played("p", "Italian", wins=30, draws=0, losses=10)

        assert weak_openings(games, "p") == ()

    def test_at_the_floor_it_is_compared(self):
        games = played("p", "Rare Line", wins=0, draws=0, losses=MIN_GAMES)
        games += played("p", "Italian", wins=30, draws=0, losses=10)

        assert [w.family for w in weak_openings(games, "p")] == ["Rare Line"]

    def test_the_rest_of_the_repertoire_must_also_clear_the_floor(self):
        # Comparing 5 games against 2 is not a comparison. Without this the
        # baseline is as noisy as the thing it is judging.
        games = played("p", "Caro-Kann", wins=0, draws=0, losses=6)
        games += played("p", "Italian", wins=2, draws=0, losses=0)

        assert weak_openings(games, "p") == ()

    def test_a_player_with_one_opening_is_not_compared_against_themselves(self):
        games = played("p", "Italian", wins=5, draws=0, losses=15)

        assert weak_openings(games, "p") == ()

    def test_overlapping_intervals_are_not_a_finding(self):
        # 40 % against 55 % over small samples is not a difference anyone can
        # stand behind, and the whole point of Wilson here is to refuse it.
        games = played("p", "Caro-Kann", wins=2, draws=0, losses=3)
        games += played("p", "Italian", wins=3, draws=0, losses=3)

        assert weak_openings(games, "p") == ()

    def test_scoring_better_is_never_returned(self):
        # A strength is not a weakness and must not be reported as one -- the
        # rule s1_tactical_gaps.NOT_ASSERTED states for executed_motif.
        games = played("p", "Italian", wins=18, draws=0, losses=1)
        games += played("p", "French", wins=8, draws=0, losses=32)

        assert [w.family for w in weak_openings(games, "p")] == ["French"]

    def test_draws_are_not_rounded_into_wins_or_losses(self):
        # Wilson needs whole successes and chess scores come in halves, so the
        # scale is doubled. Rounding a draw instead would move a 50 % score.
        all_draws = played("p", "Berlin", wins=0, draws=20, losses=0)
        mixed = played("p", "Italian", wins=10, draws=0, losses=10)

        # Both score 50 %: neither can be worse than the other.
        assert weak_openings(all_draws + mixed, "p") == ()

    def test_undecided_games_do_not_count_toward_the_floor(self):
        games = played("p", "Rare Line", wins=0, draws=0, losses=2)
        games += [game("p", "Rare Line", "*")] * 10
        games += played("p", "Italian", wins=30, draws=0, losses=10)

        assert weak_openings(games, "p") == ()

    def test_the_worst_opening_comes_first(self):
        games = played("p", "Caro-Kann", wins=0, draws=0, losses=12)
        games += played("p", "French", wins=3, draws=0, losses=15)
        games += played("p", "Italian", wins=38, draws=0, losses=2)

        found = weak_openings(games, "p")

        assert len(found) >= 2
        assert found[0].score <= found[1].score

    def test_the_baseline_excludes_the_opening_being_judged(self):
        # If the opening were left in the pool it would drag the baseline toward
        # itself, and a player with one dominant opening could never be told
        # about it.
        games = played("p", "Caro-Kann", wins=0, draws=0, losses=30)
        games += played("p", "Italian", wins=10, draws=0, losses=0)

        found = weak_openings(games, "p")

        assert [w.family for w in found] == ["Caro-Kann"]
        assert found[0].rest_games == 10
        assert found[0].rest_score == pytest.approx(1.0)

    def test_no_games_is_not_a_finding(self):
        assert weak_openings([], "p") == ()

    def test_a_game_with_no_opening_is_skipped_not_grouped_as_none(self):
        blank = game("p", "Italian", "1-0")
        blank.opening = None
        blank.moves = ()
        games = [blank] * 6 + played("p", "Caro-Kann", wins=0, draws=0, losses=6)
        games += played("p", "Italian", wins=18, draws=0, losses=2)

        found = weak_openings(games, "p")

        assert all(w.family is not None for w in found)

    def test_variations_group_into_one_family(self):
        # "Caro-Kann Defense: Advance Variation" and ": Panov Attack" are the
        # same opening to a player choosing what to study.
        games = [game("p", "Caro-Kann Defense: Advance Variation", "0-1")] * 10
        games += [game("p", "Caro-Kann Defense: Panov Attack", "0-1")] * 9
        games += played("p", "Italian", wins=24, draws=0, losses=16)

        found = weak_openings(games, "p")

        assert [w.family for w in found] == ["Caro-Kann Defense"]
        assert found[0].games == 19
