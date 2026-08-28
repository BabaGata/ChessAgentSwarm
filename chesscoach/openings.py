"""Which opening this is, and where the player left it.

Design: docs/notes/design.informative-claims.md

`early_error` tells a player they go wrong early and cannot say what to do about
it. Naming the opening and the move where theory ran out is the difference
between a circumstance and a behaviour (D22).

**The reference is absolute, not peer-relative, and that was a correction.** The
first design derived a "book" from the peer corpus — a position many peers reach
is book *at this level*. The author refused it: *"Checking whether they deviate
from what they usually do is not something that will help them if what they
usually do is not good from the beginning."* A band that leaves theory at move 6
is not a standard; matching it is not a target (L-045).

**Source:** `lichess-org/chess-openings`, **CC0 public domain**. 3,810 named
lines. Evidence class: published reference data, not folklore, and unencumbered.

**Depth.** Lines run from 1 to **36 plies**, with the bulk between 5 and 14 — deep
enough to follow a Ruy Lopez or a Najdorf to move 5 and well past where this band
leaves theory. (An early reading of "max 16" came from sampling the first 400
rows, which are all A00 irregular openings and short by nature.)

**Two indexes, and the distinction matters.** A position is *in theory* if it lies
anywhere along a named line; it has a *name* only if some line ends there. Indexing
endpoints alone undercounted badly — a game could be four moves into a mainline
and be scored as having left book, because no TSV row happened to end on that
exact position.

Entries are keyed by **EPD**, so transpositions resolve with no move-order
matching: 1.Nf3 e5 2.e4 Nc6 3.Bc4 is recognised as the Italian.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import chess

# Where a fetched book lives. Regenerable, so it is not committed -- the same
# convention the corpora follow.
DEFAULT_BOOK = Path("data/openings/book.json")

SOURCE_URL = "https://github.com/lichess-org/chess-openings"
SOURCE_LICENCE = "CC0-1.0"


@dataclass(frozen=True)
class Opening:
    """One named line, identified by the position it reaches."""

    eco: str
    name: str
    epd: str
    plies: int
    # The moves that reach it, in the source's own SAN with move numbers. Kept
    # because a player asking "what is the Pirc" wants the moves, and the EPD
    # they are indexed by cannot be replayed back into them.
    pgn: str = ""


@dataclass(frozen=True)
class BookWalk:
    """How far into named theory a game got, and who stepped out of it."""

    opening: Opening | None
    plies_in_book: int
    # None when the game never left the book within the moves given.
    left_at_ply: int | None
    # Whose move took the game out of book. The exit is a property of the GAME:
    # a player can leave book because their opponent played a sideline, and
    # attributing that to the player would measure the wrong person.
    left_by_white: bool | None = None


class OpeningBook:
    """Named lines, keyed by position."""

    def __init__(self, by_epd: dict[str, Opening], in_book: set[str] | None = None) -> None:
        self._by_epd = by_epd
        # Every position along every line, not only the ones a line ends at.
        self._in_book = in_book if in_book is not None else set(by_epd)

    def __len__(self) -> int:
        return len(self._by_epd)

    @property
    def positions_in_theory(self) -> int:
        return len(self._in_book)

    @classmethod
    def from_rows(cls, rows) -> OpeningBook:
        """Build from (eco, name, pgn) triples.

        A row that cannot be replayed is skipped rather than raised: one
        malformed line in a 3,810-line file must not cost the other 3,809.
        """
        by_epd: dict[str, Opening] = {}
        in_book: set[str] = set()
        for eco, name, pgn in rows:
            board = chess.Board()
            try:
                for token in pgn.split():
                    if token.endswith("."):
                        continue
                    board.push_san(token)
                    # Every position on the way, so a game four moves into a
                    # mainline is not scored as out of theory just because no
                    # row happens to end there.
                    in_book.add(board.epd())
            except ValueError:
                continue
            epd = board.epd()
            plies = len(board.move_stack)
            existing = by_epd.get(epd)
            # Deepest wins, so a subline beats the parent it transposes from.
            if existing is None or plies > existing.plies:
                by_epd[epd] = Opening(eco=eco, name=name, epd=epd, plies=plies,
                                      pgn=" ".join(pgn.split()))
        return cls(by_epd, in_book)

    def classify(self, board: chess.Board) -> Opening | None:
        """The named line this exact position is, if any."""
        return self._by_epd.get(board.epd())

    def lines_for(self, family: str) -> tuple[Opening, ...]:
        """Every named line in one family, shallowest first.

        **Data, not a selection.** The Sicilian has 391 named lines and the Pirc
        28, so something must choose the few a player is shown — but that choice
        belongs where the player's own games are known, not here. This returns
        the lot in a stable order and lets the caller decide.
        """
        wanted = _family(family)
        found = [o for o in self._by_epd.values() if _family(o.name) == wanted and o.pgn]
        return tuple(sorted(found, key=lambda o: (o.plies, o.name)))

    def walk(self, moves, max_plies: int = 30) -> BookWalk:
        """Replay a game and report the deepest named position it reached.

        `moves` is UCI. **The scan does not stop at the first unnamed position**,
        because the book has gaps: it names lines, not every ply of every line,
        so a game passes through unnamed positions and back into named ones. An
        earlier version stopped at the first miss and reported the King's Pawn
        Game for a full Italian.

        The exit is therefore the ply after the **deepest** named position, and
        it is only an exit if the game actually continued past it.
        """
        board = chess.Board()
        deepest: Opening | None = None
        plies_in_book = 0
        played = 0

        for index, uci in enumerate(moves[:max_plies]):
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                break
            if move not in board.legal_moves:
                break
            board.push(move)
            played = index + 1
            epd = board.epd()
            if epd in self._in_book:
                plies_in_book = played
            named = self._by_epd.get(epd)
            if named is not None:
                deepest = named

        if len(moves) <= plies_in_book:
            return BookWalk(opening=deepest, plies_in_book=plies_in_book, left_at_ply=None)

        exit_ply = plies_in_book + 1
        return BookWalk(
            opening=deepest,
            plies_in_book=plies_in_book,
            left_at_ply=exit_ply,
            # Ply 1 is White's, so odd plies are White's moves.
            left_by_white=exit_ply % 2 == 1,
        )

    # --- persistence --------------------------------------------------------

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": SOURCE_URL,
            "licence": SOURCE_LICENCE,
            "in_book": sorted(self._in_book),
            "openings": [
                {"eco": o.eco, "name": o.name, "epd": o.epd, "plies": o.plies,
                 "pgn": o.pgn}
                for o in sorted(self._by_epd.values(), key=lambda o: (o.eco, o.name))
            ],
        }
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str = DEFAULT_BOOK) -> OpeningBook:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        by_epd = {
            entry["epd"]: Opening(
                eco=entry["eco"], name=entry["name"],
                epd=entry["epd"], plies=entry["plies"],
                # Absent in books built before the moves were kept. A book
                # without them still classifies; it just cannot show a line.
                pgn=entry.get("pgn", ""),
            )
            for entry in payload["openings"]
        }
        return cls(by_epd, set(payload.get("in_book") or by_epd))


def _family(name: str) -> str:
    """The part of an opening name before the colon.

    "Pirc Defense: Classical Variation" and "Pirc Defense: Austrian Attack" are
    the same opening to a player choosing what to study, and the guide library
    keys on the same rule.
    """
    return name.split(":")[0].strip()
