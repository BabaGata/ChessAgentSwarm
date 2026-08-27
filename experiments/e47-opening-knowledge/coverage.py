"""E47 — does the opening book say anything useful about these players?

Layer 1 of [[design.informative-claims]]. Before any claim is built on it, three
questions, in the order that can kill the idea fastest:

  **1. Does it classify their games at all?** A book that names 40 % of a
  1400-1800 player's games cannot carry a claim.

  **2. Does the exit ply *separate* players?** This is the screen every claim in
  this project passes or fails — [[experiments.e09-square-candidates]]'s p90 over
  median. If everyone leaves theory at move 6, the measurement is a constant and
  names nobody.

  **3. Who actually left?** The exit is a property of the **game**. A player
  leaves book when their *opponent* plays a sideline, and a claim that blames the
  player for that is measuring the wrong person. If most exits are the
  opponent's, the claim has to be restricted to the ones that are not.

No engine time: this reads PGNs and replays moves.

Usage:
    python coverage.py [--book data/openings/book.json] [--window 20]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import DEFAULT_BOOK, OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", type=Path, default=DEFAULT_BOOK)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(args.book)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say(f"OPENING BOOK COVERAGE — {len(book)} named positions")
    say()
    say(f"{'player':<22}{'games':>6}{'named':>7}{'exit ply':>10}{'they left':>11}"
        f"   most-played opening")
    say("-" * 96)

    per_player_exit: dict[str, float] = {}
    all_exits: list[int] = []
    left_by_player = left_by_opponent = 0
    classified = total = 0

    for path in sorted(ROOT.glob("games/*.pgn")):
        player = path.stem
        games = load_games(path)[: args.window]
        exits, named, openings, mine = [], 0, Counter(), 0
        for game in games:
            total += 1
            is_white = (game.white or "").lower() == player.lower()
            walk = book.walk(list(game.moves))
            if walk.opening is not None:
                named += 1
                classified += 1
                openings[walk.opening.name.split(":")[0]] += 1
            if walk.left_at_ply is not None:
                exits.append(walk.left_at_ply)
                if walk.left_by_white == is_white:
                    left_by_player += 1
                    mine += 1
                else:
                    left_by_opponent += 1
        if not exits:
            continue
        median_exit = statistics.median(exits)
        per_player_exit[player] = median_exit
        all_exits += exits
        top = openings.most_common(1)[0] if openings else ("-", 0)
        say(f"{player:<22}{len(games):>6}{named:>7}{median_exit:>10.1f}"
            f"{mine:>7}/{len(exits):<3}   {top[0][:34]} ({top[1]})")

    say()
    say("1. CLASSIFICATION")
    say(f"   games given a named opening: {classified}/{total} ({classified/total:.0%})")

    say()
    say("2. DOES THE EXIT PLY SEPARATE PLAYERS?")
    values = sorted(per_player_exit.values())
    median = statistics.median(values)
    p90 = values[min(len(values) - 1, int(len(values) * 0.9))]
    say(f"   per-player median exit ply: min {values[0]:.1f}  median {median:.1f}  "
        f"p90 {p90:.1f}  max {values[-1]:.1f}")
    say(f"   spread p90/median = {p90/median:.2f}x   "
        f"(the screen used elsewhere in this project wants >= 1.30)")
    say(f"   in MOVES, that is {values[0]/2:.1f} to {values[-1]/2:.1f}")

    say()
    say("3. WHO LEFT THE BOOK?")
    both = left_by_player + left_by_opponent
    say(f"   the player: {left_by_player}/{both} ({left_by_player/both:.0%})")
    say(f"   the opponent: {left_by_opponent}/{both} ({left_by_opponent/both:.0%})")
    say("   A claim about the player must use only the first group.")

    say()
    say("   exit ply over all games: "
        f"median {statistics.median(all_exits):.0f}, "
        f"i.e. around move {statistics.median(all_exits)/2:.0f}")

    (args.out / "coverage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'coverage.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
