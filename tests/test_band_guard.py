"""build-peer-reference must refuse to file players under a band they are not in.

The sibling of `test_stratum_guard`, and it exists because the lesson from I-03
was recorded and then applied to only one arm of the comparison. A peer lookup is
keyed on `(band, time_control, claim)`. The speed arm has been checked against
the games since the stratum guard was written; **the band arm never was**, so
`--band` could say anything and the reference would be built and used.

What that allows was measured on the review twelve: six of the twelve are outside
1400-1800 (four above, two below) and every one of them was compared against it
anyway. The three strongest players in the corpus -- 1930, 1988, 1988 -- have
**zero** findings between them, which reads as "nothing is unusual about your
play" and means "we compared you against people rated below you".

Ratings are continuous, so purity is the wrong test here: a player at the edge of
a band legitimately drifts across it and should not be refused for that. The
median is what decides, and the tolerance is a named constant because where a
band ends is the author's judgement rather than a measurement.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import BAND_EDGE_TOLERANCE, declared_band_is_wrong


def game(player: str, own: int | None, opponent: int = 1600, as_white: bool = True):
    """One game carrying the two ratings, in the shape GameRecord exposes."""

    class _Game:
        pass

    g = _Game()
    g.white = player if as_white else "someone"
    g.black = "someone" if as_white else player
    g.white_elo = own if as_white else opponent
    g.black_elo = opponent if as_white else own
    return g


class TestBandGuard:
    def test_a_player_inside_the_band_passes(self):
        games = [game("p", 1600) for _ in range(20)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_the_player_who_started_this_is_refused(self):
        # maikel5, median 1930 across 60 games, built and diagnosed against
        # 1400-1800 without anything noticing.
        games = [game("maikel5", 1930) for _ in range(60)]

        problem = declared_band_is_wrong(games, "maikel5", "1400-1800")

        assert problem is not None
        assert "1930" in problem and "1400-1800" in problem

    def test_it_says_which_side_they_are_on(self):
        # "above" and "below" are different problems: one means the comparison
        # flatters the player, the other means it accuses them.
        above = declared_band_is_wrong([game("p", 1988)] * 10, "p", "1400-1800")
        below = declared_band_is_wrong([game("p", 1202)] * 10, "p", "1400-1800")

        assert "above" in above
        assert "below" in below

    def test_the_players_own_rating_is_read_not_the_opponents(self):
        # Playing up does not move a player's band. If the guard read whichever
        # rating came first it would band people by who they happened to meet.
        games = [game("p", 1600, opponent=1990) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_it_reads_the_right_rating_when_the_player_is_black(self):
        games = [game("p", 1930, opponent=1500, as_white=False) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is not None

    def test_a_player_at_the_edge_is_not_refused_for_drifting(self):
        # 1810 against a band ending at 1800 is the boundary doing its job, not a
        # mis-filed player.
        games = [game("p", 1800 + BAND_EDGE_TOLERANCE - 1) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_past_the_tolerance_it_is_refused(self):
        games = [game("p", 1800 + BAND_EDGE_TOLERANCE + 1) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is not None

    def test_the_median_decides_not_a_single_outlier(self):
        # One provisional game at 2400 should not reband a 1600 player.
        games = [game("p", 1600) for _ in range(19)] + [game("p", 2400)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_no_readable_ratings_is_not_an_accusation(self):
        # The same rule the speed guard follows: nothing to check against is not
        # a mismatch, and refusing here would block a legitimate corpus.
        games = [game("p", None) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_games_without_a_rating_abstain_rather_than_vote(self):
        games = [game("p", 1930) for _ in range(10)] + [game("p", None) for _ in range(30)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is not None

    def test_a_player_who_is_not_in_the_game_does_not_decide_it(self):
        # A file named for one player containing another's games is a fetch bug,
        # and banding it by the stranger's rating would hide that.
        games = [game("someone-else", 1930) for _ in range(10)]

        assert declared_band_is_wrong(games, "p", "1400-1800") is None

    def test_the_name_is_matched_case_insensitively(self):
        games = [game("MaiKeL5", 1930) for _ in range(10)]

        assert declared_band_is_wrong(games, "maikel5", "1400-1800") is not None

    @pytest.mark.parametrize("band", ["1400-1800", "1800-2000", "1000-1400"])
    def test_it_works_for_any_band_not_just_the_default(self, band):
        low, high = (int(part) for part in band.split("-"))
        middle = (low + high) // 2

        assert declared_band_is_wrong([game("p", middle)] * 10, "p", band) is None
        assert declared_band_is_wrong([game("p", high + 300)] * 10, "p", band) is not None

    def test_an_unparseable_band_is_refused_rather_than_ignored(self):
        # Returning None here would mean "this player is fine", which is the
        # empty case answering like a populated one (L-046).
        problem = declared_band_is_wrong([game("p", 1600)] * 10, "p", "not-a-band")

        assert problem is not None
        assert "not-a-band" in problem

    def test_the_message_says_what_to_do_about_it(self):
        problem = declared_band_is_wrong([game("p", 1930)] * 10, "p", "1400-1800")

        assert "--band" in problem
