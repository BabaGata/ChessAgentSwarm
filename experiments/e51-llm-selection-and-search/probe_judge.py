"""Can the search judge say yes, or does it only ever say no?

It kept 0 of 3 on all twelve attempts across four openings. Two explanations fit
that equally well: the results really were databases, shops and forums, or the
judge is stuck on NONE. Those need different actions, so they get separated
before either goes in a note (L-046).

The test is a hand-built list mixing pages known to be guides -- ones the author
has read -- with the exact junk the real run returned. A judge that works keeps
the first group and rejects the second.

Usage:
    python probe_judge.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_agent import Gap  # noqa: E402
from chesscoach.opening_search import GuidedSearcher  # noqa: E402

# The junk is verbatim from the real run, and is mixed into every question.
JUNK = [
    ("33 Chess Openings You Should Know - Duolingo Blog",
     "https://blog.duolingo.com/popular-chess-openings/", "blog.duolingo.com"),
    ("Openings with simple logic behind them - Chess Forums",
     "https://www.chess.com/forum/view/chess-openings/openings-with-simple-logic",
     "chess.com"),
    ("Bird's Opening Adviser, Setup Builder & 23 Replays",
     "https://www.chessworld.net/bird-opening.asp", "chessworld.net"),
]

# Each guide is asked about ITS OWN opening. The first version of this probe
# offered a London guide while asking about the Pirc; the judge rejected it and
# was scored wrong for doing exactly the right thing.
CASES = [
    ("Pirc Defense",
     ("Pirc Defense: plans, ideas and typical structures",
      "https://freechesstrainer.org/openings/black/e4/pirc-defense.html",
      "freechesstrainer.org")),
    ("London System",
     ("The London System: complete guide for club players",
      "https://www.firechess.com/blog/london-system-guide-club-players",
      "firechess.com")),
    ("English Opening",
     ("The ideas behind the English Opening",
      "https://www.exeterchessclub.org.uk/content/ideas-behind-english-opening",
      "exeterchessclub.org.uk")),
]


class FixedSearcher:
    """Returns one real guide plus the junk, in a fixed order."""

    name = "fixture"

    def __init__(self, guide) -> None:
        self._results = [guide] + JUNK

    def search(self, _gap):
        return list(self._results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    lines = [f"CAN THE SEARCH JUDGE SAY YES?  model={args.model}", "=" * 78, ""]
    right = total = 0
    for opening, guide in CASES:
        searcher = GuidedSearcher(inner=FixedSearcher(guide), attempts=1, wanted=99,
                                  model=args.model)
        returned = searcher.search(Gap(opening, 5, 0.3))
        # Score the JUDGE, not the safety fallback. When the judge keeps nothing,
        # `search` returns the plain results -- correct behaviour, and scoring it
        # as "the judge approved these" is how the first version of this probe
        # reported a judge that had actually said NONE.
        judged_kept = searcher.log[0]["kept"]
        kept = ({url for _t, url, _p in returned} if judged_kept else set())
        lines.append("-" * 78)
        lines.append(f"asked about: {opening}")
        lines.append(f"  model answered: {searcher.last_answer[:70]!r}")
        if not judged_kept:
            lines.append("  judge kept nothing -> the plain results were returned "
                         "by the safety fallback")
        for title, url, _publisher in [guide] + JUNK:
            is_guide = url == guide[1]
            verdict = url in kept
            ok = verdict == is_guide
            right += ok
            total += 1
            lines.append(f"  {'KEPT  ' if verdict else 'reject'}  "
                         f"{'ok   ' if ok else 'WRONG'}  "
                         f"{'(a guide)' if is_guide else '(junk)   '}  {title[:50]}")
    lines += [
        "",
        f"  agreement with a person: {right} of {total}",
        "",
        "If the guides are kept and the junk rejected, a run of all-zeroes is a",
        "fact about the search results, not about the judge.",
    ]
    text = "\n".join(lines)
    print(text)
    (args.out / "judge-probe.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
