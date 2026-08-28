"""Finding a guide for an opening the library does not cover yet.

Design: docs/notes/design.informative-claims.md

A new player arrives playing the Bird, or the Grob, or something the curated
library has never seen. The report can say which opening it is and where they
left theory — that is measured — but it has nothing to point them at.

**Four stages, and only three of them can be automated.**

    detect     which openings does this player lean on that have no guide?
    acquire    find candidate URLs                       <-- the hard one
    validate   is it alive, and what is it actually about?
    record     write it into the library, unreviewed

**Acquire is the honest problem.** There is no free, reliable search API callable
from a script: DuckDuckGo's HTML and lite endpoints return nothing parseable,
Mojeek returns only its own chrome, and everything with a real API wants a key.
So the searcher is an injected dependency, and two are provided:

  * `WikimediaSearcher` always works and is free, and its results are *reference*
    rather than *instruction* — the genre the author already refused for teaching.
    It guarantees a new player gets **something**, labelled for what it is.
  * `WorklistSearcher` finds nothing and records the exact query that would find
    it, for whoever has a search tool. **A recorded gap beats a guessed URL**:
    the gap gets filled, the guess gets trusted.
  * `SearxSearcher` is real general search, against a SearxNG the author runs
    locally — the only route that needs no API key and no signup, and the only
    one that reaches the sites carrying plan-level instruction. It raises when
    the container is down rather than quietly falling back.

Nothing this agent produces is ever shown to a player. Everything lands as
`reviewed: false`, because recommending is endorsing and only the author endorses.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from chesscoach.opening_guides import Guide
from chesscoach.opening_plans import plan_quotes

AGENT = "ChessAgentSwarm/0.1 (thesis research; opening guide lookup)"
# How much of a player's repertoire an opening must be before a missing guide is
# worth chasing. One game is noise; a fifth of their games is their repertoire.
NOTABLE_SHARE = 0.20
MIN_GAMES = 2
POLITE_SECONDS = 1.5


class SearchUnavailable(Exception):
    """The search could not be run — which is not the same as finding nothing.

    Raised rather than returning empty, because a swallowed error and a genuine
    absence are indistinguishable to the caller, and the agent would then record
    "this opening has no resource" when the truth was "I was rate limited". That
    exact confusion produced a 10-of-31 result in E48 that was entirely an
    artefact.
    """


@dataclass(frozen=True)
class Gap:
    """An opening this player leans on, with nothing to point them at."""

    opening: str
    games: int
    share: float
    # A reworded query, when something has proposed one. Empty means the default
    # below, which is the phrasing the author used by hand -- so a comparison is
    # between the agent and the author rather than between two questions.
    query_override: str = ""

    @property
    def query(self) -> str:
        """The search to run for this gap."""
        if self.query_override:
            return self.query_override
        return (f"{self.opening} plans ideas explained club players "
                f"middlegame guide")


class Searcher(Protocol):
    """Anything that can turn a query into candidate (title, url, publisher)."""

    name: str

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        ...


class WorklistSearcher:
    """Finds nothing, and says exactly what would find it.

    The correct behaviour when no search capability is available: a gap that is
    recorded gets filled later, and a URL that is guessed gets trusted forever.
    """

    name = "worklist"

    def __init__(self) -> None:
        self.pending: list[Gap] = []

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        self.pending.append(gap)
        return []


class WikimediaSearcher:
    """Free, reliable, and the wrong genre — which is why it is labelled.

    Wikipedia and Wikibooks answer for almost any named opening and need no key.
    Their prose was read by the author and refused as too advanced for 1500, so
    what this provides is a **reference of last resort**: better than sending a
    player nowhere, and never mistaken for the curated instruction.
    """

    name = "wikimedia"

    def __init__(self, opener=None) -> None:
        self._open = opener or _fetch_json

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        found: list[tuple[str, str, str]] = []
        for host, publisher in (("en.wikipedia.org", "Wikipedia"),
                                ("en.wikibooks.org", "Wikibooks")):
            title = self._best_title(host, gap.opening)
            if title is None:
                continue
            url = f"https://{host}/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
            found.append((f"{title} (reference, not a plans guide)", url, publisher))
        return found

    def _best_title(self, host: str, opening: str) -> str | None:
        query = urllib.parse.urlencode({
            "action": "query", "list": "search", "srsearch": opening,
            "srlimit": "1", "format": "json", "formatversion": "2",
        })
        payload = self._open(f"https://{host}/w/api.php?{query}")
        results = payload.get("query", {}).get("search", [])
        return results[0]["title"] if results else None


class SearxSearcher:
    """A real web search, from a SearxNG the author runs.

    The only route to general search that stays inside C1 and C7. Brave withdrew
    its free tier in February 2026 and every other hosted API wants a key, which
    means a signup an examiner cannot reproduce and a secret to manage. A local
    container needs neither, and it reaches the sites that actually carry
    plan-level instruction rather than only Wikimedia.

    Run it with `json` added to `search.formats` in `settings.yml`; the format is
    off by default and the searcher says so when it is missing.

    **It fails loudly.** There is deliberately no fallback to Wikimedia: swapping
    a real guide for an encyclopaedia article would look like success and read
    like a downgrade, which is L-046 with worse consequences because the output
    would be plausible.
    """

    name = "searx"

    # A real Ruy Lopez search returned walmart.com. A player cannot read a
    # product page, and a video cannot be validated as text or summarised from a
    # meta description.
    UNUSABLE = (
        "youtube.com", "youtu.be", "amazon.", "ebay.", "walmart.com",
        "facebook.com", "twitter.com", "x.com", "pinterest.",
    )

    # Seconds between searches. The upstream engines SearxNG queries suspend
    # themselves under load -- measured: two queries in quick succession
    # succeeded and the next four came back "Suspended: too many requests". The
    # swarm asks five queries per opening, so pacing is the difference between a
    # run that works and a run that reports an empty web.
    SPACING = 6.0

    def __init__(self, base_url: str = "http://localhost:8080",
                 limit: int = 3, opener=None, spacing: float | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._limit = limit
        self._open = opener or _fetch_json
        self._spacing = self.SPACING if spacing is None else spacing
        self._last = 0.0

    def search(self, gap: Gap) -> list[tuple[str, str, str]]:
        """The `Searcher` protocol: title, url, publisher."""
        return [(t, u, p) for t, u, p, _snippet in self.search_detailed(gap)]

    def search_detailed(self, gap: Gap) -> list[tuple[str, str, str, str]]:
        """The same results, keeping each page's snippet.

        SearxNG returns the engines' own summary in `content`, and it was being
        discarded. A judge given only a title cannot tell a real guide with a
        dull heading from a listicle with a promising one, which is the measured
        cause of E51's false negatives.
        """
        # Only paced when a real opener is in use; an injected one is a test.
        if self._spacing and self._open is _fetch_json:
            elapsed = time.monotonic() - self._last
            if elapsed < self._spacing:
                time.sleep(self._spacing - elapsed)
            self._last = time.monotonic()

        query = urllib.parse.urlencode({"q": gap.query, "format": "json"})
        payload = self._open(f"{self._base}/search?{query}")
        if "results" not in payload:
            # Most often `json` is missing from search.formats, which returns a
            # body with no results key rather than an error status.
            raise SearchUnavailable(
                f"{self._base} returned no 'results' key — is `json` in "
                f"search.formats?"
            )

        # Zero results with every engine suspended is a rate limit, not an
        # absence. SearxNG reports it and the field was being ignored, so a
        # throttled run read as "the web has nothing on the Pirc Defense" --
        # L-046 for the fifth time in this project.
        if not payload["results"] and payload.get("unresponsive_engines"):
            engines = ", ".join(
                str(entry[0]) for entry in payload["unresponsive_engines"][:4]
                if entry
            )
            raise SearchUnavailable(
                f"{self._base} returned no results and every engine is "
                f"unresponsive ({engines})"
            )

        found: list[tuple[str, str, str, str]] = []
        seen: set[str] = set()
        for result in payload["results"]:
            url = (result.get("url") or "").strip()
            title = (result.get("title") or "").strip()
            snippet = re.sub(r"\s+", " ", (result.get("content") or "")).strip()
            if not url or not title:
                continue
            publisher = _domain(url)
            if any(bad in publisher for bad in self.UNUSABLE):
                continue
            # One link per site: three pages from one publisher is less useful
            # than three publishers.
            if publisher in seen:
                continue
            seen.add(publisher)
            found.append((title, url, publisher, snippet[:400]))
            if len(found) >= self._limit:
                break
        return found


@dataclass(frozen=True)
class Checked:
    """A candidate after the agent has actually looked at it."""

    guide: Guide
    alive: bool
    status: str
    summary: str = ""
    # Bounded, attributed quotations of the page's plan sentences. Empty is a
    # normal outcome -- a reference page explains what an opening is and never
    # what to aim for, and that distinction is the whole finding of E48.
    plans: tuple[str, ...] = ()


class OpeningResourceAgent:
    """Detects gaps, acquires candidates, checks them, and records them."""

    def __init__(self, searcher: Searcher, cache_path: Path | str | None = None) -> None:
        self._searcher = searcher
        self._cache_path = Path(cache_path) if cache_path else None
        self._cache = self._load_cache()

    # --- stage 1: detect ----------------------------------------------------

    def gaps(self, openings, library) -> tuple[Gap, ...]:
        """Openings this player leans on that the library cannot speak to.

        `openings` is one family name per game, so a player's repertoire is just
        a count. Rare openings are skipped deliberately: chasing a guide for a
        line someone played once is work that helps one game once.
        """
        played = Counter(_family(name) for name in openings)
        total = sum(played.values())
        if not total:
            return ()
        covered = {_family(g.opening) for g in library.reviewed}
        return tuple(
            Gap(opening=name, games=count, share=count / total)
            for name, count in played.most_common()
            if name not in covered
            and count >= MIN_GAMES
            and count / total >= NOTABLE_SHARE
        )

    # --- stages 2-4: acquire, validate, record ------------------------------

    def acquire(self, gap: Gap) -> list[Checked]:
        """Candidates for one gap, each actually fetched before being kept."""
        out: list[Checked] = []
        for title, url, publisher in self._searcher.search(gap):
            checked = self.check(
                Guide(opening=gap.opening, title=title, url=url,
                      publisher=publisher, reviewed=False,
                      note=f"found by the {self._searcher.name} searcher"),
            )
            out.append(checked)
        return out

    def check(self, guide: Guide) -> Checked:
        """Is the link alive, and what does the page say it is about?

        A dead link in a report is worse than no link: it costs the reader time
        and the system credibility. So nothing is recorded without a fetch.
        """
        cached = self._cache.get(guide.url)
        if cached is None:
            cached = self._fetch(guide.url)
            self._cache[guide.url] = cached
            self._save_cache()
            time.sleep(POLITE_SECONDS)
        return Checked(
            guide=guide,
            alive=cached["alive"],
            status=cached["status"],
            summary=cached.get("summary", ""),
            plans=tuple(cached.get("plans") or ()),
        )

    def _fetch(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(200_000).decode("utf-8", "replace")
                return {"alive": True, "status": str(response.status),
                        "summary": _summarise(body),
                        "plans": list(plan_quotes(body))}
        except urllib.error.HTTPError as error:
            # 403 is a site refusing a bot, not a dead page. Recorded as its own
            # outcome so it is not confused with a broken link.
            return {"alive": error.code == 403, "status": f"HTTP {error.code}",
                    "summary": "", "plans": []}
        except Exception as error:  # DNS, TLS, timeout
            return {"alive": False, "status": type(error).__name__,
                    "summary": "", "plans": []}

    # --- cache --------------------------------------------------------------

    def _load_cache(self) -> dict:
        if self._cache_path and self._cache_path.exists():
            return json.loads(self._cache_path.read_text(encoding="utf-8"))
        return {}

    def _save_cache(self) -> None:
        if not self._cache_path:
            return
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(json.dumps(self._cache, indent=1), encoding="utf-8")


# --- helpers ----------------------------------------------------------------


def _family(name: str) -> str:
    return name.split(":")[0].strip()


def _domain(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _summarise(body: str) -> str:
    """What the page says it is about, in its own words.

    The meta description first, because it is the page's own summary; the title
    otherwise. Never the body text — extracting prose from arbitrary HTML is how
    a link turns back into a copy, which is the thing this whole approach exists
    to avoid.
    """
    for pattern in (
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{20,300})',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']{20,300})',
        r"<title[^>]*>([^<]{5,200})</title>",
    ):
        match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _fetch_json(url: str, attempts: int = 4) -> dict:
    """Fetch JSON, backing off on 429 and **raising** when it cannot be had.

    Returning `{}` on failure was the original shape and it was wrong: an empty
    dict is what a genuine "no results" also looks like, so the caller could not
    tell a missing article from a blocked request.
    """
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    delay = 2.0
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == attempts - 1:
                raise SearchUnavailable(f"{url} -> HTTP {error.code}") from None
            time.sleep(delay)
            delay *= 2
        except Exception as error:
            raise SearchUnavailable(f"{url} -> {type(error).__name__}") from None
    raise SearchUnavailable(f"{url} -> gave up after {attempts} attempts")
