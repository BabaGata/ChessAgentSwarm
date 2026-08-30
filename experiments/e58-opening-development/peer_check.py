"""Do the development claims separate a 1600 from another 1600?

Design: docs/notes/design.opening-development-signals.md
Evidence so far: docs/notes/experiments.e59-strong-player-expectation.md

**Everything measured up to now compared 1600s with 2600s, which is not the
claim's job.** The expectation comes from strong players, but the claim is
*"you miss it more often than players like you do"* -- and a signal that
separates 1600 from 2600 can still fire equally on every 1600 in the band, in
which case it names nobody and is worthless however large its gap looked.

This is the test that decides whether the three claims reach a report:

1. **spread** -- how far apart are the best and worst players in the band? A
   claim where everyone sits at the same rate cannot rank anyone.
2. **assertions** -- how many of the twelve review players actually get told,
   after the confidence policy and the arbiter have had their say. That is the
   only number that matters operationally.
3. **displacement** -- what these claims push out of the plan, since three new
   claims competing for three slots must take them from something.

    python peer_check.py --engine PATH --peers PATH [--cache PATH]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.opening_development import (  # noqa: E402
    LATE_CASTLING,
    REPEAT_MOVE,
    SLOW_DEVELOPMENT,
)
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

REVIEW = Path(__file__).resolve().parents[2] / "expert-review"
CORPUS = Path(__file__).resolve().parents[2] / "data" / "raw" / "corpus-rapid"
NEW = (SLOW_DEVELOPMENT, LATE_CASTLING, REPEAT_MOVE)


def is_new(key: str) -> bool:
    return any(key.startswith(f"{kind}.") for kind in NEW)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)

    # ---- 1. spread within the band, straight from the reference -----------
    print("DO THE DEVELOPMENT CLAIMS SEPARATE 1600 FROM 1600?")
    print("=" * 74)
    print()
    print("1. SPREAD WITHIN THE BAND")
    print()
    print("Per-player rates from the peer reference itself. A claim whose")
    print("players all sit at the same rate cannot rank anyone, however big its")
    print("gap against 2600s was.")
    print()
    print(f"{'claim':<28}{'players':>8}{'p10':>7}{'median':>8}{'p90':>7}{'spread':>8}")
    print("-" * 66)

    for key, contributions in sorted(peers.cells.items()):
        claim = key.split("|")[-1]
        if not is_new(claim):
            continue
        rates = [
            c.instances / c.opportunities
            for c in contributions
            if c.opportunities >= 10
        ]
        if len(rates) < 10:
            print(f"{claim[:27]:<28}{len(rates):>8}   too few players to judge")
            continue
        low, high = statistics.quantiles(rates, n=10)[0], statistics.quantiles(rates, n=10)[-1]
        print(f"{claim[:27]:<28}{len(rates):>8}{low:>7.0%}"
              f"{statistics.median(rates):>8.0%}{high:>7.0%}{high - low:>8.0%}")

    # ---- 2 & 3. what the review twelve are actually told -------------------
    print()
    print("=" * 74)
    print("2. WHAT THE REVIEW TWELVE ARE TOLD")
    print("=" * 74)
    print()

    rows = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(REVIEW.glob("games/*.pgn")):
            player = path.stem
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid", peers=peers,
            )
            result = diagnose(context, default_agents())
            selection = select_priorities(result.findings, also=result.sub_threshold)
            rows.append((player, result, selection))
            print(f"  {player}: {len(selection.priorities)} priorities", flush=True)

    print()
    print(f"{'player':<24}{'new asserted':>14}{'new watched':>13}{'in plan':>9}   headline")
    print("-" * 78)

    fired = defaultdict(int)
    in_plan = planned_players = 0
    for player, result, selection in rows:
        asserted = [f for f in result.findings if is_new(f.claim.key())]
        watched = [f for f in result.sub_threshold if is_new(f.claim.key())]
        planned = [p for p in selection.priorities if is_new(p.finding.claim.key())]
        for f in asserted:
            fired[f.claim.key()] += 1
        in_plan += len(planned)
        planned_players += int(bool(planned))
        headline = selection.priorities[0].finding.claim.key() if selection.priorities else "-"
        print(f"{player[:23]:<24}{len(asserted):>14}{len(watched):>13}"
              f"{len(planned):>9}   {headline}")

    print()
    print(f"  players with a development claim in their plan: "
          f"{planned_players}/{len(rows)}")
    print(f"  development claims occupying plan slots:        {in_plan}")
    print()
    if fired:
        print("  asserted, by claim:")
        for key, n in sorted(fired.items(), key=lambda kv: -kv[1]):
            print(f"    {key:<34} {n:>2}/{len(rows)} players")
    else:
        print("  NOTHING ASSERTED. The claims survive every screen against 2600s")
        print("  and name nobody in the band, which is the outcome this test")
        print("  exists to catch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
