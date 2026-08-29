"""Per-opening development norms, derived rather than asserted.

Design: docs/notes/design.opening-development-signals.md

The author's instruction:

    "The tests should not be general for all opening but general rules per
    opening. Like in italian game the castles should occur around move 5 and in
    ruy lopez in between moves 8-10."

**Their two numbers are the test of this script, not its input.** If castling
norms have to be written down by hand they are unfalsifiable folklore (R-03) and
they would have to be written down for every opening in the book. If the corpus
produces them on its own, then every opening has a norm for free -- including the
ones nobody has an intuition about -- and the author's Italian and Ruy Lopez
figures become independent confirmation that the derivation works.

So: walk every game, name the opening, and report the median move by which each
side castled and finished developing.

    python experiments/e58-opening-development/derive.py > results/norms.txt
"""

from __future__ import annotations

import math
import pathlib
import statistics
import sys
from collections import defaultdict

import chess
import chess.pgn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.development import measure_development  # noqa: E402
from chesscoach.openings import OpeningBook, _family  # noqa: E402

CORPUS = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw" / "corpus-rapid"

# Below this a median is a coincidence. Not a judgement about chess -- a
# judgement about how many numbers it takes to have a middle.
MIN_GAMES = 20

# Families to print in full, however the corpus ranks them: the author named
# these two and they are what the derivation has to reproduce.
NAMED_BY_AUTHOR = ("Italian Game", "Ruy Lopez")


def move_number(ply: int) -> float:
    """Plies are how the board counts; players speak in moves."""
    return math.ceil(ply / 2)


class Norms:
    """One (family, colour) cell, accumulating raw numbers only."""

    def __init__(self) -> None:
        self.castled: list[int] = []
        self.developed: list[int] = []
        self.games = 0
        self.never_castled = 0
        self.incomplete = 0
        self.repeat_rates: list[float] = []
        self.pawn_rates: list[float] = []
        self.book: list[int] = []

    def add(self, development, plies_in_book: int) -> None:
        self.games += 1
        self.book.append(plies_in_book)
        if development.castled_at is None:
            self.never_castled += 1
        else:
            self.castled.append(development.castled_at)
        if development.completed:
            self.developed.append(development.developed_at)
        else:
            self.incomplete += 1
        repeat = development.rate(development.repeat_moves)
        pawn = development.rate(development.pawn_moves)
        if repeat is not None:
            self.repeat_rates.append(repeat)
        if pawn is not None:
            self.pawn_rates.append(pawn)

    def median_castle(self) -> float | None:
        return _survival_median(self.castled, self.never_castled)

    def median_develop(self) -> float | None:
        return _survival_median(self.developed, self.incomplete)


def _survival_median(reached: list[int], never: int) -> float | None:
    """The ply by which half the games got there, counting the ones that never did.

    **A median over only the games that castled is censored the second time.**
    Bishop's Opening White castles on move 11 in the games where it castles at
    all -- and 47 % never castle, so the honest answer is not 11, it is that half
    of these games have no castling move to be late with. Dropping those games
    understates lateness exactly where lateness is worst, which is the same
    right-censoring the design note refuses for the development span.

    Games that never got there sort after every game that did, so if they carry
    the midpoint the answer is `None` rather than a number.
    """
    total = len(reached) + never
    if total == 0:
        return None
    ordered = sorted(reached)
    middle = (total - 1) // 2
    if middle >= len(ordered):
        return None
    if total % 2 == 1:
        return ordered[middle]
    upper = middle + 1
    if upper >= len(ordered):
        return None
    return (ordered[middle] + ordered[upper]) / 2


def read_corpus():
    """Every game in the rapid corpus, as (game, uci moves, moves)."""
    for path in sorted(CORPUS.glob("*.pgn")):
        with path.open(encoding="utf-8", errors="replace") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                # Games from a set-up position are not this opening's evidence.
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                if "FEN" in game.headers:
                    continue
                try:
                    played = list(game.mainline_moves())
                except (ValueError, AssertionError):
                    continue
                if len(played) < 8:
                    continue
                yield game, played


def main() -> None:
    book = OpeningBook.load()
    cells: dict[tuple[str, bool], Norms] = defaultdict(Norms)
    games = unnamed = 0

    for game, played in read_corpus():
        games += 1
        walk = book.walk([m.uci() for m in played])
        if walk.opening is None:
            unnamed += 1
            continue
        family = _family(walk.opening.name)
        for colour in (chess.WHITE, chess.BLACK):
            development = measure_development(played, colour)
            cells[(family, colour)].add(development, walk.plies_in_book)

    print("PER-OPENING DEVELOPMENT NORMS, DERIVED FROM THE CORPUS")
    print("=" * 78)
    print()
    print(f"games read            {games}")
    print(f"opening not named     {unnamed}")
    print(f"families measured     {len({f for f, _ in cells})}")
    print(f"minimum games to show {MIN_GAMES}")
    print()
    print("Median MOVE NUMBER by which the side had castled, and by which all")
    print("four minor pieces had left home. `-` means fewer than half the games")
    print("got there at all.")
    print()

    header = (f"{'opening':<34}{'side':<7}{'n':>5}{'castle':>8}{'develop':>9}"
              f"{'never':>7}{'book':>6}{'repeat':>8}{'pawn':>7}")
    print(header)
    print("-" * len(header))

    def row(family: str, colour: bool) -> str:
        cell = cells[(family, colour)]
        castle = cell.median_castle()
        develop = cell.median_develop()
        return (
            f"{family[:33]:<34}"
            f"{'White' if colour else 'Black':<7}"
            f"{cell.games:>5}"
            f"{move_number(castle) if castle else '-':>8}"
            f"{move_number(develop) if develop else '-':>9}"
            f"{cell.never_castled / cell.games:>7.0%}"
            f"{move_number(statistics.median(cell.book)):>6}"
            f"{statistics.mean(cell.repeat_rates) if cell.repeat_rates else 0:>8.0%}"
            f"{statistics.mean(cell.pawn_rates) if cell.pawn_rates else 0:>7.0%}"
        )

    ranked = sorted(
        {f for f, _ in cells},
        key=lambda f: -(cells[(f, chess.WHITE)].games),
    )
    shown = [f for f in ranked if cells[(f, chess.WHITE)].games >= MIN_GAMES]

    for family in shown:
        for colour in (chess.WHITE, chess.BLACK):
            print(row(family, colour))

    print()
    print("=" * 78)
    print("THE AUTHOR'S TWO NUMBERS")
    print("=" * 78)
    print()
    print("Stated before the corpus was asked, so this is a prediction being")
    print("checked and not a threshold being fitted:")
    print()
    print("  Italian Game   White castles around move 5")
    print("  Ruy Lopez      White castles between moves 8 and 10")
    print()
    for family in NAMED_BY_AUTHOR:
        cell = cells[(family, chess.WHITE)]
        if cell.games == 0:
            print(f"  {family:<16} NOT IN THE CORPUS -- cannot check")
            continue
        castle = cell.median_castle()
        got = move_number(castle) if castle else None
        print(f"  {family:<16} n={cell.games:<5} corpus says White castles on move "
              f"{got if got else 'NEVER, for half of them'}")

    print()
    print("=" * 78)
    print("IS THERE PER-OPENING VARIATION AT ALL?")
    print("=" * 78)
    print()
    print("The claim only needs a per-opening norm if openings actually differ.")
    print("Spread across the families shown, White and Black separately:")
    print()
    for label, get in (
        ("castles by move",
         lambda c: move_number(c.median_castle()) if c.median_castle() else None),
        ("develops by move",
         lambda c: move_number(c.median_develop()) if c.median_develop() else None),
        ("pawn share of opening moves",
         lambda c: statistics.mean(c.pawn_rates) * 100 if c.pawn_rates else None),
        ("repeat share of opening moves",
         lambda c: statistics.mean(c.repeat_rates) * 100 if c.repeat_rates else None),
        ("moves still in book", lambda c: move_number(statistics.median(c.book))),
    ):
        values = [
            (get(cells[(f, colour)]), f, colour)
            for f in shown for colour in (chess.WHITE, chess.BLACK)
            if get(cells[(f, colour)]) is not None
        ]
        if not values:
            continue
        low = min(values)
        high = max(values)
        print(f"  {label:<32} {low[0]:>5.0f}  ({low[1]}, {'W' if low[2] else 'B'})")
        print(f"  {'':<32} {high[0]:>5.0f}  ({high[1]}, {'W' if high[2] else 'B'})")
        print()


if __name__ == "__main__":
    main()
