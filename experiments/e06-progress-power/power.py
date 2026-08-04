"""E06 — does the progress check have any power?

E05 measured the **false-positive** rate: 15-23 % of untreated players meet
their target by drift. It says nothing about the other side. A target that is
well calibrated against drift but unreachable by real improvement would look
exactly like the present state, and every "not met" verdict would be
uninformative.

No coached cohort exists, and one cannot be bought under C1. The nearest free
proxy is **players whose rating climbed over the split**: not coached, but
demonstrably improving at something.

The confound, stated up front because it decides how the result may be read:
rating and error rate both regress. A player whose earlier half was a bad patch
has a depressed rating *and* an inflated error rate, and both recover together
without anyone improving. So the two possible outcomes are not symmetric:

  * **improvers meet targets no more often than the rest** -> strong evidence.
    Regression works *for* the alternative here, so a null survives it.
  * **improvers meet targets more often** -> weak evidence, because regression
    predicts exactly that. It would not establish power.

Reported both ways: a dichotomy, and a correlation that does not depend on
where the cut is drawn.

Usage:
    python power.py --results DIR/results.json --histories DIR

Named `power.py`, not `run.py`, because E05's entry point is already `run` and
two modules of the same name on `sys.path` resolve to whichever was imported
first — which made this file import itself.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e05-natural-drift"))
from run import split_by_date  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.ingest.pgn import GameRecord, parse_pgn_file  # noqa: E402
from chesscoach.planner import NO_CHANGE_RATIO  # noqa: E402

# A rated game only. Unrated ones carry no Elo and would silently average in.
MIN_RATED_GAMES_PER_PERIOD = 5


@dataclass(frozen=True)
class PlayerPower:
    player: str
    rating_change: float
    met: int
    judged: int
    improvements: list[float]
    # How inflated the earlier measurement was against its own no-change
    # estimate. This is the confound's fingerprint: if rating gain is really
    # regression wearing a disguise, the players who gained should be the ones
    # whose earlier rate was most extreme.
    extremity: list[float]


def player_rating(game: GameRecord, player: str) -> int | None:
    return game.white_elo if game.player_is_white(player) else game.black_elo


def mean_rating(games: list[GameRecord], player: str) -> float | None:
    ratings = [r for g in games if (r := player_rating(g, player)) is not None]
    if len(ratings) < MIN_RATED_GAMES_PER_PERIOD:
        return None
    return statistics.mean(ratings)


def rating_change(path: Path, player: str) -> float | None:
    """Mean rating in the later period minus the earlier one."""
    early, late = split_by_date(parse_pgn_file(path))
    before, after = mean_rating(early, player), mean_rating(late, player)
    if before is None or after is None:
        return None
    return after - before


def judgeable(outcome: dict) -> bool:
    """Everything needed to re-decide the verdict from scratch."""
    return (
        outcome["status"] in ("met", "not_met")
        and outcome.get("after") is not None
        and outcome.get("expected")
        and outcome.get("before") is not None
    )


def was_met(outcome: dict, ratio: float) -> bool:
    """Recomputed, never read from `status`.

    The stored verdict was decided by whichever constant was in force when the
    run happened — 0.34 for this corpus, which is no longer the rule. Since
    `expected` is recorded per prediction and does not depend on the target rule,
    the verdict is arithmetic and can be redecided for any constant.
    """
    return outcome["after"] <= outcome["expected"] * ratio


def collect(results: Path, histories: Path, ratio: float) -> list[PlayerPower]:
    data = json.loads(results.read_text(encoding="utf-8"))

    collected = []
    for entry in data["per_player"]:
        judged = [o for o in entry["outcomes"] if judgeable(o)]
        if not judged:
            continue

        change = rating_change(histories / f"{entry['player']}.pgn", entry["player"])
        if change is None:
            continue

        collected.append(
            PlayerPower(
                player=entry["player"],
                rating_change=change,
                met=sum(1 for o in judged if was_met(o, ratio)),
                judged=len(judged),
                improvements=[o["before"] - o["after"] for o in judged],
                extremity=[o["before"] / o["expected"] for o in judged],
            )
        )
    return collected


def fisher_one_sided(met_a: int, n_a: int, met_b: int, n_b: int) -> float:
    """P(a separation this large or larger, if the groups are really the same).

    Written out rather than imported: scipy is a heavy dependency for one
    hypergeometric sum, and C1 prefers the cheap route. Four events against
    three is exactly the regime where an eyeballed "clearly better" is how R-13
    happens, so the number is computed.
    """
    total, met_total = n_a + n_b, met_a + met_b

    def probability(k: int) -> float:
        return (
            math.comb(met_total, k)
            * math.comb(total - met_total, n_a - k)
            / math.comb(total, n_a)
        )

    upper = min(met_total, n_a)
    return sum(probability(k) for k in range(met_a, upper + 1))


def correlation(xs: list[float], ys: list[float]) -> float | None:
    """Pearson r. Reported because it does not depend on where a cut is drawn."""
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(xs, ys)


def _rate(met: int, judged: int) -> str:
    return f"{met}/{judged} ({100 * met / judged:.0f}%)" if judged else "—"


def report(players: list[PlayerPower], ratio: float) -> None:
    print(f"verdicts recomputed at NO_CHANGE_RATIO = {ratio}\n")
    ordered = sorted(players, key=lambda p: p.rating_change, reverse=True)
    cut = len(ordered) // 3 or 1
    improvers, rest = ordered[:cut], ordered[cut:]

    print(f"{len(players)} players with a judged prediction and a rating on both sides\n")
    print(f"rating change   median {statistics.median(p.rating_change for p in players):+.0f}, "
          f"min {ordered[-1].rating_change:+.0f}, max {ordered[0].rating_change:+.0f}\n")

    counts = {}
    for label, group in (("improvers (top third)", improvers), ("the rest", rest)):
        met = sum(p.met for p in group)
        judged = sum(p.judged for p in group)
        counts[label] = (met, judged)
        change = statistics.mean([p.rating_change for p in group])
        print(f"  {label:<24} n={len(group):<3} mean rating {change:+6.1f}   met {_rate(met, judged)}")

    (met_a, n_a), (met_b, n_b) = counts["improvers (top third)"], counts["the rest"]
    p = fisher_one_sided(met_a, n_a, met_b, n_b)
    print(f"\n  Fisher exact, one-sided                p = {p:.3f}"
          f"{'  — not significant' if p >= 0.05 else ''}")

    # Per prediction, so a player with two findings counts twice - the unit of
    # analysis is the prediction, as it is throughout E05.
    xs = [p.rating_change for p in players for _ in p.improvements]
    ys = [improvement for p in players for improvement in p.improvements]
    extremity = [e for p in players for e in p.extremity]

    print("\n" + "=" * 60)
    print(f"predictions                              {len(ys)}")
    _print_corr("corr(rating change, rate improvement)", correlation(xs, ys),
                "players who gained rating also cut their error rate")
    _print_corr("corr(rating change, early extremity)", correlation(xs, extremity),
                "THE CONFOUND: gainers were the ones measured at their worst")


def _print_corr(label: str, r: float | None, meaning: str) -> None:
    if r is None:
        print(f"{label}   not computable")
        return
    print(f"{label}   r = {r:+.3f}")
    print(f"    positive = {meaning}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--histories", required=True, type=Path)
    parser.add_argument("--ratio", type=float, default=NO_CHANGE_RATIO)
    args = parser.parse_args()

    players = collect(args.results, args.histories, args.ratio)
    if not players:
        print("no players with both a judged prediction and ratings")
        return 1

    report(players, args.ratio)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
