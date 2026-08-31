"""How many games does a player give one opening? The threshold, measured.

Design: docs/notes/design.detectors-name-consequences.md § 1b

The design note proposed a minimum of 5 games before an opening may be compared,
and said explicitly how that number should be settled: *"the distribution of
per-opening game counts across the 12 review players"*. This measures it, so the
threshold is a reading rather than a guess.

The author's caveat is the reason a threshold is needed at all:

    "Keep track that main openings of the players would be played much more
    often then other openings by the same player."

A player has two or three mainstays and a long tail played once or twice.
Comparing raw scores across all of them ranks the tail on noise every time -- a
single win in a one-game opening is a 100 % score.

**No engine.** Results and openings are both in the PGN headers; the book maps a
game to a named family.

    python calibrate.py [--window 60]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook, _family  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "expert-review" / "games"
# DEFAULT_BOOK is relative to the working directory, and this runs from its
# own. Resolved here so the script does not depend on where it is invoked.
BOOK = REPO / "data" / "openings" / "book.json"


def score_for(game, player: str) -> float | None:
    """1, 0.5 or 0 from the player's own side. None when the game was not decided."""
    white = (game.white or "").lower() == player.lower()
    black = (game.black or "").lower() == player.lower()
    if not (white or black):
        return None
    if game.result == "1-0":
        return 1.0 if white else 0.0
    if game.result == "0-1":
        return 0.0 if white else 1.0
    if game.result == "1/2-1/2":
        return 0.5
    return None


def family_of(game, book: OpeningBook) -> str | None:
    """The opening family this game belongs to, by name or by walking the book."""
    if game.opening:
        return _family(game.opening)
    walk = book.walk(game.moves)
    return _family(walk.opening.name) if walk.opening else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    per_player: dict[str, Counter] = {}
    scores: dict[tuple[str, str], list[float]] = defaultdict(list)

    for path in sorted(ROOT.glob("*.pgn")):
        player = path.stem
        counts: Counter = Counter()
        for game in load_games(path)[: args.window]:
            score = score_for(game, player)
            family = family_of(game, book)
            if score is None or family is None:
                continue
            counts[family] += 1
            scores[(player, family)].append(score)
        if counts:
            per_player[player] = counts

    lines = [
        "HOW MANY GAMES DOES A PLAYER GIVE ONE OPENING?",
        "=" * 86, "",
        f"{len(per_player)} players, up to {args.window} games each, families by book name.",
        "",
        f"  {'player':<24}{'games':>7}{'openings':>10}{'top 3':>8}{'once':>7}  most played",
        "  " + "-" * 82,
    ]
    all_counts: list[int] = []
    covered_at: dict[int, list[float]] = defaultdict(list)

    for player, counts in per_player.items():
        total = sum(counts.values())
        top3 = sum(n for _, n in counts.most_common(3))
        once = sum(1 for n in counts.values() if n == 1)
        biggest = ", ".join(f"{name} {n}" for name, n in counts.most_common(2))
        all_counts.extend(counts.values())
        lines.append(f"  {player[:23]:<24}{total:>7}{len(counts):>10}"
                     f"{top3 / total:>7.0%}{once:>7}  {biggest[:34]}")
        for floor in range(1, 11):
            kept = sum(n for n in counts.values() if n >= floor)
            covered_at[floor].append(kept / total)

    lines += [
        "", "=" * 86,
        "WHAT A MINIMUM-GAMES FLOOR KEEPS AND THROWS AWAY",
        "=" * 86, "",
        "  A floor decides which openings may be compared at all. Too low and a",
        "  single win in a one-game opening reads as a 100 % score; too high and",
        "  a player has fewer than two comparable openings and nothing can be",
        "  said at all.",
        "",
        f"  {'floor':>6}{'% of games kept':>18}{'players with >=2':>19}"
        f"{'players with >=3':>19}",
        "  " + "-" * 60,
    ]
    for floor in range(1, 11):
        share = statistics.mean(covered_at[floor])
        two = sum(1 for counts in per_player.values()
                  if sum(1 for n in counts.values() if n >= floor) >= 2)
        three = sum(1 for counts in per_player.values()
                    if sum(1 for n in counts.values() if n >= floor) >= 3)
        lines.append(f"  {floor:>6}{share:>17.0%}{two:>19}{three:>19}")

    lines += [
        "",
        f"  openings per player     median {statistics.median(len(c) for c in per_player.values()):.0f}",
        f"  games per opening       median {statistics.median(all_counts):.0f}, "
        f"mean {statistics.mean(all_counts):.1f}, max {max(all_counts)}",
        f"  openings played once    {sum(1 for n in all_counts if n == 1)} of {len(all_counts)} "
        f"({sum(1 for n in all_counts if n == 1) / len(all_counts):.0%})",
        "",
    ]

    text = "\n".join(lines) + "\n"
    (args.out / "calibration.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
