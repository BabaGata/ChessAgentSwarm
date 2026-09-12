"""Build the population baseline for how much of the opening is outside theory.

Design: docs/notes/design.detectors-name-consequences.md § 1a --
    "what does not exist is a peer baseline for book depth. That is new work on
    the peer corpus, not a threshold change."

This is that work, and it costs seconds rather than an hour, because **book depth
needs no engine**. The peer reference does, so the baseline lives in its own file
alongside `development-norms.json`, which was separated for the same reason.

Keyed on `(band, time_control)` -- both, because a blitz player compared against a
rapid baseline is I-03 all over again, and because leaving theory early is exactly
the kind of thing that should differ between speeds.

    python build_norms.py [--band 1400-1800] [--write]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.book_depth import EARLY_PLIES, BookDepthNorms, out_of_book_share  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402
from chesscoach.speed import speed_class  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BOOK = REPO / "data" / "openings" / "book.json"
CORPORA = ("corpus-rapid", "corpus-blitz")
MIN_GAMES_PER_PLAYER = 10
# A family needs this many players before it gets its own baseline. Below it the
# claim falls back to the pooled share, which is blunter and measured, rather
# than to a number three people set -- the same reasoning as MIN_PLAYERS, and
# lower because a family is a slice of an already-filtered population.
MIN_PLAYERS_PER_FAMILY = 5
MIN_GAMES_PER_PLAYER_FAMILY = 3
# `opening_development.developments` skips games under this length; the baseline
# must skip them too.
MIN_MOVES = 8
MIN_PLAYERS = 5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--band", default="1400-1800")
    parser.add_argument("--write", action="store_true",
                        help="write data/openings/book-depth-norms.json")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)

    # (speed) -> player -> walks. Each game is filed under its OWN speed rather
    # than the directory's, because the corpora are not perfectly pure and a
    # mislabelled game lands in the wrong baseline.
    by_speed: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    by_family: dict[str, dict[str, dict[str, list]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    total_games = 0

    for corpus in CORPORA:
        directory = REPO / "data" / "raw" / corpus
        if not directory.is_dir():
            print(f"  {corpus}: not present, skipped")
            continue
        for path in sorted(directory.glob("*.pgn")):
            player = path.stem.lower()
            for game in load_games(path):
                white = (game.white or "").lower() == player
                black = (game.black or "").lower() == player
                if not (white or black):
                    continue
                speed = speed_class(game.time_control)
                if not speed:
                    continue
                # The same two filters `opening_development.developments`
                # applies, because the baseline and the claim must be computed
                # over the same population. Measured before it was assumed: the
                # medians differ by 0.7 points, which is small and is exactly
                # the kind of small that makes a comparison's arms not be what
                # the comparison says they are (L-046).
                if len(game.moves) < MIN_MOVES:
                    continue
                walk = book.walk(list(game.moves))
                if walk.opening is None:
                    continue
                by_speed[speed][player].append((walk, white))
                # **Per family too, because the claim is per family.** The book
                # is 57 points deeper in the Italian Game than in the Van't
                # Kruijs, so a pooled baseline scores the opening rather than
                # the player -- see `BookDepthNorms.share_for`.
                family = walk.opening.name.split(":")[0].strip()
                by_family[speed][family][player].append((walk, white))
                total_games += 1

    shares: dict[str, float] = {}
    lines = [
        "OUT-OF-BOOK BASELINE",
        "=" * 76, "",
        f"band {args.band}, first {EARLY_PLIES} plies, {len(book)} named lines.",
        "",
        "  Each player contributes one share; the baseline is the median of",
        "  those, not a pooled total. Pooling would let a player with many games",
        "  set the population's number.",
        "",
        f"  {'speed':<14}{'players':>9}{'games':>9}{'median share':>15}{'IQR':>8}",
        "  " + "-" * 55,
    ]
    for speed, players in sorted(by_speed.items()):
        per_player = {
            p: out_of_book_share(walks)
            for p, walks in players.items()
            if len(walks) >= MIN_GAMES_PER_PLAYER
        }
        per_player = {p: v for p, v in per_player.items() if v is not None}
        if len(per_player) < MIN_PLAYERS:
            lines.append(f"  {speed:<14}{len(per_player):>9}   too few players, skipped")
            continue
        median = statistics.median(per_player.values())
        quarters = statistics.quantiles(per_player.values(), n=4)
        shares[BookDepthNorms.key(args.band, speed)] = round(median, 4)
        lines.append(
            f"  {speed:<14}{len(per_player):>9}"
            f"{sum(len(w) for w in players.values()):>9}"
            f"{median:>14.1%}{quarters[2] - quarters[0]:>8.2f}"
        )

    # Each family that clears the floor gets its own number, by the same
    # per-player median as the pooled one: pooling would let a player with many
    # games in one opening set that opening's baseline.
    lines += ["", f"  {'family':<34}{'speed':<8}{'players':>8}{'median':>9}", "  " + "-" * 59]
    for speed, families in sorted(by_family.items()):
        for family, players in sorted(families.items()):
            per_player = {
                p: out_of_book_share(walks)
                for p, walks in players.items()
                if len(walks) >= MIN_GAMES_PER_PLAYER_FAMILY
            }
            per_player = {p: v for p, v in per_player.items() if v is not None}
            if len(per_player) < MIN_PLAYERS_PER_FAMILY:
                continue
            median = statistics.median(per_player.values())
            shares[BookDepthNorms.key(args.band, speed, family)] = round(median, 4)
            lines.append(f"  {family[:33]:<34}{speed:<8}{len(per_player):>8}{median:>8.1%}")

    norms = BookDepthNorms(
        shares=shares,
        source=f"{', '.join(CORPORA)} at band {args.band}",
        players=sum(len(p) for p in by_speed.values()),
        games=total_games,
    )

    lines += ["", "=" * 76, ""]
    if args.write:
        norms.save()
        lines.append(f"  written to {BookDepthNorms.__module__.split('.')[0]}"
                     f"/../data/openings/book-depth-norms.json")
    else:
        lines.append("  dry run — pass --write to save")
    lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "norms.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
