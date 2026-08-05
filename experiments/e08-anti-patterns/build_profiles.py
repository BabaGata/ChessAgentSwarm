"""Generate current profiles for a set of players, so the anti-pattern metrics
have something real to measure.

The profiles left over from earlier cycles predate the planner, so they carry
findings and no plan — and D1 asks what a player is actually *told*, which is
the plan. One process rather than repeated CLI calls, so the engine and cache
are opened once.

Usage:
    python build_profiles.py --pgn DIR --engine PATH --cache DB --peers JSON --out DIR
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.parallel import prefetch  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.orchestrator import apply_to_profile, default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.planner import build_plan  # noqa: E402
from chesscoach.profile.io import save_profile  # noqa: E402
from chesscoach.profile.models import PlayerProfile, PlayerRef  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

BAND = "1400-1800"
TIME_CONTROL = "rapid"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    peers = PeerReference.load(args.peers)
    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"{len(paths)} players\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            player = path.stem
            games = parse_pgn_file(path)
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                print(f"  {index:>3}/{len(paths)} {player}: no games", flush=True)
                continue

            prefetch(games, session.cache, engine=args.engine,
                     depth=args.depth, workers=args.workers)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations,
                corpus,
                session.provenance(corpus.corpus_id),
                band=BAND,
                time_control=TIME_CONTROL,
                peers=peers,
            )

            profile = apply_to_profile(
                PlayerProfile(
                    player=PlayerRef(source="lichess", username=player, band=BAND),
                    corpus=corpus.to_ref(),
                ),
                diagnose(context, default_agents()),
            )
            selection = select_priorities(profile.findings)
            profile = replace(
                profile,
                plan=build_plan(
                    selection.priorities,
                    created=date.today().isoformat(),
                    peers=peers,
                    band=BAND,
                    time_control=TIME_CONTROL,
                    player=player,
                ),
            )
            save_profile(profile, args.out / f"{player}.json")
            steps = len(profile.plan.steps) if profile.plan else 0
            print(f"  {index:>3}/{len(paths)} {player}: "
                  f"{len(profile.findings)} findings, {steps} steps", flush=True)

    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
