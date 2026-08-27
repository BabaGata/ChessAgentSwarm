"""Build the guide-library skeleton and the sheet for reviewing it.

Design: docs/notes/design.informative-claims.md

Lists every opening family these players actually reach, ranked by games, with
whatever candidate links exist. **Everything starts `reviewed: false`**, and
`GuideLibrary.for_opening` never returns an unreviewed entry, so nothing here can
reach a player before the author has looked at it.

**No URL is invented.** A slot with no candidate stays empty and says so, because
a plausible-looking guessed URL is worse than an obvious gap: the gap gets filled
and the guess gets trusted.

Usage:
    python build_guides.py [--window 20] [--out data/openings/guides.json]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chesscoach.opening_guides import DEFAULT_LIBRARY, Guide, GuideLibrary  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

from candidates import CANDIDATES  # noqa: E402

# Why the obvious free source is only a candidate: its prose was harvested, read
# by the author and refused as too advanced for this audience. Linking to it is
# still an option, but it is not an obvious yes and the note says why.
WIKIBOOKS_NOTE = (
    "free (CC BY-SA) but its prose was judged too advanced for 1500 on 2026-08-23 "
    "— annotates what happened rather than what to plan"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--out", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--sheet", type=Path,
                        default=Path(__file__).parent / "results" / "guides-to-review.txt")
    args = parser.parse_args()

    book = OpeningBook.load()
    played: Counter = Counter()
    who: dict[str, Counter] = {}
    for path in sorted(ROOT.glob("games/*.pgn")):
        player = path.stem
        for game in load_games(path)[: args.window]:
            walk = book.walk(list(game.moves))
            if walk.opening is None:
                continue
            family = walk.opening.name.split(":")[0]
            played[family] += 1
            who.setdefault(family, Counter())[player] += 1

    guides: list[Guide] = []
    for family, _ in played.most_common():
        for title, url, publisher in CANDIDATES.get(family, []):
            guides.append(Guide(opening=family, title=title, url=url,
                                publisher=publisher, reviewed=False))

    library = GuideLibrary(tuple(guides))
    library.save(args.out)

    lines = [
        "OPENING GUIDES TO REVIEW",
        "=" * 78,
        "",
        "One entry per opening these twelve players actually reach, most played",
        "first. For each candidate: open it, and decide whether you would send a",
        "1500 there to learn this opening's plans.",
        "",
        "  [y] approve — set reviewed=true in data/openings/guides.json",
        "  [n] reject  — delete the line",
        "",
        "Nothing reaches a player until it is approved. Openings with NO CANDIDATE",
        "need a link found; the system stays silent for them rather than guessing.",
        "",
        f"{len(played)} opening families, {sum(played.values())} games — but the",
        "tail is long and thin, so the whole list is not the job:",
        "",
    ]
    running = 0
    for rank, (_, count) in enumerate(played.most_common(), start=1):
        running += count
        if rank in (5, 8, 15, 25):
            lines.append(f"    curating the top {rank:>2} covers "
                         f"{running}/{sum(played.values())} games "
                         f"({running / sum(played.values()):.0%})")
    once = sum(1 for _, n in played.items() if n == 1)
    lines += [f"    {once} of {len(played)} families appear in a single game.", ""]
    covered = 0
    for family, games in played.most_common():
        entries = CANDIDATES.get(family, [])
        covered += bool(entries)
        top = ", ".join(f"{p} ({n})" for p, n in who[family].most_common(3))
        lines += ["-" * 78, f"{family}  —  {games} games", f"  played by: {top}"]
        if not entries:
            lines.append("  NO CANDIDATE YET")
            continue
        for title, url, publisher in entries:
            lines += [f"  [ ] {title}", f"      {url}  ({publisher})"]

    lines += ["", "=" * 78,
              f"{covered} of {len(played)} families have at least one candidate."]
    args.sheet.parent.mkdir(parents=True, exist_ok=True)
    args.sheet.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    print(f"{len(played)} families, {len(guides)} candidate links, none reviewed")
    print(f"written {args.out}")
    print(f"written {args.sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
