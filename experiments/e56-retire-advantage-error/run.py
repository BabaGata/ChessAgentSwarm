"""What moved when `advantage_error` stopped being counted.

Screen: docs/notes/experiments.e56-retire-advantage-error.md

The design note committed to inspecting this rather than assuming it harmless:
`advantage_error` fired **182 times across six players** and was the
second-commonest claim in the system, so removing it frees slots in every report
where it ranked. What fills those slots is the question.

Three things are counted, and the third is the one that could go wrong:

    top finding   did the headline claim change for a player?
    plan length   does anyone now have less to work on?
    silence       does anyone now have NOTHING to work on?

**Silence is the real risk.** The confidence policy already refuses to speak
without evidence, and removing a claim that reached the report for six players
could push one of them under. [[decisions.0010-three-priorities-and-the-cost-pool]]
took silence from 2/12 to 0/12 and it must not come back unnoticed.

**The retirement flag is switched back on for the BEFORE arm.** A first version
filtered the claim out of a diagnosis that had already retired it, which measured
nothing and reported 0 of 12 -- the arm was empty because the code it was meant
to compare against no longer existed. Two diagnoses per player, one engine pass:
the analysis is cached, only the sections re-run.

Usage:
    python run.py --engine PATH --peers PEERS [--cache CACHE]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections import s3_endgame_technique as s3  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
RETIRED = "advantage_error"


def top(selection) -> str:
    """The claim the player is actually told about first."""
    return selection.priorities[0].finding.claim.key() if selection.priorities else "-"


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
    rows = []

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
            # The claim switched on, then off. Only the sections re-run --
            # the engine work is done once and cached in `observations`.
            was_retired = s3.ADVANTAGE_ERROR_RETIRED
            try:
                s3.ADVANTAGE_ERROR_RETIRED = False
                old = diagnose(context, default_agents())
                s3.ADVANTAGE_ERROR_RETIRED = True
                new = diagnose(context, default_agents())
            finally:
                s3.ADVANTAGE_ERROR_RETIRED = was_retired

            before = select_priorities(old.findings, also=old.sub_threshold)
            after = select_priorities(new.findings, also=new.sub_threshold)

            fired = sum(1 for f in old.findings + old.sub_threshold
                        if f.claim.kind == RETIRED)
            rows.append((player, fired, before, after, old.findings, new.findings))
            print(f"  {player}: {len(before.priorities)} -> {len(after.priorities)} priorities",
                  flush=True)

    lines = [
        "RETIRING advantage_error — WHAT MOVED",
        "=" * 88,
        "",
        "Measured as before and dropped afterwards, which is what retirement does.",
        "",
        f"  {'player':<24}{'fired':>7}{'priorities':>13}{'top finding':>16}", "",
    ]
    changed_top = lost_steps = silenced = 0

    for player, fired, before, after, was, now in rows:
        before_top, after_top = top(before), top(after)
        moved = "CHANGED" if before_top != after_top else "same"
        changed_top += int(before_top != after_top)
        lost_steps += int(len(after.priorities) < len(before.priorities))
        silenced += int(bool(before.priorities) and not after.priorities)
        lines.append(
            f"  {player[:23]:<24}{fired:>7}"
            f"{len(before.priorities):>7} ->{len(after.priorities):>3}{moved:>16}"
        )
        if before_top != after_top:
            lines.append(f"      was  {before_top}")
            lines.append(f"      now  {after_top}")

    lines += [
        "",
        "=" * 88,
        f"  players where it fired at all      {sum(1 for r in rows if r[1]):>3} of {len(rows)}",
        f"  headline finding changed           {changed_top:>3}",
        f"  plan got shorter                   {lost_steps:>3}",
        f"  **left with nothing to work on**   {silenced:>3}",
        "",
        "The last line is the one that matters. Silence went 2/12 to 0/12 when the",
        "cost pool was built (ADR-0010) and must not come back unnoticed; a claim",
        "that named nothing actionable is still better removed, but not silently.",
    ]

    text = "\n".join(lines)
    print("\n" + text[-1500:])
    (args.out / "moved.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
