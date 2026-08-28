"""A local model may rephrase what it may not assert.

Design: docs/notes/decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert.md

No model runs in these tests. What must be right is the accept/reject logic and
what happens when the check fails — the HTTP is incidental, so the transport is
injected and the rules are exercised directly.

The property that carries the whole design: **a rejected rewrite leaves the
player exactly where they were**, reading the publisher's own sentences. If that
ever silently produced something worse, the model would be a downgrade wearing
the appearance of an upgrade.
"""

from __future__ import annotations

import pytest

from chesscoach.opening_summary import (
    OllamaSummariser,
    QuoteSummariser,
    SummariserUnavailable,
)

QUOTES = (
    "Black allows White to occupy the center with pawns on e4 and d4, aiming to "
    "undermine it later with well timed pawn breaks.",
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break.",
)


def replying(text: str):
    """A transport that always answers with `text`."""
    def post(_url, _body):
        return {"response": text}
    return post


def failing():
    def post(_url, _body):
        raise SummariserUnavailable("localhost:11434 -> URLError")
    return post


class TestTheFloor:
    def test_the_quote_arm_changes_nothing(self):
        summary = QuoteSummariser().summarise("Pirc Defense", QUOTES)

        assert summary.text == " ".join(QUOTES)
        assert summary.evidence_class == "quoted"


class TestAGoodRewriteIsKept:
    def test_a_grounded_rewrite_is_accepted_and_labelled_composed(self):
        summariser = OllamaSummariser(post=replying(
            "In this opening you let White build the centre with pawns on e4 and "
            "d4, then undermine it later. Complete development first and choose "
            "your pawn break once White has committed."
        ))

        summary = summariser.summarise("Pirc Defense", QUOTES)

        assert summary.accepted is True
        assert summary.evidence_class == "composed"
        assert "e4" in summary.text

    def test_the_evidence_class_never_claims_the_publisher_wrote_it(self):
        # A reader told a model's phrasing is a publisher's has been misled about
        # the one thing that decides how much to trust it.
        summariser = OllamaSummariser(post=replying(
            "Let White take the centre with pawns on e4 and d4 and undermine it "
            "later, after completing development and choosing a pawn break."
        ))

        assert summariser.summarise("Pirc", QUOTES).evidence_class == "composed"


class TestABadRewriteCostsNothing:
    def test_an_invented_square_falls_back_to_the_quotes(self):
        # The real failure, seen in a real run: qwen2.5 wrote "f6" for the
        # Italian Game and the source never mentioned it.
        summariser = OllamaSummariser(post=replying(
            "Black should aim to break with c5 and develop the pieces quickly."
        ))

        summary = summariser.summarise("Pirc Defense", QUOTES)

        assert summary.accepted is False
        assert summary.text == " ".join(QUOTES)
        assert summary.evidence_class == "quoted"
        assert "c5" in summary.rejected_for

    def test_an_empty_response_falls_back_rather_than_shipping_nothing(self):
        # How a reasoning model behaved when its whole token budget went on
        # thinking. Shipping "" would have emptied the section silently.
        summariser = OllamaSummariser(post=replying("   "))

        summary = summariser.summarise("Pirc Defense", QUOTES)

        assert summary.accepted is False
        assert summary.text == " ".join(QUOTES)

    def test_a_model_writing_from_its_training_falls_back(self):
        summariser = OllamaSummariser(post=replying(
            "This hypermodern system rewards prophylaxis, dynamic imbalance, "
            "flexible manoeuvring, rich strategic nuance and patient regrouping."
        ))

        assert summariser.summarise("Pirc Defense", QUOTES).accepted is False


class TestFailuresAreNotRewrites:
    def test_an_unreachable_model_raises_rather_than_falling_back(self):
        # "Ollama is not running" and "the model wrote something ungrounded"
        # need different actions, so they must not look identical (L-046).
        summariser = OllamaSummariser(post=failing(), think=None)

        with pytest.raises(SummariserUnavailable):
            summariser.summarise("Pirc Defense", QUOTES)

    def test_a_model_rejecting_the_think_option_is_retried_without_it(self):
        calls: list[dict] = []

        def post(_url, body):
            calls.append(body)
            if "think" in body:
                raise SummariserUnavailable("HTTP 400")
            return {"response": "Let White build the centre on e4 and d4, then "
                                "undermine it after completing development."}

        summary = OllamaSummariser(post=post, think=False).summarise("Pirc", QUOTES)

        assert len(calls) == 2
        assert summary.accepted is True

    def test_nothing_to_rephrase_is_not_a_question_for_the_model(self):
        # Asking a model to describe an opening with no source material is
        # exactly the request this design refuses.
        asked = []

        def post(_url, body):
            asked.append(body)
            return {"response": "The Pirc is a hypermodern defence."}

        summary = OllamaSummariser(post=post).summarise("Pirc Defense", ())

        assert asked == []
        assert summary.text == ""
