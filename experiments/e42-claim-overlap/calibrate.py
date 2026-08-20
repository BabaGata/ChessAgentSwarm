"""E42b — what does "redundant" measure, on the pairs already treated as redundant?

E42 found no cross-section containment structure worth a rule: 0.8 % of ordered
candidate pairs reach 50 % coverage and **none reach 80 %**. So a cross-section
suppressor has almost nothing to suppress, and my E41 explanation — that
`early_error` outprices `hangingPiece` by *containing* it — is wrong.

What E42 did find is a short tail of real overlap, and the top of it is mixed:
some pairs are a pooled parent against its own subdivision (which
`drop_redundant_aggregates` exists to delete) and some are genuinely different
claims from different sections.

That gives a way to set a threshold without inventing one. The project **already**
declares pooled-parent-versus-subdivision redundant, by convention, with no
measurement behind it. Measure the coverage on exactly those pairs and the
convention becomes a number — and a cross-section rule set at the same number is
consistent with the judgement the codebase already makes, rather than with my
taste.

Usage:
    python calibrate.py --engine PATH --peers PEERS [--cache CACHE] [--window 20]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import POOLED_SUBJECT, SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"


def moves(finding) -> frozenset:
    return frozenset(finding.measurement.instances_at)


def coverage(wide, narrow) -> float:
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

    # Pairs the project ALREADY deletes: same kind, one pooled, one subdivided.
    already_redundant: list[float] = []
    # Pairs from different sections entirely — no convention covers these.
    cross_section: list[tuple[float, str, str, str]] = []
    # Same section, same kind, neither pooled: siblings, which nothing deletes.
    siblings: list[float] = []
    split_pools = 0

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
            asserted = list(result.findings)
            watched = list(result.sub_threshold)
            everything = asserted + watched

            for a in everything:
                for b in everything:
                    if a.id == b.id or not moves(a) or not moves(b):
                        continue
                    if len(moves(a)) < len(moves(b)):
                        continue
                    c = coverage(a, b)
                    same_kind = a.claim.kind == b.claim.kind
                    a_pooled = a.claim.subject == POOLED_SUBJECT
                    b_pooled = b.claim.subject == POOLED_SUBJECT
                    if same_kind and a_pooled and not b_pooled:
                        already_redundant.append(c)
                        # Does the existing rule actually see this pair? It runs
                        # on each pool separately, so a parent asserted and a
                        # subdivision watched escape it entirely.
                        if (a in asserted) != (b in asserted):
                            split_pools += 1
                    elif a.section != b.section:
                        cross_section.append((c, player, a.claim.key(), b.claim.key()))
                    elif same_kind and not a_pooled and not b_pooled:
                        siblings.append(c)

    def describe(name: str, values: list[float]) -> None:
        if not values:
            say(f"{name}: none")
            return
        vs = sorted(values)
        say(f"{name}  n={len(vs)}")
        say(f"    min {vs[0]:.0%}   p10 {vs[max(0, len(vs)//10)]:.0%}   "
            f"median {statistics.median(vs):.0%}   "
            f"p90 {vs[min(len(vs)-1, len(vs)*9//10)]:.0%}   max {vs[-1]:.0%}")

    say("COVERAGE OF THE WIDE CLAIM BY THE NARROW ONE, BY RELATIONSHIP")
    say()
    say("A. pairs the project already deletes (pooled parent vs its subdivision)")
    describe("   ", already_redundant)
    say(f"    of these, pairs SPLIT across the asserted and watched pools, which "
        f"the existing rule cannot see: {split_pools}")
    say()
    say("B. same kind, neither pooled (siblings — nothing deletes these)")
    describe("   ", siblings)
    say()
    say("C. different sections entirely (no convention covers these)")
    describe("   ", [c for c, _, _, _ in cross_section])
    say()
    say("   the strongest cross-section pairs:")
    for c, player, wide, narrow in sorted(cross_section, reverse=True)[:12]:
        say(f"     {c:.0%}  {player:<20} {wide:<34} <- {narrow}")

    if already_redundant:
        vs = sorted(already_redundant)
        floor = vs[max(0, len(vs) // 10)]
        say()
        say(f"CALIBRATION: the weakest tenth of the pairs the project already "
            f"calls redundant sits at {floor:.0%}.")
        say("A cross-section rule set there deletes nothing the codebase would "
            "not already delete if the two claims shared a kind.")
        n = sum(1 for c, _, _, _ in cross_section if c >= floor)
        say(f"At that threshold it would fire on {n} of {len(cross_section)} "
            f"cross-section pairs.")

    (args.out / "calibrate.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'calibrate.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
