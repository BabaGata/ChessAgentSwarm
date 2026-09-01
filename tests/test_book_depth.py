"""How much of a player's opening happens outside known theory.

Design: docs/notes/design.detectors-name-consequences.md § 1a, and the author's
ruling that made it worth building:

    "It is coaching to tell the player that they don't know the opening"

The measure is **the share of the first `EARLY_PLIES` half-moves spent outside
the book**, not "did they leave before move N". Both were measured
([[experiments.e76-leaving-theory]]) and the threshold version is markedly worse:
split-half **+0.65** at its best setting against **+0.83** for this one, because
thresholding throws away how *far* out of theory the game went.

It is a rate, so it flows through the confidence policy unchanged: instances are
plies out of book, opportunities are games times the cap.
"""

from __future__ import annotations

import pytest

from chesscoach.book_depth import (
    EARLY_PLIES,
    BookDepthNorms,
    moves_per_game,
    out_of_book_moves,
    out_of_book_share,
)


class _Walk:
    def __init__(self, plies_in_book: int, left_by_white=None):
        self.plies_in_book = plies_in_book
        self.left_by_white = left_by_white
        self.opening = None
        self.left_at_ply = plies_in_book + 1


class TestOutOfBookMoves:
    """Counted as the player's OWN moves, because every instance a claim reports
    must be locatable and only the player's own moves can be cited. A first
    version counted the game's plies and was refused by `Measurement` for
    reporting 105 instances with 19 places to point at."""

    def test_a_game_entirely_in_theory_costs_nothing(self):
        assert out_of_book_moves(_Walk(EARLY_PLIES), True) == 0

    def test_deeper_than_the_cap_still_costs_nothing(self):
        # A 20-ply book line is not better than a 10-ply one for this measure;
        # the question is the opening, and the cap is where the opening ends.
        assert out_of_book_moves(_Walk(EARLY_PLIES + 12), True) == 0

    def test_leaving_immediately_costs_every_move_in_the_window(self):
        assert out_of_book_moves(_Walk(0), True) == moves_per_game()
        assert out_of_book_moves(_Walk(0), False) == moves_per_game()

    def test_leaving_halfway_costs_the_remainder(self):
        # White moves on plies 0,2,4,6,8. Leaving after ply 4 leaves 4,6,8 out.
        assert out_of_book_moves(_Walk(4), True) == 3

    def test_white_and_black_are_counted_on_their_own_plies(self):
        # Black moves on 1,3,5,7,9. A book depth of 5 leaves 5,7,9 for Black
        # and 6,8 for White: the same game, a different number each side.
        assert out_of_book_moves(_Walk(5), False) == 3
        assert out_of_book_moves(_Walk(5), True) == 2


class TestOutOfBookShare:
    def test_no_games_is_none_not_zero(self):
        # Zero would read as "never leaves theory", which is the empty case
        # answering exactly like a perfect one (L-046).
        assert out_of_book_share([]) is None

    def test_every_game_in_theory_is_zero(self):
        assert out_of_book_share([(_Walk(EARLY_PLIES), True)] * 5) == 0.0

    def test_every_game_out_immediately_is_one(self):
        assert out_of_book_share([(_Walk(0), True)] * 5) == 1.0

    def test_it_averages_over_games(self):
        # One game fully in book, one fully out.
        assert out_of_book_share(
            [(_Walk(EARLY_PLIES), True), (_Walk(0), True)]) == pytest.approx(0.5)

    def test_a_game_that_never_left_the_book_counts_as_in_theory(self):
        assert out_of_book_share([(_Walk(EARLY_PLIES, left_by_white=None), True)]) == 0.0


class TestNorms:
    def test_a_missing_baseline_is_none_not_a_default(self):
        norms = BookDepthNorms(shares={})

        assert norms.share_for("1400-1800", "rapid") is None

    def test_a_present_baseline_is_returned(self):
        norms = BookDepthNorms(shares={"1400-1800|rapid": 0.47})

        assert norms.share_for("1400-1800", "rapid") == 0.47

    def test_the_key_is_band_and_speed_together(self):
        # A blitz player compared against a rapid baseline is I-03 again.
        norms = BookDepthNorms(shares={"1400-1800|rapid": 0.47,
                                       "1400-1800|blitz": 0.55})

        assert norms.share_for("1400-1800", "blitz") == 0.55
        assert norms.share_for("1400-1800", "classical") is None

    def test_round_trips_through_json(self, tmp_path):
        path = tmp_path / "norms.json"
        BookDepthNorms(
            shares={"1400-1800|rapid": 0.47},
            source="test", players=84, games=3908,
        ).save(path)

        loaded = BookDepthNorms.load(path)

        assert loaded.share_for("1400-1800", "rapid") == 0.47
        assert loaded.players == 84

    def test_loading_a_missing_file_raises_rather_than_returning_empty(self, tmp_path):
        # An empty norms object would silence every claim quietly. The caller
        # decides what to do about a missing file; it must be told.
        with pytest.raises(OSError):
            BookDepthNorms.load(tmp_path / "nothing.json")
