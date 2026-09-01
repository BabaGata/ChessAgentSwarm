"""Does book depth have anything left to add beside the development claims?

Note: docs/notes/experiments.e75-book-depth.md
Design: docs/notes/design.detectors-name-consequences.md § 1a

The commitment being honoured, written when 1a was set aside:

    "1a is held, not deleted: a correlation screen against `plies_in_book`
    decides whether book depth has anything left to add."

[[experiments.e69-development-correlations]] screened the four development claims
against each other and against the claims they might restate. It could not screen
this pair, and said so: **book depth is not a claim in the peer reference**, so
there was no per-player rate to correlate. This computes one.

Three questions, and the third is the one that decides it:

    redundant?   does book depth track `slow_development`? Above E69's ceiling of
                 |r| > 0.85 the two are one signal with two names.

    whose exit?  `BookWalk` records `left_by_white` precisely because *"a player
                 can leave book because their opponent played a sideline, and
                 attributing that to the player would measure the wrong person"*.
                 So book depth is measured twice: the game's, and the player's
                 own.

    just skill?  E14 found four of six style candidates were **strength wearing a
                 style label**. A book depth that is only rating adds nothing a
                 rating estimate does not, whatever it does against the
                 development claims.

**No engine.** The book walk is deterministic and the claim rates already exist
in the peer reference, rebuilt at HEAD.

    python run.py [--peers PATH] [--min-opportunities 10]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BOOK = REPO / "data" / "openings" / "book.json"
CORPORA = ("corpus-rapid", "corpus-blitz")

# The same four E69 screened, and the same ceiling.
DEVELOPMENT = ("slow_development.book", "late_castling.book",
               "repeat_move.any", "pawn_error.any")
CEILING = 0.85


def rates(peers: dict, claim: str, floor: int) -> dict[str, float]:
    """Per-player rate for one claim, pooled across strata. E69's function."""
    totals: dict[str, list[int]] = {}
    for key, contributions in peers["cells"].items():
        if key.split("|")[-1] != claim:
            continue
        for row in contributions:
            got = totals.setdefault(row["player"].lower(), [0, 0])
            got[0] += row["instances"]
            got[1] += row["opportunities"]
    return {p: hits / chances for p, (hits, chances) in totals.items() if chances >= floor}


def book_depth(book: OpeningBook) -> dict[str, dict[str, float]]:
    """Per player: how deep their games stayed in theory, two ways."""
    per_player: dict[str, list[tuple[int, bool | None, bool]]] = defaultdict(list)

    for corpus in CORPORA:
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
                # `left_by_white` is None when the game never left the book.
                mine = (walk.left_by_white is white
                        if walk.left_by_white is not None else None)
                per_player[player].append((walk.plies_in_book, mine, white))

    measured: dict[str, dict[str, float]] = {}
    for player, games in per_player.items():
        if len(games) < 5:
            continue
        depths = [d for d, _, _ in games]
        own = [d for d, mine, _ in games if mine is True]
        left_by_someone = [1 for _, mine, _ in games if mine is not None]
        measured[player] = {
            "games": len(games),
            "plies": statistics.mean(depths),
            "plies_own_exit": statistics.mean(own) if len(own) >= 5 else float("nan"),
            "share_left_first": (len(own) / len(left_by_someone)
                                 if left_by_someone else float("nan")),
        }
    return measured


def split_half(book: OpeningBook) -> dict[str, tuple[float, float]]:
    """Book depth computed twice per player, on alternate games.

    Odd/even rather than first-half/second-half: a player's rating and repertoire
    drift over a corpus, so splitting by time would measure the drift.
    """
    per_player: dict[str, list[int]] = defaultdict(list)
    for corpus in CORPORA:
        directory = REPO / "data" / "raw" / corpus
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.pgn")):
            player = path.stem.lower()
            for game in load_games(path):
                white = (game.white or "").lower() == player
                black = (game.black or "").lower() == player
                if white or black:
                    per_player[player].append(book.walk(list(game.moves)).plies_in_book)

    measured: dict[str, tuple[float, float]] = {}
    for player, depths in per_player.items():
        odd, even = depths[::2], depths[1::2]
        if len(odd) >= 5 and len(even) >= 5:
            measured[player] = (statistics.mean(odd), statistics.mean(even))
    return measured


def ratings() -> dict[str, float]:
    """Median own rating per player, from the PGN headers."""
    per_player: dict[str, list[int]] = defaultdict(list)
    for corpus in CORPORA:
        directory = REPO / "data" / "raw" / corpus
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.pgn")):
            player = path.stem.lower()
            for game in load_games(path):
                white = (game.white or "").lower() == player
                black = (game.black or "").lower() == player
                elo = game.white_elo if white else (game.black_elo if black else None)
                if elo is not None:
                    per_player[player].append(elo)
    return {p: statistics.median(v) for p, v in per_player.items() if v}


def correlation(left: dict[str, float], right: dict[str, float]) -> tuple[float, int]:
    shared = sorted(k for k in set(left) & set(right)
                    if left[k] == left[k] and right[k] == right[k])
    if len(shared) < 3:
        return float("nan"), len(shared)
    a = [left[k] for k in shared]
    b = [right[k] for k in shared]
    if len(set(a)) < 2 or len(set(b)) < 2:
        return float("nan"), len(shared)
    return statistics.correlation(a, b), len(shared)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", type=Path,
                        default=REPO / "data/raw/out/peers-3af3206.json")
    parser.add_argument("--min-opportunities", type=int, default=10)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    peers = json.loads(args.peers.read_text(encoding="utf-8"))
    depth = book_depth(book)
    elo = ratings()
    claims = {c: rates(peers, c, args.min_opportunities) for c in DEVELOPMENT}

    columns = {
        "plies in book": {p: v["plies"] for p, v in depth.items()},
        "plies (own exits)": {p: v["plies_own_exit"] for p, v in depth.items()},
        "share left first": {p: v["share_left_first"] for p, v in depth.items()},
    }

    lines = [
        "DOES BOOK DEPTH ADD ANYTHING THE DEVELOPMENT CLAIMS DO NOT?",
        "=" * 88, "",
        f"reference   {args.peers.name}",
        f"players     {len(depth)} with book depth, "
        f"at least {args.min_opportunities} opportunities on a claim",
        f"book        {len(book)} named lines, walk capped at 30 plies",
        "",
        "  book depth, measured:",
    ]
    for name, values in columns.items():
        got = [v for v in values.values() if v == v]
        if got:
            lines.append(f"    {name:<20} median {statistics.median(got):.2f}, "
                         f"range {min(got):.2f}-{max(got):.2f}, n={len(got)}")

    lines += [
        "", "=" * 88,
        f"AGAINST THE DEVELOPMENT CLAIMS   (E69's ceiling |r| > {CEILING})",
        "=" * 88, "",
        f"  {'claim':<26}" + "".join(f"{name:>21}" for name in columns),
        "  " + "-" * (26 + 21 * len(columns)),
    ]
    redundant = []
    for claim in DEVELOPMENT:
        cells = []
        for name, values in columns.items():
            r, n = correlation(claims[claim], values)
            cells.append("--" if r != r else f"{r:+.2f} (n={n})")
            if r == r and abs(r) > CEILING:
                redundant.append((claim, name, r))
        lines.append(f"  {claim:<26}" + "".join(f"{c:>21}" for c in cells))

    lines += [
        "", "=" * 88, "IS IT JUST STRENGTH?", "=" * 88, "",
        "  E14 found four of six style candidates were strength wearing a style",
        "  label. A book depth that is only rating adds nothing a rating estimate",
        "  does not already give.",
        "",
    ]
    for name, values in columns.items():
        r, n = correlation(values, elo)
        lines.append(f"  {name:<20} vs rating   "
                     + ("--" if r != r else f"{r:+.2f}") + f"   (n={n})")
    for claim in DEVELOPMENT:
        r, n = correlation(claims[claim], elo)
        lines.append(f"  {claim:<20} vs rating   "
                     + ("--" if r != r else f"{r:+.2f}") + f"   (n={n})")

    # Split-half reliability (B1). E73 shipped a claim that passed every screen
    # and then flipped its named set with the window; a measure that does not
    # agree with itself cannot be distinct from anything.
    halves = split_half(book)
    r_half, n_half = correlation({p: a for p, (a, _) in halves.items()},
                                 {p: b for p, (_, b) in halves.items()})
    lines += [
        "", "=" * 88, "DOES THE MEASURE AGREE WITH ITSELF?", "=" * 88, "",
        "  Each player's games split odd/even, book depth computed in each half.",
        "  A measure whose halves disagree is noise, and no correlation with",
        "  anything else would mean much.",
        "",
        f"  split-half r = " + ("--" if r_half != r_half else f"{r_half:+.2f}")
        + f"   over {n_half} players",
    ]

    lines += ["", "=" * 88, ""]
    if redundant:
        lines.append("  REDUNDANT — one signal with two names:")
        for claim, name, r in redundant:
            lines.append(f"    {claim} and {name} at r = {r:+.2f}")
    else:
        lines.append("  No pair reaches the ceiling: book depth is not a restatement")
        lines.append("  of any development claim.")
    lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "book-depth.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
