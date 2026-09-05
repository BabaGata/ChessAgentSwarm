"""A domain that has helped before is read before one that has not.

Spec: docs/notes/experiments.e89-why-nothing-usable.md

The search instance returns a different ordering on each call. Asked twice for
`late_castling` within a minute it gave

    en.wikipedia.org/wiki/Castling        <- the definition
    en.wikipedia.org/wiki/1904_in_chess   <- a list of tournaments

and only three web pages are read, so a bad draw loses the concept entirely.
That is what produced "0 source(s) read" for a claim whose definition is on
Wikipedia and already in the fetch cache.

The skiplist already records which domains have produced usable text --
`mark_useful` is called on every page that helps. Ordering candidates by that
costs nothing and uses evidence the run already collects.
"""

from __future__ import annotations

from chesscoach.knowledge_swarm import KnowledgeScout
from chesscoach.skiplist import SkipList


class Searcher:
    """Returns a fixed list, junk first."""

    name = "fake"

    def __init__(self, urls):
        self.urls = urls

    def search(self, gap):
        return [(u, u, u.split("/")[2]) for u in self.urls]


URLS = [
    "https://unknown-site.example/page",
    "https://en.wikipedia.org/wiki/Castling",
    "https://another-unknown.example/page",
]


class TestUsefulDomainsComeFirst:
    def test_a_domain_that_helped_before_is_read_first(self):
        known = SkipList().mark_useful("https://en.wikipedia.org/wiki/Anything")

        found = KnowledgeScout(Searcher(URLS), known).find("late_castling")

        assert found[0].url == "https://en.wikipedia.org/wiki/Castling"

    def test_without_that_history_the_search_order_is_kept(self):
        # No preference invented where there is no evidence: an engine's own
        # ranking is the only signal left.
        found = KnowledgeScout(Searcher(URLS), SkipList()).find("late_castling")

        assert found[0].url == URLS[0]

    def test_nothing_is_dropped_by_the_reordering(self):
        known = SkipList().mark_useful("https://en.wikipedia.org/wiki/Anything")

        found = KnowledgeScout(Searcher(URLS), known).find("late_castling")

        assert {c.url for c in found} == set(URLS)
