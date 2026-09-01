"""Sites the swarm has learned not to bother reading.

Design: [[decisions.0015-a-learned-skip-list-and-a-bullet-brief]]

The Scout kept bringing back TikTok links and Reddit threads, and the Assessor
kept spending a model call to say so. A domain that cannot carry plan-level prose
cannot carry it next week either, so the verdict is **remembered** rather than
re-derived — cheaper, and it makes the swarm improve with use instead of
repeating itself.

**This is persistent state that a language model may write to**, which is the
only place in this project where that is true. Four guards, because a poisoned
skip list fails silently and forever:

  1. **Domains only**, never paths. A model cannot exclude one article.
  2. **A reason from a fixed set**, never free text. Anything else is refused.
  3. **A domain that has ever yielded a usable sentence can never be skipped.**
     This is the strong one: it makes the list unable to delete a source the
     swarm has already been helped by.
  4. **Plain JSON, with who added each entry and when**, so the author can read
     the whole list in a minute and delete anything wrong.

The seed is the hand-written blocklist that used to live in `SearxSearcher`,
marked `seed` so it is distinguishable from what the swarm learned.
"""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

# Resolved from this file, never from the working directory. A relative
# default silenced five claims for as long as they had existed (I-09),
# because every script in this repository runs from its own folder.
_DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_PATH = _DATA / "openings" / "skiplist.json"

# The only reasons a domain may be skipped. A model answering anything else has
# not given a reason this list accepts, and the entry is refused.
REASONS = ("social", "video", "shop", "database", "forum", "no-text")

# Where the swarm started: hosts that cannot carry an article about plans. A
# real Ruy Lopez search returned walmart.com.
SEED = {
    "youtube.com": "video", "youtu.be": "video", "tiktok.com": "video",
    "vimeo.com": "video", "twitch.tv": "video",
    "reddit.com": "forum", "quora.com": "forum",
    "facebook.com": "social", "twitter.com": "social", "x.com": "social",
    "instagram.com": "social", "pinterest.com": "social", "threads.net": "social",
    "amazon.com": "shop", "ebay.com": "shop", "walmart.com": "shop",
    "houseofstaunton.com": "shop",
}


@dataclass(frozen=True)
class SkipEntry:
    domain: str
    reason: str
    # "seed", "assessor" or "author" -- so a wrong entry can be traced to
    # whatever added it rather than argued about.
    added_by: str
    added_on: str = ""


class SkipList:
    """Domains not worth fetching, and the ones that have proved themselves."""

    def __init__(self, entries: tuple[SkipEntry, ...] = (),
                 useful: frozenset[str] = frozenset()) -> None:
        self._entries = entries
        # Domains that have yielded at least one sentence the swarm kept. These
        # can never be skipped, however a model votes.
        self._useful = useful

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> tuple[SkipEntry, ...]:
        return self._entries

    @property
    def learned(self) -> tuple[SkipEntry, ...]:
        """What the swarm added, as opposed to what it was given."""
        return tuple(e for e in self._entries if e.added_by != "seed")

    @property
    def useful(self) -> frozenset[str]:
        return self._useful

    def skips(self, url: str) -> bool:
        """Is this URL on a domain worth not fetching?

        Matched on the registrable tail so `blog.duolingo.com` and
        `www.reddit.com` are the same site as `reddit.com` -- otherwise a
        subdomain walks straight past the list.
        """
        domain = domain_of(url)
        if domain in self._useful:
            return False
        return any(_same_site(domain, e.domain) for e in self._entries)

    def add(self, domain: str, reason: str, added_by: str,
            today: str = "") -> SkipList:
        """A copy with one more domain skipped, or the same list if refused.

        Refusing rather than raising: the caller is a loop over a model's
        answers, and one bad suggestion must not stop the run.
        """
        domain = domain_of(domain)
        if not domain or "." not in domain:
            return self
        if reason not in REASONS:
            return self
        # Guard 3, the load-bearing one.
        if domain in self._useful:
            return self
        if any(_same_site(domain, e.domain) for e in self._entries):
            return self
        return SkipList(
            self._entries + (SkipEntry(domain, reason, added_by, today),),
            self._useful,
        )

    def mark_useful(self, url: str) -> SkipList:
        """Record that this domain produced something worth keeping."""
        domain = domain_of(url)
        if not domain:
            return self
        return SkipList(self._entries, self._useful | {domain})

    @classmethod
    def seeded(cls) -> SkipList:
        return cls(tuple(
            SkipEntry(domain, reason, "seed") for domain, reason in sorted(SEED.items())
        ))

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> SkipList:
        path = Path(path)
        if not path.exists():
            return cls.seeded()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            tuple(SkipEntry(**entry) for entry in payload.get("skip", [])),
            frozenset(payload.get("useful", [])),
        )

    def save(self, path: Path | str = DEFAULT_PATH) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "note": (
                "Domains the swarm does not fetch. Edit or delete freely -- "
                "anything added by 'assessor' is a model's judgement, not a fact. "
                "A domain listed under 'useful' has produced a sentence worth "
                "keeping and can never be skipped."
            ),
            "skip": [
                {"domain": e.domain, "reason": e.reason,
                 "added_by": e.added_by, "added_on": e.added_on}
                for e in sorted(self._entries, key=lambda e: e.domain)
            ],
            "useful": sorted(self._useful),
        }
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def domain_of(url: str) -> str:
    """The host, without `www.`, whether given a URL or a bare domain."""
    text = url.strip().lower()
    if "//" not in text:
        text = "//" + text
    host = urllib.parse.urlparse(text).netloc or ""
    host = host.split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _same_site(domain: str, listed: str) -> bool:
    """`blog.duolingo.com` is `duolingo.com`; `notreddit.com` is not `reddit.com`."""
    return domain == listed or domain.endswith("." + listed)
