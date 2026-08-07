"""E25 — is a weakness the whole band shares still worth coaching?

Peer-relative severity (step 3) ranks by what a claim costs a player **above**
what it costs their peers, which stops one expensive-for-everybody claim being
named to 70 % of players (E17). The objection, from the author: a mistake
everyone at your level makes is still a mistake, and fixing it is exactly how you
stop being at that level.

The objection is right about *cost* and the ranking is right about
*personalisation*, so the question that separates them is:

    among claims that are expensive for everyone, which ones do players at
    the top of the band actually commit less often than players at the bottom?

A claim whose rate **falls with rating** is something this band demonstrably
learns to fix -- shared, expensive and learnable, which is the highest-leverage
thing a coach could name. A claim that is **flat across the band** is a property
of chess at this level, and telling someone to fix it says "be better at chess".

The confound, and it is fatal if ignored: rating is largely *determined* by error
rate -- V1 estimates one from the other at ±103 points. So any error-type claim
correlates with rating by construction. Both are therefore measured:

    raw       corr(claim rate, rating)
    divided   corr(claim rate / the player's overall error rate, rating)

The second is L-025's screen -- does it survive dividing out what is already
measured? Only a claim that still falls with rating **after** general skill is
divided out is specifically learnable rather than a shadow of getting better.

Usage:
    python run.py --pgn DIR --blitz DIR --engine PATH --cache DB --peers JSON
"""

from __future__ import annotations

import argparse
import collections
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach import confidence  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.parallel import prefetch  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.profile.models import ConfidenceTier  # noqa: E402
from chesscoach.sections.base import SectionContext, diagnosable  # noqa: E402

BAND = "1400-1800"
MIN_PLAYERS = 15


def force_assertable() -> None:
    """Admit every candidate claim: the gates are not what is being screened."""
    original = confidence.assign_tier

    def permissive(stats):
        decision = original(stats)
        if decision.insufficient_data:
            return decision
        return confidence.TierDecision(
            tier=ConfidenceTier.FOCUS, reasons=decision.reasons, insufficient_data=False
        )

    confidence.assign_tier = permissive
    for module in list(sys.modules.values()):
        if module and getattr(module, "__name__", "").startswith("chesscoach.sections"):
            if hasattr(module, "assign_tier"):
                module.assign_tier = permissive


def own_rating(games, player) -> float | None:
    elos = [
        g.white_elo if g.player_is_white(player) else g.black_elo
        for g in games
    ]
    known = [e for e in elos if e]
    return statistics.mean(known) if known else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--blitz", type=Path, default=None)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)
    force_assertable()

    ratings: list[float] = []
    overall: list[float] = []
    rates: dict[str, list[tuple[int, float]]] = collections.defaultdict(list)
    costs: dict[str, list[float]] = collections.defaultdict(list)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(sorted(args.pgn.glob("*.pgn")), start=1):
            player = path.stem
            games = [g for g in parse_pgn_file(path) if g.involves(player)]
            if args.blitz and (extra := args.blitz / f"{player}.pgn").exists():
                games += [g for g in parse_pgn_file(extra) if g.involves(player)]

            rating = own_rating(games, player)
            corpus = build_corpus(player, games)
            if rating is None or corpus.n_games == 0:
                continue

            prefetch(games, session.cache, engine=args.engine,
                     depth=args.depth, workers=args.workers)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band=BAND, time_control="rapid", peers=peers,
            )

            mine = diagnosable(context.player_observations())
            if not mine:
                continue
            error_rate = sum(1 for o in mine if o.is_error) / len(mine)

            slot = len(ratings)
            ratings.append(rating)
            overall.append(error_rate)
            for finding in diagnose(context, default_agents()).findings:
                key = finding.claim.key()
                if finding.measurement.rate:
                    rates[key].append((slot, finding.measurement.rate))
                cost = finding.measurement.cost_per_game
                if cost:
                    costs[key].append(cost)

            print(f"  {index:>3} {player}: rating {rating:.0f}, "
                  f"error rate {error_rate:.1%}", flush=True)

    print(f"\n{'=' * 88}")
    print(f"{len(ratings)} players, rating {min(ratings):.0f}-{max(ratings):.0f}, "
          f"median error rate {statistics.median(overall):.1%}\n")
    print(f"{'claim':<38}{'players':>8}{'cost/game':>11}{'raw r':>8}{'divided r':>11}")

    rows = []
    for key, pairs in sorted(rates.items()):
        if len(pairs) < MIN_PLAYERS:
            continue
        slots = [s for s, _ in pairs]
        values = [v for _, v in pairs]
        who = [ratings[s] for s in slots]
        # Divided by the player's own overall error rate: what is left is how
        # much of this claim is *specific* rather than a shadow of general skill.
        relative = [v / overall[s] for s, v in pairs if overall[s] > 0]
        who_relative = [ratings[s] for s, _ in pairs if overall[s] > 0]

        try:
            raw = statistics.correlation(values, who)
        except statistics.StatisticsError:
            continue
        try:
            divided = statistics.correlation(relative, who_relative)
        except statistics.StatisticsError:
            divided = float("nan")

        typical = statistics.median(costs[key]) if costs.get(key) else 0.0
        rows.append((typical, key, len(pairs), raw, divided))

    for typical, key, n, raw, divided in sorted(rows, reverse=True):
        shown = f"{divided:>11.2f}" if divided == divided else f"{'-':>11}"
        print(f"{key:<38}{n:>8}{typical:>11.1f}{raw:>8.2f}{shown}")

    priced = [r for r in rows if r[0] > 0]
    if priced:
        print(f"\nacross {len(priced)} claims that can price themselves:")
        print(f"  median raw correlation with rating       "
              f"{statistics.median([r[3] for r in priced]):+.2f}")
        divided_all = [r[4] for r in priced if r[4] == r[4]]
        if divided_all:
            print(f"  median AFTER dividing out general skill  "
                  f"{statistics.median(divided_all):+.2f}")
        learnable = [r for r in priced if r[4] == r[4] and r[4] < -0.2]
        print(f"\n  claims still falling with rating after the division: "
              f"{len(learnable)} of {len(divided_all)}")
        for typical, key, _, raw, divided in sorted(learnable)[:10]:
            print(f"    {key:<38} {typical:>6.1f}/game   r {divided:+.2f}")
        print("\n  a steep negative here = shared, expensive AND demonstrably learnable")
        print("  flat = a property of the band, and 'fix this' means 'be better at chess'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
