"""Can the specified rule ever fire? Asked before it is built.

Design: docs/notes/design.detectors-name-consequences.md § 1b

The note specifies the comparison exactly:

    "1b needs a minimum games per opening before an opening may be compared, and
    the comparison must be against *that player's own* other openings rather
    than a population."

    how much worse counts as worse | Wilson intervals must not overlap

`calibrate.py` measured the distribution the floor was to be read from: a median
of **2 games per opening** and **46 % of openings played exactly once**, which
already says the proposed floor of 5 is far too high -- it discards 47 % of games
and leaves one of twelve players with nothing comparable at all.

But the floor and the Wilson test **interact**, and that is the thing worth
knowing before any code is written. A score over 4 games has an interval roughly
half the width of the whole scale, so requiring two such intervals to be disjoint
is a very demanding test. **L-049**: if a positive case cannot be built, the rule
is saying something.

So this sweeps the floor and counts, for each, how many (player, opening) pairs
would actually be claimed -- and how much has to be given up to get one.

    python can_it_fire.py [--window 60]
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.profile.models import wilson_interval  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.pipeline import load_games  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calibrate import BOOK, ROOT, family_of, score_for  # noqa: E402


def halves(scores) -> tuple[int, int]:
    """Score as successes out of doubled games, so draws stay integers.

    A Wilson interval needs whole successes. Chess scores come in halves, so the
    whole scale is doubled rather than a draw being rounded into a win or a loss.
    """
    return int(round(sum(scores) * 2)), len(scores) * 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for path in sorted(ROOT.glob("*.pgn")):
        player = path.stem
        for game in load_games(path)[: args.window]:
            score = score_for(game, player)
            family = family_of(game, book)
            if score is not None and family is not None:
                scores[player][family].append(score)

    lines = [
        "CAN 1b EVER FIRE?",
        "=" * 88, "",
        "For each floor: an opening with at least that many games is compared",
        "against everything else the player played, pooled. It is claimed when",
        "the two Wilson intervals do not overlap -- the note's own rule.",
        "",
        f"  {'floor':>6}{'comparable pairs':>19}{'WORSE':>8}{'better':>8}"
        f"{'players named':>16}",
        "  " + "-" * 60,
    ]

    hits_by_floor: dict[int, list[tuple]] = {}
    for floor in range(2, 11):
        comparable = worse = better = 0
        named: set[str] = set()
        hits: list[tuple] = []
        for player, families in scores.items():
            for family, got in families.items():
                if len(got) < floor:
                    continue
                rest = [s for other, ss in families.items() if other != family for s in ss]
                if len(rest) < floor:
                    continue
                comparable += 1
                lo, hi = wilson_interval(*halves(got))
                rest_lo, rest_hi = wilson_interval(*halves(rest))
                if hi < rest_lo:
                    worse += 1
                    named.add(player)
                    hits.append((player, family, len(got), sum(got) / len(got),
                                 len(rest), sum(rest) / len(rest), "WORSE"))
                elif lo > rest_hi:
                    better += 1
                    hits.append((player, family, len(got), sum(got) / len(got),
                                 len(rest), sum(rest) / len(rest), "better"))
        hits_by_floor[floor] = hits
        lines.append(f"  {floor:>6}{comparable:>19}{worse:>8}{better:>8}{len(named):>16}")

    lines += ["", "=" * 88, "EVERY SEPARATION FOUND, AT ANY FLOOR", "=" * 88, ""]
    seen: set[tuple] = set()
    any_hit = False
    for floor in sorted(hits_by_floor):
        for player, family, n, share, rest_n, rest_share, direction in hits_by_floor[floor]:
            if (player, family) in seen:
                continue
            seen.add((player, family))
            any_hit = True
            lines.append(f"  {direction:<7}{player[:20]:<22}{family[:26]:<28}"
                         f"{share:>6.0%} over {n:>2}   vs {rest_share:>4.0%} over {rest_n:>3}")
    if not any_hit:
        lines += [
            "  NONE. At no floor from 2 to 10 does any opening separate from the",
            "  rest of a player's repertoire by non-overlapping Wilson intervals.",
            "",
            "  That is a result about the rule, not about these players. A score",
            "  over a handful of games carries an interval nearly as wide as the",
            "  scale, and two such intervals cannot come apart. The specified test",
            "  is not reachable at the sample size a real player brings.",
        ]

    lines.append("")
    text = "\n".join(lines) + "\n"
    (args.out / "can-it-fire.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
