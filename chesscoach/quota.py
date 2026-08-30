"""A hard cap on a metered search API, so a free tier cannot be overrun.

Design: docs/notes/design.knowledge-base.md § the dependency

The author's condition for adding a keyed provider:

    "I can configure brave search mcp for example if you can block searches that
    will go over the free limit"

So the cap has to be **enforced by us, before the request leaves**, rather than
trusted to the provider to reject. A provider that answers the 2,001st query and
bills for it has not broken any promise; the limit is ours to keep.

Three properties, and the second is the one this project keeps having to relearn:

**It counts attempts, not successes.** A request that times out has still been
made and is still likely to be billed. Counting only successes would let a run
of failures spend the budget invisibly.

**It refuses loudly.** Exhaustion raises `QuotaExhausted`, never returns an empty
result list. An empty list means *"the web has nothing on this"*; a quota block
means *"we did not look"*, and letting the second read as the first is L-046 --
six instances in this project so far, and the reason `SearchUnavailable` exists.

**It reserves.** `keep_back` holds a slice of the allowance aside so an automated
run cannot consume the whole month and leave the author unable to search by
hand.

The counter is persisted, because a limit that resets when the process restarts
is not a limit.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from chesscoach.opening_agent import Gap, SearchUnavailable

DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "data" / "search-quota.json"


class QuotaExhausted(SearchUnavailable):
    """The allowance is spent. A subclass so existing handlers already catch it.

    Callers that treat `SearchUnavailable` as *"could not ask"* -- which is every
    caller, by design -- get the right behaviour without knowing quotas exist.
    """


@dataclass(frozen=True)
class Quota:
    """What a provider's free tier actually grants."""

    limit: int
    # "month" or "day". Providers meter on one or the other, and a guard set to
    # the wrong one is either useless or needlessly strict.
    period: str = "month"
    # Held back from automated use, so the author can still search by hand at
    # the end of a month a swarm run has mostly consumed.
    keep_back: int = 0

    def key(self, today: date) -> str:
        """The bucket this day's spending belongs to."""
        if self.period == "day":
            return today.isoformat()
        if self.period == "month":
            return f"{today.year:04d}-{today.month:02d}"
        raise ValueError(f"unknown quota period: {self.period!r}")

    @property
    def usable(self) -> int:
        return max(self.limit - self.keep_back, 0)


class QuotaLedger:
    """Spending per period, on disk.

    A JSON file rather than the run store: the run store is per-run and this has
    to outlive every run. Old periods are kept -- they are three numbers and they
    are the only record of what a month actually cost.
    """

    def __init__(self, path: Path | str = DEFAULT_LEDGER) -> None:
        self._path = Path(path)

    def _read(self) -> dict[str, int]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            # A corrupt ledger must not read as "nothing spent". Refusing is the
            # safe direction for a cap: the cost of a false stop is a delay, the
            # cost of a false go is a bill.
            raise QuotaExhausted(
                f"quota ledger at {self._path} is unreadable; refusing to search"
            ) from None

    def spent(self, key: str) -> int:
        return int(self._read().get(key, 0))

    def record(self, key: str, count: int = 1) -> int:
        ledger = self._read()
        ledger[key] = int(ledger.get(key, 0)) + count
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(ledger, indent=1, sort_keys=True),
                              encoding="utf-8")
        return ledger[key]


class MeteredSearcher:
    """Wraps any `Searcher` and refuses the query that would exceed the tier.

    The same shape as `GuidedSearcher`: a searcher in, a searcher out, so it
    composes with everything already built and nothing downstream changes.
    """

    def __init__(self, inner, quota: Quota,
                 ledger: QuotaLedger | None = None, today=None) -> None:
        self.inner = inner
        self.quota = quota
        self._ledger = ledger or QuotaLedger()
        self._today = today or date.today
        self.name = f"metered/{getattr(inner, 'name', 'searcher')}"

    def remaining(self) -> int:
        """How many searches are still allowed in this period."""
        key = self.quota.key(self._today())
        return max(self.quota.usable - self._ledger.spent(key), 0)

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        return [(t, u, p) for t, u, p, *_ in self.search_detailed(gap)]

    def search_detailed(self, gap: Gap):
        key = self.quota.key(self._today())
        spent = self._ledger.spent(key)
        if spent >= self.quota.usable:
            raise QuotaExhausted(
                f"{self.name}: {spent}/{self.quota.limit} used this "
                f"{self.quota.period}"
                + (f" ({self.quota.keep_back} held back for manual use)"
                   if self.quota.keep_back else "")
            )

        # Counted BEFORE the request. A call that fails has still been made and
        # is still likely to be billed, so the conservative order is the correct
        # one -- and it is the order that cannot be defeated by an exception.
        self._ledger.record(key)

        inner = getattr(self.inner, "search_detailed", None)
        if inner is not None:
            return inner(gap)
        return [(t, u, p, "") for t, u, p in self.inner.search(gap)]
