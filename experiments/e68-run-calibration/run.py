"""How long a run has to be before it means anything.

Design: docs/notes/design.detectors-name-consequences.md § 6

    "Endgame error should be calculated just when there are big drops of the
    advantage in a few consecutive moves. So that it can be seen that the player
    is imprecise one move after the other."

E67 shipped the design note's first proposal -- 3 drops within 4 moves -- and
the note promised to settle it against "how often runs of each length occur in
the corpus". This is that measurement, and it asks a sharper question than
frequency.

**A player who errs often will produce runs by chance.** If three-in-a-row
happens no more often than independent errors at that player's own rate would
produce, then the run condition is measuring the error rate wearing a different
name -- which is what closed a section slot in E10, and exactly what the claim
must not be.

So the baseline is a **permutation test**: keep each player's endgame moves and
their number of errors, shuffle WHICH moves erred, and count runs again. That
holds the error rate fixed by construction and destroys only the clustering, so
the gap between observed and shuffled is the clustering and nothing else.

    python run.py --engine PATH [--cache PATH] [--shuffles 200]
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext, diagnosable  # noqa: E402
from chesscoach.sections.s3_endgame_technique import _is_tactical  # noqa: E402

REVIEW = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# (run length, window). The shipped pair is (3, 4).
SETTINGS = ((2, 2), (2, 3), (3, 3), (3, 4), (3, 5), (4, 4), (4, 5), (4, 6))


def runs_in(flags: list[bool], length: int, window: int) -> int:
    """Moves belonging to a run of `length` errors inside `window` moves."""
    losing = [i for i, erred in enumerate(flags) if erred]
    found: set[int] = set()
    for start in range(len(losing) - length + 1):
        chunk = losing[start:start + length]
        if chunk[-1] - chunk[0] < window:
            found |= set(chunk)
    return len(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--shuffles", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260831)
    args = parser.parse_args()

    # Per game: the sequence of "this endgame move erred and was not tactical".
    games_flags: list[list[bool]] = []
    players = 0
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(REVIEW.glob("*.pgn")):
            games = load_games(path)[: args.window]
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id)
            )
            players += 1
            by_game: dict[str, list] = {}
            for observation in diagnosable(context.player_observations()):
                if observation.phase == "endgame":
                    by_game.setdefault(observation.game_id, []).append(observation)
            for played in by_game.values():
                played.sort(key=lambda o: o.ply)
                games_flags.append([
                    o.label is not None and not _is_tactical(o) for o in played
                ])
            print(f"  {path.stem}: {len(by_game)} endgame games", flush=True)

    total_moves = sum(len(f) for f in games_flags)
    total_errors = sum(sum(f) for f in games_flags)
    print()
    print("HOW LONG A RUN HAS TO BE")
    print("=" * 78)
    print()
    print(f"players            {players}")
    print(f"endgame games      {len(games_flags)}")
    print(f"endgame moves      {total_moves}")
    print(f"non-tactical drops {total_errors}  ({total_errors / max(total_moves, 1):.0%})")
    print()
    print("Observed runs against a permutation baseline: the same moves and the")
    print("same number of errors, shuffled within each game. The baseline holds")
    print("the error rate fixed and destroys only the clustering, so the gap is")
    print("the clustering and nothing else.")
    print()
    print(f"{'run/window':<14}{'observed':>10}{'by chance':>12}{'ratio':>8}"
          f"{'above chance':>14}")
    print("-" * 58)

    rng = random.Random(args.seed)
    for length, window in SETTINGS:
        observed = sum(runs_in(f, length, window) for f in games_flags)

        shuffled = []
        for _ in range(args.shuffles):
            total = 0
            for flags in games_flags:
                copy = list(flags)
                rng.shuffle(copy)
                total += runs_in(copy, length, window)
            shuffled.append(total)
        expected = statistics.mean(shuffled)
        ratio = observed / expected if expected else float("inf")
        # How often chance alone produced at least what was observed.
        above = sum(1 for s in shuffled if s >= observed) / len(shuffled)
        print(f"{f'{length} in {window}':<14}{observed:>10}{expected:>12.1f}"
              f"{ratio:>8.2f}{above:>13.0%}")

    print()
    print("`ratio` near 1.00 means the setting finds no more clustering than a")
    print("player's own error rate produces on its own -- it would be measuring")
    print("how often they err, which S3 already reports, and not whether the")
    print("errors come one after another.")
    print()
    print("`above chance` is the share of shuffles that matched or beat the real")
    print("games. Small is good: it is the chance of seeing this much clustering")
    print("if the drops were independent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
