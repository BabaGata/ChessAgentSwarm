"""E42 — how much do the swarm's claims describe the same moves?

[[experiments.e41-cost-ranking]] found the reviewer's top concern losing to
`early_error`, which tallies *every* diagnosable error in the opening window —
hung pieces included. That makes cost a function of category width, and it makes
a top three potentially three descriptions of one set of mistakes.

`drop_redundant_aggregates` already handles this **inside** a section, using the
pooled-subject convention. Across sections there is no such convention, and
inventing a table of which claim contains which would be fabricated pedagogy that
goes stale the first time a section changes what it counts.

So measure it instead. Every claim now reports `instances_at` — the (game_id,
ply) of every instance — so containment is an observable rather than an
assertion.

Three questions, in the order that decides the rule:

    1. How much do the SHIPPED three overlap? That is the defect as the player
       experiences it.
    2. Across all candidate pairs, is there a clean containment structure, or
       only diffuse partial overlap? A rule is only justified if the first.
    3. Where would a threshold sit, and is the answer stable or a knife edge?

Usage:
    python run.py --engine PATH --peers PEERS [--cache CACHE] [--window 20]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"


def moves(finding) -> frozenset:
    return frozenset(finding.measurement.instances_at)


def covered(wide, narrow) -> float:
    """Fraction of `wide`'s instances that `narrow` also claims."""
    w, n = moves(wide), moves(narrow)
    return len(w & n) / len(w) if w else 0.0


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

    shipped_overlaps: list[float] = []
    pair_coverages: list[float] = []
    unreported = 0
    top_pairs: list[tuple[float, str, str, str]] = []
    players = 0
    shipped_sharing: Counter = Counter()

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
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
            everything = [f for f in result.findings + result.sub_threshold]
            unreported += sum(1 for f in everything if not f.measurement.instances_at)
            players += 1

            # 1. the shipped three
            selection = select_priorities(result.findings, limit=3, also=result.sub_threshold)
            chosen = [p.finding for p in selection.priorities]
            say(f"{player}  ({len(everything)} candidates)")
            for i, a in enumerate(chosen):
                for b in chosen[i + 1:]:
                    share = len(moves(a) & moves(b))
                    smaller = min(len(moves(a)), len(moves(b))) or 1
                    frac = share / smaller
                    shipped_overlaps.append(frac)
                    if frac >= 0.5:
                        shipped_sharing[player] += 1
                    say(f"    {a.claim.key():<34} vs {b.claim.key():<34} "
                        f"share {share:>4} = {frac:.0%} of the smaller")

            # 2. every candidate pair, both directions
            for a in everything:
                for b in everything:
                    if a.id == b.id or not moves(a) or not moves(b):
                        continue
                    if len(moves(a)) < len(moves(b)):
                        continue
                    c = covered(a, b)
                    pair_coverages.append(c)
                    if c >= 0.5:
                        top_pairs.append((c, player, a.claim.key(), b.claim.key()))
            say()

    say("=" * 78)
    say(f"players {players}   candidate claims not reporting instances: {unreported}")
    say()
    say("1. THE SHIPPED THREE - how much of the smaller claim the other one repeats")
    if shipped_overlaps:
        say(f"   pairs {len(shipped_overlaps)}   median {statistics.median(shipped_overlaps):.0%}"
            f"   mean {statistics.mean(shipped_overlaps):.0%}"
            f"   max {max(shipped_overlaps):.0%}")
        for bar in (0.25, 0.5, 0.75, 0.9):
            n = sum(1 for v in shipped_overlaps if v >= bar)
            say(f"   pairs sharing >= {bar:.0%} of the smaller claim: "
                f"{n}/{len(shipped_overlaps)} ({n/len(shipped_overlaps):.0%})")
        say(f"   players with at least one >=50% pair in their three: "
            f"{len(shipped_sharing)}/{players}")

    say()
    say("2. ALL CANDIDATE PAIRS - is there containment, or only diffuse overlap?")
    if pair_coverages:
        say(f"   ordered pairs (wide, narrow): {len(pair_coverages)}")
        for bar in (0.5, 0.7, 0.8, 0.9, 0.95, 1.0):
            n = sum(1 for v in pair_coverages if v >= bar)
            say(f"   wide claims with >= {bar:.0%} of their instances inside a narrower one: "
                f"{n} ({n/len(pair_coverages):.1%})")

    say()
    say("3. THE STRONGEST CONTAINMENTS (wide claim <- the narrower one inside it)")
    for c, player, wide, narrow in sorted(top_pairs, reverse=True)[:25]:
        say(f"   {c:.0%}  {player:<20} {wide:<36} contains {narrow}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
