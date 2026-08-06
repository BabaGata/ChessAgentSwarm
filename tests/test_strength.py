"""V1 — estimating playing strength from a player's own games.

Screen and fit: docs/notes/experiments.e13-strength-signal.md

The estimator is one line of arithmetic, so the tests that matter are about the
things around it: that it refuses to speak on too little evidence, that it says
when it is extrapolating, and that the error bar travels with the number.
"""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.strength import (
    FITTED_RANGE,
    INTERCEPT,
    MIN_MOVES,
    SLOPE,
    TYPICAL_ERROR,
    estimate,
)

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def moves(count: int, blunders: int, mover: str = "alice") -> tuple[Observation, ...]:
    return tuple(
        Observation(
            game_id=f"g{index // 20}",
            ply=20 + index,
            mover=mover,
            mover_is_white=True,
            fen_before=FEN,
            move_played="e2e4",
            best_move="d2d4",
            score_cp_before=0,
            score_cp_after=0,
            loss_wp=35.0 if index < blunders else 1.0,
            label=ErrorLabel.BLUNDER if index < blunders else None,
            phase="opening_middlegame",
            played_best=False,
            clock_before=None,
            clock_after=None,
            engine="stub",
            depth=15,
        )
        for index in range(count)
    )


class TestWhenItWillSpeak:
    def test_too_few_moves_is_no_answer_rather_than_a_bad_one(self):
        # One blunder in 80 moves and one in 90 are the same player; the
        # arithmetic would put 250 rating points between them.
        assert estimate(moves(MIN_MOVES - 1, 5), "alice") is None

    def test_enough_moves_produces_an_estimate(self):
        assert estimate(moves(400, 8), "alice") is not None

    def test_only_the_players_own_moves_count(self):
        mixed = moves(400, 8) + moves(400, 200, mover="bob")

        assert estimate(mixed, "alice").moves == 400


class TestTheEstimate:
    def test_fewer_blunders_reads_as_stronger(self):
        careful = estimate(moves(400, 4), "alice")
        loose = estimate(moves(400, 40), "alice")

        assert careful.rating > loose.rating

    def test_it_follows_the_fitted_line(self):
        result = estimate(moves(400, 8), "alice")
        expected = INTERCEPT + SLOPE * (8 / 400)

        assert result.rating == round(expected)

    def test_the_error_travels_with_the_number(self):
        # A bare rating claims a precision the measurement does not have.
        result = estimate(moves(400, 8), "alice")

        assert result.typical_error == TYPICAL_ERROR
        assert result.range == (result.rating - TYPICAL_ERROR, result.rating + TYPICAL_ERROR)

    def test_the_blunder_rate_is_recorded_so_the_number_can_be_rederived(self):
        result = estimate(moves(400, 8), "alice")

        assert result.blunder_rate == pytest.approx(0.02)


class TestExtrapolation:
    def test_a_rate_inside_the_fitted_range_is_not_flagged(self):
        inside = round(sum(FITTED_RANGE) / 2 * 400)

        assert not estimate(moves(400, inside), "alice").extrapolated

    def test_a_player_far_better_than_the_sample_is_flagged(self):
        # A linear fit outside its range is a guess with a decimal point on it.
        assert estimate(moves(400, 1), "alice").extrapolated

    def test_a_player_far_worse_than_the_sample_is_flagged(self):
        assert estimate(moves(400, 120), "alice").extrapolated


class TestTheReportSaysWhatItIs:
    def profile(self, **overrides):
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef, Strength

        strength = Strength(
            **{
                "rating": 1650,
                "typical_error": 103,
                "moves": 400,
                "method": "blunder-rate-ols/e13",
                "extrapolated": False,
                **overrides,
            }
        )
        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
            strength=strength,
        )

    def test_it_reports_a_range_not_a_number(self):
        from chesscoach.explainer import render

        report = render(self.profile())

        assert "About 1650, and most likely between 1547 and 1753" in report

    def test_it_says_the_rating_was_never_shown_to_it(self):
        from chesscoach.explainer import render

        assert "which was never shown to it" in render(self.profile())

    def test_extrapolation_is_admitted(self):
        from chesscoach.explainer import render

        report = render(self.profile(extrapolated=True))

        assert "a direction rather than a figure" in report

    def test_a_profile_without_an_estimate_says_nothing(self):
        from chesscoach.explainer import render
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        bare = PlayerProfile(
            player=PlayerRef(source="lichess", username="alice"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
        )

        assert "HOW STRONG YOUR PLAY LOOKS" not in render(bare)


def test_a_strength_estimate_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef, Strength

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        strength=Strength(1650, 103, 400, "blunder-rate-ols/e13", False),
    )

    assert from_dict(to_dict(profile)).strength == profile.strength
