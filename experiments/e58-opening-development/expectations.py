"""The expectation, built from players who know the openings.

Design: docs/notes/design.opening-development-signals.md

    "I don't want this to be built by peer reference but by better players who
    usually know the opening... The expected moves are not going to be the exact
    average or median of the higher ranked players but average/median + 1/2."

Three questions, and the claim cannot be wired up until all three are answered:

1. **Does the strong corpus cover the openings the subjects actually play?**
   Elite repertoires are not 1600 repertoires, and an expectation that is thin
   exactly where it is needed would push every subject onto the own-median
   fallback.
2. **What does the tolerance have to be?** A threshold at the median flags half
   of the population it came from, by definition. The tolerance is calibrated by
   asking what share of the STRONG players' own games each setting flags -- they
   are a known-good population, so that share is a direct read of the false
   positives.
3. **Do strong players differ from the review corpus at all?** If they castle
   when 1600s castle there is nothing here to teach.

    python experiments/e58-opening-development/expectations.py > results/expectations.txt
"""

from __future__ import annotations

import pathlib
import statistics
import sys
from collections import defaultdict

import chess

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.development import measure_development  # noqa: E402
from chesscoach.openings import OpeningBook, _family  # noqa: E402
from derive import Norms, move_number, read_corpus  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
STRONG = ROOT / "data" / "raw" / "corpus-strong"
SUBJECTS = ROOT / "data" / "raw" / "corpus-rapid"

# Below this a median is a coincidence rather than a norm.
MIN_GAMES = 20

# The settings the author named, in moves. Measured, not chosen.
TOLERANCES = (0, 1, 2)

# The share of a KNOWN-GOOD population a threshold may flag before it is
# measuring something other than knowing the opening. Anchored the same way
# PRECISION_FLOOR is in E55: on a population whose answer is already known.
FALSE_POSITIVE_CEILING = 0.25


def norms_for(directory: pathlib.Path, book: OpeningBook):
    """Per (family, colour) numbers for one corpus."""
    cells: dict[tuple[str, bool], Norms] = defaultdict(Norms)
    games = 0
    for _game, played in read_corpus(directory):
        games += 1
        walk = book.walk([m.uci() for m in played])
        if walk.opening is None:
            continue
        family = _family(walk.opening.name)
        for colour in (chess.WHITE, chess.BLACK):
            cells[(family, colour)].add(measure_development(played, colour),
                                        walk.plies_in_book)
    return cells, games


def flagged_share(cell: Norms, threshold_ply: float, which: str) -> float | None:
    """Share of this cell's games that a threshold would call late.

    A game that never got there counts as late -- not reaching the threshold at
    all is the most extreme way of being past it, and dropping those games is
    the censoring E58 already fell into once.
    """
    reached = cell.castled if which == "castle" else cell.developed
    never = cell.never_castled if which == "castle" else cell.incomplete
    total = len(reached) + never
    if total == 0:
        return None
    late = sum(1 for ply in reached if ply > threshold_ply) + never
    return late / total


def main() -> None:
    book = OpeningBook.load()

    print("THE EXPECTATION, FROM PLAYERS WHO KNOW THE OPENINGS")
    print("=" * 78)
    print()

    strong, strong_games = norms_for(STRONG, book)
    subjects, subject_games = norms_for(SUBJECTS, book)
    print(f"strong corpus    {strong_games:5} games, "
          f"{len({f for f, _ in strong})} families")
    print(f"subject corpus   {subject_games:5} games, "
          f"{len({f for f, _ in subjects})} families")
    print()

    # ---- 1. coverage -------------------------------------------------------
    print("=" * 78)
    print("1. DOES THE STRONG CORPUS COVER WHAT THE SUBJECTS PLAY?")
    print("=" * 78)
    print()
    print("Every subject family with 20+ subject games, and whether the strong")
    print("corpus has 20+ of its own to build an expectation from.")
    print()
    print(f"{'opening':<32}{'subject':>9}{'strong':>8}   expectation")
    print("-" * 78)

    subject_families = sorted(
        {f for f, _ in subjects if subjects[(f, chess.WHITE)].games >= MIN_GAMES},
        key=lambda f: -subjects[(f, chess.WHITE)].games,
    )
    covered = uncovered = covered_games = uncovered_games = 0
    for family in subject_families:
        n_sub = subjects[(family, chess.WHITE)].games
        n_str = strong[(family, chess.WHITE)].games
        ok = n_str >= MIN_GAMES
        if ok:
            covered += 1
            covered_games += n_sub
        else:
            uncovered += 1
            uncovered_games += n_sub
        print(f"{family[:31]:<32}{n_sub:>9}{n_str:>8}   "
              f"{'yes' if ok else 'NO -- own-median fallback'}")

    total_games = covered_games + uncovered_games
    print()
    print(f"  {covered} of {covered + uncovered} families covered, carrying "
          f"{covered_games / total_games:.0%} of subject games")
    print(f"  {uncovered} fall back to the player's own median, carrying "
          f"{uncovered_games / total_games:.0%}")

    # ---- 2. tolerance ------------------------------------------------------
    print()
    print("=" * 78)
    print("2. WHAT MUST THE TOLERANCE BE?")
    print("=" * 78)
    print()
    print("A threshold at the median flags half of the population it came from,")
    print("by construction. Below: the share of the STRONG players' OWN games")
    print("each setting calls late. They know the openings, so this is a direct")
    print(f"read of the false-positive rate. Target <= {FALSE_POSITIVE_CEILING:.0%}.")
    print()
    print(f"{'':<20}{'castling':>26}{'development':>26}")
    print(f"{'tolerance':<20}" + "".join(f"{t:>13}" for t in TOLERANCES) * 2)
    print("-" * 72)

    def sweep(which: str) -> list[float]:
        out = []
        for tolerance in TOLERANCES:
            shares = []
            for (family, colour), cell in strong.items():
                if cell.games < MIN_GAMES:
                    continue
                base = (cell.median_castle() if which == "castle"
                        else cell.median_develop())
                if base is None:
                    continue
                share = flagged_share(cell, base + 2 * tolerance, which)
                if share is not None:
                    shares.append(share)
            out.append(statistics.mean(shares) if shares else float("nan"))
        return out

    castle_sweep, develop_sweep = sweep("castle"), sweep("develop")
    print(f"{'flagged, strong':<20}"
          + "".join(f"{s:>12.0%} " for s in castle_sweep)
          + "".join(f"{s:>12.0%} " for s in develop_sweep))
    print()
    for label, sweep_result in (("castling", castle_sweep), ("development", develop_sweep)):
        passing = [t for t, s in zip(TOLERANCES, sweep_result)
                   if s == s and s <= FALSE_POSITIVE_CEILING]
        verdict = (f"+{passing[0]} is the smallest that clears the ceiling"
                   if passing else "NO setting clears the ceiling")
        print(f"  {label:<14}{verdict}")

    # ---- 3. is there a gap at all? ----------------------------------------
    print()
    print("=" * 78)
    print("3. DO STRONG PLAYERS ACTUALLY DIFFER FROM THE SUBJECTS?")
    print("=" * 78)
    print()
    print("If they castle when 1600s castle there is nothing here to teach.")
    print("Median move number, strong vs subject, White then Black.")
    print()
    print(f"{'opening':<30}{'side':<7}{'strong':>8}{'subject':>9}{'gap':>6}"
          f"{'  strong pawn':>14}{'subj pawn':>11}")
    print("-" * 86)

    gaps = []
    for family in subject_families:
        for colour in (chess.WHITE, chess.BLACK):
            s_cell, u_cell = strong[(family, colour)], subjects[(family, colour)]
            if s_cell.games < MIN_GAMES:
                continue
            s_med, u_med = s_cell.median_castle(), u_cell.median_castle()
            if s_med is None or u_med is None:
                continue
            gap = move_number(u_med) - move_number(s_med)
            gaps.append(gap)
            print(f"{family[:29]:<30}{'White' if colour else 'Black':<7}"
                  f"{move_number(s_med):>8}{move_number(u_med):>9}{gap:>+6}"
                  f"{statistics.mean(s_cell.pawn_rates):>14.0%}"
                  f"{statistics.mean(u_cell.pawn_rates):>11.0%}")

    if gaps:
        print()
        print(f"  median gap {statistics.median(gaps):+.1f} moves over {len(gaps)} cells; "
              f"subjects later in {sum(1 for g in gaps if g > 0)} of them")


if __name__ == "__main__":
    main()
