"""Finding a guide for an opening the library has never seen.

Design: docs/notes/design.informative-claims.md

Four stages, and only three can be automated. Detect, acquire, validate, record —
`acquire` needs a web search, and no free reliable search API is callable from a
script, so the searcher is injected and the tests use fakes.

Two properties these tests exist to hold:

  * **a gap that cannot be filled is recorded, never guessed** — a plausible URL
    is worse than an obvious hole;
  * **nothing the agent produces is reviewed**, so none of it can reach a player.
"""

from __future__ import annotations

from chesscoach.opening_agent import (
    Gap,
    OpeningResourceAgent,
    WikimediaSearcher,
    WorklistSearcher,
)
from chesscoach.opening_guides import Guide, GuideLibrary


def a_library() -> GuideLibrary:
    return GuideLibrary((
        Guide(opening="French Defense", title="French plans",
              url="https://example.org/french", publisher="Example", reviewed=True),
        Guide(opening="Sicilian Defense", title="candidate only",
              url="https://example.org/sicilian", publisher="Example", reviewed=False),
    ))


class FakeSearcher:
    name = "fake"

    def __init__(self, results=None):
        self.results = results or []
        self.asked: list[Gap] = []

    def search(self, gap):
        self.asked.append(gap)
        return self.results


def an_agent(searcher=None, fetched=None) -> OpeningResourceAgent:
    agent = OpeningResourceAgent(searcher or FakeSearcher())
    agent._cache = fetched or {}
    return agent


class TestDetectingGaps:
    def test_an_opening_the_player_leans_on_with_no_guide_is_a_gap(self):
        games = ["Bird Opening"] * 8 + ["French Defense"] * 2

        gaps = an_agent().gaps(games, a_library())

        assert [g.opening for g in gaps] == ["Bird Opening"]
        assert gaps[0].games == 8

    def test_an_opening_with_a_reviewed_guide_is_not_a_gap(self):
        games = ["French Defense"] * 10

        assert an_agent().gaps(games, a_library()) == ()

    def test_an_unreviewed_candidate_does_not_count_as_covered(self):
        # The library holds a Sicilian candidate, but nobody has approved it, so
        # the player still has nothing to be pointed at.
        games = ["Sicilian Defense"] * 10

        assert [g.opening for g in an_agent().gaps(games, a_library())] == [
            "Sicilian Defense"
        ]

    def test_a_one_off_opening_is_not_chased(self):
        # Chasing a guide for a line played once helps one game once.
        games = ["Grob Opening"] + ["French Defense"] * 9

        assert an_agent().gaps(games, a_library()) == ()

    def test_sublines_count_towards_their_family(self):
        games = ["Bird Opening: Dutch Variation"] * 5 + ["Bird Opening"] * 5

        gaps = an_agent().gaps(games, a_library())

        assert [(g.opening, g.games) for g in gaps] == [("Bird Opening", 10)]

    def test_no_games_is_no_gaps(self):
        assert an_agent().gaps([], a_library()) == ()


class TestTheWorklistSearcher:
    def test_it_finds_nothing_and_records_what_would(self):
        searcher = WorklistSearcher()
        agent = an_agent(searcher)
        gap = Gap(opening="Bird Opening", games=8, share=0.8)

        assert agent.acquire(gap) == []
        assert searcher.pending == [gap]

    def test_the_recorded_query_is_the_one_that_worked_by_hand(self):
        gap = Gap(opening="Bird Opening", games=8, share=0.8)

        assert gap.query == (
            "Bird Opening plans ideas explained club players middlegame guide"
        )


class TestWikimediaSearcher:
    def test_it_returns_a_reference_labelled_as_one(self):
        searcher = WikimediaSearcher(
            opener=lambda url: {"query": {"search": [{"title": "Bird's Opening"}]}}
        )

        found = searcher.search(Gap(opening="Bird Opening", games=8, share=0.8))

        assert len(found) == 2  # Wikipedia and Wikibooks
        assert all("reference, not a plans guide" in title for title, _, _ in found)
        assert found[0][1].startswith("https://en.wikipedia.org/wiki/")

    def test_an_opening_with_no_article_yields_nothing(self):
        searcher = WikimediaSearcher(opener=lambda url: {"query": {"search": []}})

        assert searcher.search(Gap(opening="Nonsense", games=8, share=0.8)) == []


class TestCheckingBeforeRecording:
    def test_a_dead_link_is_marked_dead(self):
        agent = an_agent(fetched={"https://example.org/gone":
                                  {"alive": False, "status": "HTTP 404"}})

        checked = agent.check(Guide(opening="X", title="t",
                                    url="https://example.org/gone", publisher="P"))

        assert not checked.alive
        assert checked.status == "HTTP 404"

    def test_a_site_refusing_a_bot_is_not_a_dead_page(self):
        # 403 means "not to you", not "not there". Conflating them would delete
        # good links for the wrong reason.
        agent = an_agent(fetched={"https://example.org/blocked":
                                  {"alive": True, "status": "HTTP 403"}})

        checked = agent.check(Guide(opening="X", title="t",
                                    url="https://example.org/blocked", publisher="P"))

        assert checked.alive
        assert checked.status == "HTTP 403"


class TestNothingIsEverPreApproved:
    def test_everything_the_agent_produces_is_unreviewed(self):
        searcher = FakeSearcher([("t", "https://example.org/x", "P")])
        agent = an_agent(searcher, fetched={"https://example.org/x":
                                            {"alive": True, "status": "200"}})

        found = agent.acquire(Gap(opening="Bird Opening", games=8, share=0.8))

        assert found and all(not c.guide.reviewed for c in found)


class TestAnErrorIsNotAnAbsence:
    """A blocked request and an empty result must not look alike.

    E48's first run reported the agent finding resources for only 10 of 31
    openings. Every "nothing" was an HTTP 429 that `_fetch_json` swallowed into
    an empty dict. The agent would have recorded "this opening has no resource"
    for openings that plainly have one.
    """

    def test_a_failed_search_raises_rather_than_reporting_nothing(self):
        import pytest

        from chesscoach.opening_agent import SearchUnavailable

        def blocked(url):
            raise SearchUnavailable("HTTP 429")

        with pytest.raises(SearchUnavailable):
            WikimediaSearcher(opener=blocked).search(
                Gap(opening="French Defense", games=8, share=0.8)
            )

    def test_a_genuine_absence_still_returns_nothing(self):
        searcher = WikimediaSearcher(opener=lambda url: {"query": {"search": []}})

        assert searcher.search(Gap(opening="Nonsense", games=8, share=0.8)) == []
