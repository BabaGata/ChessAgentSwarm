"""What the coach may say when a player asks it a chess question.

Design: docs/notes/design.graph-knowledge-base.md

One line runs through all of it: **the answer says who says a thing, never that
it is so.** *"Capablanca and Staunton describe it this way"* is a claim about the
literature and is checkable against the locators beside it. *"A backward pawn is
one that…"* is a chess claim this project cannot support, and a model's own words
wearing the authority of a knowledge base is exactly what R-03 forbids.

Refusal is a real outcome and is tested as one. E79 measured 5 concepts of 19
with no corroboration at all, and `skewer` is not in these books.
"""

from __future__ import annotations

from chesscoach.answering import REFUSAL, Answer, answer


class FakeStore:
    """A graph that returns what the test says it returns."""

    def __init__(self, hits):
        self._hits = hits

    def search(self, question, k=3):
        return self._hits[:k]


def transport_saying(text):
    def send(url, payload):
        return {"response": text}
    return send


HITS = [
    {"locator": "book://capablanca#12", "text": "A backward pawn cannot be "
     "defended by another pawn.", "author": "José Raúl Capablanca",
     "title": "Chess Fundamentals", "year": "1921", "score": 0.9},
    {"locator": "book://staunton#7", "text": "Such a pawn remains a permanent "
     "object of attack.", "author": "Howard Staunton",
     "title": "The Blue Book", "year": "1848", "score": 0.8},
]


class TestAttribution:
    def test_two_authors_are_both_named(self):
        got = Answer("...", "q", voices=("Capablanca", "Staunton"))

        assert got.attribution == "Capablanca and Staunton describe it this way"

    def test_one_author_is_singular(self):
        got = Answer("...", "q", voices=("Capablanca",))

        assert got.attribution == "Capablanca describes it this way"

    def test_it_never_asserts_the_chess(self):
        got = Answer("...", "q", voices=("Capablanca", "Staunton"))

        said = got.attribution.lower()
        # "is", "means", "correct" would make this project the authority rather
        # than the books it is quoting.
        assert " is " not in said and "means" not in said

    def test_no_voices_is_no_attribution(self):
        assert Answer("...", "q").attribution == ""


class TestCorroboration:
    def test_two_voices_is_corroborated(self):
        assert Answer("...", "q", voices=("a", "b")).corroborated

    def test_one_voice_is_not(self):
        assert not Answer("...", "q", voices=("a",)).corroborated

    def test_a_single_voice_is_flagged_to_the_reader(self):
        # One book is one opinion, however eminent its author, and the reader
        # is told rather than left to count the citations.
        rendered = Answer("Text.", "q", locators=("book://a#1",),
                          voices=("Capablanca",)).rendered()

        assert "one author's view" in rendered

    def test_a_corroborated_answer_is_not_hedged(self):
        rendered = Answer("Text.", "q", locators=("book://a#1",),
                          voices=("Capablanca", "Staunton")).rendered()

        assert "one author's view" not in rendered


class TestAnswering:
    def test_it_answers_from_the_passages_and_cites_them(self):
        got = answer("What is a backward pawn?", FakeStore(HITS),
                     transport=transport_saying(
                         "A pawn that cannot be defended by another pawn."))

        assert got.grounded
        assert got.locators == ("book://capablanca#12", "book://staunton#7")
        assert "Capablanca" in got.attribution and "Staunton" in got.attribution

    def test_nothing_retrieved_is_a_refusal(self):
        got = answer("What is a Sveshnikov?", FakeStore([]),
                     transport=transport_saying("irrelevant"))

        assert not got.grounded
        assert got.text == REFUSAL

    def test_the_models_own_refusal_is_kept(self):
        got = answer("What is a skewer?", FakeStore(HITS),
                     transport=transport_saying(
                         "The books I have do not cover that."))

        assert not got.grounded

    def test_a_refusal_cites_nothing(self):
        # Naming books beside "I cannot answer" implies they were consulted and
        # found wanting on this point, which is more than was established.
        got = answer("What is a skewer?", FakeStore(HITS),
                     transport=transport_saying(
                         "The books I have do not cover that."))

        assert got.locators == ()
        assert "book://" not in got.rendered()

    def test_an_empty_reply_is_a_refusal_not_an_empty_answer(self):
        got = answer("q", FakeStore(HITS), transport=transport_saying("   "))

        assert not got.grounded

    def test_the_same_author_twice_is_one_voice(self):
        hits = [dict(HITS[0]), dict(HITS[0], locator="book://capablanca#40")]

        got = answer("q", FakeStore(hits),
                     transport=transport_saying("An answer."))

        assert got.voices == ("José Raúl Capablanca",)
        assert not got.corroborated

    def test_every_cited_locator_appears_in_the_rendering(self):
        got = answer("q", FakeStore(HITS), transport=transport_saying("An answer."))

        rendered = got.rendered()
        for locator in got.locators:
            assert locator in rendered
