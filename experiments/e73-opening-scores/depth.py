"""Does the claim survive being measured over a different number of games?

Design: docs/notes/design.detectors-name-consequences.md § 1b ·
Method: [[experiments.e26-depth-robustness]], and the standing rule from L-008 /
R-13 that a discovered association must reproduce before it is written down.

A player brings whatever history they have. A claim that names one person at 20
games, nobody at 30 and somebody else at 40 is not measuring a property of the
player -- it is measuring the window, and the report would change its mind every
time the player came back.

`screen.py` found the replacement names 2 of 12 at 60 games. This asks whether
those 2 are the same 2 at any other depth.

    python depth.py [--from 15] [--to 60] [--step 5]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_scores import MIN_GAMES, weak_openings  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "expert-review" / "games"
BOOK = REPO / "data" / "openings" / "book.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="start", type=int, default=15)
    parser.add_argument("--to", dest="stop", type=int, default=60)
    parser.add_argument("--step", type=int, default=5)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    windows = list(range(args.start, args.stop + 1, args.step))
    games_by_player = {p.stem: load_games(p) for p in sorted(ROOT.glob("*.pgn"))}

    # player -> window -> the families named at that depth
    named: dict[str, dict[int, set[str]]] = defaultdict(dict)
    for player, games in games_by_player.items():
        for window in windows:
            found = weak_openings(games[:window], player, book)
            named[player][window] = {w.family for w in found}

    lines = [
        "IS THE CLAIM THE SAME CLAIM AT A DIFFERENT DEPTH?",
        "=" * 86, "",
        f"{len(games_by_player)} players, floor {MIN_GAMES}, windows "
        f"{windows[0]}-{windows[-1]} in steps of {args.step}.",
        "",
        "  A cell is the number of openings named at that depth.",
        "",
        f"  {'player':<24}" + "".join(f"{w:>5}" for w in windows) + "   verdict",
        "  " + "-" * (24 + 5 * len(windows) + 12),
    ]

    flips = 0
    ever = 0
    stable = 0
    for player in sorted(named):
        row = named[player]
        counts = [len(row[w]) for w in windows]
        appears = [w for w in windows if row[w]]
        if not appears:
            verdict = "never named"
        else:
            ever += 1
            # Named at the deepest window and at every window after it first
            # appears, with the same opening: that is a claim about the player.
            families = {frozenset(row[w]) for w in windows if row[w]}
            contiguous = all(row[w] for w in windows if w >= appears[0])
            if len(families) == 1 and contiguous:
                verdict = "stable once it appears"
                stable += 1
            else:
                verdict = f"FLIPS — named at {len(appears)} of {len(windows)} depths"
                flips += 1
        lines.append(f"  {player[:23]:<24}" + "".join(f"{c:>5}" for c in counts)
                     + f"   {verdict}")

    lines += [
        "", "=" * 86, "",
        f"  named at some depth        {ever:>2} of {len(named)}",
        f"  stable once named          {stable:>2}",
        f"  flips in and out           {flips:>2}",
        "",
    ]
    per_window = {w: sorted(p for p in named if named[p][w]) for w in windows}
    lines.append("  who is named, by depth:")
    for w in windows:
        lines.append(f"    {w:>3} games   {', '.join(per_window[w]) or '—'}")

    lines += [
        "",
        "  A claim whose named set changes with the window is measuring the",
        "  window. R-13 and L-008 require an association to reproduce on a",
        "  different sample before it is written down; a different depth of the",
        "  SAME player is a weaker test than that, and it is the one being failed.",
        "",
    ]

    text = "\n".join(lines) + "\n"
    (args.out / "depth.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
