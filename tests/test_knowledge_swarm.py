"""Drafting a knowledge-base entry, and the things the swarm may not do.

Design: docs/notes/design.knowledge-base.md (Option C)

The guarantees under test are what make Option C safe under R-03:

- the **definition is a retrieved sentence chosen by index**, never model prose;
- `why` and `practice` are **grounded** against the kept notes or dropped;
- `not_this` is **never written** by the swarm;
- nothing drafted is ever `reviewed`.
"""

from __future__ import annotations

import json

import pytest

from chesscoach.knowledge_swarm import (
    KnowledgeCompiler,
    KnowledgeScout,
    KnowledgeSwarm,
    topic_for,
)
from chesscoach.opening_agent import SearchUnavailable
from chesscoach.knowledge import Source

# Two real-looking sentences from a page, and one that defines the thing.
NOTES = (
    "A fork is a move that attacks two or more enemy pieces at the same time.",
    "The knight is the most common forking piece because of its unusual move.",
    "Because the opponent can only save one piece, a fork usually wins material.",
)


class FakeTransport:
    """Returns whatever the model is supposed to have said."""

    def __init__(self, payload) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def __call__(self, url, body, timeout=None):  # pragma: no cover - shape only
        self.prompts.append(body.get("prompt", ""))
        return {"response": self.payload}


def compiler(payload: dict) -> KnowledgeCompiler:
    return KnowledgeCompiler(transport=FakeTransport(json.dumps(payload)))


def sources() -> tuple[Source, ...]:
    return (Source(url="https://en.wikibooks.org/wiki/Chess", publisher="Wikibooks"),)


class TestTheDefinitionIsNotWritten:
    def test_the_definition_is_a_retrieved_sentence_chosen_by_index(self):
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == NOTES[0]
        assert entry.quote == NOTES[0]

    def test_a_different_index_selects_a_different_sentence(self):
        entry = compiler({"definition": 2, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == NOTES[2]

    def test_an_index_outside_the_list_is_dropped_rather_than_clamped(self):
        # An impossible index is a hallucination, not a near miss. Clamping it
        # to the nearest sentence would silently pick one nobody chose.
        entry = compiler({"definition": 99, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == ""

    def test_prose_in_the_definition_field_yields_nothing(self):
        # The one field the detector review is compared against must be the
        # source's own words or empty -- never the model's.
        entry = compiler(
            {"definition": "a fork attacks two pieces", "why": "", "practice": []}
        ).compile("fork", NOTES, sources())
        assert entry.definition == ""


class TestGrounding:
    def test_an_ungrounded_why_is_dropped(self):
        entry = compiler({
            "definition": 0,
            "why": "Forks are the cornerstone of Najdorf theory and endgame zugzwang.",
            "practice": [],
        }).compile("fork", NOTES, sources())
        assert entry.why == ""

    def test_a_grounded_why_is_kept(self):
        entry = compiler({
            "definition": 0,
            "why": "A fork usually wins material because the opponent can save only one piece.",
            "practice": [],
        }).compile("fork", NOTES, sources())
        assert entry.why

    def test_invented_practice_advice_is_dropped(self):
        # capacity.knowledge records that training-method evidence is thin and
        # coaching's value contested, so unsupported practice advice is exactly
        # the unfalsifiable coaching CLAUDE.md forbids.
        entry = compiler({
            "definition": 0, "why": "",
            "practice": ["Solve twenty puzzles every morning on a tactics trainer."],
        }).compile("fork", NOTES, sources())
        assert entry.practice == ()


class TestWhatTheSwarmMayNotDo:
    def test_it_never_writes_what_the_thing_is_not(self):
        # The web's definition of a fork is the vague one, and the vague one is
        # what the broken detector implemented. That field is the author's.
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.not_this == ()

    def test_nothing_drafted_is_ever_reviewed(self):
        entry = compiler({"definition": 0, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.reviewed is False

    def test_no_notes_means_no_entry_and_no_model_call(self):
        transport = FakeTransport(json.dumps({"definition": 0}))
        entry = KnowledgeCompiler(transport=transport).compile("fork", (), ())
        assert entry.definition == ""
        assert transport.prompts == []  # the model was never asked


class TestTheScout:
    def test_it_asks_three_questions_about_the_claim(self):
        asked = []

        class Searcher:
            name = "fake"

            def search(self, gap):
                asked.append(gap.query)
                return [("t", "https://example.org/a", "Example")]

        found = KnowledgeScout(Searcher()).find("fork")
        assert len(asked) == 3
        assert any("what is" in q for q in asked)
        assert all("fork tactic in chess" in q for q in asked)
        assert len(found) == 1  # the same URL three times is one candidate

    def test_every_query_failing_raises_rather_than_reporting_nothing(self):
        # L-046: "we could not ask" must never read as "nothing was found".
        class Broken:
            name = "broken"

            def search(self, gap):
                raise SearchUnavailable("blocked")

        with pytest.raises(SearchUnavailable):
            KnowledgeScout(Broken()).find("fork")


class TestTopics:
    def test_a_camel_case_motif_gets_a_readable_topic(self):
        assert topic_for("hangingPawn") == "hanging pawn in chess"

    def test_an_unlisted_key_still_gets_a_searchable_phrase(self):
        assert topic_for("some_new_claim") == "some new claim in chess"


class TestEndToEnd:
    def test_it_drafts_an_unreviewed_entry_from_a_page(self):
        # The Assessor refuses a page under MIN_PAGE_WORDS (120), so the fixture
        # has to be a real page's worth of text rather than three sentences.
        page = " ".join(NOTES * 12)

        class Searcher:
            name = "fake"

            def search(self, gap):
                return [("Forks", "https://example.org/forks", "Example")]

        answers = [
            json.dumps({"keep": [0, 1, 2]}),          # assessor
            json.dumps({"definition": 0, "why": "", "practice": []}),  # compiler
        ]

        class Transport:
            def __call__(self, url, body, timeout=None):
                return {"response": answers.pop(0) if answers else "{}"}

        swarm = KnowledgeSwarm(Searcher(), lambda url: page, transport=Transport())
        entry = swarm.draft("fork")
        assert entry.key == "fork"
        assert entry.reviewed is False
        assert entry.sources and entry.sources[0].publisher == "Example"


class TestItCanSayNoneOfThese:
    """Choosing by index guarantees provenance, not relevance.

    The first live run produced a "definition" of castling that read *"There are
    two possible moves that place a pawn in the centre of the board"* -- a real
    sentence from a real page, about something else. Without a way to refuse,
    the model has to return the least-bad sentence, and a plausible wrong answer
    where "nothing found" was the truth is the worst outcome available.
    """

    def test_minus_one_means_no_definition_was_found(self):
        entry = compiler({"definition": -1, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        )
        assert entry.definition == ""
        assert entry.complete is False

    def test_an_entry_that_found_no_definition_cannot_be_endorsed(self):
        from chesscoach.knowledge import KnowledgeBase, NotEndorsed

        kb = KnowledgeBase()
        kb.draft(compiler({"definition": -1, "why": "", "practice": []}).compile(
            "fork", NOTES, sources()
        ))
        with pytest.raises(NotEndorsed):
            kb.endorse("fork")

    def test_the_prompt_tells_the_model_that_refusing_is_normal(self):
        transport = FakeTransport(json.dumps({"definition": -1, "why": "", "practice": []}))
        KnowledgeCompiler(transport=transport).compile("fork", NOTES, sources())
        assert "-1" in transport.prompts[0]
