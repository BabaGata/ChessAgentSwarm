"""Where to send a player to learn the opening they are actually playing.

Design: docs/notes/design.informative-claims.md § "the conclusion this forces"

The plan-level material a 1500 needs exists in abundance, one opening at a time,
and **none of it is licensed** — every site carrying it is copyright, and the
public-domain books are 19th century and predate the openings in question. So the
material cannot be copied. It can be **pointed at**.

That is a better division of labour than it first looks. This project's expertise
is *measurement*: which opening, where theory ran out, how the player fared. It
has no business paraphrasing a blog and calling the result knowledge (R-03). It
says what it measured and links to instruction it did not write.

**Nothing unreviewed ever reaches a player.** A link in this library is a
recommendation, and recommending is endorsing, so `for_opening` returns only
entries the author has marked reviewed. Candidates can sit here indefinitely
without being shown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LIBRARY = Path("data/openings/guides.json")


@dataclass(frozen=True)
class Guide:
    """One place a player can go to learn an opening's plans."""

    opening: str
    title: str
    url: str
    # Who publishes it, so a reader can weigh it and the thesis can cite it.
    publisher: str
    # False until the author has read it and judged it fit for this audience.
    # Curating is endorsing; an unreviewed link is a candidate, not advice.
    reviewed: bool = False
    note: str = ""
    # Stamped by the maintenance pass. **None means never checked, which is not
    # the same as dead** — the author approved it by opening it, so absence of a
    # check is not evidence of absence of a page (L-046).
    alive: bool | None = None
    checked_on: str | None = None
    # The page's own description, kept as a fallback for the hand-written title.
    # Taken from `meta description` only.
    summary: str = ""
    # Sentences quoted verbatim from the page, saying what to aim for. Bounded
    # and attributed -- see [[decisions.0012-quote-the-plans-rather-than-write-them]],
    # which reverses this module's original "never from body text" rule and
    # gives the reasons. Never shown without `url` and `publisher` beside them.
    plans: tuple[str, ...] = ()


class GuideLibrary:
    """Curated links, keyed by opening family."""

    def __init__(self, guides: tuple[Guide, ...]) -> None:
        self._guides = guides

    def __len__(self) -> int:
        return len(self._guides)

    @property
    def reviewed(self) -> tuple[Guide, ...]:
        return tuple(g for g in self._guides if g.reviewed)

    @property
    def candidates(self) -> tuple[Guide, ...]:
        return tuple(g for g in self._guides if not g.reviewed)

    @property
    def dead(self) -> tuple[Guide, ...]:
        """Links a check has confirmed gone. E48 found one already in here."""
        return tuple(g for g in self._guides if g.alive is False)

    @property
    def unchecked(self) -> tuple[Guide, ...]:
        return tuple(g for g in self._guides if g.alive is None)

    def stale(self, before: str) -> tuple[Guide, ...]:
        """Checked, but not since `before` — a date string, compared as one."""
        return tuple(
            g for g in self._guides
            if g.checked_on is not None and g.checked_on < before
        )

    def validated(self, agent, today: str) -> GuideLibrary:
        """A copy with every link fetched and stamped.

        **A maintenance pass, never a read.** `for_opening` must not touch the
        network: a report is built in an inner loop, and an HTTP call there would
        be slow, flaky, and against C1. So liveness is stamped here and filtered
        at read time.
        """
        from dataclasses import replace

        stamped = []
        for guide in self._guides:
            checked = agent.check(guide)
            stamped.append(replace(
                guide,
                alive=checked.alive,
                checked_on=today,
                summary=checked.summary or guide.summary,
                # A fetch that found no plan sentence must not erase ones a
                # previous pass found: 403 and a timeout both return nothing,
                # and nothing is not a finding of absence (L-046).
                plans=checked.plans or guide.plans,
            ))
        return GuideLibrary(tuple(stamped))

    def for_opening(self, name: str) -> tuple[Guide, ...]:
        """Reviewed guides for this opening, most specific first.

        Usually matched on the **family** — the part before the colon — because
        "Scandinavian Defense: Mieses-Kotroc Variation" and "Scandinavian
        Defense: Modern Variation" want the same guide, and curating one per
        subline would be fifteen times the work for no gain.

        **A guide may name a subline instead, and then it only reaches players
        who play that subline.** Some families are not openings anyone studies:
        "Indian Defense" is `1. d4 Nf6`, and half those games become a London
        while the rest go elsewhere. Serving a London guide to the whole family
        is right for half the players and wrong for the other half, which is
        worse than covering neither ([[experiments.e50-ollama-summaries]]).

        Subline guides sort ahead of family ones, which is what "most specific
        first" always claimed and did not do.
        """
        family = _family(name)
        available = [
            g for g in self._guides
            if g.reviewed and g.alive is not False and _family(g.opening) == family
        ]
        specific = [g for g in available if ":" in g.opening and _covers(g.opening, name)]
        general = [g for g in available if ":" not in g.opening]
        return tuple(specific + general)

    def openings_without_a_guide(self, names) -> tuple[str, ...]:
        """Families with no reviewed guide, so silence is visible rather than assumed."""
        covered = {_family(g.opening) for g in self._guides if g.reviewed}
        return tuple(sorted({_family(n) for n in names} - covered))

    @classmethod
    def load(cls, path: Path | str = DEFAULT_LIBRARY) -> GuideLibrary:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(tuple(
            Guide(
                opening=entry["opening"], title=entry["title"], url=entry["url"],
                publisher=entry["publisher"], reviewed=entry.get("reviewed", False),
                note=entry.get("note", ""),
                alive=entry.get("alive"), checked_on=entry.get("checked_on"),
                summary=entry.get("summary", ""),
                plans=tuple(entry.get("plans") or ()),
            )
            for entry in payload["guides"]
        ))

    def save(self, path: Path | str = DEFAULT_LIBRARY) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "note": (
                "Links only. Nothing here is copied into a report, and nothing "
                "with reviewed=false is ever shown to a player."
            ),
            "guides": [
                {
                    "opening": g.opening, "title": g.title, "url": g.url,
                    "publisher": g.publisher, "reviewed": g.reviewed, "note": g.note,
                    "alive": g.alive, "checked_on": g.checked_on,
                    "summary": g.summary, "plans": list(g.plans),
                }
                for g in sorted(self._guides, key=lambda g: (g.opening, g.url))
            ],
        }
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def _family(name: str) -> str:
    return name.split(":")[0].strip()


def _covers(scope: str, played: str) -> bool:
    """Does a subline-scoped guide apply to the line the player actually reached?

    Exact, or a deeper variant of it: a guide for the "Accelerated London
    System" also covers "Accelerated London System, Something Variation". The
    separator must be part of the comparison, or "London System" would claim
    "London Systematic" and any other line that happens to start the same way.
    """
    scope, played = scope.strip(), played.strip()
    return played == scope or played.startswith(scope + ",") or played.startswith(scope + ":")
