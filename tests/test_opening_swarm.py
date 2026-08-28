"""Three agents with three roles, and the boundaries between them.

Design: docs/notes/decisions.0014-three-agents-for-the-opening-brief.md

No model runs here. What these hold is the separation of duties and the failure
behaviour of each role — which is the part that decides whether a swarm of
language models can be trusted with a player-facing brief:

  the Scout may not make the search worse than not asking it;
  the Assessor's silence is not rejection;
  the Compiler may not speak when nothing was approved, and its two halves are
    kept or dropped independently.
"""

from __future__ import annotations

import pytest

from chesscoach import ollama
from chesscoach.opening_swarm import (
    Assessor,
    Brief,
    Candidate,
    Compiler,
    OpeningSwarm,
    Scout,
    _queries,
    _two_parts,
)

NOTES = (
    "Black allows White to occupy the center with pawns on e4 and d4, aiming to "
    "undermine it later with well timed pawn breaks.",
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break.",
)


def answering(*replies: str):
    remaining = list(replies)

    def transport(_url, _body):
        return {"response": remaining.pop(0) if len(remaining) > 1 else remaining[0]}
    return transport


def failing(_url, _body):
    raise ollama.OllamaUnavailable("localhost:11434 -> URLError")


class FakeSearcher:
    name = "fake"

    def __init__(self, by_query=None, default=()) -> None:
        self._by_query = by_query or {}
        self._default = list(default)
        self.queries: list[str] = []

    def search_detailed(self, gap):
        self.queries.append(gap.query)
        return list(self._by_query.get(gap.query, self._default))


PAGE_A = ("Pirc plans", "https://a.org/pirc", "a.org", "the plans explained")
PAGE_B = ("33 openings you should know", "https://b.org/list", "b.org", "a list")


class TestTheScoutCastsAWideNet:
    def test_its_queries_are_run_as_well_as_the_defaults(self):
        searcher = FakeSearcher(default=[PAGE_A])
        scout = Scout(searcher=searcher, transport=answering("pirc defense plans"))

        scout.find("Pirc Defense")

        assert len(searcher.queries) == 3
        assert "pirc defense plans" in searcher.queries

    def test_one_default_query_asks_about_the_opponent(self):
        # The brief has a WATCH half, so the search needs an angle that can
        # supply it. Without this, 0 of 6 WATCH halves survived.
        searcher = FakeSearcher(default=[PAGE_A])
        Scout(searcher=searcher, transport=failing).find("Pirc Defense")

        assert any("against" in q for q in searcher.queries)

    def test_the_default_query_runs_even_if_the_model_is_down(self):
        # A model that cannot be reached must not be able to make the search
        # worse than never having asked it.
        searcher = FakeSearcher(default=[PAGE_A])
        scout = Scout(searcher=searcher, transport=failing)

        assert len(scout.find("Pirc Defense")) == 1
        assert len(searcher.queries) == 2  # both defaults, no model queries

    def test_the_same_page_from_two_queries_is_one_candidate(self):
        searcher = FakeSearcher(default=[PAGE_A])
        scout = Scout(searcher=searcher, transport=answering("pirc plans ideas"))

        assert len(scout.find("Pirc Defense")) == 1

    def test_a_sentence_is_not_a_query(self):
        assert _queries("Here is a good search you could try:", 3) == []

    def test_a_title_cased_heading_is_too_long_to_be_a_query(self):
        # The real failure: "Bird Opening Strategy for Club Players: Middlegame
        # Guide" is a heading, and search engines do worse with those.
        assert _queries("Bird Opening Strategy for Club Players Middlegame Guide "
                        "And More Words", 3) == []

    def test_plain_queries_are_taken_in_order(self):
        assert _queries("pirc defense plans\npirc middlegame ideas", 2) == [
            "pirc defense plans", "pirc middlegame ideas"
        ]


class TestTheAssessorDiscards:
    def test_a_discarded_page_is_dropped_with_its_reason(self):
        verdicts = Assessor(transport=answering(
            "0 KEEP explains the plans\n1 DISCARD a list of many openings"
        )).assess("Pirc Defense", [Candidate(*PAGE_A), Candidate(*PAGE_B)])

        assert [v.keep for v in verdicts] == [True, False]
        assert "list of many openings" in verdicts[1].reason

    def test_silence_about_a_page_is_not_rejection(self):
        # A parse failure must not read as a verdict.
        verdicts = Assessor(transport=answering("0 KEEP good")).assess(
            "Pirc Defense", [Candidate(*PAGE_A), Candidate(*PAGE_B)]
        )

        assert verdicts[1].keep is True
        assert verdicts[1].reason == "not judged"

    def test_an_unavailable_model_keeps_everything_and_says_so(self):
        verdicts = Assessor(transport=failing).assess(
            "Pirc Defense", [Candidate(*PAGE_A)]
        )

        assert verdicts[0].keep is True
        assert "unavailable" in verdicts[0].reason

    def test_nothing_to_assess_is_not_a_question_for_the_model(self):
        asked = []

        def transport(_url, body):
            asked.append(body)
            return {"response": "0 KEEP"}

        assert Assessor(transport=transport).assess("Pirc", []) == []
        assert asked == []


class TestTheCompilerWritesOnlyFromWhatSurvived:
    def test_both_halves_are_produced(self):
        compiler = Compiler(transport=answering(
            "PLAN: Let White build the centre with pawns on e4 and d4, then "
            "undermine it. Complete development before choosing a pawn break.\n"
            "WATCH: White will aim to keep the centre, so be ready to time the "
            "break well."
        ))

        brief = compiler.compile("Pirc Defense", NOTES)

        assert brief.plan.startswith("Let White build")
        assert brief.watch.startswith("White will aim")
        assert brief.accepted is True

    def test_an_ungrounded_half_is_dropped_and_the_other_kept(self):
        # The reason the two are checked separately: a good plan should not be
        # lost because the opponent half wandered.
        compiler = Compiler(transport=answering(
            "PLAN: Let White build the centre with pawns on e4 and d4 and "
            "undermine it later after completing development.\n"
            "WATCH: White will push c5 and h5 to open the queenside quickly."
        ))

        brief = compiler.compile("Pirc Defense", NOTES)

        assert brief.plan
        assert brief.watch == ""
        assert "c5" in brief.watch_grounding.reason

    def test_nothing_approved_means_nothing_said(self):
        asked = []

        def transport(_url, body):
            asked.append(body)
            return {"response": "PLAN: something. WATCH: something."}

        brief = Compiler(transport=transport).compile("Pirc Defense", ())

        assert brief.accepted is False
        assert asked == []

    def test_missing_labels_produce_no_brief_rather_than_a_guess(self):
        brief = Compiler(transport=answering(
            "Black should develop and then break in the centre."
        )).compile("Pirc Defense", NOTES)

        assert brief.plan == ""
        assert brief.watch == ""

    def test_the_labels_are_read_case_insensitively(self):
        plan, watch = _two_parts("plan: aim for the centre.\nwatch: be ready.")

        assert plan == "aim for the centre."
        assert watch == "be ready."


class TestTheSwarmEndToEnd:
    def test_a_discarded_page_is_never_read(self):
        fetched: list[str] = []

        def fetch(url):
            fetched.append(url)
            return "<p>Black aims to stay flexible and choose a pawn break later.</p>"

        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A, PAGE_B]),
            fetch=fetch,
            transport=answering(
                "pirc defense plans",                       # scout
                "0 KEEP explains plans\n1 DISCARD a list",  # assessor
                "0",                                        # selector
                "PLAN: Black aims to stay flexible and choose a pawn break "
                "later.\nWATCH: nothing.",                  # compiler
            ),
        )

        swarm.run("Pirc Defense")

        assert fetched == ["https://a.org/pirc"]

    def test_the_trace_records_what_was_discarded_and_why(self):
        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A, PAGE_B]),
            fetch=lambda _url: "",
            transport=answering(
                "pirc defense plans",
                "0 KEEP explains plans\n1 DISCARD a list of many openings",
                "NONE",
                "PLAN: x.\nWATCH: y.",
            ),
        )

        swarm.run("Pirc Defense")

        assert swarm.trace[0]["found"] == 2
        assert swarm.trace[0]["kept"] == 1
        assert swarm.trace[0]["discarded"][0][0] == "b.org"

    def test_pages_that_yield_no_sentences_contribute_no_source(self):
        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A]),
            fetch=lambda _url: "<p>The opening is named after a player.</p>",
            transport=answering(
                "pirc defense plans", "0 KEEP good", "NONE", "PLAN: x.\nWATCH: y."
            ),
        )

        brief = swarm.run("Pirc Defense")

        assert brief.sources == ()
        assert brief.accepted is False


class TestTheBrief:
    def test_a_brief_with_neither_half_is_not_accepted(self):
        assert Brief("Pirc", "", "", ()).accepted is False


def test_the_compiler_raises_when_the_model_is_down():
    # Distinct from "it wrote something bad", which returns an empty brief.
    with pytest.raises(ollama.OllamaUnavailable):
        Compiler(transport=failing).compile("Pirc Defense", NOTES)


class TestTheWatchHalfMustSaySomethingNew:
    """A WATCH that repeats the PLAN is the failure a real run produced.

    The Pirc brief's WATCH was its PLAN with the colour flipped, and it passed
    the grounding check because every word came from the source. The checker
    compares tokens against a source; it cannot see a restatement.
    """

    def test_a_restated_plan_is_dropped(self):
        compiler = Compiler(transport=answering(
            "PLAN: Black aims to stay flexible and choose a pawn break later "
            "after completing development.\n"
            "WATCH: Black will aim to stay flexible and will choose a pawn break "
            "later after completing development."
        ))

        brief = compiler.compile("Pirc Defense", NOTES)

        assert brief.plan
        assert brief.watch == ""

    def test_a_genuinely_different_watch_survives(self):
        compiler = Compiler(transport=answering(
            "PLAN: Complete development first, then choose a pawn break.\n"
            "WATCH: White will occupy the center with pawns on e4 and d4 and try "
            "to keep the pressure."
        ))

        brief = compiler.compile("Pirc Defense", NOTES)

        assert brief.plan
        assert brief.watch.startswith("White will occupy")

    def test_the_compiler_may_decline_the_watch_half(self):
        # "none" is the prompt's escape hatch, and silence is a real answer.
        compiler = Compiler(transport=answering(
            "PLAN: Complete development first, then choose a pawn break.\n"
            "WATCH: none"
        ))

        brief = compiler.compile("Pirc Defense", NOTES)

        assert brief.plan
        assert brief.watch == ""
        assert brief.watch_grounding is None
