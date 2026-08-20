"""E41b — is the reviewer's top concern outranked, or is it never measured?

E41 tested the reviewer's proposal — rank by cost instead of by peer excess — and
it agreed with their notes **0 times in 6**, exactly like the shipping ranking,
with a *worse* median overlap (0.0 against 0.5).

Two rules disagreeing about everything and agreeing on the answer means the
ranking rule is not what decides the answer. Which leaves one explanation worth
testing: the claim the reviewer cares about is not losing the ranking, it is
**not in the list being ranked**.

So dump the whole candidate list for the annotated players and find out where
`hangingPawn` and `hangingPiece` actually sit:

    ranked and lost       -> the arbiter is the thing to fix
    measured, no cost     -> the pricing is the thing to fix
    absent entirely       -> the detector or its threshold is, and no ranking
                             change could ever have helped

Usage:
    python where_is_material.py --engine PATH --peers PEERS [--cache CACHE]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e40-derived-ranking"))

from run import claim_family  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
ANNOTATED = ["bjagus", "cademan", "Crossfire1983", "goydorak", "Hirsican", "maikel5"]
WANTED = {"motif:hangingPawn", "motif:hangingPiece"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    tally = {"asserted": 0, "sub_threshold": 0, "absent": 0}

    with engine_session(args.engine, args.depth, args.cache) as session:
        for player in ANNOTATED:
            games = load_games(ROOT / "games" / f"{player}.pgn")[: args.window]
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid", peers=peers,
            )
            result = diagnose(context, default_agents())

            say(f"{player}")
            for family in sorted(WANTED):
                hits = [
                    (pool, f)
                    for pool, bag in (("asserted", result.findings),
                                      ("sub_threshold", result.sub_threshold))
                    for f in bag
                    if claim_family(f.claim.key()) == family
                ]
                if not hits:
                    tally["absent"] += 1
                    say(f"    {family:<24} ABSENT - never became a candidate")
                    continue
                for pool, finding in hits:
                    tally[pool] += 1
                    m = finding.measurement
                    cost = m.cost_per_game
                    say(f"    {family:<24} {pool:<14} "
                        f"rate {m.rate:.1%} vs peer "
                        f"{'--' if m.peer_rate is None else f'{m.peer_rate:.1%}'}  "
                        f"cost {'--' if cost is None else f'{cost:.2f}'}  "
                        f"{m.distinct_games}/{m.games_with_data} games  "
                        f"tier {finding.confidence.tier.value}")
            say()

    say("-" * 70)
    say(f"  asserted (ranked and lost)        {tally['asserted']}")
    say(f"  sub-threshold (priced, outranked) {tally['sub_threshold']}")
    say(f"  absent (never a candidate)        {tally['absent']}")

    (args.out / "where_is_material.txt").write_text("\n".join(lines) + "\n",
                                                    encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
