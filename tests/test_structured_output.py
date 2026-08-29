"""Schema-constrained answers, and the prose fallback behind them.

Design: docs/notes/decisions.0017-constrain-the-answer-with-a-schema.md

Ollama's `format` restricts decoding at the token level, so the failures E51 and
E52 measured become unrepresentable rather than merely discouraged:

  a model answering `NONE` where a list of integers was required;
  a model answering `"3, NONE"` -- half a verdict;
  prose whose digits a number-scraper read as indices ("c5" -> sentence 5).

**The prose parsers stay and are tested here too.** A schema is a request, not a
guarantee: support varies by model and Ollama Cloud has none. A model that
ignores the schema must behave exactly as it did before, so every agent is
exercised on both paths.
"""

from __future__ import annotations

import json

from chesscoach import ollama
from chesscoach.opening_swarm import Assessor, Candidate, Compiler, Scout, _points
from chesscoach.plan_selector import LlmSelector


def answering(text: str):
    def transport(_url, _body):
        return {"response": text}
    return transport


def recording():
    """A transport that keeps the request bodies, to inspect what was sent."""
    sent: list[dict] = []

    def transport(_url, body):
        sent.append(body)
        return {"response": json.dumps({"keep": [0]})}
    return transport, sent


class FakeSearcher:
    name = "fake"

    def __init__(self, default=()) -> None:
        self._default = list(default)
        self.queries: list[str] = []

    def search_detailed(self, gap):
        self.queries.append(gap.query)
        return list(self._default)


PAGE = ("Pirc plans", "https://a.org/pirc", "a.org", "the plans")
ARTICLE = ("<p>" + "Black stays flexible and breaks against the d4 pawn later. " * 30
           + "</p>")


class TestTheSchemaIsActuallySent:
    def test_the_format_field_carries_the_schema(self):
        transport, sent = recording()

        Assessor(transport=transport).read("Pirc", Candidate(*PAGE), ARTICLE)

        assert sent[0]["format"]["type"] == "object"
        assert "keep" in sent[0]["format"]["properties"]

    def test_every_property_is_required(self):
        # An optional field is how a model returns half an answer, which is what
        # a schema is here to prevent.
        schema = ollama.schema_of(a={"type": "string"}, b={"type": "integer"})

        assert schema["required"] == ["a", "b"]

    def test_a_call_without_a_schema_sends_no_format(self):
        sent: list[dict] = []

        def transport(_url, body):
            sent.append(body)
            return {"response": "x"}

        ollama.generate("m", "p", transport=transport)

        assert "format" not in sent[0]


class TestReadingAConstrainedAnswer:
    def test_json_is_parsed(self):
        assert ollama.as_json('{"keep": [1, 2]}') == {"keep": [1, 2]}

    def test_a_fenced_block_is_tolerated(self):
        # A model told to answer in JSON sometimes wraps it in markdown anyway.
        assert ollama.as_json('```json\n{"keep": [1]}\n```') == {"keep": [1]}

    def test_prose_is_not_json_and_says_so(self):
        # None means "not JSON", never "the model said nothing useful" -- the
        # caller falls back rather than treating this as an empty answer.
        assert ollama.as_json("I would keep the third one.") is None

    def test_an_empty_answer_is_not_json(self):
        assert ollama.as_json("   ") is None

    def test_a_bare_list_is_refused_when_an_object_is_expected(self):
        assert ollama.as_json("[1, 2]") is None


class TestBoundsStillApplyAfterTheSchema:
    def test_an_out_of_range_index_is_dropped_not_clamped(self):
        # A schema can require integers; it cannot know how many were offered.
        assert ollama.ints({"keep": [0, 99]}, "keep", 3) == (0,)

    def test_duplicates_are_dropped(self):
        assert ollama.ints({"keep": [1, 1, 2]}, "keep", 5) == (1, 2)

    def test_booleans_are_not_integers(self):
        # `True` is an int in Python and would select sentence one.
        assert ollama.ints({"keep": [True, 2]}, "keep", 5) == (2,)

    def test_a_missing_key_yields_nothing(self):
        assert ollama.ints({"other": [1]}, "keep", 5) == ()

    def test_empty_strings_are_not_answers(self):
        assert ollama.strings({"queries": ["  ", "pirc plans"]}, "queries") == \
            ("pirc plans",)


class TestTheFailuresThatBecameUnrepresentable:
    def test_none_can_no_longer_be_a_selection(self):
        # E52: handed 50 sentences, the model answered NONE on four pages of six.
        # Under the schema the same intent is an empty list, which is a verdict
        # rather than an unparseable word.
        reading = Assessor(transport=answering('{"keep": []}')).read(
            "Pirc", Candidate(*PAGE), ARTICLE
        )

        assert reading.sentences == ()

    def test_a_square_in_prose_can_no_longer_become_an_index(self):
        # E52: "Black should break with c5" selected sentence five.
        selector = LlmSelector(transport=answering('{"keep": [0]}'))
        page = "<p>Black stays flexible and breaks against the d4 pawn later.</p>"

        assert len(selector.select("Pirc", page, limit=3)) == 1

    def test_half_a_verdict_is_no_longer_possible(self):
        # E51 produced the literal answer "3, NONE".
        assert ollama.as_json("3, NONE") is None


class TestTheProseFallbackStillWorks:
    """A model that ignores the schema must behave exactly as it did before."""

    def test_the_assessor_still_reads_bare_indices(self):
        # Two, not one: the page is 30 sentences and CHUNK is 25, so it is asked
        # twice and this stub answers "0" to each. The chunking is the point --
        # a long article is read whole rather than truncated.
        reading = Assessor(transport=answering("0")).read(
            "Pirc", Candidate(*PAGE), ARTICLE
        )

        assert len(reading.sentences) == 2
        assert all(s in " ".join(ARTICLE.split()) for s in reading.sentences)

    def test_the_assessor_still_honours_a_bare_none(self):
        reading = Assessor(transport=answering("NONE")).read(
            "Pirc", Candidate(*PAGE), ARTICLE
        )

        assert reading.sentences == ()

    def test_the_compiler_still_reads_labelled_bullets(self):
        notes = ("Black stays flexible and breaks against the d4 pawn later.",)
        brief = Compiler(transport=answering(
            "PLAN: Break against the d4 pawn once development is done."
        )).compile("Pirc", notes)

        assert len(brief.plans) == 1

    def test_the_compiler_reads_the_schema_when_it_is_honoured(self):
        notes = ("Black stays flexible and breaks against the d4 pawn later.",)
        brief = Compiler(transport=answering(json.dumps({
            "plans": ["Break against the d4 pawn once development is done."],
            "watches": [],
        }))).compile("Pirc", notes)

        assert len(brief.plans) == 1
        assert brief.watches == ()

    def test_points_prefers_the_schema_and_falls_back_to_labels(self):
        assert _points('{"plans": ["a b c d"], "watches": []}') == [("plan", "a b c d")]
        assert _points("PLAN: a b c d") == [("plan", "a b c d")]

    def test_the_scout_still_reads_one_query_per_line(self):
        searcher = FakeSearcher(default=[PAGE])
        Scout(searcher=searcher,
              transport=answering("pirc defense plans")).find("Pirc Defense")

        assert "pirc defense plans" in searcher.queries

    def test_the_scout_reads_the_schema_when_it_is_honoured(self):
        searcher = FakeSearcher(default=[PAGE])
        Scout(searcher=searcher, transport=answering(
            json.dumps({"queries": ["pirc middlegame ideas"]})
        )).find("Pirc Defense")

        assert "pirc middlegame ideas" in searcher.queries

    def test_a_sentence_in_a_schema_field_is_still_not_a_query(self):
        # The shape rules survive the schema: it guarantees a string, not a
        # query, and a model can still write prose into a string field.
        searcher = FakeSearcher(default=[PAGE])
        Scout(searcher=searcher, transport=answering(
            json.dumps({"queries": ["Here is a search you could try:"]})
        )).find("Pirc Defense")

        assert all("Here is" not in q for q in searcher.queries)
