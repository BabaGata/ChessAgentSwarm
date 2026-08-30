"""Real positions where `pawn_error` fired, for the author to read.

Design: docs/notes/design.opening-development-signals.md
Evidence: docs/notes/experiments.e61-habit-cost.md

Every number about this claim so far is a count. **No instance has been read by
a person**, which is the same debt the fork sample is waiting on, and the same
debt that L-046's six instances were all found by paying.

The claim says: *of the pawn moves you played instead of developing, this one
went wrong.* Three things have to be true of each position below, and a person
is the only instrument that can check the third:

1. it really was a pawn move;
2. a minor really was still at home -- the "instead of developing" condition;
3. **developing would actually have been better** -- which is the claim's whole
   content and is a chess judgement.

The engine's own best move is printed beside each one, because if the engine
also wanted a pawn move then this instance is measuring a bad pawn move rather
than a missed development, and the claim's name is wrong.

    python pawn_sample.py --engine PATH [--cache PATH] > results/pawn-sample.txt
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.opening_development import (  # noqa: E402
    _is_theory,
    developments,
    engine_wanted_development,
)
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402

REVIEW = Path(__file__).resolve().parents[2] / "expert-review" / "games"
WANTED = 15
SEED = 20260830

MINOR_NAMES = {chess.KNIGHT: "knight", chess.BISHOP: "bishop"}


def diagram(board: chess.Board) -> str:
    """White at the bottom, with file letters, as the author reads it."""
    rows = str(board).splitlines()
    return "\n".join(f"  {8 - i}  {row}" for i, row in enumerate(rows)) + \
        "\n\n     a b c d e f g h"


def still_home(board: chess.Board, colour: chess.Color) -> list[str]:
    """Which minors had not moved, named so the condition can be checked by eye."""
    home = (chess.B1, chess.C1, chess.F1, chess.G1) if colour else \
        (chess.B8, chess.C8, chess.F8, chess.G8)
    found = []
    for square in home:
        piece = board.piece_at(square)
        if piece and piece.color == colour and piece.piece_type in MINOR_NAMES:
            found.append(f"{MINOR_NAMES[piece.piece_type]} on {chess.square_name(square)}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    args = parser.parse_args()

    book = OpeningBook.load()
    found = []
    scanned = 0
    best_kind = Counter()

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(REVIEW.glob("*.pgn")):
            games = load_games(path)[: args.window]
            corpus = build_corpus(path.stem, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            for game in developments(observations, path.stem, book):
                by_ply = {o.ply: o for o in game.mine}
                for window_move in game.development.window_moves:
                    if not window_move.pawn_instead_of_developing:
                        continue
                    if _is_theory(game, window_move.ply):
                        continue
                    observation = by_ply.get(window_move.ply)
                    if observation is None:
                        continue
                    scanned += 1
                    if not observation.is_error:
                        continue
                    if not engine_wanted_development(observation):
                        continue
                    board = chess.Board(observation.fen_before)
                    best = observation.best_move
                    kind = "none"
                    if best:
                        move = chess.Move.from_uci(best)
                        piece = board.piece_at(move.from_square)
                        if board.is_castling(move):
                            kind = "castling"
                        elif piece and piece.piece_type in MINOR_NAMES:
                            kind = "develops a minor"
                        elif piece and piece.piece_type == chess.PAWN:
                            kind = "another pawn move"
                        else:
                            kind = "something else"
                    best_kind[kind] += 1
                    found.append((path.stem, game, observation, board, kind))

    print("PAWN MOVES THE CLAIM CALLS ERRORS")
    print("=" * 78)
    print()
    print(f"pawn-instead-of-developing moves examined   {scanned}")
    print(f"of those, called errors                     {len(found)}")
    print()
    print("What the engine wanted instead, across ALL of them:")
    for kind, n in best_kind.most_common():
        print(f"  {n:>4}  {kind}   ({n / max(len(found), 1):.0%})")
    print()
    print("Every instance now has development or castling as the engine's own")
    print("preference -- that condition was ADDED after a first reading of these")
    print("positions found the engine wanting another pawn move 40 % of the")
    print("time. So what is left for a person to judge is the chess: was")
    print("developing really better here, or is the engine's preference thin?")
    print()
    print("Mark each position:  [y] developing was better   [n] it was not")
    print("                     [?] cannot tell")
    print()

    random.Random(SEED).shuffle(found)
    for i, (player, game, observation, board, kind) in enumerate(found[:WANTED], 1):
        colour = chess.WHITE if observation.mover_is_white else chess.BLACK
        san = board.san(chess.Move.from_uci(observation.move_played))
        best_san = (board.san(chess.Move.from_uci(observation.best_move))
                    if observation.best_move else "-")
        number = (observation.ply + 1) // 2
        print("=" * 78)
        print(f"[ ]  {i}.  {player} plays {number}"
              f"{'.' if observation.mover_is_white else '...'}{san}"
              f"   ({game.family})")
        print()
        print(diagram(board))
        print()
        print(f"     engine wanted   {best_san}   ({kind})")
        print(f"     cost            {observation.loss_wp:.1f} win probability")
        print(f"     still at home   {', '.join(still_home(board, colour)) or 'nothing'}")
        print(f"     left book after ply {game.plies_in_book}")
        print(f"     FEN  {observation.fen_before}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
