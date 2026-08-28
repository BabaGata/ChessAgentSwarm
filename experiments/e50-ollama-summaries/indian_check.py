"""Do the Indian Defense games actually reach a London structure?

The candidate list serves London System guides for the Indian Defense, and the
entry's own title asserts why: *"(the structure these games reach)"*. That is a
claim about these players' games, so it can be checked rather than argued about.

Two questions, both answerable from the games already on disk:

  1. which named lines do the Indian Defense games actually reach?
  2. in how many does White put a bishop on f4 early -- the move that makes a
     London a London?

A guide is correct for a family if it describes what the player will face. If
most of these games are Londons the mapping is right and the label is what needs
fixing; if they are not, the guide is wrong and must go.

Usage:
    python indian_check.py [--family "Indian Defense"]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

# How far in to look for the defining bishop move. The London plays Bf4 on move
# 2 or 3; allowing 6 is generous to the mapping rather than to the argument.
LONDON_WINDOW = 12


def reaches_london(moves: list[str]) -> bool:
    """Did White's dark-squared bishop land on f4 in the opening?"""
    board = chess.Board()
    for index, uci in enumerate(moves[:LONDON_WINDOW]):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return False
        if move not in board.legal_moves:
            return False
        piece = board.piece_at(move.from_square)
        board.push(move)
        if (piece is not None and piece.piece_type == chess.BISHOP
                and piece.color == chess.WHITE
                and move.to_square == chess.F4 and index % 2 == 0):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", default="Indian Defense")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load()
    lines: Counter = Counter()
    london = 0
    total = 0

    for path in sorted(ROOT.glob("games/*.pgn")):
        for game in load_games(path)[:20]:
            moves = list(game.moves)
            walk = book.walk(moves)
            if not walk.opening:
                continue
            if walk.opening.name.split(":")[0].strip() != args.family:
                continue
            total += 1
            lines[walk.opening.name] += 1
            london += int(reaches_london(moves))

    out = [
        f"DOES THE {args.family.upper()} REACH A LONDON STRUCTURE?",
        "=" * 78,
        "",
        f"games classified {args.family}: {total}",
        f"White plays an early Bf4 (London): {london}"
        + (f"  ({100 * london / total:.0f} %)" if total else ""),
        "",
        "named lines actually reached:",
    ]
    for name, count in lines.most_common():
        out.append(f"  {count:>3}  {name}")
    out += [
        "",
        "A guide is right for a family when it describes what the player faces.",
    ]
    text = "\n".join(out)
    print(text)
    (args.out / "indian-check.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
