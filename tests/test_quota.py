"""A free tier that cannot be overrun, and that says so when it is spent.

Design: docs/notes/design.knowledge-base.md
"""

from __future__ import annotations

from datetime import date

import pytest

from chesscoach.opening_agent import Gap, SearchUnavailable
from chesscoach.quota import MeteredSearcher, Quota, QuotaExhausted, QuotaLedger


class FakeSearcher:
    name = "fake"

    def __init__(self, results=None, raises=None) -> None:
        self.calls = 0
        self._results = results if results is not None else [("t", "u", "p")]
        self._raises = raises

    def search(self, gap):
        self.calls += 1
        if self._raises:
            raise self._raises
        return list(self._results)


def gap(query: str = "q") -> Gap:
    return Gap(opening="Italian Game", games=5, share=0.3, query_override=query)


def metered(tmp_path, limit=3, period="month", keep_back=0, searcher=None,
            today=date(2026, 8, 30)):
    return MeteredSearcher(
        searcher or FakeSearcher(),
        Quota(limit=limit, period=period, keep_back=keep_back),
        QuotaLedger(tmp_path / "quota.json"),
        today=lambda: today,
    )


class TestTheCapHolds:
    def test_it_allows_searches_up_to_the_limit(self, tmp_path):
        m = metered(tmp_path, limit=3)
        for _ in range(3):
            assert m.search(gap())
        assert m.inner.calls == 3

    def test_the_search_past_the_limit_never_reaches_the_provider(self, tmp_path):
        m = metered(tmp_path, limit=2)
        m.search(gap())
        m.search(gap())
        with pytest.raises(QuotaExhausted):
            m.search(gap())
        # The point of the guard: the request is refused HERE, not billed there.
        assert m.inner.calls == 2

    def test_remaining_counts_down(self, tmp_path):
        m = metered(tmp_path, limit=3)
        assert m.remaining() == 3
        m.search(gap())
        assert m.remaining() == 2


class TestItRefusesLoudly:
    def test_exhaustion_raises_rather_than_returning_nothing(self, tmp_path):
        # L-046, six instances in this project. An empty list means "the web has
        # nothing on this"; a spent quota means "we did not look". Letting the
        # second read as the first is how a throttled run became "the web has
        # nothing on the Pirc Defense".
        m = metered(tmp_path, limit=1)
        m.search(gap())
        with pytest.raises(QuotaExhausted):
            m.search(gap())

    def test_it_is_a_SearchUnavailable_so_existing_callers_already_handle_it(self, tmp_path):
        m = metered(tmp_path, limit=0)
        with pytest.raises(SearchUnavailable):
            m.search(gap())

    def test_an_unreadable_ledger_refuses_rather_than_assuming_zero_spent(self, tmp_path):
        # The safe direction for a cap: a false stop costs a delay, a false go
        # costs money.
        (tmp_path / "quota.json").write_text("{not json", encoding="utf-8")
        m = metered(tmp_path, limit=5)
        with pytest.raises(QuotaExhausted):
            m.search(gap())


class TestItCountsAttempts:
    def test_a_failed_search_still_spends_its_allowance(self, tmp_path):
        # The provider bills the attempt. Counting only successes would let a
        # run of failures spend the month invisibly.
        m = metered(tmp_path, limit=2,
                    searcher=FakeSearcher(raises=SearchUnavailable("upstream down")))
        with pytest.raises(SearchUnavailable):
            m.search(gap())
        assert m.remaining() == 1


class TestPersistence:
    def test_spending_survives_a_new_process(self, tmp_path):
        metered(tmp_path, limit=3).search(gap())
        metered(tmp_path, limit=3).search(gap())
        fresh = metered(tmp_path, limit=3)
        assert fresh.remaining() == 1

    def test_a_new_month_starts_a_new_allowance(self, tmp_path):
        august = metered(tmp_path, limit=1, today=date(2026, 8, 30))
        august.search(gap())
        with pytest.raises(QuotaExhausted):
            august.search(gap())
        september = metered(tmp_path, limit=1, today=date(2026, 9, 1))
        assert september.remaining() == 1

    def test_a_daily_quota_resets_daily(self, tmp_path):
        monday = metered(tmp_path, limit=1, period="day", today=date(2026, 8, 30))
        monday.search(gap())
        tuesday = metered(tmp_path, limit=1, period="day", today=date(2026, 8, 31))
        assert tuesday.remaining() == 1

    def test_a_monthly_quota_does_not_reset_on_a_new_day(self, tmp_path):
        first = metered(tmp_path, limit=1, today=date(2026, 8, 30))
        first.search(gap())
        later = metered(tmp_path, limit=1, today=date(2026, 8, 31))
        assert later.remaining() == 0


class TestKeepBack:
    def test_held_back_queries_are_not_available_to_automation(self, tmp_path):
        # 5 granted, 3 reserved for the author's own use: automation gets 2.
        m = metered(tmp_path, limit=5, keep_back=3)
        assert m.remaining() == 2
        m.search(gap())
        m.search(gap())
        with pytest.raises(QuotaExhausted) as caught:
            m.search(gap())
        assert "held back" in str(caught.value)
