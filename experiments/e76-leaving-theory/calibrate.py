"""When is "early" early? The threshold, swept through the rule.

Design: docs/notes/design.detectors-name-consequences.md § 1a
Screen:  docs/notes/experiments.e75-book-depth.md

The author, asked whether telling a player they leave theory a move and a half
before their peers is coaching or trivia:

    "It is coaching to tell the player that they don't know the opening"

So 1a is built. E75 established the measure is real -- split-half **+0.81**,
distinct from every development claim at worst -0.49, and not merely rating. What
it did not establish is the *claim*: a mean book depth is not something a player
can be told, and "you leave theory earlier than your peers" needs a rate.

The rate proposed here: **the share of a player's games in which they were the
one who left theory, and did so before ply N.** Every game is an opportunity; the
instances are the games they stepped out first and stepped out early. Whose exit
it was matters because `BookWalk.left_by_white` exists precisely so that leaving
because the *opponent* played a sideline is not charged to the player.

N is swept rather than read off the distribution. **L-054**: a distribution says
what a threshold discards, only firing says what it buys.

Two baselines are computed, because the project has used both and they answer
different questions:

    peers   the 1400-1800 corpus, which is what the design note specifies
    strong  the top-100 corpus behind development-norms.json, which is what the
            author asked for when the same choice came up for development:
            "I dont want this to be built by peer reference but by better
            players who usually know the opening"

    python calibrate.py [--from 4] [--to 14]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BOOK = REPO / "data" / "openings" / "book.json"
PEERS = ("corpus-rapid", "corpus-blitz")
STRONG = ("corpus-strong",)
MIN_GAMES = 10


def exits(book: OpeningBook, corpora) -> dict[str, list[tuple[int, bool]]]:
    """Per player: (plies_in_book, was_it_my_exit) for every game."""
    per_player: dict[str, list[tuple[int, bool]]] = defaultdict(list)
    for corpus in corpora:
        directory = REPO / "data" / "raw" / corpus
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.pgn")):
            player = path.stem.lower()
            for game in load_games(path):
                white = (game.white or "").lower() == player
                black = (game.black or "").lower() == player
                if not (white or black):
                    continue
                walk = book.walk(list(game.moves))
                mine = walk.left_by_white is white if walk.left_by_white is not None else False
                per_player[player].append((walk.plies_in_book, mine))
    return {p: g for p, g in per_player.items() if len(g) >= MIN_GAMES}


def early_rate(games, before_ply: int) -> float:
    """Share of games the player left theory first, and before `before_ply`."""
    if not games:
        return 0.0
    return sum(1 for plies, mine in games if mine and plies < before_ply) / len(games)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start", type=int, default=4)
    parser.add_argument("--to", dest="stop", type=int, default=14)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    peers = exits(book, PEERS)
    strong = exits(book, STRONG)

    lines = [
        "WHEN IS LEAVING THEORY *EARLY*?",
        "=" * 92, "",
        f"peers   {len(peers)} players, {sum(len(g) for g in peers.values()):,} games "
        f"(1400-1800 corpora)",
        f"strong  {len(strong)} players, {sum(len(g) for g in strong.values()):,} games "
        f"(top-100 corpus)",
        f"book    {len(book)} named lines",
        "",
        "  rate = share of a player's games where THEY left theory, before ply N.",
        "",
        f"  {'ply':>4}{'peer median':>14}{'peer IQR':>11}"
        f"{'strong median':>16}{'gap':>8}{'split-half':>13}",
        "  " + "-" * 66,
    ]

    for ply in range(args.start, args.stop + 1):
        peer_rates = {p: early_rate(g, ply) for p, g in peers.items()}
        strong_rates = {p: early_rate(g, ply) for p, g in strong.items()}
        peer_median = statistics.median(peer_rates.values())
        strong_median = statistics.median(strong_rates.values()) if strong_rates else float("nan")
        spread = (statistics.quantiles(peer_rates.values(), n=4)[2]
                  - statistics.quantiles(peer_rates.values(), n=4)[0])
        # Does the RATE agree with itself? E75 checked the mean book depth and
        # got 0.81; a rate built on a threshold is a different statistic and
        # inherits none of that. E73 shipped a claim whose underlying numbers
        # were fine and whose named set flipped anyway.
        odd = {p: early_rate(g[::2], ply) for p, g in peers.items() if len(g) >= 2 * MIN_GAMES}
        even = {p: early_rate(g[1::2], ply) for p, g in peers.items() if len(g) >= 2 * MIN_GAMES}
        shared = sorted(set(odd) & set(even))
        reliability = float("nan")
        if len(shared) >= 3:
            a = [odd[p] for p in shared]
            b = [even[p] for p in shared]
            if len(set(a)) > 1 and len(set(b)) > 1:
                reliability = statistics.correlation(a, b)
        lines.append(
            f"  {ply:>4}{peer_median:>13.0%} {spread:>10.2f}"
            f"{strong_median:>15.0%} {strong_median - peer_median:>+7.0%}"
            + ("        --" if reliability != reliability else f"{reliability:>+13.2f}")
        )

    lines += [
        "", "=" * 92, "WHAT TO READ HERE", "=" * 92, "",
        "  `peer spread` is the interquartile range of the rate. A threshold where",
        "  every player scores the same measures nothing; the spread is what a",
        "  claim has to work with.",
        "",
        "  `gap` is strong players minus peers at the same threshold. A negative",
        "  gap means stronger players leave theory early less often, which is the",
        "  direction the claim assumes. A gap near zero at some threshold would",
        "  mean the threshold is not measuring opening knowledge at all.",
        "",
    ]

    text = "\n".join(lines) + "\n"
    (args.out / "calibration.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
