"""Real fork positions, for the author to read.

The rebuilt detector fires **zero** times in S1's claim populations
([[experiments.e57-fork-rebuilt]]), which is either the correction working or
the rule being unreachable. Waiting for an S1 population to produce one settles
nothing cheaply; scanning played moves produces the same detector's own
positives in seconds and costs no engine time.

Every position below is a move somebody actually played in the review corpus,
on which `_is_fork` fires. If they are forks, the rule is right and the zero is
the populations being narrow. If they are not, the rule is still wrong.

    python experiments/e57-fork-rebuilt/sample.py > results/fork-sample.txt
"""

from __future__ import annotations

import pathlib
import random
import sys

import chess
import chess.pgn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.tactics import _is_fork  # noqa: E402

CORPUS = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw" / "corpus-rapid"
WANTED = 15
SEED = 20260829


def diagram(board: chess.Board) -> str:
    """The board as the author reads it, White at the bottom, with file letters."""
    rows = str(board).splitlines()
    numbered = [f"  {8 - i}  {row}" for i, row in enumerate(rows)]
    return "\n".join(numbered) + "\n\n     a b c d e f g h"


def forks_in(game: chess.pgn.Game):
    board = game.board()
    for move in game.mainline_moves():
        mover = board.turn
        before = board.copy(stack=False)
        after = board.copy(stack=False)
        after.push(move)
        if _is_fork(before, after, move, mover):
            yield before, move, board.fullmove_number, mover
        board.push(move)


def main() -> None:
    found = []
    files = sorted(CORPUS.glob("*.pgn"))
    scanned = 0
    for path in files:
        with path.open(encoding="utf-8", errors="replace") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                scanned += 1
                try:
                    for hit in forks_in(game):
                        found.append((path.stem, game.headers.get("Site", "?"), *hit))
                except (ValueError, AssertionError):
                    continue  # a malformed game is not a measurement

    random.Random(SEED).shuffle(found)
    sample = found[:WANTED]

    print("FORKS THE REBUILT DETECTOR FIRES ON")
    print("=" * 72)
    print()
    print(f"games scanned            {scanned}")
    print(f"forks found on played moves  {len(found)}")
    print(f"shown below (seed {SEED})    {len(sample)}")
    print()
    print("Mark each one:  [y] a fork   [n] not a fork   [?] cannot tell")
    print()
    print("If most are [y], the rule is right and the zero in S1 is its")
    print("populations being narrow. If most are [n], the rule is still wrong.")
    print()

    for i, (player, site, board, move, number, mover) in enumerate(sample, 1):
        san = board.san(move)
        colour = "White" if mover == chess.WHITE else "Black"
        print("=" * 72)
        print(f"[ ]  {i}.  {colour} plays {number}{'.' if mover else '...'}{san}"
              f"   ({player}, {site})")
        print()
        print(diagram(board))
        print()
        print(f"     FEN  {board.fen()}")
        print()


if __name__ == "__main__":
    main()
