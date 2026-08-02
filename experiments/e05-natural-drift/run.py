"""E05 — what does a plan's target look like when nobody follows the plan?

The control condition for every claim this project might ever make about
coaching. For each player: build a plan from their earlier games, then check it
against their later ones — with **no intervention in between**, because they were
never told anything.

Any target met here was met by drift. If a large share of targets are met by
drift alone, the targets are not predictions and the planner needs rethinking.
If almost none are, the targets are demanding, and a later study with real
coaching has something to beat.

Usage:
    python run.py --histories DIR --engine PATH --cache DB --peers JSON --out DIR
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.parallel import prefetch
from chesscoach.arbiter import select_priorities
from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import GameRecord, parse_pgn_file
from chesscoach.orchestrator import default_agents, diagnose
from chesscoach.peers import PeerReference
from chesscoach.pipeline import engine_session
from chesscoach.planner import build_plan, expected_no_change
from chesscoach.progress import check_plan
from chesscoach.sections.base import SectionContext

BAND = "1400-1800"
TIME_CONTROL = "rapid"


@dataclass(frozen=True)
class PlayerResult:
    player: str
    early_games: int
    late_games: int
    steps: int
    outcomes: list[dict]


def split_by_date(games: tuple[GameRecord, ...]) -> tuple[list[GameRecord], list[GameRecord]]:
    """Earlier half and later half. Ties broken by id so the split is stable."""
    ordered = sorted(games, key=lambda g: (g.date or "", g.game_id))
    middle = len(ordered) // 2
    return ordered[:middle], ordered[middle:]


def analyse(session, games, player: str, args) -> tuple:
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return None, ()
    prefetch(games, session.cache, engine=args.engine, depth=args.depth, workers=args.workers)
    observations = analyse_corpus(corpus, games, session.analyser)
    return corpus, observations


def run_player(session, player: str, games, peers, args) -> PlayerResult | None:
    early, late = split_by_date(games)
    if len(early) < 15 or len(late) < 15:
        return None

    early_corpus, early_obs = analyse(session, early, player, args)
    if early_corpus is None:
        return None

    context = SectionContext(
        early_obs,
        early_corpus,
        session.provenance(early_corpus.corpus_id),
        band=BAND,
        time_control=TIME_CONTROL,
        peers=peers,
    )
    findings = diagnose(context, default_agents()).findings
    plan = build_plan(
        select_priorities(findings).priorities,
        created=date.today().isoformat(),
        peers=peers,
        band=BAND,
        time_control=TIME_CONTROL,
        player=player,
    )
    if plan is None:
        return PlayerResult(player, len(early), len(late), 0, [])

    late_corpus, late_obs = analyse(session, late, player, args)
    later_context = SectionContext(
        late_obs, late_corpus, session.provenance(late_corpus.corpus_id)
    )
    later = {
        m.claim_key: m for agent in default_agents() for m in agent.measure(later_context)
    }
    report = check_plan(
        plan,
        later,
        previous_rates={f.claim.key(): f.measurement.rate for f in findings},
        games_since=len(late),
        checked_at=date.today().isoformat(),
    )

    # The no-change estimate is recorded per prediction so a target rule can be
    # cross-validated afterwards without re-analysing anything: the predictions
    # and their before/after rates do not depend on the rule, only the verdict
    # does.
    by_id = {f.id: f for f in findings}
    expectations = {
        step.finding_id: expected_no_change(
            by_id[step.finding_id], peers, BAND, TIME_CONTROL, player
        )
        for step in plan.steps
        if step.finding_id in by_id
    }

    return PlayerResult(
        player=player,
        early_games=len(early),
        late_games=len(late),
        steps=len(plan.steps),
        outcomes=[
            {
                "finding_id": o.finding_id,
                "status": o.status,
                "target": o.target_rate,
                "before": o.previous_rate,
                "after": o.observed_rate,
                "expected": expectations.get(o.finding_id),
            }
            for o in report.outcomes
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--histories", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=18)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    paths = sorted(args.histories.glob("*.pgn"))

    results = _resume(args.out)
    done = {r.player for r in results}
    if done:
        print(f"resuming: {len(done)} players already done", flush=True)
    print(f"{len(paths)} players at depth {args.depth}\n", flush=True)

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            if path.stem in done:
                print(f"  {index:>2}/{len(paths)} {path.stem}: done earlier", flush=True)
                continue
            games = parse_pgn_file(path)
            result = run_player(session, path.stem, games, peers, args)
            if result is None:
                print(f"  {index:>2}/{len(paths)} {path.stem}: too few games", flush=True)
                continue
            results.append(result)
            verdicts = ", ".join(o["status"] for o in result.outcomes) or "no plan"
            print(f"  {index:>2}/{len(paths)} {path.stem}: {verdicts}", flush=True)
            # Written after every player: this run takes hours, and a machine
            # that dies at player 80 should not cost the other 79.
            _report(results, args.out, quiet=True)

    _report(results, args.out)
    return 0


def _resume(out: Path) -> list[PlayerResult]:
    """Players already finished in an earlier, interrupted run of the same set."""
    path = out / "results.json"
    if not path.exists():
        return []
    saved = json.loads(path.read_text(encoding="utf-8"))
    return [
        PlayerResult(
            player=entry["player"],
            early_games=entry["early_games"],
            late_games=entry["late_games"],
            steps=entry.get("steps", len(entry["outcomes"])),
            outcomes=entry["outcomes"],
        )
        for entry in saved.get("per_player", [])
    ]


def _report(results: list[PlayerResult], out: Path, quiet: bool = False) -> None:
    outcomes = [o for r in results for o in r.outcomes]
    statuses = {
        status: sum(1 for o in outcomes if o["status"] == status)
        for status in ("met", "not_met", "too_early", "not_measurable")
    }
    judged = statuses["met"] + statuses["not_met"]

    moves = [
        o["before"] - o["after"]
        for o in outcomes
        if o["after"] is not None and o["before"] is not None
    ]
    asks = [
        o["before"] - o["target"]
        for o in outcomes
        if o["target"] is not None and o["before"] is not None
    ]

    summary = {
        "players": len(results),
        "players_with_a_plan": sum(1 for r in results if r.steps),
        "predictions": len(outcomes),
        "statuses": statuses,
        "met_share_of_judged": round(statuses["met"] / judged, 3) if judged else None,
        "drift_without_coaching": {
            "mean_improvement": round(statistics.mean(moves), 4) if moves else None,
            "median_improvement": round(statistics.median(moves), 4) if moves else None,
        },
        "target_asked_for": {
            "mean_improvement": round(statistics.mean(asks), 4) if asks else None,
        },
        "per_player": [
            {
                "player": r.player,
                "early_games": r.early_games,
                "late_games": r.late_games,
                "steps": r.steps,
                "outcomes": r.outcomes,
            }
            for r in results
        ],
    }
    (out / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if quiet:
        return

    print("\n" + "=" * 60)
    print(f"players with a plan   {summary['players_with_a_plan']} of {len(results)}")
    print(f"predictions made      {len(outcomes)}")
    print(f"  met                 {statuses['met']}")
    print(f"  not met             {statuses['not_met']}")
    print(f"  too early           {statuses['too_early']}")
    print(f"  not measurable      {statuses['not_measurable']}")
    if judged:
        print(f"met by drift alone    {100 * statuses['met'] / judged:.0f}% of judged predictions")
    if moves:
        print(f"drift, no coaching    {statistics.mean(moves):+.1%} mean improvement")
    if asks:
        print(f"target asked for      {statistics.mean(asks):+.1%} mean improvement")
    print(f"\nwritten {out / 'results.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
