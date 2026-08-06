"""E19 — is blitz a second stratum, or the same player with an offset?

Step 5 of [[design.short-history-prioritisation]] would admit the ~82 % of a
player's games the swarm currently discards. Before building it, the question
that decides its shape, and it is the L-023/L-025 screen applied to a corpus
rather than to a claim:

  **does a claim's blitz-versus-rapid gap vary between players, or is it a
  constant of chess?**

  constant  -> pool the two with a per-speed offset. One corpus, ~5x the
               evidence, and the rarity gate that silences half of players
               (E16) is directly attacked.

  varies    -> stratify. Three corpora, three peer references, and the gap
               itself becomes diagnostic: under three minutes a player plays
               what is internalised, over ten what they can work out, so the
               difference may separate SKILL from FRAGILE for free -- which the
               prober currently has to ask a player about.

Method: the same players, both speeds, **matched game counts** so neither the
sample size nor the period differs between strata. Gates forced open, because a
screen must see the claims the gates would hide.

Usage:
    python run.py --rapid DIR --blitz DIR --engine PATH --cache DB --peers JSON
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

# Below this many games in a stratum the player's rates are noise.
MIN_GAMES = 15

# A claim needs this many players contributing a gap before its spread means
# anything.
MIN_PLAYERS = 8


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


def rates(player, games, session, peers, args) -> dict[str, float]:
    """Every claim's rate for this player in this stratum."""
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return {}
    prefetch(games, session.cache, engine=args.engine, depth=args.depth, workers=args.workers)
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band=BAND, time_control="rapid", peers=peers,
    )
    # `peers` is the rapid-built reference and is passed only so that
    # selection-confounded conditions are not withheld for want of one. Nothing
    # here reads a peer rate -- the screen compares a player against themselves.
    return {
        f.claim.key(): f.measurement.rate
        for f in diagnose(context, default_agents()).findings
        if f.measurement.rate is not None
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapid", required=True, type=Path)
    parser.add_argument("--blitz", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)
    force_assertable()

    gaps: dict[str, list[float]] = collections.defaultdict(list)
    paired: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    # The control that decides everything. A low blitz~rapid correlation means
    # nothing on its own: at ~45 games these rates are noisy, and noise
    # attenuates any correlation towards zero. The only interpretable question is
    # whether blitz predicts rapid **worse than rapid predicts itself** at the
    # same sample size -- so rapid is split into two disjoint windows and
    # correlated with itself as a ceiling.
    control: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    matched_sizes: list[int] = []
    # A player's blitz rating is often not their rapid rating, so the two strata
    # may face different opposition. Free to check, from the PGN tags.
    own_elo: dict[str, list[float]] = {"blitz": [], "rapid": []}

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(sorted(args.rapid.glob("*.pgn")), start=1):
            player = path.stem
            blitz_path = args.blitz / f"{player}.pgn"
            if not blitz_path.exists():
                continue

            blitz_games = [g for g in parse_pgn_file(blitz_path) if g.involves(player)]
            rapid_games = sorted(
                (g for g in parse_pgn_file(path) if g.involves(player)),
                key=lambda g: (g.date or "", g.game_id),
            )
            # Two disjoint rapid windows are needed for the control, so the
            # matched size is capped at half the rapid history.
            n = min(len(blitz_games), len(rapid_games) // 2)
            if n < MIN_GAMES:
                print(f"  {index:>3} {player}: only {n} matched games", flush=True)
                continue

            # Matched counts throughout: neither sample size nor recency differs
            # between any two strata being compared.
            blitz_games = blitz_games[-n:]
            recent_rapid = rapid_games[-n:]
            earlier_rapid = rapid_games[-2 * n:-n]
            matched_sizes.append(n)

            for label, games in (("blitz", blitz_games), ("rapid", recent_rapid)):
                elos = [g.white_elo if g.player_is_white(player) else g.black_elo
                        for g in games]
                known = [e for e in elos if e]
                if known:
                    own_elo[label].append(statistics.mean(known))

            in_blitz = rates(player, blitz_games, session, peers, args)
            in_rapid = rates(player, recent_rapid, session, peers, args)
            in_earlier = rates(player, earlier_rapid, session, peers, args)

            shared = 0
            for key in set(in_blitz) & set(in_rapid):
                if in_rapid[key] > 0 and in_blitz[key] > 0:
                    gaps[key].append(in_blitz[key] / in_rapid[key])
                    paired[key].append((in_blitz[key], in_rapid[key]))
                    shared += 1
            for key in set(in_earlier) & set(in_rapid):
                if in_rapid[key] > 0 and in_earlier[key] > 0:
                    control[key].append((in_earlier[key], in_rapid[key]))
            print(f"  {index:>3} {player}: {n} games each, {shared} claims in both", flush=True)

    print(f"\n{'=' * 84}")
    print(f"{len(matched_sizes)} players, median {statistics.median(matched_sizes):.0f} "
          f"games per stratum\n")
    def corr_of(pairs):
        if len(pairs) < MIN_PLAYERS:
            return float("nan")
        try:
            return statistics.correlation([a for a, _ in pairs], [b for _, b in pairs])
        except statistics.StatisticsError:
            return float("nan")

    print(f"{'claim':<38}{'players':>8}{'gap':>7}{'spread':>8}"
          f"{'blitz':>8}{'rapid':>8}{'ratio':>7}")
    print(f"{'':<38}{'':>8}{'med':>7}{'p90/med':>8}"
          f"{'~rapid':>8}{'~rapid':>8}{'':>7}")

    summary = []
    control_spreads: list[float] = []
    for key, values in sorted(gaps.items()):
        if len(values) < MIN_PLAYERS:
            continue
        ordered = sorted(values)
        median = statistics.median(ordered)
        p90 = ordered[9 * len(ordered) // 10]
        spread = p90 / median if median else float("nan")
        cross, ceiling = corr_of(paired[key]), corr_of(control[key])
        # The gap spread needs the same control as the correlation did. A ratio
        # of two noisy rates is itself very noisy, so "the gap varies 2.4x
        # between players" means nothing until rapid's ratio against *itself* is
        # measured the same way.
        same_speed = sorted(a / b for a, b in control[key] if b > 0)
        if len(same_speed) >= MIN_PLAYERS:
            same_median = statistics.median(same_speed)
            if same_median:
                control_spreads.append(
                    same_speed[9 * len(same_speed) // 10] / same_median
                )
        # How much of rapid's own self-agreement does blitz recover? 1.0 means
        # blitz is as good a predictor of rapid as rapid itself is.
        share = cross / ceiling if ceiling == ceiling and ceiling > 0.05 else float("nan")
        summary.append((key, len(values), median, spread, cross, ceiling, share))
        print(f"{key:<38}{len(values):>8}{median:>7.2f}{spread:>8.2f}"
              f"{cross:>8.2f}{ceiling:>8.2f}"
              + (f"{share:>7.2f}" if share == share else f"{'-':>7}"))

    if summary:
        medians = [m for _, _, m, *_ in summary]
        spreads = [s for _, _, _, s, *_ in summary]
        crosses = [c for *_, c, _, _ in summary if c == c]
        ceilings = [c for *_, c, _ in summary if c == c]
        shares = [s for *_, s in summary if s == s]
        print(f"\nacross {len(summary)} claims:")
        print(f"  gap between speeds          median {statistics.median(medians):.2f}x   "
              f"range {min(medians):.2f}-{max(medians):.2f}x")
        print(f"  how much that gap VARIES    median spread {statistics.median(spreads):.2f}x")
        if control_spreads:
            print(f"  the same, rapid vs ITSELF   median spread "
                  f"{statistics.median(control_spreads):.2f}x"
                  "   <- what noise alone produces")
        print(f"  blitz predicts rapid        median r {statistics.median(crosses):+.2f}")
        print(f"  rapid predicts ITSELF       median r {statistics.median(ceilings):+.2f}"
              "   <- the ceiling noise allows")
        if shares:
            print(f"  share of the ceiling blitz recovers   "
                  f"median {statistics.median(shares):.0%}")
        for label, values in own_elo.items():
            if values:
                print(f"  mean own rating, {label:<7} {statistics.mean(values):>7.0f}")
        print("\n  blitz ~= the ceiling  -> the speeds are interchangeable; POOL")
        print("  blitz << the ceiling  -> blitz measures something else; STRATIFY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
