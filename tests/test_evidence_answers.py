"""Questions about the player's own positions are answered from the profile.

Design: docs/notes/design.narrated-session.md

Found by the author on her own session: "Can you tell me from my own games where I
miss pins" was refused, although her profile held four positions for exactly that
finding. It was measured and not planned (half an hour a week buys one priority),
so the report never printed them, and the follow-up model reads only the report.
The positions are data; they need no model to be shown.
"""

from __future__ import annotations

from chesscoach.evidence_answers import from_profile
from chesscoach.followup import Source, answer_followup
from test_explainer import a_finding, a_profile
from test_narrator import REPORT


def profile():
    pins = a_finding(subject="pin")
    forks = a_finding(kind="allowed_motif", subject="fork")
    return a_profile(pins, forks)


def never_called(_url, _body):
    raise AssertionError("the model must not be asked")


class TestWhere:
    def test_where_do_i_miss_pins_lists_the_positions(self):
        reply = from_profile("Can you tell me from my own games where I miss pins?", profile())

        assert reply is not None
        assert "lichess.org/abc123#39" in reply
        assert "move 20" in reply

    def test_croatian_works(self):
        assert from_profile("Gdje propuštam vezivanja?", profile()) is not None

    def test_the_kind_follows_the_verb(self):
        reply = from_profile("Show me where forks punished me", profile())

        assert "fork" in reply.lower()
        assert "pin" not in reply.lower().split("fork")[0]


class TestPractise:
    def test_how_to_practise_gives_the_system_s_own_advice(self):
        reply = from_profile("How to practice pins?", profile())

        assert reply is not None
        assert "pin" in reply.lower()


class TestNotThisRoute:
    def test_a_pattern_the_profile_does_not_have_falls_through(self):
        assert from_profile("Where do I miss skewers?", profile()) is None

    def test_a_question_without_a_pattern_falls_through(self):
        assert from_profile("What should I practise first?", profile()) is None


class TestInTheSession:
    def test_the_profile_answers_before_the_model_is_asked(self):
        reply = answer_followup("Where do I miss pins?", REPORT, profile=profile(),
                                transport=never_called)

        assert reply.source is Source.PROFILE
