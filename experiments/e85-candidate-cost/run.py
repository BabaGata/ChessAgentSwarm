"""How many candidate moves would need an engine evaluation, and how many are free?

Note: docs/notes/experiments.e85-candidate-cost.md

[[design.punishment-validity]] proposes counting a punishment when *some* reply
within a win-probability window of the best executes the motif, rather than only
the single best reply. That needs an evaluation of each **candidate** -- a reply
that executes a motif -- and the design could only bound the cost between 8,000
and 80,000 evaluations, which is too wide to build on.

Three things shrink the bill, and this measures all three:

  1. **`detect_motifs` is already the static filter.** A move only becomes a
     candidate by passing the existing SEE checks -- `_lands_safely`,
     `_is_worth_winning`, `_loses_material_whatever_the_defender_does`. Nothing
     new has to be written to filter; the question is what fraction survives.
  2. **A motif the best reply already executes costs nothing.** Its evaluation is
     the best evaluation, which is already stored. Only motifs the best reply
     does *not* execute need a candidate priced.
  3. **The engine cache is keyed on position.** Repeated positions across players
     are paid for once, so the distinct count is the real bill.

No engine work beyond re-deriving observations, which the cache already holds.

    python run.py [--players N] [--corpus data/raw/corpus-blitz]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

import chess

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import Corpus  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402


def candidates(board: chess.Board) -> dict[chess.Move, frozenset[str]]:
    """Every legal reply that executes at least one motif, and which ones.

    This *is* stage one. A move reaches this dict only by passing the material
    checks the detectors already apply, so the survivor count is what the engine
    would have to price.
    """
    found: dict[chess.Move, frozenset[str]] = {}
    for move in board.legal_moves:
        motifs = detect_motifs(board, move)
        if motifs:
            found[move] = frozenset(m.value if hasattr(m, "value") else m for m in motifs)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=REPO / "data/raw/corpus-blitz")
    parser.add_argument("--players", type=int, default=12)
    parser.add_argument("--engine", default="stockfish")
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--cache", type=Path, default=REPO / "data/cache/peers.db")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    paths = sorted(args.corpus.glob("*.pgn"))[: args.players]
    if not paths:
        print(f"no PGNs in {args.corpus}")
        return 1

    legal_counts: list[int] = []
    candidate_counts: list[int] = []
    priced_counts: list[int] = []
    motif_free = Counter()
    motif_priced = Counter()
    distinct: set[tuple[str, str]] = set()
    errors = positions = 0

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in paths:
            games = load_games(path)
            corpus = Corpus(
                username=path.stem,
                corpus_id=f"e85-{path.stem}",
                game_ids=tuple(g.game_id for g in games),
            )
            observations = analyse_corpus(corpus, games, session.analyser)
            by_ply = {(o.game_id, o.ply): o for o in observations}

            for observation in observations:
                if observation.label is None or observation.mover.lower() != path.stem.lower():
                    continue
                errors += 1
                reply = by_ply.get((observation.game_id, observation.ply + 1))
                if reply is None or reply.best_move is None:
                    continue
                board = chess.Board(reply.fen_before)
                try:
                    best = chess.Move.from_uci(reply.best_move)
                except ValueError:
                    continue
                if best not in board.legal_moves:
                    continue

                positions += 1
                found = candidates(board)
                legal_counts.append(board.legal_moves.count())
                candidate_counts.append(len(found))

                # A motif the best reply already executes is free: its evaluation
                # *is* the best evaluation, and that is already on disk.
                free = found.get(best, frozenset())
                motif_free.update(free)

                needed = 0
                for move, motifs in found.items():
                    if move == best or motifs <= free:
                        continue
                    needed += 1
                    motif_priced.update(motifs - free)
                    distinct.add((reply.fen_before, move.uci()))
                priced_counts.append(needed)

        stats = session.cache_stats()

    def spread(values: list[int]) -> str:
        if not values:
            return "--"
        values = sorted(values)
        return (f"mean {statistics.mean(values):.1f}  median {statistics.median(values):.0f}  "
                f"p90 {values[min(len(values)-1, int(0.9*len(values)))]}  max {max(values)}")

    lines = [
        "HOW MANY CANDIDATES WOULD ACTUALLY NEED PRICING?",
        "=" * 84, "",
        f"  {len(paths)} players from {args.corpus.name}",
        f"  errors by the player                    {errors:,}",
        f"  of those, with a usable reply position  {positions:,}",
        "",
        "  Per error position:",
        f"    legal replies                         {spread(legal_counts)}",
        f"    executing a motif (survive stage 1)   {spread(candidate_counts)}",
        f"    still needing an engine call          {spread(priced_counts)}",
        "",
        f"  candidate moves total                   {sum(candidate_counts):,}",
        f"  of those, free (best reply's own)       {sum(candidate_counts) - sum(priced_counts):,}",
        f"  needing an evaluation                   {sum(priced_counts):,}",
        f"  distinct (position, move) to cache      {len(distinct):,}",
        "",
    ]
    if positions:
        per_error = len(distinct) / positions
        lines += [
            f"  distinct evaluations per error position {per_error:.2f}",
            "",
            "  Extrapolated to a full three-band reference rebuild:",
        ]
        for scale, label in ((20_600, "the blitz+rapid reference (~20,600 errors)"),
                             (41_200, "all three bands, overlapping (~2x)")):
            lines.append(f"    {label:<44} {scale * per_error:>10,.0f} evaluations")
    if stats:
        lines += ["", f"  cache {stats.hits:,}/{stats.lookups:,} hits, {stats.rows:,} rows"]

    lines += ["", "  Motifs the best reply already executes (free):"]
    for motif, n in motif_free.most_common():
        lines.append(f"    {motif:<24}{n:>8,}")
    lines += ["", "  Motifs only a non-best candidate executes (must be priced):"]
    for motif, n in motif_priced.most_common():
        lines.append(f"    {motif:<24}{n:>8,}")
    lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "candidates.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
