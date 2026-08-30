"""What the habit's own moves actually cost, summed across the opening.

Design: docs/notes/design.opening-development-signals.md

The author, rejecting an end-of-opening measure:

    "Maybe calculating the cumulative cost that happened during the opening
    would be good option. In the games of weaker players they don't have to
    eventually end opening worse because their opponent also plays badly. Maybe
    combining cost of the moves when the same piece was moved repeatedly instead
    of developing the other piece, combining the cost of every pawn move when
    the piece should be developed instead and combining the cost for every move
    when the player should castle the king but he did something else."

**The objection is correct and kills the alternative.** Two weak players' errors
cancel, so a position that ends the opening level says nothing about how badly
it was played. Per-move attribution never touches the opponent's play.

It also matches the arbiter's own cost model exactly -- win probability lost on
the moves a claim names -- so the number is directly comparable with every other
claim rather than being a second currency.

**The screen that decides whether it is real.** A habit cost is only a finding if
it is not just the player's general error rate re-labelled: someone who errs more
will err more on pawn moves too. So the cost is reported beside the same player's
overall opening error rate, and the correlation between them is the number that
matters -- E10's screen, which closed a section slot at +0.917.

    python habit_cost.py --engine PATH [--cache PATH]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.opening_development import _is_theory, developments  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402

CORPUS = Path(__file__).resolve().parents[2] / "data" / "raw" / "corpus-rapid"

HABITS = (
    ("repeat", "repeat_instead_of_developing"),
    ("pawn", "pawn_instead_of_developing"),
    ("no_castle", "declined_available_castle"),
)


def costs_for(observations, username, book, skip_theory: bool = True):
    """Per-game cost of each habit, and the player's overall opening cost.

    `skip_theory` is the author's gambit guard: a move the book still names is
    not the player's own choice, so it is not charged to them. Reported both
    ways because the guard's SIZE is the interesting number -- if it changes
    nothing, gambits are too rare here to matter; if it changes a lot, the
    unguarded figures were partly measuring who plays sharp openings.
    """
    played = developments(observations, username, book)
    if not played:
        return None

    totals = {name: 0.0 for name, _ in HABITS}
    counts = {name: 0 for name, _ in HABITS}
    opening_loss = 0.0
    opening_moves = 0
    opening_errors = 0
    pawn_opportunities = pawn_errors = 0

    for game in played:
        by_ply = {o.ply: o for o in game.mine}
        for window_move in game.development.window_moves:
            observation = by_ply.get(window_move.ply)
            if observation is None:
                continue
            opening_moves += 1
            opening_loss += observation.loss_wp
            opening_errors += int(observation.is_error)
            if skip_theory and _is_theory(game, window_move.ply):
                continue
            if window_move.pawn_instead_of_developing:
                pawn_opportunities += 1
                pawn_errors += int(observation.is_error)
            for name, attribute in HABITS:
                if getattr(window_move, attribute):
                    totals[name] += observation.loss_wp
                    counts[name] += 1

    games = len(played)
    return {
        "games": games,
        "per_game": {name: totals[name] / games for name, _ in HABITS},
        "share_of_opening_loss": {
            name: (totals[name] / opening_loss if opening_loss else 0.0)
            for name, _ in HABITS
        },
        "moves": counts,
        "opening_loss_per_game": opening_loss / games,
        "opening_error_rate": opening_errors / opening_moves if opening_moves else 0.0,
        "pawn_error_rate": (pawn_errors / pawn_opportunities
                            if pawn_opportunities else None),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--players", type=int, default=40)
    args = parser.parse_args()

    book = OpeningBook.load()
    rows = []
    unguarded = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(CORPUS.glob("*.pgn"))[: args.players]:
            games = load_games(path)[: args.window]
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            guarded = costs_for(observations, path.stem, book, skip_theory=True)
            raw = costs_for(observations, path.stem, book, skip_theory=False)
            if guarded and raw:
                rows.append((path.stem, guarded))
                unguarded.append((path.stem, raw))
                print(f"  {path.stem}: {guarded['games']} games", flush=True)

    print()
    print("WHAT EACH HABIT COSTS, IN WIN PROBABILITY PER GAME")
    print("=" * 74)
    print()
    print(f"players measured  {len(rows)}")
    print()
    print("Summed loss_wp over the moves the habit names -- the arbiter's own")
    print("cost model, so these are comparable with every other claim.")
    print()
    print(f"{'habit':<14}{'median':>9}{'p90':>9}{'max':>9}"
          f"{'share of opening loss':>24}")
    print("-" * 66)
    for name, _ in HABITS:
        per_game = [r[1]["per_game"][name] for r in rows]
        share = [r[1]["share_of_opening_loss"][name] for r in rows]
        print(f"{name:<14}{statistics.median(per_game):>9.3f}"
              f"{statistics.quantiles(per_game, n=10)[-1]:>9.3f}"
              f"{max(per_game):>9.3f}"
              f"{statistics.median(share):>23.0%}")

    print()
    print("The author's gambit guard: a move the book still names is theory,")
    print("not the player's mistake. What excluding it changes:")
    print()
    print(f"{'habit':<14}{'unguarded':>11}{'guarded':>10}{'change':>10}")
    print("-" * 45)
    for name, _ in HABITS:
        before = statistics.median([r[1]["per_game"][name] for r in unguarded])
        after = statistics.median([r[1]["per_game"][name] for r in rows])
        pct = (after - before) / before if before else 0.0
        print(f"{name:<14}{before:>11.3f}{after:>10.3f}{pct:>9.0%}")

    print()
    print("And the pawn claim as a RATE OF ERROR rather than a rate of pawn")
    print("moves -- the question E59's dropped claim could not ask:")
    print()
    pawn_rates = [r[1]["pawn_error_rate"] for r in rows
                  if r[1]["pawn_error_rate"] is not None]
    if pawn_rates:
        qs = statistics.quantiles(pawn_rates, n=10)
        print(f"  pawn moves that were errors: p10 {qs[0]:.0%}  "
              f"median {statistics.median(pawn_rates):.0%}  p90 {qs[-1]:.0%}  "
              f"spread {qs[-1] - qs[0]:.0%}")
        errs = [r[1]["opening_error_rate"] for r in rows
                if r[1]["pawn_error_rate"] is not None]
        print(f"  r with the overall opening error rate: "
              f"{statistics.correlation(pawn_rates, errs):.2f}")

    total = [sum(r[1]["per_game"][n] for n, _ in HABITS) for r in rows]
    overall = [r[1]["opening_loss_per_game"] for r in rows]
    print()
    print(f"{'ALL THREE':<14}{statistics.median(total):>9.3f}"
          f"{statistics.quantiles(total, n=10)[-1]:>9.3f}{max(total):>9.3f}")
    print(f"{'whole opening':<14}{statistics.median(overall):>9.3f}"
          f"{statistics.quantiles(overall, n=10)[-1]:>9.3f}{max(overall):>9.3f}")

    print()
    print("=" * 74)
    print("IS THIS JUST THE GENERAL ERROR RATE WEARING A HABIT'S NAME?")
    print("=" * 74)
    print()
    print("A player who errs more errs more on pawn moves too. If a habit cost")
    print("tracks the overall opening error rate it carries no new information,")
    print("which is what closed a section slot in E10 at +0.917.")
    print()
    error_rate = [r[1]["opening_error_rate"] for r in rows]
    print(f"{'habit':<14}{'r with opening error rate':>28}")
    print("-" * 44)
    for name, _ in HABITS:
        per_game = [r[1]["per_game"][name] for r in rows]
        print(f"{name:<14}{statistics.correlation(per_game, error_rate):>28.2f}")
    print(f"{'ALL THREE':<14}{statistics.correlation(total, error_rate):>28.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
