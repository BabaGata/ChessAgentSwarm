"""Is the pawn difference about WHICH openings, or about HOW one is played?

Design: docs/notes/design.opening-development-signals.md

The author, reading E59's inverted pawn result:

    "My concern is that weaker players maybe play more commonly openings with not
    many pawn moves while stronger players more commonly play openings with more
    pawn moves, but when they play the same opening stronger players might have
    less pawn moves before castling and developing all light pieces while weaker
    players might move more pawns in the same opening before developing pieces
    and casteling."

**A confound E59 was open to.** Its separation test pooled every game a player
played, so a population difference in the *mix* of openings is indistinguishable
from a difference in *play* within one. Two tests separate them:

- **direct standardisation** -- score both populations under the SAME opening
  mix. If the crude gap survives reweighting it is about play; if it collapses
  it was composition.
- **paired within-family differences** -- compare the two populations inside each
  opening and aggregate the differences, which never lets one mix influence the
  other.

**And a second flaw the author's wording exposes.** E59 measured pawn *share*,
but the hypothesis is about *how many pawn moves happen before the pieces are
out*. Share divides by the window, and the window is systematically shorter for
strong players -- so share can fall while the count rises. Both are reported.

    python experiments/e58-opening-development/composition.py > results/composition.txt
"""

from __future__ import annotations

import pathlib
import statistics
import sys
from collections import defaultdict

import chess
import chess.pgn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.development import measure_development  # noqa: E402
from chesscoach.openings import OpeningBook, _family  # noqa: E402
from expectations import MIN_GAMES, STRONG, SUBJECTS  # noqa: E402


# A fixed early window, used ONLY as the censoring check. Every game reaches it,
# so it cannot be biased by dropping the games where development never finished
# -- which are exactly the games the hypothesis is about.
EARLY_PLIES = 20

# +2 moves, the author's upper setting.
TOLERANCE_PLIES = 4


class Cell:
    """Per-game numbers for one (family, colour) in one corpus."""

    def __init__(self) -> None:
        self.share: list[float] = []
        self.count: list[int] = []
        self.window: list[int] = []
        # Censoring-free, measured on every game including the unfinished ones.
        self.early: list[int] = []
        self.late: list[int] = []
        self.slow: list[int] = []
        self.repeat: list[float] = []
        self.games = 0

    def add(self, development, early_pawns: int, late: bool | None,
            slow: bool | None = None) -> None:
        self.games += 1
        self.early.append(early_pawns)
        if late is not None:
            self.late.append(1 if late else 0)
        if slow is not None:
            self.slow.append(1 if slow else 0)
        repeat = development.rate(development.repeat_moves)
        if repeat is not None:
            self.repeat.append(repeat)

        # The three below need a finished window: it has no length to normalise
        # by and no end to count up to until development completes.
        if not development.completed:
            return
        share = development.rate(development.pawn_moves)
        if share is None:
            return
        self.share.append(share)
        self.count.append(development.pawn_moves)
        self.window.append(development.moves_in_window)

    @property
    def n(self) -> int:
        return len(self.share)


def early_pawn_moves(played, colour: chess.Color) -> int:
    """Pawn moves in the player's first `EARLY_PLIES` plies, whatever happened after."""
    board = chess.Board()
    count = 0
    for move in played[:EARLY_PLIES]:
        if board.turn == colour:
            piece = board.piece_at(move.from_square)
            if piece is not None and piece.piece_type == chess.PAWN:
                count += 1
        board.push(move)
    return count


def walk_corpus(directory: pathlib.Path, book: OpeningBook, expectation=None):
    """Per (family, colour) cells for one corpus."""
    cells: dict[tuple[str, bool], Cell] = defaultdict(Cell)
    for path in sorted(directory.glob("*.pgn")):
        with path.open(encoding="utf-8", errors="replace") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if "FEN" in game.headers:
                    continue
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                try:
                    played = list(game.mainline_moves())
                except (ValueError, AssertionError):
                    continue
                if len(played) < 8:
                    continue
                walk = book.walk([m.uci() for m in played])
                if walk.opening is None:
                    continue
                family = _family(walk.opening.name)
                for colour in (chess.WHITE, chess.BLACK):
                    development = measure_development(played, colour)
                    late = slow = None
                    cell = expectation.get((family, colour)) if expectation else None
                    if cell is not None and cell.games >= MIN_GAMES:
                        base = cell.median_castle()
                        if base is not None:
                            late = (development.castled_at is None
                                    or development.castled_at > base + TOLERANCE_PLIES)
                        ready = cell.median_ready()
                        if ready is not None:
                            # Never finishing is the most extreme way of being
                            # past the expectation, not a missing value.
                            slow = (development.ready_at is None
                                    or development.ready_at > ready + TOLERANCE_PLIES)
                    cells[(family, colour)].add(
                        development, early_pawn_moves(played, colour), late, slow
                    )
    return cells


def crude(cells, key: str) -> float:
    """Pooled mean over every game, which is what E59 reported."""
    values = [v for cell in cells.values() for v in getattr(cell, key)]
    return statistics.mean(values)


def standardised(cells, weights, key: str) -> float:
    """The same population scored under someone else's opening mix.

    Direct standardisation: each cell keeps its own mean, and the cells are
    re-weighted to the reference mix. Any gap that survives this is about how an
    opening is played, because the mix is now identical by construction.
    """
    total = num = 0.0
    for cell_key, weight in weights.items():
        cell = cells.get(cell_key)
        if cell is None or cell.n < MIN_GAMES:
            continue
        num += statistics.mean(getattr(cell, key)) * weight
        total += weight
    return num / total if total else float("nan")


def main() -> None:
    book = OpeningBook.load()
    from expectations import norms_for
    expectation, _ = norms_for(STRONG, book)
    strong = walk_corpus(STRONG, book, expectation)
    subjects = walk_corpus(SUBJECTS, book, expectation)

    shared = sorted(
        k for k in subjects
        if subjects[k].n >= MIN_GAMES and strong.get(k) and strong[k].n >= MIN_GAMES
    )
    # Every metric is compared on the same cells, so the three lines of one
    # block are about one population and not three different ones.
    weights = {k: subjects[k].n for k in shared}

    print("PAWN MOVES: WHICH OPENING, OR HOW IT IS PLAYED?")
    print("=" * 76)
    print()
    print(f"families x colours compared   {len(shared)}")
    print(f"strong games in them          {sum(strong[k].n for k in shared)}")
    print(f"subject games in them         {sum(subjects[k].n for k in shared)}")
    print()
    print("Completed openings only: an unfinished window has no length to")
    print("normalise by and no end to count up to.")
    print()

    for key, label, fmt in (("share", "pawn SHARE of opening moves", "{:.1%}"),
                            ("count", "pawn MOVE COUNT before ready", "{:.2f}"),
                            ("early", f"pawn moves in first {EARLY_PLIES // 2} moves "
                                      "(no censoring)", "{:.2f}"),
                            ("window", "opening window, moves", "{:.2f}"),
                            ("late", "LATE CASTLING rate", "{:.1%}"),
                            ("slow", "SLOW DEVELOPMENT rate", "{:.1%}"),
                            ("repeat", "REPEAT-MOVE share", "{:.1%}")):
        s_crude, u_crude = crude(strong, key), crude(subjects, key)
        s_std = standardised(strong, weights, key)
        u_std = standardised(subjects, weights, key)
        print("-" * 76)
        print(f"{label}")
        print(f"  crude          strong {fmt.format(s_crude):>8}   "
              f"subject {fmt.format(u_crude):>8}   "
              f"gap {fmt.format(u_crude - s_crude):>8}")
        print(f"  standardised   strong {fmt.format(s_std):>8}   "
              f"subject {fmt.format(u_std):>8}   "
              f"gap {fmt.format(u_std - s_std):>8}   <- same opening mix")

        diffs = [
            statistics.mean(getattr(subjects[k], key)) - statistics.mean(getattr(strong[k], key))
            for k in shared
        ]
        worse = sum(1 for d in diffs if d > 0)
        print(f"  within-opening median difference {fmt.format(statistics.median(diffs)):>8}"
              f"   subjects higher in {worse}/{len(diffs)} openings")
        print()

    print("=" * 76)
    print("PER OPENING, SUBJECT MINUS STRONG")
    print("=" * 76)
    print()
    print(f"{'opening':<30}{'side':<7}{'share':>9}{'count':>9}{'window':>9}")
    print("-" * 64)
    rows = sorted(
        shared,
        key=lambda k: statistics.mean(subjects[k].count) - statistics.mean(strong[k].count),
        reverse=True,
    )
    for k in rows:
        family, colour = k
        d_share = statistics.mean(subjects[k].share) - statistics.mean(strong[k].share)
        d_count = statistics.mean(subjects[k].count) - statistics.mean(strong[k].count)
        d_window = statistics.mean(subjects[k].window) - statistics.mean(strong[k].window)
        print(f"{family[:29]:<30}{'White' if colour else 'Black':<7}"
              f"{d_share:>+8.1%}{d_count:>+9.2f}{d_window:>+9.2f}")


if __name__ == "__main__":
    main()
