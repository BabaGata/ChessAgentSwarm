"""E23 — do a player's older games still describe them?

Step 7 of [[design.short-history-prioritisation]] proposes decaying a game's
weight by its age, on the reasoning that players drift and a game from years ago
is a different player. The reasoning is plausible and the cost is real: decay
**spends effective sample size**, which [[experiments.e16-shallow-corpus]] found
to be the binding constraint, and [[experiments.e20-shrinkage]] is a fresh
reminder that plausible reasoning about this system has been wrong before.

So the question is measured before anything is built, with the control that
[[experiments.e19-blitz-stratum]] showed to be indispensable:

    does an OLD window predict a player's recent behaviour worse than a
    RECENT window predicts it?

Three disjoint windows of equal size per player -- recent, middle, old. The
middle-against-recent correlation is the **ceiling** that noise allows at this
sample size; the old-against-recent correlation is the same measurement two
windows further back. If they match, age costs nothing and decay is unjustified.
If the old one is markedly worse, the calendar gap between the windows says
roughly what half-life would be right.

Usage:
    python run.py --pgn DIR --engine PATH --cache DB --peers JSON
"""

from __future__ import annotations

import argparse
import collections
import datetime
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
WINDOW = 40
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
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return {}
    prefetch(games, session.cache, engine=args.engine, depth=args.depth, workers=args.workers)
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band=BAND, time_control="rapid", peers=peers,
    )
    return {
        f.claim.key(): f.measurement.rate
        for f in diagnose(context, default_agents()).findings
        if f.measurement.rate is not None
    }


def midpoint(games) -> datetime.date | None:
    dates = sorted(
        datetime.date.fromisoformat(g.date.replace(".", "-"))
        for g in games
        if g.date
    )
    return dates[len(dates) // 2] if dates else None


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
    force_assertable()

    near: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    far: dict[str, list[tuple[float, float]]] = collections.defaultdict(list)
    near_gap: list[int] = []
    far_gap: list[int] = []
    by_gap: dict[str, list[tuple[int, float, float]]] = collections.defaultdict(list)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(sorted(args.pgn.glob("*.pgn")), start=1):
            player = path.stem
            games = sorted(
                (g for g in parse_pgn_file(path) if g.involves(player)),
                key=lambda g: (g.date or "", g.game_id),
            )
            if len(games) < 3 * WINDOW:
                continue

            recent = tuple(games[-WINDOW:])
            middle = tuple(games[-2 * WINDOW:-WINDOW])
            old = tuple(games[-3 * WINDOW:-2 * WINDOW])

            for label, window, store in (
                ("middle", middle, near_gap), ("old", old, far_gap)
            ):
                here, there = midpoint(recent), midpoint(window)
                if here and there:
                    store.append((here - there).days)

            in_recent = rates(player, recent, session, peers, args)
            in_middle = rates(player, middle, session, peers, args)
            in_old = rates(player, old, session, peers, args)

            here, back = midpoint(recent), midpoint(old)
            gap = (here - back).days if here and back else None

            for other, store in ((in_middle, near), (in_old, far)):
                for key in set(in_recent) & set(other):
                    if in_recent[key] > 0 and other[key] > 0:
                        store[key].append((other[key], in_recent[key]))

            # The case that motivates decay is a *years*-old game, not a
            # months-old one. Kept separately so the two can be compared:
            # a median gap of four months would otherwise hide the tail.
            if gap is not None:
                for key in set(in_recent) & set(in_old):
                    if in_recent[key] > 0 and in_old[key] > 0:
                        by_gap[key].append((gap, in_old[key], in_recent[key]))

            print(f"  {index:>3} {player}: {len(in_recent)} claims", flush=True)

    def corr_of(pairs):
        if len(pairs) < MIN_PLAYERS:
            return float("nan")
        try:
            return statistics.correlation([a for a, _ in pairs], [b for _, b in pairs])
        except statistics.StatisticsError:
            return float("nan")

    print(f"\n{'=' * 76}")
    print("Does an OLD window predict recent play worse than a RECENT one?\n")
    print(f"{'claim':<38}{'players':>8}{'middle':>9}{'old':>8}{'ratio':>8}")

    ratios, nears, fars = [], [], []
    for key in sorted(set(near) | set(far)):
        a, b = corr_of(near[key]), corr_of(far[key])
        if a != a or b != b:
            continue
        nears.append(a)
        fars.append(b)
        ratio = b / a if abs(a) > 0.05 else float("nan")
        if ratio == ratio:
            ratios.append(ratio)
        print(f"{key:<38}{len(near[key]):>8}{a:>9.2f}{b:>8.2f}"
              + (f"{ratio:>8.2f}" if ratio == ratio else f"{'-':>8}"))

    print(f"\nacross {len(nears)} claims:")
    print(f"  middle window predicts recent   median r {statistics.median(nears):+.2f}"
          "   <- the ceiling")
    print(f"  old window predicts recent      median r {statistics.median(fars):+.2f}")
    if ratios:
        print(f"  share of the ceiling the old window keeps   "
              f"median {statistics.median(ratios):.0%}")
    if near_gap and far_gap:
        print(f"\n  calendar gap to the middle window   median "
              f"{statistics.median(near_gap):.0f} days")
        print(f"  calendar gap to the old window      median "
              f"{statistics.median(far_gap):.0f} days")
    # Does the tail behave differently from the median? Split each claim's
    # players at a year and correlate the halves separately.
    A_YEAR = 365
    fresh_side, stale_side = [], []
    counted = 0
    for key, rows in by_gap.items():
        recent_half = [(o, r) for gap, o, r in rows if gap < A_YEAR]
        old_half = [(o, r) for gap, o, r in rows if gap >= A_YEAR]
        a, b = corr_of(recent_half), corr_of(old_half)
        if a == a and b == b:
            fresh_side.append(a)
            stale_side.append(b)
            counted += 1

    print(f"\nSplitting each claim's players at a year of separation:")
    if counted:
        print(f"  windows under a year apart   median r {statistics.median(fresh_side):+.2f}")
        print(f"  windows over  a year apart   median r {statistics.median(stale_side):+.2f}"
              f"   ({counted} claims had enough of both)")
    else:
        every = [gap for rows in by_gap.values() for gap, _, _ in rows]
        over = sum(1 for g in every if g >= A_YEAR)
        print(f"  not enough players on both sides to compare "
              f"({over} of {len(every)} pairs are over a year)")
        print("  -> this corpus cannot answer the years-old case at all")

    print("\n  old ~= middle  -> age costs nothing; decay is unjustified")
    print("  old << middle  -> age matters, and the gaps suggest the half-life")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
