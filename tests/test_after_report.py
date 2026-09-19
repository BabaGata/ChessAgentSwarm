"""The session around the report, driven without a terminal.

Design: docs/notes/design.narrated-session.md
"""

from __future__ import annotations

from chesscoach.after_report import SUMMARY_HEADING, ask_questions, practise, summary_lines
from chesscoach.ollama import OllamaUnavailable
from test_explainer import a_finding, a_profile
from test_narrator import REPORT


def replying(text: str):
    def post(_url, _body):
        return {"response": text}
    return post


def failing():
    def post(_url, _body):
        raise OllamaUnavailable("localhost:11434 -> URLError")
    return post


def lines_from(*answers: str):
    queue = list(answers)

    def read(_prompt):
        if not queue:
            raise EOFError
        return queue.pop(0)
    return read


class TestSummary:
    def test_an_accepted_summary_is_labelled_as_the_model_s(self):
        lines = summary_lines(a_profile(a_finding()),
                              transport=replying("You miss pins in 8 of 24 games."))

        assert lines[0] == SUMMARY_HEADING
        assert any("local language model" in line for line in lines)

    def test_a_rejected_one_leaves_a_single_line(self):
        lines = summary_lines(a_profile(a_finding()),
                              transport=replying("You miss pins 99% of the time."))

        assert lines[0].startswith("(no summary:")


class TestQuestions:
    def test_it_answers_until_an_empty_line(self):
        said = []
        asked = ask_questions(REPORT, lines_from("How often do I miss pins?", ""), said.append,
                              transport=replying("30% of the time, against 12%."))

        assert asked == 1
        assert any("30%" in line for line in said)

    def test_end_of_input_ends_it(self):
        assert ask_questions(REPORT, lines_from(), print, transport=replying("x")) == 0

    def test_a_stopped_model_ends_the_questions(self):
        said = []
        asked = ask_questions(REPORT, lines_from("a", "b"), said.append, transport=failing())

        assert asked == 1
        assert any("not running" in line for line in said)


class TestPractice:
    def test_declining_changes_nothing(self):
        profile = a_profile(a_finding())

        assert practise(profile, lines_from("n"), lambda _l: None) == profile

    def test_an_attempt_is_checked_and_recorded(self):
        said = []
        profile = practise(a_profile(a_finding()), lines_from("y", "Bb5"), said.append)

        assert profile.probes[0].move_correct is True
        assert any("Yes." in line for line in said)
