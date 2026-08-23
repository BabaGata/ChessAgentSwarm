"""Rebuild the reports in the review pack, and nothing else in it.

Protocol: docs/notes/evaluation.expert-review.md, and its **amendment of
2026-08-19**: the reports must be built from the same games the reviewer read.
[[experiments.e39-review-window]] found the swarm changes its own leading finding
9 times in 12 between a 20-game window and the full corpus, so a report built
from ~50 games and a reading built from 20 are not measuring the same system.

**This script rewrites `report.txt` only.** Form A in `a-your-reading/` holds the
reviewer's own diagnosis and Form B/C holds their judgement of the system's;
neither is touched, and neither is invalidated by a rebuild, because Form A is
written before the report is opened. `prepare.py` builds the whole pack including
the forms and **re-samples which players are in it** — running that instead would
silently discard the reviewer's work and the pre-registered sample.

Everything except the window is held constant on purpose. The reports the
reviewer has been reading carry no strength or style section, so this does not
add one: the amendment asks for a window change, and a rebuild that quietly
changed the report's shape as well would confound the two.

Usage:
    python regenerate.py --engine PATH --peers PEERS [--cache CACHE] [--window 20]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.arbiter import MAX_PRIORITIES, select_priorities  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.band import notes_for  # noqa: E402
from chesscoach.explainer import render  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import apply_to_profile, default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.planner import build_plan  # noqa: E402
from chesscoach.profile.models import PlayerProfile, PlayerRef  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
BAND = "1400-1800"
TIME_CONTROL = "rapid"


def build(session, peers, player: str, window: int) -> tuple[str, int, int]:
    """One player's report, by the same route `cli coach` takes."""
    games = load_games(ROOT / "games" / f"{player}.pgn")[:window]
    corpus = build_corpus(player, games)
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band=BAND, time_control=TIME_CONTROL, peers=peers,
    )
    diagnosis = diagnose(context, default_agents())

    profile = apply_to_profile(
        PlayerProfile(
            player=PlayerRef(source="lichess", username=player, band=BAND),
            corpus=corpus.to_ref(),
            band_notes=notes_for(context),
        ),
        diagnosis,
    )

    # `cli._planned`, without the context questions: no answers were collected
    # for the review, and `priorities_for(None)` is the arbiter's own ceiling.
    also = diagnosis.sub_threshold
    selection = select_priorities(profile.findings, limit=MAX_PRIORITIES, also=also)
    chosen = {p.finding.id for p in selection.priorities}
    known = {f.id for f in profile.findings}
    profile = replace(
        profile,
        findings=tuple(sorted(
            profile.findings + tuple(f for f in also if f.id in chosen and f.id not in known),
            key=lambda finding: finding.id,
        )),
    )
    profile = replace(profile, plan=build_plan(
        selection.priorities, created=date.today().isoformat(), peers=peers,
        band=BAND, time_control=TIME_CONTROL, player=player,
    ))
    return render(profile), corpus.n_games, len(selection.priorities)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20,
                        help="games per player; 20 matches what the reviewer read")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without writing")
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)
    changed, unchanged = [], []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            folder = ROOT / "b-the-system" / player
            if not folder.is_dir():
                print(f"  {player}: not in the pack, skipped")
                continue

            text, n_games, n_priorities = build(session, peers, player, args.window)
            target = folder / "report.txt"
            before = target.read_text(encoding="utf-8-sig") if target.exists() else ""
            if before == text:
                unchanged.append(player)
            else:
                changed.append(player)
                if not args.dry_run:
                    target.write_text(text, encoding="utf-8-sig")
            print(f"  {player}: {n_games} games, {n_priorities} priorities, "
                  f"{'unchanged' if before == text else 'REWRITTEN'}", flush=True)

    verb = "would change" if args.dry_run else "rewritten"
    print(f"\n{len(changed)} {verb}, {len(unchanged)} unchanged")
    if changed:
        print("  " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
