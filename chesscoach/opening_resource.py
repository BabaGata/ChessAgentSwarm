"""What a player is actually shown about the opening they play.

Design: [[decisions.0012-quote-the-plans-rather-than-write-them]]

Three parts, from three different places, and keeping them apart is the point:

  **the moves** — from `lichess-org/chess-openings`, CC0, already downloaded.
    Reference data, not a claim about chess, so nothing needs to endorse it.
  **the plans** — sentences quoted from the linked page, selected by
    `opening_plans` and attributed to their publisher. Never written here.
  **the link** — the guide itself, for the reader who wants more than three
    sentences, which is the only honest thing to offer them.

**Which few variants to show is decided from the player's own games.** The
Sicilian has 391 named lines; picking four by editorial judgement would be this
project inventing chess opinion, which it does not do (R-03). Picking the four
the player has actually reached is a measurement, and it is the same evidence
rule every other claim obeys (V8). With no games to go on it falls back to the
shallowest lines — stated as a fallback rather than dressed up as a choice.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from chesscoach.opening_guides import Guide, GuideLibrary
from chesscoach.openings import Opening, OpeningBook

# Enough to show the shape of the opening, few enough to read. A player who
# wants the twentieth Sicilian sideline is past what this resource is for.
MAX_VARIANTS = 4


@dataclass(frozen=True)
class Line:
    """One named line and the moves that reach it."""

    name: str
    eco: str
    moves: str
    plies: int
    # How many of the player's games reached it. None when no games were given.
    games: int | None = None

    @property
    def variation(self) -> str:
        """The subline's own name, or a label when this is the family itself."""
        _, _, tail = self.name.partition(":")
        return tail.strip() or "Main line"


@dataclass(frozen=True)
class OpeningResource:
    """Everything the report can say about one opening family."""

    family: str
    main_line: Line | None
    variants: tuple[Line, ...]
    # Quoted, in the publisher's own words. Empty when nothing was endorsed or
    # the page carries no plan sentence -- silence, never a substitute.
    plans: tuple[str, ...]
    guide: Guide | None

    @property
    def has_plans(self) -> bool:
        return bool(self.plans and self.guide)

    @property
    def attribution(self) -> str:
        """Who said it and where, so no quoted sentence travels unattributed."""
        if self.guide is None:
            return ""
        return f"{self.guide.publisher} — {self.guide.url}"


def _line(opening: Opening, games: int | None = None) -> Line:
    return Line(name=opening.name, eco=opening.eco, moves=opening.pgn,
                plies=opening.plies, games=games)


def build_resource(
    family: str,
    book: OpeningBook,
    library: GuideLibrary,
    reached=(),
) -> OpeningResource:
    """Assemble the moves, the quoted plans and the link for one family.

    `reached` is the opening name of each of the player's games — repeated, one
    per game — so the variants shown are the ones they meet.
    """
    lines = book.lines_for(family)
    played = Counter(name for name in reached if name)

    main = _pick_main_line(lines, family)
    variants = _pick_variants(lines, main, played)

    guides = library.for_opening(family)
    guide = guides[0] if guides else None

    return OpeningResource(
        family=family.split(":")[0].strip(),
        main_line=_line(main, played.get(main.name)) if main else None,
        variants=variants,
        plans=guide.plans if guide else (),
        guide=guide,
    )


def _pick_main_line(lines: tuple[Opening, ...], family: str) -> Opening | None:
    """The line that *is* the opening, rather than one of its branches.

    Preferring a row named exactly for the family matters: the shallowest row
    overall can be a one-move ancestor shared with a dozen other openings.

    Among those, the **deepest** — a player asking what the Pirc is wants
    `1. e4 d6 2. d4 Nf6 3. Nc3 g6`, not `1. e4 d6`. No depth cap is needed
    rather than none is wanted: measured across the families these players
    actually reach, the deepest plain-named row runs 1 to 6 plies.
    """
    if not lines:
        return None
    bare = family.split(":")[0].strip()
    exact = [o for o in lines if o.name.strip() == bare]
    if exact:
        return exact[-1]
    return lines[0]


def _pick_variants(
    lines: tuple[Opening, ...],
    main: Opening | None,
    played: Counter,
) -> tuple[Line, ...]:
    """The few *named* branches worth showing, the player's own first.

    Only sublines qualify. The book carries several rows under the family's
    bare name at different depths, and offering those as variations printed
    "Main line" three times under the main line.
    """
    candidates = [
        o for o in lines
        if ":" in o.name and (main is None or o.epd != main.epd)
    ]
    if not candidates:
        return ()
    # Most-played first; among unplayed lines the shallowest, which is the
    # fallback and is why `games` is carried on the Line rather than inferred.
    ranked = sorted(
        candidates,
        key=lambda o: (-played.get(o.name, 0), o.plies, o.name),
    )
    # One row per named variation. The book lists a variation at several depths,
    # so without this the Classical Variation appears twice with two move
    # lengths, which reads as two different things.
    seen: set[str] = set()
    chosen: list[Line] = []
    for opening in ranked:
        label = _line(opening).variation
        if label in seen:
            continue
        seen.add(label)
        chosen.append(_line(opening, played.get(opening.name) or None))
        if len(chosen) >= MAX_VARIANTS:
            break
    return tuple(chosen)
