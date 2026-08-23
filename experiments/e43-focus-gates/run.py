"""E43 — sweep the two gates that keep expensive claims at `watch`.

D15 defect (b). [[experiments.e41-cost-ranking]] found seven material claims that
are **above the peer rate on every one** and cost 6.3-15.1 points of win
probability a game, and are still not assertable. Two constants in
`chesscoach/confidence.py` do it, and they fail for different reasons.

**FOCUS_GAMES_WITH_DATA = 20 is a units bug.** `games_with_data` counts the games
in which a *section* found any diagnosable move, so on a 20-game corpus its
ceiling is 20 and ordinary attrition puts it at 18-19. The gate demands 20, which
on a 20-game read is a demand for a perfect score. cademan 18, goydorak 19.
Neither was blocked for weak evidence; they were blocked because the corpus is
exactly the size of the threshold. Expressed as a **fraction of the corpus** the
gate stops depending on the window at all, and that is a correction rather than a
loosening.

**FOCUS_MARGIN = 1.25 is an unvalidated threshold.** Its own comment says it was
"chosen to match PRIORITY_MARGIN rather than tuned", justified by the fact that
the smallest of the swarm's 40 findings was 1.40 so the floor "removes none of
them". That is a no-harm argument, not a correctness one. Crossfire1983's
`hangingPiece` is 1.14x and Hirsican's `hangingPawn` 1.21x -- above peers,
expensive, refused for being above by not quite enough.

**Lowering it is not free**, and the specific failure it exists to prevent is
recorded: S5 arrived carrying 526 opportunities per player and produced claims
that were statistically solid and worthless to say aloud, deviating 1.24x at the
90th percentile (L-023, D12). So the sweep must check whether S5's pooled claim
comes back, not only whether coverage rises.

Every input to `assign_tier` survives on the Finding, so the sweep re-derives
tiers in memory from **one** diagnosis per player per window. The engine runs 24
times, not 24 x the number of variants.

Usage:
    python run.py --engine PATH --peers PEERS [--cache CACHE]
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import confidence as conf  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

REVIEW_WINDOW = 20
FULL_WINDOW = 60

# The absolute floor this experiment retired, kept so its own rows reproduce.
RETIRED_ABSOLUTE = 20

# The claim S5 produces that FOCUS_MARGIN exists to keep quiet (L-023, D12).
# **The pooled one specifically** -- D12's objection was to S5's large-denominator
# aggregate deviating 1.24x at the 90th percentile, not to its subdivisions, and
# counting the subdivisions too reports a regression that was never the concern.
S5_REGRESSION = "concedes_weakness"
POOLED = "any"

# What the reviewer's notes are about, and what D15 is chasing.
MATERIAL = ("hangingPiece", "hangingPawn", "moved_into_attack", "miscounted_exchange",
            "sacrificed_for_attack", "trappedPiece")


@dataclass(frozen=True)
class Candidate:
    """One measured claim, carrying everything `assign_tier` needs."""

    player: str
    claim_id: str
    kind: str
    subject: str
    stats: conf.ClaimStats
    cost_per_game: float | None
    lift: float | None


def collect(session, peers, player: str, window: int) -> tuple[list[Candidate], int]:
    games = load_games(ROOT / "games" / f"{player}.pgn")[:window]
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return [], 0
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band="1400-1800", time_control="rapid", peers=peers,
    )
    result = diagnose(context, default_agents())

    out = []
    for f in tuple(result.findings) + tuple(result.sub_threshold):
        m = f.measurement
        baseline = m.baseline_rate if m.baseline_rate is not None else m.peer_rate
        if baseline is None or m.ci95 is None:
            continue
        out.append(Candidate(
            player=player,
            claim_id=f.id,
            kind=f.claim.kind,
            subject=f.claim.subject,
            stats=conf.ClaimStats(
                distinct_games=m.distinct_games,
                games_with_data=m.games_with_data,
                corpus_games=corpus.n_games,
                rate=m.rate,
                baseline_rate=baseline,
                ci95=m.ci95,
                replicated=f.confidence.replicated,
            ),
            cost_per_game=m.cost_per_game,
            lift=(m.rate / baseline) if baseline else None,
        ))
    return out, corpus.n_games


def assertable_under(candidate: Candidate, n_games: int, fraction: float | None,
                     margin: float) -> bool:
    """Re-run the real tier logic with the two constants moved.

    A fractional rule is applied by setting the absolute constant to the number
    of games that fraction implies, which is exactly equivalent and needs no
    change to `ClaimStats`.
    """
    old_fraction, old_margin = conf.FOCUS_GAMES_FRACTION, conf.FOCUS_MARGIN
    try:
        # `fraction=None` reproduces the **retired** absolute floor of 20, which
        # is what this experiment was run against. Expressing it as 20/n_games
        # makes ceil(f * n_games) land exactly on 20, so the historical rows in
        # experiments.e43-focus-gates still reproduce after the fix shipped.
        conf.FOCUS_GAMES_FRACTION = (RETIRED_ABSOLUTE / n_games) if fraction is None else fraction
        conf.FOCUS_MARGIN = margin
        return conf.assign_tier(candidate.stats).is_assertable
    finally:
        conf.FOCUS_GAMES_FRACTION, conf.FOCUS_MARGIN = old_fraction, old_margin


def blocked_only_by_games(candidate: Candidate, n_games: int,
                          fraction: float | None) -> bool:
    """Would this be assertable if the games_with_data floor were the only change?"""
    if assertable_under(candidate, n_games, fraction, conf.FOCUS_MARGIN):
        return False
    old = conf.FOCUS_GAMES_FRACTION
    try:
        conf.FOCUS_GAMES_FRACTION = 0.0
        return conf.assign_tier(candidate.stats).is_assertable
    finally:
        conf.FOCUS_GAMES_FRACTION = old


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    short: dict[str, list[Candidate]] = {}
    full: dict[str, list[Candidate]] = {}
    sizes: dict[tuple[str, str], int] = {}

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            short[player], sizes[(player, "short")] = collect(
                session, peers, player, REVIEW_WINDOW)
            full[player], sizes[(player, "full")] = collect(
                session, peers, player, FULL_WINDOW)
            print(f"  {player}: {len(short[player])} / {len(full[player])} candidates",
                  flush=True)

    players = sorted(short)

    # Cheap insurance: the engine time is the expensive part, and every later
    # question about these numbers should be answerable without spending it again.
    import json
    (args.out / "candidates.json").write_text(json.dumps({
        window: {
            p: [{"claim_id": c.claim_id, "kind": c.kind, "subject": c.subject,
                 "distinct_games": c.stats.distinct_games,
                 "games_with_data": c.stats.games_with_data,
                 "rate": c.stats.rate, "baseline_rate": c.stats.baseline_rate,
                 "ci95": list(c.stats.ci95), "replicated": c.stats.replicated,
                 "cost_per_game": c.cost_per_game, "lift": c.lift,
                 "n_games": sizes[(p, window)]}
                for c in bag[p]]
            for p in players
        }
        for window, bag in (("short", short), ("full", full))
    }, indent=1), encoding="utf-8")

    # --- 1. the units bug, measured directly -------------------------------
    say()
    say("1. HOW OFTEN IS THE ONLY BLOCKER THE GAMES_WITH_DATA FLOOR?")
    say(f"{'rule':<28}{'at 20 games':>14}{'at 60 games':>14}")
    say("-" * 56)
    for label, fraction in (("absolute 20 (shipping)", None), ("fraction 0.90", 0.90),
                            ("fraction 0.80", 0.80), ("fraction 0.70", 0.70)):
        counts = []
        for bag, key in ((short, "short"), (full, "full")):
            n = sum(
                1 for p in players for c in bag[p]
                if blocked_only_by_games(c, sizes[(p, key)], fraction)
            )
            counts.append(n)
        say(f"{label:<28}{counts[0]:>14}{counts[1]:>14}")

    # --- 2. does the window still decide the answer? -----------------------
    say()
    say("2. WINDOW AGREEMENT - same claim, 20 games vs 60, same verdict?")
    say(f"{'rule':<28}{'agree':>10}{'of':>6}{'rate':>9}")
    say("-" * 53)
    for label, fraction in (("absolute 20 (shipping)", None), ("fraction 0.90", 0.90),
                            ("fraction 0.80", 0.80), ("fraction 0.70", 0.70)):
        agree = total = 0
        for p in players:
            by_id = {c.claim_id: c for c in full[p]}
            for c in short[p]:
                other = by_id.get(c.claim_id)
                if other is None:
                    continue
                total += 1
                a = assertable_under(c, sizes[(p, "short")], fraction, conf.FOCUS_MARGIN)
                b = assertable_under(other, sizes[(p, "full")], fraction, conf.FOCUS_MARGIN)
                agree += a == b
        say(f"{label:<28}{agree:>10}{total:>6}{agree/total:>8.0%}" if total else label)

    # --- 3. the margin sweep, with the regression check --------------------
    say()
    say("3. FOCUS_MARGIN SWEEP (at 60 games, fraction 0.80 for the games floor)")
    say(f"{'margin':>8}{'advised':>9}{'claims':>8}{'kinds':>7}{'material':>10}"
        f"{'top-claim share':>17}{'  S5 pooled back?':>18}")
    say("-" * 78)
    for margin in (1.10, 1.15, 1.20, 1.25, 1.30, 1.40):
        advised = 0
        asserted: list[Candidate] = []
        leaders: Counter = Counter()
        for p in players:
            ok = [c for c in full[p]
                  if assertable_under(c, sizes[(p, "full")], 0.80, margin)]
            asserted += ok
            if ok:
                advised += 1
                leaders[max(ok, key=lambda c: c.cost_per_game or 0).kind] += 1
        kinds = len({c.kind for c in asserted})
        material = sum(1 for c in asserted if c.subject in MATERIAL or c.kind in MATERIAL)
        s5 = sum(1 for c in asserted
                 if c.kind == S5_REGRESSION and c.subject == POOLED)
        s5_sub = sum(1 for c in asserted
                     if c.kind == S5_REGRESSION and c.subject != POOLED)
        share = (leaders.most_common(1)[0][1] / advised) if advised else 0
        say(f"{margin:>8.2f}{advised:>9}{len(asserted):>8}{kinds:>7}{material:>10}"
            f"{share:>16.0%}"
            f"{('  YES x' + str(s5)) if s5 else f'  no ({s5_sub} subdiv)':>18}")

    # --- 4. what the two fixes admit, named --------------------------------
    say()
    say("4. WHAT CHANGES AT 20 GAMES - claims admitted by each fix, named")
    for label, fraction, margin in (("games floor -> 0.80 of corpus", 0.80, 1.25),
                                    ("margin -> 1.15", None, 1.15),
                                    ("both", 0.80, 1.15)):
        gained = []
        for p in players:
            for c in short[p]:
                before = assertable_under(c, sizes[(p, "short")], None, 1.25)
                after = assertable_under(c, sizes[(p, "short")], fraction, margin)
                if after and not before:
                    gained.append(c)
        say(f"  {label}: +{len(gained)} claims")
        for c in sorted(gained, key=lambda c: -(c.cost_per_game or 0))[:8]:
            say(f"      {c.player:<20} {c.kind}.{c.subject:<22} "
                f"lift {c.lift:.2f}x  cost {c.cost_per_game or 0:.1f}  "
                f"{c.stats.distinct_games}/{c.stats.games_with_data} games")
        say()

    # --- 5. cost, per C4 ---------------------------------------------------
    silent = [p for p in players
              if not [c for c in full[p]
                      if assertable_under(c, sizes[(p, "full")], 0.80, 1.25)]]
    say(f"   players with nothing assertable at 60 games: {silent or 'none'}")
    say()
    say("5. COST")
    say("   the sweep re-derives tiers in memory; the engine ran twice per player")
    say(f"   candidates collected: {sum(len(v) for v in short.values())} at 20 games, "
        f"{sum(len(v) for v in full.values())} at 60")
    say(f"   median games_with_data at 20-game window: "
        f"{statistics.median([c.stats.games_with_data for p in players for c in short[p]]):.0f}")

    (args.out / "sweep.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'sweep.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
