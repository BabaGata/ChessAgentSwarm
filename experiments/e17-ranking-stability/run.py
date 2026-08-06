"""E17 — can a weakness ranking be trusted at 20 games?

A proposal on the table replaces the confidence gates with an importance score
(rate, severity, recency, game length) and takes the top-scoring claims, so the
swarm always says something whatever the history length. The appeal is real:
[[experiments.e16-shallow-corpus]] showed the gates silence 43 % of players at 24
games, and a re-evaluation after coaching can only ever bring ~20 new games.

The premise underneath it is testable, and it is not about weights: **is the
ranking itself stable at 20 games?** A score is a point estimate, and ranking by
a point estimate from a small sample selects for whichever claim is noisiest —
R-15 (regression to the mean) acting at selection time rather than at
re-measurement time. If two disjoint windows of the same player disagree about
what matters most, no choice of weights repairs that.

Method: split each history into two **disjoint, adjacent** windows of equal size,
force every candidate claim past the gates — since removing the gates is the
proposal — and rank them three ways:

    deviation      rate / peer rate, what the arbiter ranked on before E15
    severity       win probability given away per game, what E15 added
    deviation x severity   the proposal's core

Then measure how often the two windows pick the same top claim, against the
agreement two random picks from the same pool would give.

Usage:
    python run.py --pgn DIR --engine PATH --cache DB --peers JSON
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
from chesscoach.sections.base import SectionContext  # noqa: E402

BAND = "1400-1800"
TIME_CONTROL = "rapid"
WINDOWS = (20, 60)

SCORES = {
    "deviation": lambda m: (m.lift_vs_peer or m.lift_vs_baseline or 1.0),
    "severity": lambda m: (m.cost_per_game or 0.0),
    "deviation x severity": lambda m: (m.lift_vs_peer or m.lift_vs_baseline or 1.0)
    * (m.cost_per_game or 0.0),
}


def force_assertable() -> None:
    """Let every candidate claim through, because that is what is proposed.

    A section that declines for lack of data still declines — that is a missing
    measurement, not a suppressed one. Everything else is admitted so the ranking
    can be judged on the claims the gates would have hidden.
    """
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


def rank_window(games, player, session, peers, args) -> dict[str, list[str]]:
    """Rank this window's claims by each candidate score."""
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return {}
    prefetch(games, session.cache, engine=args.engine, depth=args.depth, workers=args.workers)
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band=BAND, time_control=TIME_CONTROL, peers=peers,
    )
    findings = diagnose(context, default_agents()).findings
    ranked = {}
    ties = {}
    for name, score in SCORES.items():
        scored = [(f.claim.key(), score(f.measurement)) for f in findings]
        scored = [(key, value) for key, value in scored if value > 0]
        ranked[name] = [key for key, _ in sorted(scored, key=lambda pair: -pair[1])]
        # How much of this ranking is real ordering rather than arbitrary
        # tie-breaking? A score where every claim takes the same value ranks at
        # chance no matter how good the idea behind it is.
        ties[name] = (len({round(v, 6) for _, v in scored}), len(scored))
    return ranked, ties


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)
    paths = sorted(args.pgn.glob("*.pgn"))
    force_assertable()

    agree: dict = {(s, n, t): [] for s in WINDOWS for n in SCORES for t in (1, 2)}
    expected: dict = {(s, n): [] for s in WINDOWS for n in SCORES}
    pool_sizes: dict = {s: [] for s in WINDOWS}
    # Stability is worthless if it comes from every player getting the same
    # answer -- that is anti-pattern D2, a description rather than a diagnosis.
    winners: dict = {(s, n): collections.Counter() for s in WINDOWS for n in SCORES}
    # And "deviation looks like chance" would be an artifact if most claims tie
    # at 1.0, because then the sort order is arbitrary by construction.
    distinct_scores: dict = {n: [] for n in SCORES}

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            player = path.stem
            games = sorted(parse_pgn_file(path), key=lambda g: (g.date or "", g.game_id))
            line = f"  {index:>3}/{len(paths)} {player}:"

            for size in WINDOWS:
                if len(games) < 2 * size:
                    line += f"  {size}:--"
                    continue
                earlier, _ = rank_window(
                    tuple(games[-2 * size:-size]), player, session, peers, args)
                recent, ties = rank_window(tuple(games[-size:]), player, session, peers, args)

                for name in SCORES:
                    first, second = earlier.get(name, []), recent.get(name, [])
                    if not first or not second:
                        continue
                    if size == 20 and name in ties and ties[name][1]:
                        distinct_scores[name].append(ties[name][0] / ties[name][1])
                    winners[(size, name)][second[0]] += 1
                    for top in (1, 2):
                        if len(first) >= top and len(second) >= top:
                            agree[(size, name, top)].append(
                                len(set(first[:top]) & set(second[:top])) / top
                            )
                    # What agreement chance alone would give, from the same pool.
                    pool = set(first) | set(second)
                    if pool:
                        expected[(size, name)].append(1 / len(pool))
                        pool_sizes[size].append(len(pool))

                shown = agree[(size, "deviation x severity", 1)]
                line += f"  {size}:{shown[-1]:.0%}" if shown else f"  {size}:--"
            print(line, flush=True)

    print(f"\n{'=' * 78}")
    print("Two disjoint windows of the SAME player — do they agree on what matters most?\n")
    print(f"{'window':>7}  {'score':<22}  {'players':>7}  {'top-1':>7}  {'top-2':>7}  "
          f"{'chance':>7}")
    for size in WINDOWS:
        for name in SCORES:
            top1 = agree[(size, name, 1)]
            top2 = agree[(size, name, 2)]
            if not top1:
                continue
            baseline = statistics.mean(expected[(size, name)])
            print(f"{size:>7}  {name:<22}  {len(top1):>7}  "
                  f"{statistics.mean(top1):>6.0%}  {statistics.mean(top2):>6.0%}  "
                  f"{baseline:>6.0%}")
        if pool_sizes[size]:
            print(f"{'':>7}  {'(claims to choose from: ':<22}  "
                  f"{statistics.mean(pool_sizes[size]):.0f})")

    print("\nIs the ranking a real ordering, or arbitrary tie-breaking?")
    print("  share of a player's claims holding a DISTINCT score, at 20 games:")
    for name, shares in distinct_scores.items():
        if shares:
            print(f"    {name:<22} {statistics.mean(shares):.0%}")

    print("\nStable, or just the same answer for everybody? (top claim at 20 games)")
    for name in SCORES:
        counter = winners[(20, name)]
        if not counter:
            continue
        total = sum(counter.values())
        top, count = counter.most_common(1)[0]
        print(f"  {name:<22} {len(counter):>2} distinct winners over {total} players; "
              f"most common {count / total:>4.0%}  ({top})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
