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
    matched_sizes: list[int] = []

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
            n = min(len(blitz_games), len(rapid_games))
            if n < MIN_GAMES:
                print(f"  {index:>3} {player}: only {n} matched games", flush=True)
                continue

            # Matched counts: the most recent n of each, so neither sample size
            # nor recency differs between the strata being compared.
            blitz_games = blitz_games[-n:]
            rapid_games = rapid_games[-n:]
            matched_sizes.append(n)

            in_blitz = rates(player, blitz_games, session, peers, args)
            in_rapid = rates(player, rapid_games, session, peers, args)

            shared = 0
            for key in set(in_blitz) & set(in_rapid):
                if in_rapid[key] > 0 and in_blitz[key] > 0:
                    gaps[key].append(in_blitz[key] / in_rapid[key])
                    paired[key].append((in_blitz[key], in_rapid[key]))
                    shared += 1
            print(f"  {index:>3} {player}: {n} games each, {shared} claims in both", flush=True)

    print(f"\n{'=' * 84}")
    print(f"{len(matched_sizes)} players, median {statistics.median(matched_sizes):.0f} "
          f"games per stratum\n")
    print(f"{'claim':<38}{'players':>8}{'median':>9}{'spread':>9}{'corr':>8}")
    print(f"{'':<38}{'':>8}{'gap':>9}{'p90/med':>9}{'b~r':>8}")

    summary = []
    for key, values in sorted(gaps.items()):
        if len(values) < MIN_PLAYERS:
            continue
        ordered = sorted(values)
        median = statistics.median(ordered)
        p90 = ordered[9 * len(ordered) // 10]
        spread = p90 / median if median else float("nan")
        blitz_side = [b for b, _ in paired[key]]
        rapid_side = [r for _, r in paired[key]]
        try:
            corr = statistics.correlation(blitz_side, rapid_side)
        except statistics.StatisticsError:
            corr = float("nan")
        summary.append((spread, key, len(values), median, corr))
        print(f"{key:<38}{len(values):>8}{median:>9.2f}{spread:>9.2f}{corr:>8.2f}")

    if summary:
        spreads = [s for s, *_ in summary]
        medians = [m for *_, m, _ in summary]
        corrs = [c for *_, c in summary if c == c]
        print(f"\nacross {len(summary)} claims:")
        print(f"  gap between speeds        median {statistics.median(medians):.2f}x   "
              f"range {min(medians):.2f}-{max(medians):.2f}x")
        print(f"  how much that gap VARIES  median spread {statistics.median(spreads):.2f}x   "
              f"max {max(spreads):.2f}x")
        if corrs:
            print(f"  blitz rate ~ rapid rate   median r {statistics.median(corrs):+.2f}")
        print("\n  a constant gap with high r  -> pool with a per-speed offset")
        print("  a varying gap or low r      -> stratify, and the gap is diagnostic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
