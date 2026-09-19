"""Questions after the report: from the report, then from the books, else a refusal.

Design: docs/notes/design.narrated-session.md

The model never answers from its own chess knowledge. What is tested is the
routing and the checks, with the model and the book store both faked.
"""

from __future__ import annotations

from chesscoach.followup import NOT_COVERED, REFUSAL, Source, answer_followup
from chesscoach.ollama import OllamaUnavailable
from test_narrator import REPORT


def replying(*texts: str):
    """Answers in turn, so the report step and the book step can differ."""
    queue = list(texts)

    def post(_url, _body):
        return {"response": queue.pop(0) if len(queue) > 1 else queue[0]}
    return post


def failing():
    def post(_url, _body):
        raise OllamaUnavailable("localhost:11434 -> URLError")
    return post


class Books:
    """A stand-in for the graph store with one passage about pins."""

    def __init__(self, hits=None):
        self.hits = hits if hits is not None else [{
            "locator": "book://capablanca#12",
            "author": "Capablanca", "lineage": "Capablanca",
            "text": "A pinned piece cannot move without exposing a more valuable piece.",
            "embedding": [],
        }]

    def search(self, _question, k=3):
        return self.hits[:k]


class TestFromTheReport:
    def test_a_question_the_report_answers_is_answered_from_it(self):
        reply = answer_followup(
            "How often do I miss pins?", REPORT,
            transport=replying("You miss pins 30% of the time, against 12% for your level."))

        assert reply.source is Source.REPORT
        assert "30%" in reply.text

    def test_an_answer_that_invents_a_number_is_not_given(self):
        reply = answer_followup(
            "How often do I miss pins?", REPORT,
            transport=replying("You miss pins 55% of the time."))

        assert reply.source is Source.REFUSED
        assert reply.text == REFUSAL


class TestConceptQuestionsNeverUseTheReport:
    """E90: asked "What is a pin?", the model answered from the report with a wrong
    definition, and it passed the check at 42 % novelty -- the same as a good
    answer. A definition is chess knowledge, so it only ever comes from the books."""

    @staticmethod
    def counting():
        calls = []

        def post(_url, body):
            calls.append(body["prompt"])
            # Built from the report's own words, so the grounding check would pass it.
            return {"response": "A pin is what you miss 30% of the time."}
        return post, calls

    def test_a_what_is_question_skips_the_report(self):
        post, calls = self.counting()
        reply = answer_followup("What is a pin?", REPORT, store=None, transport=post)

        assert calls == []
        assert reply.source is Source.REFUSED

    def test_croatian_is_recognised_too(self):
        post, calls = self.counting()
        answer_followup("Što je vezivanje?", REPORT, store=None, transport=post)

        assert calls == []

    def test_a_question_about_the_player_still_uses_the_report(self):
        reply = answer_followup(
            "What should I practise first?", REPORT,
            transport=replying("Solve pin puzzles for accuracy, not speed."))

        assert reply.source is Source.REPORT


class TestFromTheBooks:
    def test_a_concept_question_goes_to_the_books(self):
        reply = answer_followup(
            "What is a pin?", REPORT, store=Books(),
            transport=replying(NOT_COVERED,
                               "A pinned piece cannot move without exposing a more valuable piece."))

        assert reply.source is Source.BOOKS
        assert "Capablanca" in reply.text

    def test_without_a_book_store_it_refuses_rather_than_guessing(self):
        reply = answer_followup(
            "What is a pin?", REPORT, store=None, transport=replying(NOT_COVERED))

        assert reply.source is Source.REFUSED

    def test_the_books_saying_nothing_is_a_refusal(self):
        reply = answer_followup(
            "Who won the 1972 match?", REPORT, store=Books(hits=[]),
            transport=replying(NOT_COVERED))

        assert reply.source is Source.REFUSED


class TestNoModel:
    def test_a_stopped_backend_is_said(self):
        reply = answer_followup("How often do I miss pins?", REPORT, transport=failing())

        assert reply.source is Source.UNAVAILABLE
