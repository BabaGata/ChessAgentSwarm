"""The four context questions.

Spec: docs/notes/architecture.interaction.md step 2

Only one answer changes what the swarm decides, and that is the test that
matters: study time sizes the plan. The rest change what the report can honestly
say — which is a smaller job, and the reason a context field is not another
inert feature like the prober was before `coach` wired it through.
"""

from __future__ import annotations

import pytest

from chesscoach.arbiter import MAX_PRIORITIES
from chesscoach.context import (
    FOCUSED_EFFORT_HOURS,
    QUESTIONS,
    STEADY_EFFORT_HOURS,
    ask,
    from_answers,
    parse_hours,
    priorities_for,
)
from chesscoach.profile.models import PlayerContext


class TestReadingTheHours:
    @pytest.mark.parametrize(
        "answer,expected",
        [
            ("4", 4.0),
            ("  4  ", 4.0),
            ("about 4", 4.0),
            ("4h", 4.0),
            ("4-5", 4.0),
            ("2.5", 2.5),
            ("2,5", 2.5),
            ("0", 0.0),
        ],
    )
    def test_a_number_is_found_in_whatever_was_typed(self, answer, expected):
        assert parse_hours(answer) == expected

    @pytest.mark.parametrize("answer", ["", "   ", "not much", "loads", "?"])
    def test_an_unreadable_answer_gives_up_rather_than_guessing(self, answer):
        # The plan falls back to its default; a session must not fail over a
        # formatting question.
        assert parse_hours(answer) is None

    @pytest.mark.parametrize("answer", ["-3", "500"])
    def test_an_impossible_number_is_refused(self, answer):
        assert parse_hours(answer) is None


class TestSizingThePlan:
    """The whole reason these questions exist."""

    def test_a_busy_player_gets_one_thing(self):
        context = PlayerContext(weekly_study_hours=FOCUSED_EFFORT_HOURS - 0.5)

        assert priorities_for(context) == 1

    def test_a_moderate_week_gets_two(self):
        context = PlayerContext(weekly_study_hours=FOCUSED_EFFORT_HOURS + 0.5)

        assert priorities_for(context) == 2

    def test_a_player_with_real_time_gets_the_full_three(self):
        context = PlayerContext(weekly_study_hours=STEADY_EFFORT_HOURS + 2)

        assert priorities_for(context) == MAX_PRIORITIES

    def test_no_answer_falls_back_to_the_default(self):
        assert priorities_for(PlayerContext()) == MAX_PRIORITIES
        assert priorities_for(None) == MAX_PRIORITIES

    def test_it_never_exceeds_the_arbiters_own_ceiling(self):
        # A player with forty hours a week still gets at most three things,
        # because "list nine weaknesses" is the anti-pattern regardless of their
        # time. The cap is the ceiling; study hours only lower it.
        context = PlayerContext(weekly_study_hours=40)

        assert priorities_for(context) == MAX_PRIORITIES

    def test_even_half_an_hour_a_week_gets_something(self):
        # Diagnosing and then prescribing nothing is the worse failure.
        assert priorities_for(PlayerContext(weekly_study_hours=0.5)) == 1


class TestBuildingTheContext:
    def test_answers_become_a_context(self):
        context = from_answers(
            {
                "goals": "beat my brother",
                "weekly_study_hours": "about 4",
                "already_tried": "puzzle rush",
                "plays_elsewhere": "at my club",
            }
        )

        assert context.goals == "beat my brother"
        assert context.weekly_study_hours == 4.0
        assert context.already_tried == "puzzle rush"
        assert context.plays_elsewhere == "at my club"

    def test_skipping_everything_produces_no_context_at_all(self):
        # Rather than an object full of Nones that reads as "asked and answered".
        assert from_answers({q.field: "" for q in QUESTIONS}) is None

    def test_skipping_some_keeps_the_rest(self):
        context = from_answers({"goals": "have more fun", "weekly_study_hours": ""})

        assert context.goals == "have more fun"
        assert context.weekly_study_hours is None

    def test_answers_are_stored_verbatim(self):
        # Nothing here interprets free text; a model that misread a goal would
        # quietly plan for the wrong person.
        context = from_answers({"goals": "  I want to stop hanging pieces  "})

        assert context.goals == "I want to stop hanging pieces"

    def test_invisible_characters_do_not_reach_the_report(self):
        # A byte-order mark on pasted input printed verbatim as
        # "You want ﻿stop losing to my brother".
        context = from_answers({"goals": "﻿stop losing to my brother"})

        assert context.goals == "stop losing to my brother"

    def test_an_answer_of_only_invisible_characters_counts_as_skipped(self):
        assert from_answers({"goals": "﻿", "weekly_study_hours": "​"}) is None


class TestAsking:
    def test_every_question_is_put(self):
        asked = []
        answers = iter(["a goal", "5", "nothing", "no"])

        ask(reader=lambda _: next(answers), writer=asked.append)

        printed = " ".join(asked)
        for question in QUESTIONS:
            assert question.prompt in printed

    def test_it_says_they_can_be_skipped(self):
        asked = []
        ask(reader=lambda _: "", writer=asked.append)

        assert "skippable" in " ".join(asked)

    def test_skipping_all_of_them_is_allowed(self):
        assert ask(reader=lambda _: "", writer=lambda _: None) is None


class TestTheReportUsesIt:
    def profile(self, context: PlayerContext | None):
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
            context=context,
        )

    def test_it_reads_the_answers_back(self):
        from chesscoach.explainer import render

        report = render(self.profile(PlayerContext(goals="beat my brother")))

        assert "WHAT YOU TOLD ME" in report
        assert "beat my brother" in report

    def test_it_explains_why_the_plan_is_the_size_it_is(self):
        from chesscoach.explainer import render

        report = render(self.profile(PlayerContext(weekly_study_hours=1)))

        assert "one thing in it, not two" in report

    def test_one_hour_is_an_hour(self):
        from chesscoach.explainer import render

        assert "1 hour a week" in render(self.profile(PlayerContext(weekly_study_hours=1)))

    def test_more_than_one_is_hours(self):
        from chesscoach.explainer import render

        assert "2.5 hours a week" in render(self.profile(PlayerContext(weekly_study_hours=2.5)))

    def test_an_invisible_game_becomes_a_stated_limitation(self):
        from chesscoach.explainer import render

        report = render(self.profile(PlayerContext(plays_elsewhere="over the board at my club")))

        section = report.split("WHAT THIS DOES NOT KNOW")[1]
        assert "over the board at my club" in section
        assert "invisible" in section

    def test_a_player_who_answered_nothing_sees_no_such_section(self):
        from chesscoach.explainer import render

        assert "WHAT YOU TOLD ME" not in render(self.profile(None))


def test_context_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

    context = PlayerContext(
        goals="beat my brother",
        weekly_study_hours=2.5,
        already_tried="puzzle rush",
        plays_elsewhere="at my club",
    )
    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        context=context,
    )

    assert from_dict(to_dict(profile)).context == context
