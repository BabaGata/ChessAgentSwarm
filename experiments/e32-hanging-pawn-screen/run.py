"""E32 — does the free-pawn detector earn its place?

A new claim is not shipped in this project because it sounds useful. E09, E11
and E25 all screened candidates and most of them failed: 2 of 5, 1 of 4, 5 of 27.
The same two questions apply here.

  1. Does it fire sensibly, and how often?
  2. Does it DISTINGUISH players, or does everyone do it at the same rate?
     A claim every player scores alike cannot select anyone's priority, which is
     what killed most of E09's and E11's candidates (L-024).

And the specific payoff this detector was built for: **45 of 45 reviewer notes
mentioning a pawn were unnameable** ([[experiments.e31-move-level-agreement]]).
If naming does not move, the detector is not worth its opportunities.

Usage:
    python run.py --engine PATH [--cache CACHE]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# The claims under test, and the ones they must be compared against: if the pawn
# claims spread no wider than the piece claims already shipping, they add noise
# rather than signal.
UNDER_TEST = ("missed_motif.hangingPawn.own", "allowed_motif.hangingPawn.own")
REFERENCE = ("missed_motif.hangingPiece.own", "allowed_motif.hangingPiece.own",
             "missed_motif.fork.own", "allowed_motif.fork.own")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    agents = default_agents()
    rates: dict[str, list[float]] = {}
    totals: dict[str, tuple[int, int]] = {}

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(GAMES.glob("*.pgn")):
            player = path.stem
            games = load_games(path)
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid",
            )
            for agent in agents:
                for m in agent.measure(context):
                    if m.claim_key not in UNDER_TEST + REFERENCE or not m.opportunities:
                        continue
                    rates.setdefault(m.claim_key, []).append(m.instances / m.opportunities)
                    seen, opps = totals.get(m.claim_key, (0, 0))
                    totals[m.claim_key] = (seen + m.instances, opps + m.opportunities)
            print(f"  {player}: done", flush=True)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say()
    say(f"{'claim':<38}{'players':>8}{'instances':>10}{'opps':>8}"
        f"{'pooled':>9}{'median':>9}{'p90':>8}{'spread':>8}")
    say("-" * 96)

    for key in UNDER_TEST + REFERENCE:
        values = sorted(rates.get(key, []))
        if not values:
            say(f"{key:<38}{'never fired':>8}")
            continue
        instances, opps = totals[key]
        median = statistics.median(values)
        p90 = values[min(len(values) - 1, int(0.9 * len(values)))]
        spread = (p90 / median) if median else float("inf")
        mark = "  <-- new" if key in UNDER_TEST else ""
        say(f"{key:<38}{len(values):>8}{instances:>10}{opps:>8}"
            f"{instances / opps:>8.1%}{median:>9.1%}{p90:>8.1%}{spread:>7.2f}x{mark}")

    say()
    say("The spread is the screen: p90 divided by the median. A claim every player")
    say("scores alike cannot select anyone's priority, however common it is (L-024).")
    say("The new claims have to spread at least as wide as the ones already shipping.")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
