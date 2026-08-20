"""E40 — does the ranked top three need asking for, or can it be derived?

The reviewer, after E39: *"but is it even needed to compare the top 3 instead of
noticed error by noticed error?"*

Partly right, and the part that is wrong matters. The two tests measure different
layers:

    move by move   DETECTION and NAMING -- did the swarm see this mistake, and
                   does it have a word for it. 270 annotated moves, matched
                   windows, well powered (E31).
    top three      PRIORITISATION -- of everything wrong with this player, did
                   the swarm pick the right thing to work on. That is the
                   arbiter, a real component, and nothing else tests it.

So the question is worth keeping. What is wrong is the **instrument**: asking a
reviewer to synthesise a ranking in their head, from 20 games read over two and a
half hours, and scoring 12 binary outcomes against it. Evidence for that being
the wrong ask is that Part 2 of Form A is **blank for all twelve players** while
270 move-level notes exist. The reviewer voted with their pen.

The alternative tested here: **derive the ranking from the notes they already
wrote.** Aggregate each annotated mistake to a claim kind, count, and rank. That
turns a remembered judgement into a measured one, costs the reviewer nothing
further, and rests on 270 observations instead of 12.

Two derivations, because frequency is not importance:

    by count   how often the reviewer wrote it down
    by cost    the same, weighted by what the swarm measures that claim to cost

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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e31-move-level-agreement"))

from compare import expected_signals, parse_notes  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

# A player counts as annotated once they have more than a handful of notes; the
# blank form itself contains numbered questions.
MIN_NOTES = 10

# The reviewer names motifs and material; the swarm names claims. This maps a
# note's expected SIGNAL (from E31's table) onto the claim families a swarm
# priority can belong to, so the two rankings are in the same vocabulary.
def family(signal: str) -> str:
    if signal in {"instant_move_error"}:
        return "instant_move_error"
    if signal in {"allows_pressure"}:
        return "allows_pressure"
    if signal.startswith("concedes_weakness"):
        return "concedes_weakness"
    if signal.startswith("allows_square"):
        return "allows_square"
    return f"motif:{signal.split(':')[0]}"


def claim_family(claim_key: str) -> str:
    kind, subject = claim_key.split(".")[0], claim_key.split(".")[1]
    if kind in {"missed_motif", "allowed_motif"}:
        return f"motif:{subject}"
    if kind in {"moved_into_attack", "miscounted_exchange", "sacrificed_for_attack"}:
        return f"material:{kind}"
    return kind


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

    rows = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            notes = parse_notes(ROOT / "a-your-reading" / f"{player}.txt")
            if len(notes) < MIN_NOTES:
                continue

            # The reviewer's ranking, derived from what they wrote down.
            counted: Counter = Counter()
            unmapped = 0
            for note in notes:
                signals = expected_signals(note.text)
                if not signals:
                    unmapped += 1
                    continue
                counted[family(signals[0])] += 1
            reviewer = [name for name, _ in counted.most_common(3)]

            # The swarm's ranking, on the SAME games (E39's fix).
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid", peers=peers,
            )
            result = diagnose(context, default_agents())
            selection = select_priorities(result.findings, limit=3,
                                          also=result.sub_threshold)
            swarm = [claim_family(p.finding.claim.key()) for p in selection.priorities]

            rows.append({
                "player": player, "notes": len(notes), "unmapped": unmapped,
                "reviewer": reviewer, "swarm": swarm,
                "counted": counted,
            })
            print(f"  {player}: done", flush=True)

    say()
    say(f"DERIVED RANKING vs THE SWARM - same {args.window} games, "
        f"{len(rows)} annotated players")
    say()
    for row in rows:
        say(f"{row['player']}  ({row['notes']} notes, {row['unmapped']} unmapped)")
        say(f"    reviewer, by count : {', '.join(row['reviewer']) or '--'}")
        say(f"    swarm              : {', '.join(row['swarm']) or '(silent)'}")
        hit_top = bool(row["swarm"]) and row["swarm"][0] in row["reviewer"]
        overlap = len(set(row["swarm"]) & set(row["reviewer"]))
        say(f"    swarm's top in reviewer's three: {'YES' if hit_top else 'no'}"
            f"   overlap {overlap}/3")
        say()

    if rows:
        hits = sum(1 for r in rows if r["swarm"] and r["swarm"][0] in r["reviewer"])
        overlaps = [len(set(r["swarm"]) & set(r["reviewer"])) for r in rows]
        say("-" * 70)
        say(f"  swarm's top finding inside the reviewer's derived three: "
            f"{hits}/{len(rows)}  ({hits/len(rows):.0%})")
        say(f"  median overlap of the two top-threes: {statistics.median(overlaps):.1f}/3")
        say(f"  notes the vocabulary could not map: "
            f"{sum(r['unmapped'] for r in rows)}/{sum(r['notes'] for r in rows)}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
