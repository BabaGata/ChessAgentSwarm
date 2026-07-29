"""Error classification: win-probability conversion and thresholds."""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import (
    BLUNDER_WP,
    CLAMP_CP,
    ErrorLabel,
    classify,
    clamp_cp,
    move_loss_wp,
    win_probability,
)


class TestWinProbability:
    def test_equal_position_is_fifty_percent(self):
        assert win_probability(0) == pytest.approx(50.0)

    def test_is_monotonically_increasing(self):
        values = [win_probability(cp) for cp in (-800, -200, 0, 200, 800)]
        assert values == sorted(values)

    def test_is_symmetric_about_equality(self):
        assert win_probability(300) + win_probability(-300) == pytest.approx(100.0)

    def test_a_pawn_at_equality_matters_more_than_a_pawn_when_winning(self):
        # The whole reason for using win probability rather than centipawns.
        at_equality = win_probability(100) - win_probability(0)
        when_winning = win_probability(1000) - win_probability(900)

        assert at_equality > when_winning * 3


class TestClamp:
    def test_bounds_extreme_evaluations(self):
        assert clamp_cp(30000) == CLAMP_CP
        assert clamp_cp(-30000) == -CLAMP_CP

    def test_leaves_ordinary_evaluations_alone(self):
        assert clamp_cp(250) == 250


class TestClassify:
    @pytest.mark.parametrize(
        "loss,expected",
        [
            (0.0, None),
            (5.0, None),
            (10.0, ErrorLabel.INACCURACY),
            (25.0, ErrorLabel.MISTAKE),
            (60.0, ErrorLabel.BLUNDER),
        ],
    )
    def test_assigns_the_expected_label(self, loss, expected):
        assert classify(loss) is expected

    def test_blunder_threshold_is_inclusive(self):
        assert classify(BLUNDER_WP) is ErrorLabel.BLUNDER


class TestMoveLoss:
    def test_playing_the_engine_move_is_never_an_error(self):
        # Guards the mate-transition bug: Qxf7# would otherwise register a
        # colossal "loss" because mate is encoded as a huge centipawn value.
        loss = move_loss_wp(before_cp=50, after_cp=-CLAMP_CP, mover_is_white=True, played_best=True)

        assert loss == 0.0

    def test_measures_loss_from_the_movers_point_of_view(self):
        white_loss = move_loss_wp(before_cp=0, after_cp=-300, mover_is_white=True, played_best=False)
        black_loss = move_loss_wp(before_cp=0, after_cp=300, mover_is_white=False, played_best=False)

        assert white_loss == pytest.approx(black_loss)
        assert white_loss > 0

    def test_an_improving_position_is_not_a_loss(self):
        loss = move_loss_wp(before_cp=0, after_cp=300, mover_is_white=True, played_best=False)

        assert loss == 0.0
