"""E41 — would ranking by cost beat ranking by peer-relative excess?

The reviewer, after E40's 0-of-6:

    "didn't you previously do the updates about the mistakes that are not unusual
     to still be counted, because for stronger players they do mistakes less
     often so probably every their mistake will be disregarded while the severity
     and the count can still make a good rank for the mistakes"

Two claims in that, and both are testable.

**One: the cost pool was supposed to fix this.**
[[decisions.0010-three-priorities-and-the-cost-pool]] added a second selection
pool so expensive-but-ordinary patterns could reach the report. E40 found the
reviewer's top concern missing from the swarm's three for six players out of six,
so either the pool is not firing or it is not reaching high enough.

**Two: it should get worse the stronger the player is.** A player near the top of
the band is below the population rate on nearly everything, so a peer-relative
ranking has nothing to promote and the whole report falls to the pool. If that is
true, the mechanism degrades exactly where it is most needed.

**And the alternative is specific:** rank by what a mistake costs — severity times
count, which is what `cost_per_game` already is.

The catch is that [[experiments.e17-ranking-stability]] measured raw-cost ranking
and refused it: it named one claim to 70 % of players. So this is not a free
swap, and the experiment has to measure **both** things at once — does cost rank
agree with the reviewer better, and does it collapse into telling everyone the
same thing?

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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e40-derived-ranking"))

from compare import expected_signals, parse_notes  # noqa: E402
from run import claim_family, family  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
MIN_NOTES = 10


def by_cost(findings, limit=3):
    """The reviewer's proposal: rank on what it costs, ignore how unusual it is."""
    priced = [f for f in findings if (f.measurement.cost_per_game or 0) > 0]
    priced.sort(key=lambda f: -(f.measurement.cost_per_game or 0))

    chosen, subjects = [], set()
    for finding in priced:
        if len(chosen) >= limit:
            break
        if finding.claim.subject in subjects:
            continue
        chosen.append(finding)
        subjects.add(finding.claim.subject)
    return chosen


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
            result = diagnose(context, default_agents())
            everything = result.findings + result.sub_threshold

            selection = select_priorities(result.findings, limit=3,
                                          also=result.sub_threshold)
            shipped = [claim_family(p.finding.claim.key()) for p in selection.priorities]
            from_pool = sum(1 for p in selection.priorities if p.shared)

            cost_ranked = [claim_family(f.claim.key()) for f in by_cost(everything)]

            elos = [g.white_elo if (g.white or "").lower() == player.lower()
                    else g.black_elo for g in load_games(path)]
            rating = round(statistics.mean([e for e in elos if e])) if any(elos) else 0

            notes = parse_notes(ROOT / "a-your-reading" / f"{player}.txt")
            reviewer = []
            if len(notes) >= MIN_NOTES:
                counted: Counter = Counter()
                for note in notes:
                    signals = expected_signals(note.text)
                    if signals:
                        counted[family(signals[0])] += 1
                reviewer = [name for name, _ in counted.most_common(3)]

            rows.append({
                "player": player, "rating": rating, "shipped": shipped,
                "from_pool": from_pool, "cost": cost_ranked, "reviewer": reviewer,
            })
            print(f"  {player}: done", flush=True)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say()
    say("CLAIM ONE - does the report fall to the cost pool as players get stronger?")
    say(f"{'player':<22}{'rating':>7}{'from cost pool':>16}   shipped three")
    say("-" * 92)
    for row in sorted(rows, key=lambda r: r["rating"]):
        say(f"{row['player']:<22}{row['rating']:>7}{row['from_pool']:>10} of 3   "
            f"{', '.join(row['shipped'])[:46]}")
    rated = [r for r in rows if r["rating"]]
    if len(rated) >= 3:
        xs = [r["rating"] for r in rated]
        ys = [r["from_pool"] for r in rated]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        vx = sum((x - mx) ** 2 for x in xs)
        vy = sum((y - my) ** 2 for y in ys)
        r = cov / (vx * vy) ** 0.5 if vx and vy else float("nan")
        say(f"\n  corr(rating, slots filled from the cost pool) = {r:+.2f}")
        say(f"  mean slots from the pool: {statistics.mean(ys):.1f} of 3")

    annotated = [r for r in rows if r["reviewer"]]
    say()
    say("CLAIM TWO - would cost ranking agree with the reviewer better?")
    say(f"{'player':<22}{'reviewer top-3':<44}{'shipped':>8}{'by cost':>9}")
    say("-" * 86)
    ship_hits = cost_hits = 0
    ship_overlap, cost_overlap = [], []
    for row in annotated:
        s_hit = bool(row["shipped"]) and row["shipped"][0] in row["reviewer"]
        c_hit = bool(row["cost"]) and row["cost"][0] in row["reviewer"]
        ship_hits += s_hit
        cost_hits += c_hit
        ship_overlap.append(len(set(row["shipped"]) & set(row["reviewer"])))
        cost_overlap.append(len(set(row["cost"]) & set(row["reviewer"])))
        say(f"{row['player']:<22}{', '.join(row['reviewer'])[:42]:<44}"
            f"{'YES' if s_hit else 'no':>8}{'YES' if c_hit else 'no':>9}")
    n = len(annotated)
    if n:
        say()
        say(f"  top finding in the reviewer's three   shipped {ship_hits}/{n}"
            f"   by cost {cost_hits}/{n}")
        say(f"  median overlap of three               shipped "
            f"{statistics.median(ship_overlap):.1f}   by cost "
            f"{statistics.median(cost_overlap):.1f}")

    say()
    say("THE CATCH - E17 refused cost ranking for naming one claim to 70% of players")
    for label, key in (("shipped", "shipped"), ("by cost", "cost")):
        tops = Counter(r[key][0] for r in rows if r[key])
        top, count = tops.most_common(1)[0]
        say(f"  {label:<9} most-named leading claim: {top} -> {count}/{len(rows)} "
            f"({count/len(rows):.0%}),  {len(tops)} distinct")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
