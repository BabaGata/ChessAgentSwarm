"""E11 — which attack-and-defence claims could S8 actually make?

Third outing for the screen, and the first designed around both questions:

  * **L-023** — does the candidate vary between players at all?
  * **L-025** — does it survive dividing out what we already measure? A candidate
    can spread handsomely and still be the overall error rate wearing a better
    name, which is how S7 nearly got built.

And with **L-024** as a prior: candidates framed as *what the opponent achieved*
have discriminated (outposts 2.15, rooks on the seventh 1.82) where candidates
framed as *what the position contains* have not (holes 1.25, bad bishop 1.27).
So the headline candidate here is what the opponent gets **at the player's king**,
and a king-shape candidate is carried alongside it as the control.

Candidates:

    allows_king_pressure   the opponent's reply brings a third attacker to bear
                           on the squares round the player's king
    shield_broken          the player's castled king has lost its pawn cover
                           (a state -- the control, expected to fail)
    errs_under_pressure    error rate while the king is already under pressure
    errs_safe              error rate while it is not
    pressure_penalty       the ratio of those two, per player -- the contrast,
                           which is what the section would actually claim

Usage:
    python run.py --pgn DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

CANDIDATES = ("allows_king_pressure", "shield_broken", "errs_under_pressure", "errs_safe")

# Three attackers on the king zone is the conventional point where an attack
# stops being an inconvenience. Two is enough to call a king "under pressure"
# for the purpose of splitting error rates.
PRESSURE_ATTACKERS = 3
UNDER_PRESSURE_ATTACKERS = 2

MIN_OPPORTUNITIES = 40


def king_zone(board: chess.Board, colour: chess.Color) -> list[int]:
    """The king's square and everything touching it."""
    king = board.king(colour)
    if king is None:
        return []
    file_, rank = chess.square_file(king), chess.square_rank(king)
    squares = []
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            f, r = file_ + df, rank + dr
            if 0 <= f <= 7 and 0 <= r <= 7:
                squares.append(chess.square(f, r))
    return squares


def zone_attackers(board: chess.Board, colour: chess.Color) -> int:
    """How many distinct enemy pieces bear on the squares round `colour`'s king."""
    enemy = not colour
    attackers: set[int] = set()
    for square in king_zone(board, colour):
        attackers |= set(board.attackers(enemy, square))
    return len(attackers)


def shield_broken(board: chess.Board, colour: chess.Color) -> bool:
    """Fewer than two friendly pawns covering the three files in front of the king.

    Only counted once the king has actually castled somewhere off the centre --
    a king still on e1 has no shield to lose and would otherwise register as
    permanently broken.
    """
    king = board.king(colour)
    if king is None:
        return False
    file_ = chess.square_file(king)
    if 2 < file_ < 5:
        return False

    rank = chess.square_rank(king)
    ahead = range(rank + 1, min(rank + 3, 8)) if colour == chess.WHITE else range(max(rank - 2, 0), rank)
    cover = 0
    for f in (file_ - 1, file_, file_ + 1):
        if not 0 <= f <= 7:
            continue
        for r in ahead:
            piece = board.piece_at(chess.square(f, r))
            if piece and piece.piece_type == chess.PAWN and piece.color == colour:
                cover += 1
                break
    return cover < 2


def screen(observations, player: str) -> dict[str, tuple[int, int]]:
    tally: Counter[str] = Counter()
    by_ply = {(o.game_id, o.ply): o for o in observations}
    mine = tuple(o for o in observations if o.mover.lower() == player.lower())

    for observation in diagnosable(mine):
        colour = chess.WHITE if observation.mover_is_white else chess.BLACK
        board = chess.Board(observation.fen_before)
        before = zone_attackers(board, colour)
        erred = observation.label is not None

        tally["shield_broken.opportunities"] += 1
        if shield_broken(board, colour):
            tally["shield_broken.instances"] += 1

        # Splitting the player's error rate by whether the king was already
        # under pressure. The ratio of these two is the real candidate (L-025).
        bucket = (
            "errs_under_pressure" if before >= UNDER_PRESSURE_ATTACKERS else "errs_safe"
        )
        tally[f"{bucket}.opportunities"] += 1
        if erred:
            tally[f"{bucket}.instances"] += 1

        # What the opponent achieves, judged across their reply (E09's lesson:
        # a concession is realised on the other side's move).
        answered = by_ply.get((observation.game_id, observation.ply + 2))
        if answered is None:
            continue
        after = zone_attackers(chess.Board(answered.fen_before), colour)
        tally["allows_king_pressure.opportunities"] += 1
        if after >= PRESSURE_ATTACKERS > before:
            tally["allows_king_pressure.instances"] += 1

    return {
        name: (tally[f"{name}.instances"], tally[f"{name}.opportunities"])
        for name in CANDIDATES
    }


def _spread(rates: list[float]) -> tuple[float, float, float, float]:
    rates = sorted(rates)
    median = statistics.median(rates)
    p10 = rates[int(0.10 * (len(rates) - 1))]
    p90 = rates[int(0.90 * (len(rates) - 1))]
    return median, p10, p90, (p90 / median if median else float("inf"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    args = parser.parse_args()

    per_candidate: dict[str, list[float]] = {}
    opportunities: dict[str, list[int]] = {}
    by_player: dict[str, dict[str, float]] = {}

    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"screening {len(paths)} players at depth {args.depth}\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            games = parse_pgn_file(path)
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)

            rates = {}
            for name, (instances, chances) in screen(observations, path.stem).items():
                if chances < MIN_OPPORTUNITIES:
                    continue
                rates[name] = instances / chances
                per_candidate.setdefault(name, []).append(rates[name])
                opportunities.setdefault(name, []).append(chances)
            by_player[path.stem] = rates
            print(f"  {index:>2}/{len(paths)} {path.stem}", flush=True)

    print(f"\n{'candidate':<22} {'n':>3} {'median':>8} {'p10':>7} {'p90':>7} "
          f"{'p90/med':>8} {'opps':>6}")
    for name, rates in sorted(per_candidate.items()):
        median, p10, p90, spread = _spread(rates)
        print(f"{name:<22} {len(rates):>3} {median:>8.4f} {p10:>7.4f} {p90:>7.4f} "
              f"{spread:>8.2f} {statistics.median(opportunities[name]):>6.0f}")

    # L-025 applied *between* candidates rather than against the error rate:
    # a broken shield and an opponent massing on the king may simply be one
    # phenomenon described twice, in which case only one of them is a claim.
    both = [
        (r["allows_king_pressure"], r["shield_broken"])
        for r in by_player.values()
        if "allows_king_pressure" in r and "shield_broken" in r
    ]
    if len(both) >= 3:
        r = statistics.correlation([p for p, _ in both], [s for _, s in both])
        print(f"\ncorr(allows_king_pressure, shield_broken) over {len(both)} players   r = {r:+.3f}")
        print("  high = one phenomenon described twice, so at most one is a claim")

    # L-025: the contrast, not the rate.
    paired = [
        (r["errs_under_pressure"], r["errs_safe"])
        for r in by_player.values()
        if r.get("errs_safe") and "errs_under_pressure" in r
    ]
    if len(paired) >= 3:
        r = statistics.correlation([u for u, _ in paired], [s for _, s in paired])
        penalties = [u / s for u, s in paired]
        median, p10, p90, spread = _spread(penalties)
        print(f"\ncorr(errs_under_pressure, errs_safe) over {len(paired)} players   r = {r:+.3f}")
        print(f"pressure_penalty  n={len(penalties)}  median {median:.2f}  "
              f"p10 {p10:.2f}  p90 {p90:.2f}  spread {spread:.2f}")

    print(
        "\nfor scale — discriminating: concedes_outpost 2.15 · early_error.black 1.92\n"
        "            not:            concedes_hole 1.25 · quiet_penalty 1.27"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
