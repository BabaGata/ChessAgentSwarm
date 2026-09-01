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
from chesscoach.opening_summary import Summariser, Summary
from chesscoach.openings import Opening, OpeningBook

# Enough to show the shape of the opening, few enough to read. A player who
# wants the twentieth Sicilian sideline is past what this resource is for.
MAX_VARIANTS = 4

# A main line advances a move or two at a time. A bigger jump means the deeper
# row is a different line that shares the family's name, not a continuation of
# it -- which is how the Indian Defense came to present `1. d4 Nf6 2. c4 e6
# 3. Qb3` as its main line.
MAX_MAINLINE_STEP = 2


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
    # Present only when a summariser was supplied AND its rewrite passed the
    # grounding check. `summary.evidence_class` says whether the words are the
    # publisher's or a local model's, and the report must print that.
    summary: Summary | None = None

    @property
    def prose(self) -> str:
        """What to show: the rewrite when it earned its place, the quotes otherwise."""
        if self.summary is not None and self.summary.accepted:
            return self.summary.text
        return " ".join(self.plans)

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
    summariser: Summariser | None = None,
) -> OpeningResource:
    """Assemble the moves, the quoted plans and the link for one family.

    `reached` is the opening name of each of the player's games — repeated, one
    per game — so the variants shown are the ones they meet.
    """
    lines = book.lines_for(family)
    played = Counter(name for name in reached if name)

    main = _pick_main_line(lines, family)
    variants = _pick_variants(lines, main, played)

    # Ask with the line the player most often reaches, not the bare family.
    # A subline-scoped guide can only be matched against a subline, and
    # "Indian Defense" on its own is `1. d4 Nf6` -- a move, not something anyone
    # studies. The most-played line is what a guide has to be right about.
    asked_about = played.most_common(1)[0][0] if played else family
    guides = library.for_opening(asked_about)
    guide = guides[0] if guides else None

    plans = guide.plans if guide else ()
    # Never rephrase what was never endorsed. An unreviewed page contributes no
    # sentences, so there is nothing to hand a model -- and asking it anyway
    # would be asking it what the opening is about, which is the refused
    # request (ADR-0013).
    summary = summariser.summarise(family, plans) if (summariser and plans) else None

    return OpeningResource(
        family=family.split(":")[0].strip(),
        main_line=_line(main, played.get(main.name)) if main else None,
        variants=variants,
        plans=plans,
        guide=guide,
        summary=summary,
    )


def _pick_main_line(lines: tuple[Opening, ...], family: str) -> Opening | None:
    """The line that *is* the opening, rather than one of its branches.

    Preferring a row named exactly for the family matters: the shallowest row
    overall can be a one-move ancestor shared with a dozen other openings.

    Among those, the deepest **reached in small steps** — a player asking what
    the Pirc is wants `1. e4 d6 2. d4 Nf6 3. Nc3 g6`, not `1. e4 d6`.

    "Small steps" is the correction. Taking the deepest row outright gave the
    Indian Defense `1. d4 Nf6 2. c4 e6 3. Qb3` as its main line — an obscure
    sideline that the source data also happens to name plainly. It is a genuine
    continuation of `1. d4 Nf6`, so checking that the rows form a chain does not
    catch it; what marks it is the **jump**, three plies in one go where the Pirc
    and the Sicilian advance one or two at a time
    ([[experiments.e50-ollama-summaries]]).
    """
    if not lines:
        return None
    bare = family.split(":")[0].strip()
    # Sorted by moves as well as depth so the walk is deterministic when several
    # rows share a name and a length, which happens in the Queen's Pawn Game.
    exact = sorted((o for o in lines if o.name.strip() == bare),
                   key=lambda o: (o.plies, o.pgn))
    if not exact:
        return lines[0]

    # A main line is a **trunk**: something other named lines grow out of. The
    # Scandinavian has exactly two rows named plainly for the family, `1. e4 d5`
    # and `1. e4 d5 2. b3`, one ply apart -- so the small-steps guard does not
    # fire and the walk lands on a rare sideline. Requiring the row to be a
    # prefix of at least one named subline separates them by measurement rather
    # than by taste: `2. b3` continues into **0** named Scandinavian lines,
    # `1. e4 d5` into 43, and the Italian's `3. Bc4` into 177.
    #
    # Found only when `build_resource` was finally wired into the report. It had
    # been correct-looking and unread since it was written.
    branches = tuple(o for o in lines if o.name.strip() != bare)

    def is_trunk(opening: Opening) -> bool:
        return any(o.pgn.startswith(opening.pgn + " ") for o in branches)

    current = exact[0]
    while True:
        deeper = [
            o for o in exact
            if o.plies > current.plies
            and o.plies - current.plies <= MAX_MAINLINE_STEP
            and o.pgn.startswith(current.pgn + " ")
            # A family with no sublines at all keeps its own row rather than
            # being silenced; the check only ever *refuses to go deeper*.
            and (is_trunk(o) or not branches)
        ]
        if not deeper:
            return current
        current = deeper[0]


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
