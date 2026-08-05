"""E10 — which calculation claims could S7 actually make?

E09's pattern, second outing: screen the candidates against real players before
writing the section (L-023). Unlike E09 this one cannot be engine-free — every
candidate needs the engine's preferred move and an error label — but the cache is
warm, so it is still minutes rather than hours.

The idea S7 rests on is a **contrast**, not a rate. Everyone errs; the question is
whether a player errs *more when the answer is quiet than when it is forcing*.
A check or a capture announces itself, and a quiet move has to be found — so the
gap between those two rates is as close to "calculation" as game records get.

Candidates:

    missed_quiet      error rate where the best move is quiet
    missed_forcing    error rate where the best move is forcing (the control)
    forcing_reflex    played a forcing move where the best one was quiet
    quiet_penalty     missed_quiet / missed_forcing, per player -- the contrast
                      itself, which is the thing the section would actually claim

L-024 says claims about what the opponent achieves discriminate and claims about
what the position contains do not. These are neither: they are about the player's
own choices, like S1's `missed_motif`, which fires readily. Whether that third
category behaves like the first or the second is exactly what this measures.

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

CANDIDATES = ("missed_quiet", "missed_forcing", "forcing_reflex")

MIN_OPPORTUNITIES = 40


def is_forcing(board: chess.Board, move: chess.Move) -> bool:
    """A move that announces itself: a capture, a check, or a promotion.

    Deliberately crude. The point is not a theory of forcing moves but the split
    an improving player is told to make -- "checks, captures, threats" -- so the
    measure should use their categories, not a better one.
    """
    return bool(
        board.is_capture(move) or move.promotion is not None or board.gives_check(move)
    )


def _legal(board: chess.Board, uci: str | None) -> chess.Move | None:
    if not uci:
        return None
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return None
    return move if move in board.legal_moves else None


def screen(observations, player: str) -> dict[str, tuple[int, int]]:
    tally: Counter[str] = Counter()
    mine = tuple(o for o in observations if o.mover.lower() == player.lower())

    for observation in diagnosable(mine):
        board = chess.Board(observation.fen_before)
        best = _legal(board, observation.best_move)
        played = _legal(board, observation.move_played)
        if best is None:
            continue

        quiet_best = not is_forcing(board, best)
        erred = observation.label is not None

        if quiet_best:
            tally["missed_quiet.opportunities"] += 1
            tally["forcing_reflex.opportunities"] += 1
            if erred:
                tally["missed_quiet.instances"] += 1
            if played is not None and is_forcing(board, played):
                tally["forcing_reflex.instances"] += 1
        else:
            tally["missed_forcing.opportunities"] += 1
            if erred:
                tally["missed_forcing.instances"] += 1

    return {
        name: (tally[f"{name}.instances"], tally[f"{name}.opportunities"])
        for name in CANDIDATES
    }


def report(per_candidate: dict[str, list[float]], opportunities: dict[str, list[int]]) -> None:
    print(f"\n{'candidate':<18} {'n':>3} {'median':>8} {'p10':>7} {'p90':>7} "
          f"{'p90/med':>8} {'opps':>6}")
    for name, rates in sorted(per_candidate.items()):
        rates = sorted(rates)
        median = statistics.median(rates)
        p10 = rates[int(0.10 * (len(rates) - 1))]
        p90 = rates[int(0.90 * (len(rates) - 1))]
        spread = p90 / median if median else float("inf")
        print(f"{name:<18} {len(rates):>3} {median:>8.4f} {p10:>7.4f} {p90:>7.4f} "
              f"{spread:>8.2f} {statistics.median(opportunities[name]):>6.0f}")


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
    penalties: list[float] = []

    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"screening {len(paths)} players at depth {args.depth}\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            games = parse_pgn_file(path)
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            counts = screen(observations, path.stem)

            rates = {}
            for name, (instances, chances) in counts.items():
                if chances < MIN_OPPORTUNITIES:
                    continue
                rate = instances / chances
                rates[name] = rate
                per_candidate.setdefault(name, []).append(rate)
                opportunities.setdefault(name, []).append(chances)
            by_player[path.stem] = rates

            if rates.get("missed_forcing"):
                penalties.append(rates["missed_quiet"] / rates["missed_forcing"])
            print(f"  {index:>2}/{len(paths)} {path.stem}", flush=True)

    report(per_candidate, opportunities)

    # The decisive question. `missed_quiet` spreading is only interesting if it
    # is *not* the player's overall error rate wearing a new name. If quiet and
    # forcing rates move together across players, the claim restates what S1 and
    # S2 already measure -- the L-014 failure, where `allowed_motif` divided by
    # all moves and tracked how often the player erred at all.
    paired = [
        (rates["missed_quiet"], rates["missed_forcing"])
        for rates in by_player.values()
        if "missed_quiet" in rates and "missed_forcing" in rates
    ]
    if len(paired) >= 3:
        r = statistics.correlation([q for q, _ in paired], [f for _, f in paired])
        print(f"\ncorr(missed_quiet, missed_forcing) over {len(paired)} players   r = {r:+.3f}")
        print("  high = the same players err at both, so this is error rate, not calculation")

    if penalties:
        ordered = sorted(penalties)
        median = statistics.median(ordered)
        p90 = ordered[int(0.90 * (len(ordered) - 1))]
        print(f"\nquiet_penalty (missed_quiet / missed_forcing), per player")
        print(f"  n={len(ordered)}  median {median:.2f}  "
              f"p10 {ordered[int(0.10 * (len(ordered) - 1))]:.2f}  p90 {p90:.2f}  "
              f"spread {p90 / median:.2f}")

    print(
        "\nfor scale — discriminating: concedes_outpost 2.15 · early_error.black 1.92\n"
        "            not:            concedes_hole 1.25 · concedes_weakness.any 1.24"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
