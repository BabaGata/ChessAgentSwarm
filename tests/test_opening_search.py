"""A model filtering search results and rewording the query.

Design: docs/notes/decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert.md

No model runs here. What must hold is the control flow around it, and one
property above the rest: **the guided searcher never returns less than the plain
one would have.** A judge that rejects everything must not turn a working search
into a silent absence — the failure L-046 keeps producing in this codebase.
"""

from __future__ import annotations

from chesscoach import ollama
from chesscoach.opening_agent import Gap
from chesscoach.opening_search import GuidedSearcher, _one_line

GAP = Gap(opening="Grob Opening", games=5, share=0.3)

GOOD = ("Grob Opening: plans and ideas", "https://example.org/grob", "example.org")
LISTICLE = ("33 Chess Openings You Should Know", "https://blog.duolingo.com/x",
            "blog.duolingo.com")
FORUM = ("Openings with simple logic", "https://www.chess.com/forum/view/y", "chess.com")


class FakeSearcher:
    """Returns a scripted result list per query, and records what was asked."""

    name = "fake"

    def __init__(self, by_query: dict, default=()) -> None:
        self._by_query = by_query
        self._default = list(default)
        self.queries: list[str] = []

    def search(self, gap: Gap):
        self.queries.append(gap.query)
        return list(self._by_query.get(gap.query, self._default))


def answering(*replies: str):
    """A transport returning each reply in turn, then repeating the last."""
    remaining = list(replies)

    def transport(_url, _body):
        text = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return {"response": text}
    return transport


class TestJudging:
    def test_results_the_model_rejects_are_dropped(self):
        inner = FakeSearcher({}, default=[GOOD, LISTICLE, FORUM])
        searcher = GuidedSearcher(inner=inner, wanted=1, transport=answering("0"))

        assert searcher.search(GAP) == [GOOD]

    def test_a_none_answer_drops_everything_and_triggers_a_reword(self):
        inner = FakeSearcher({GAP.query: [LISTICLE], "grob opening strategy": [GOOD]})
        searcher = GuidedSearcher(
            inner=inner, wanted=1,
            transport=answering("NONE", "grob opening strategy", "0"),
        )

        assert searcher.search(GAP) == [GOOD]
        assert inner.queries == [GAP.query, "grob opening strategy"]

    def test_an_unparseable_answer_keeps_everything(self):
        # Refusing to guess: if the judge cannot be read, it has not judged, and
        # dropping results on that basis would lose good pages for no reason.
        inner = FakeSearcher({}, default=[GOOD, LISTICLE])
        searcher = GuidedSearcher(inner=inner, wanted=9, transport=answering("hmm"))

        assert len(searcher.search(GAP)) == 2


class TestTheModelIsAnImprovementNotADependency:
    def test_an_unreachable_model_leaves_the_plain_results(self):
        def failing(_url, _body):
            raise ollama.OllamaUnavailable("localhost:11434 -> URLError")

        inner = FakeSearcher({}, default=[GOOD, LISTICLE])
        searcher = GuidedSearcher(inner=inner, wanted=9, transport=failing)

        assert len(searcher.search(GAP)) == 2

    def test_a_judge_that_rejects_everything_still_returns_the_plain_search(self):
        # The property this file exists for.
        inner = FakeSearcher({}, default=[GOOD, LISTICLE])
        searcher = GuidedSearcher(inner=inner, attempts=1, transport=answering("NONE"))

        assert searcher.search(GAP) == [GOOD, LISTICLE]

    def test_an_empty_search_stays_empty(self):
        inner = FakeSearcher({}, default=[])
        searcher = GuidedSearcher(inner=inner, transport=answering("NONE"))

        assert searcher.search(GAP) == []


class TestRewording:
    def test_it_stops_when_enough_results_survive(self):
        inner = FakeSearcher({}, default=[GOOD, LISTICLE])
        searcher = GuidedSearcher(inner=inner, wanted=2, transport=answering("0,1"))

        searcher.search(GAP)

        assert inner.queries == [GAP.query]

    def test_a_repeated_wording_ends_the_loop(self):
        inner = FakeSearcher({}, default=[LISTICLE])
        searcher = GuidedSearcher(
            inner=inner, attempts=3, wanted=2,
            transport=answering("NONE", "same query", "NONE", "same query"),
        )

        searcher.search(GAP)

        assert inner.queries.count("same query") <= 1

    def test_every_query_and_verdict_is_recorded(self):
        # Acquisition becomes non-deterministic, so it has to become legible.
        inner = FakeSearcher({}, default=[GOOD, LISTICLE])
        searcher = GuidedSearcher(inner=inner, wanted=1, transport=answering("0"))

        searcher.search(GAP)

        assert searcher.log[0]["query"] == GAP.query
        assert searcher.log[0]["returned"] == 2
        assert searcher.log[0]["kept"] == 1


class TestReadingTheModelsQuery:
    def test_a_bare_query_is_taken(self):
        assert _one_line("grob opening plans for beginners") == \
            "grob opening plans for beginners"

    def test_quotes_and_list_markers_are_stripped(self):
        assert _one_line('- "grob opening plans"') == "grob opening plans"

    def test_a_model_explaining_itself_is_not_a_query(self):
        assert _one_line("Here is a better search you could use:") == ""

    def test_a_paragraph_is_refused(self):
        assert _one_line("The Grob is an unusual opening and searching for it "
                         "requires care because many pages are about other lines") == ""
