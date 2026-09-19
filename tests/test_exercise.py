"""The prober's move check, used as practice rather than diagnosis.

Design: docs/notes/design.narrated-session.md

The property that matters: an exercise never changes what the system believes
about the player. D10 is open, so the answer is checked and recorded, and the
gap type stays exactly as the sections inferred it.
"""

from __future__ import annotations

from dataclasses import replace

from chesscoach.exercise import check, exercises_for, record
from chesscoach.profile.models import DeterminedBy
from test_explainer import a_finding, a_profile


def a_process_finding():
    """A clock claim: not probeable for diagnosis, but a fine position to practise."""
    return a_finding(kind="time_pressure_error", subject="clock")


class TestChoosingPositions:
    def test_each_planned_finding_gives_one_position(self):
        profile = a_profile(a_finding())

        exercises = exercises_for(profile)

        assert len(exercises) == 1
        assert exercises[0].better_move == "Bb5"
        assert exercises[0].played == "h3"
        assert "lichess.org/abc123#40" in exercises[0].where

    def test_process_claims_qualify_too(self):
        assert exercises_for(a_profile(a_process_finding()))

    def test_no_plan_means_no_exercise(self):
        assert exercises_for(a_profile(a_finding(), with_plan=False)) == ()

    def test_a_position_without_a_better_move_is_skipped(self):
        finding = a_finding()
        bare = replace(finding, evidence=(replace(finding.evidence[0], better_move=None),))

        assert exercises_for(a_profile(bare)) == ()


class TestChecking:
    def test_the_engine_move_is_right(self):
        exercise = exercises_for(a_profile(a_finding()))[0]

        assert check(exercise, "Bb5").correct
        assert check(exercise, " bb5 ").correct

    def test_another_move_is_answered_with_both_moves(self):
        exercise = exercises_for(a_profile(a_finding()))[0]

        result = check(exercise, "Kb1")

        assert not result.correct
        assert "Bb5" in result.feedback and "h3" in result.feedback

    def test_no_answer_shows_the_move(self):
        exercise = exercises_for(a_profile(a_finding()))[0]

        assert "Bb5" in check(exercise, "").feedback


class TestNotation:
    """E92: profiles store moves as UCI (`c8g4`). Shown as UCI, and compared as
    text, a player typing the move the report printed (`Bg4`) would be told it
    was wrong. Moves are shown in SAN and an answer is read on the board."""

    FEN = "r1bq1rk1/ppp1ppbp/2np2p1/8/3PPP2/2N1QN2/PPP3PP/2KR1B1R b - - 0 9"

    def exercise(self):
        finding = a_finding()
        real = replace(finding, evidence=(replace(
            finding.evidence[0], fen=self.FEN, move_played="e7e5", better_move="c8g4"),))
        return exercises_for(a_profile(real))[0]

    def test_it_shows_standard_notation(self):
        exercise = self.exercise()

        assert exercise.better_move == "Bg4"
        assert exercise.played == "e5"

    def test_standard_uci_and_lowercase_answers_are_all_right(self):
        exercise = self.exercise()

        assert check(exercise, "Bg4").correct
        assert check(exercise, "c8g4").correct
        assert check(exercise, "bg4").correct

    def test_the_game_move_is_not_right(self):
        result = check(self.exercise(), "e5")

        assert not result.correct
        assert "e5" in result.feedback and "Bg4" in result.feedback

    def test_nonsense_is_not_right_and_does_not_raise(self):
        assert not check(self.exercise(), "Qxz9").correct


class TestNothingChanges:
    def test_recording_leaves_the_gap_type_alone(self):
        profile = a_profile(a_finding())
        exercise = exercises_for(profile)[0]

        after = record(profile, ((exercise, "Kb1"),))

        assert after.findings == profile.findings
        assert all(f.gap_type.determined_by is DeterminedBy.INFERRED for f in after.findings)
        assert len(after.probes) == 1
        assert after.probes[0].player_move == "Kb1"
        assert after.probes[0].move_correct is False
