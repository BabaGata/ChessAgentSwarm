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

    def for_opening(self, name: str) -> tuple[Guide, ...]:
        """Reviewed guides for this opening, most specific first.

        Matched on the **family** — the part of an opening name before the colon —
        because "Scandinavian Defense: Mieses-Kotroc Variation" and "Scandinavian
        Defense: Modern Variation" want the same guide, and curating one per
        subline would be fifteen times the work for no gain.
        """
        family = _family(name)
        return tuple(g for g in self._guides if g.reviewed and _family(g.opening) == family)

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
                }
                for g in sorted(self._guides, key=lambda g: (g.opening, g.url))
            ],
        }
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def _family(name: str) -> str:
    return name.split(":")[0].strip()
