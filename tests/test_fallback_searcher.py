"""A Wikimedia fallback that says it fell back.

Design: docs/notes/design.knowledge-base.md

`SearxSearcher` deliberately refuses to fall back, because swapping a real
opening guide for an encyclopaedia article "would look like success and read
like a downgrade". That rule is about GENRE and it still holds for opening
plans. For motif definitions Wikimedia is the right genre, so the fallback is
allowed here -- and made safe by being recorded rather than silent.
"""

from __future__ import annotations

import pytest

from chesscoach.opening_agent import FallbackSearcher, Gap, SearchUnavailable


class Stub:
    def __init__(self, name, results=None, raises=None):
        self.name = name
        self.calls = 0
        self._results = results or []
        self._raises = raises

    def search(self, gap):
        self.calls += 1
        if self._raises:
            raise self._raises
        return list(self._results)


def gap():
    return Gap(opening="Italian Game", games=5, share=0.3, query_override="fork")


WEB = [("Tactics guide", "https://example.org/fork", "Example")]
WIKI = [("Chess/Fork (reference, not a plans guide)", "https://en.wikibooks.org/x", "Wikibooks")]


class TestItPrefersTheRealSearch:
    def test_the_fallback_is_untouched_when_the_primary_answers(self):
        primary, fallback = Stub("searx", WEB), Stub("wikimedia", WIKI)
        s = FallbackSearcher(primary, fallback)
        assert s.search(gap()) == WEB
        assert fallback.calls == 0
        assert s.fell_back is False


class TestItFallsBackAndSaysSo:
    def test_an_unavailable_primary_falls_back(self):
        s = FallbackSearcher(Stub("searx", raises=SearchUnavailable("blocked")),
                             Stub("wikimedia", WIKI))
        assert s.search(gap()) == WIKI
        assert s.fell_back is True

    def test_a_primary_that_finds_nothing_falls_back(self):
        # An empty web result is not an error, but it is still nothing to show.
        s = FallbackSearcher(Stub("searx", []), Stub("wikimedia", WIKI))
        assert s.search(gap()) == WIKI
        assert s.fell_back is True

    def test_the_flag_resets_between_queries(self):
        # A stale flag would mislabel the NEXT entry's provenance, which is the
        # one property that makes this fallback safe at all.
        primary = Stub("searx", WEB)
        s = FallbackSearcher(Stub("searx", []), Stub("wikimedia", WIKI))
        s.search(gap())
        assert s.fell_back is True
        s.primary = primary
        s.search(gap())
        assert s.fell_back is False

    def test_it_still_fails_loudly_when_both_are_unavailable(self):
        # The fallback must not turn "we could not ask" into "there is nothing".
        s = FallbackSearcher(Stub("searx", raises=SearchUnavailable("blocked")),
                             Stub("wikimedia", raises=SearchUnavailable("down")))
        with pytest.raises(SearchUnavailable):
            s.search(gap())

    def test_the_name_records_both_searchers(self):
        s = FallbackSearcher(Stub("searx", WEB), Stub("wikimedia", WIKI))
        assert s.name == "searx+wikimedia"
