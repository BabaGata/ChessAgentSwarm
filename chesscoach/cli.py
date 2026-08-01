"""Command line entry point for the analysis pipeline.

    python -m chesscoach.cli analyse --pgn DIR --player NAME --engine PATH --out profile.json

Runs layers 1-2 of the architecture — ingest and the analysis core — and writes a
player profile. The profile has **no findings yet**: section agents arrive in M4.
That is the point of a skeleton, and the summary says so rather than implying
the analysis found nothing wrong.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import replace
from datetime import date
from pathlib import Path

from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.engine import DEFAULT_DEPTH
from chesscoach.analysis.parallel import prefetch
from chesscoach.arbiter import select_priorities
from chesscoach.planner import build_plan
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import build_corpus
from chesscoach.orchestrator import apply_to_profile, default_agents, diagnose, summarise
from chesscoach.pipeline import CacheStats, engine_session, load_games
from chesscoach.profile.io import load_profile, save_profile
from chesscoach.profile.models import PlayerProfile, PlayerRef
from chesscoach.sections.base import SectionContext


def analyse(args: argparse.Namespace) -> int:
    games = load_games(args.pgn)
    if not games:
        print(f"no standard games found in {args.pgn}")
        return 1

    corpus = build_corpus(args.player, games)
    if corpus.n_games == 0:
        print(f"no games found for player {args.player!r} in {args.pgn}")
        return 1

    print(f"player   {args.player}")
    print(f"games    {corpus.n_games}")
    print(f"corpus   {corpus.corpus_id}")
    print(f"depth    {args.depth}")

    with engine_session(args.engine, args.depth, args.cache) as session:
        print(f"engine   {session.analyser.engine_name}\nanalysing...", flush=True)
        _prefetch(session, games, args)
        observations = analyse_corpus(corpus, games, session.analyser)
        provenance = session.provenance(corpus.corpus_id)

    peers = None
    if args.peers:
        from chesscoach.peers import PeerReference

        peers = PeerReference.load(args.peers)
        if peers.depth != args.depth:
            print(
                f"peer reference was built at depth {peers.depth}, analysis is at {args.depth};"
                " rates are not comparable across depths"
            )
            return 1

    context = SectionContext(
        observations,
        corpus,
        provenance,
        band=args.band,
        time_control=args.time_control,
        peers=peers,
    )
    diagnosis = diagnose(context, default_agents())

    profile = apply_to_profile(
        PlayerProfile(
            player=PlayerRef(source=args.source, username=args.player, band=args.band),
            corpus=corpus.to_ref(),
        ),
        diagnosis,
    )

    selection = select_priorities(profile.findings)
    profile = replace(
        profile,
        plan=build_plan(
            selection.priorities,
            created=date.today().isoformat(),
            peers=peers,
            band=args.band,
            time_control=args.time_control,
            player=args.player,
        ),
    )
    save_profile(profile, args.out)

    _report(observations, session.cache_stats())

    print("\nsections")
    for line in summarise(diagnosis):
        print(line)
    for finding in profile.findings:
        print(f"\n  [{finding.confidence.tier.value}] {finding.claim.kind} ({finding.claim.subject})")
        print(f"    {_comparison_line(finding.measurement)}")
        measurement = finding.measurement
        print(f"    seen in {measurement.distinct_games} of {measurement.games_with_data} games")

    _print_plan(selection, profile.plan)

    print(f"\nprofile  {args.out}  ({len(profile.findings)} findings)")

    if args.observations:
        _write_observations(observations, Path(args.observations))
        print(f"moves    {args.observations}")

    return 0


def _prefetch(session, games, args) -> None:
    """Fill the cache in parallel before the sequential pass reads it.

    Skipped without a cache, since there would be nowhere to put the results.
    """
    if session.cache is None:
        return

    def show(done: int, total: int) -> None:
        print(f"  evaluated {done}/{total} positions", end="\r", flush=True)

    new = prefetch(
        games,
        session.cache,
        engine=args.engine,
        depth=args.depth,
        workers=getattr(args, "workers", None),
        progress=show,
    )
    if new:
        print(f"  evaluated {new} new positions in parallel   ")


def _print_plan(selection, plan) -> None:
    """The plan, with the check the system is committing to."""
    if plan is None:
        return

    print(f"\nplan  ({selection.considered} findings considered, {len(plan.steps)} chosen)")
    for step, priority in zip(plan.steps, selection.priorities):
        claim = priority.finding.claim
        print(f"\n  {priority.rank}. {claim.kind} ({claim.subject})")
        print(f"       do    {step.action}")
        print(f"       why   {step.why}")
        print(f"       check {step.progress_sign}")

    if selection.not_selected:
        print(f"\n  set aside: {', '.join(selection.not_selected)}")


def _comparison_line(measurement) -> str:
    """State the comparison the decision was actually made against.

    Showing a self-baseline lift for a claim promoted on a peer comparison would
    misrepresent the evidence, which is the one thing this project's output must
    not do.
    """
    parts = [f"{measurement.rate:.1%}"]
    if measurement.peer_rate is not None:
        lift = measurement.lift_vs_peer
        parts.append(
            f"vs {measurement.peer_rate:.1%} for peers"
            + (f" — {lift:.2f}x" if lift else "")
        )
        if measurement.baseline_rate is not None:
            parts.append(f"(own other moves: {measurement.baseline_rate:.1%})")
    elif measurement.baseline_rate is not None:
        lift = measurement.lift_vs_baseline
        parts.append(
            f"vs {measurement.baseline_rate:.1%} on their other moves"
            + (f" — {lift:.2f}x" if lift else "")
        )
    return " ".join(parts)


def _report(observations: tuple[Observation, ...], cache: CacheStats | None) -> None:
    labels = Counter(o.label.value for o in observations if o.label)
    total = len(observations)
    errors = sum(labels.values())

    print(f"\nmoves    {total}")
    print(f"errors   {errors} ({100 * errors / max(1, total):.1f}%)")
    for name in ("inaccuracy", "mistake", "blunder"):
        print(f"  {name:<12} {labels.get(name, 0)}")

    phases = Counter(o.phase for o in observations)
    print("phases   " + ", ".join(f"{phase} {count}" for phase, count in sorted(phases.items())))

    if cache is not None:
        print(
            f"cache    {cache.hits} hits / {cache.lookups} lookups "
            f"({100 * cache.hit_rate:.1f}%), {cache.rows} rows"
        )


def _write_observations(observations: tuple[Observation, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as sink:
        for observation in observations:
            record = observation.__dict__.copy()
            record["label"] = observation.label.value if observation.label else None
            sink.write(json.dumps(record) + "\n")


def make_eval_set(args: argparse.Namespace) -> int:
    """Generate games carrying one known weakness, then check it is findable."""
    from chesscoach.evaluation.choosers import EngineMoveChooser
    from chesscoach.evaluation.planted import (
        FLAWED_PLAYER,
        TimeModel,
        WeaknessSpec,
        generate_games,
        total_spoiled,
        write_eval_set,
    )

    spec = WeaknessSpec(
        kind=args.kind,
        severity=args.severity,
        threshold_seconds=args.threshold_seconds,
        phase=args.phase,
        background_severity=args.background,
    )
    model = TimeModel(
        initial_seconds=args.initial_seconds,
        normal_think=args.normal_think,
        slow_think=args.slow_think,
        slow_until_ply=args.slow_until_ply,
    )

    print(f"planting {spec.kind} (severity {spec.severity}) across {args.games} games...", flush=True)
    with EngineMoveChooser(args.engine, depth=args.gen_depth) as chooser:
        games = generate_games(
            chooser, spec, n_games=args.games, seed=args.seed, time_model=model,
            max_plies=args.max_plies,
        )

    truth_path = write_eval_set(games, spec, args.out)
    plies = sum(game.n_plies for game in games)
    print(f"games    {len(games)} ({plies} plies)")
    print(f"planted  {total_spoiled(games)} spoiled moves, all played by {FLAWED_PLAYER}")
    print(f"written  {args.out}\n         {truth_path}")
    return 0


def check_eval_set(args: argparse.Namespace) -> int:
    """Confirm the planted weakness is actually visible to the analysis core.

    A planted flaw that the deterministic layer cannot see is not a test of any
    agent -- it is a broken fixture. This checks the fixture before anything is
    ever measured against it.
    """
    import json

    from chesscoach.evaluation.planted import FLAWED_PLAYER

    directory = Path(args.eval_set)
    truth = json.loads((directory / "ground_truth.json").read_text(encoding="utf-8"))
    spoiled = {
        game["game_id"]: set(game["spoiled_plies"]) for game in truth["games"]
    }

    games = load_games(directory / "planted.pgn")
    corpus = build_corpus(FLAWED_PLAYER, games)

    with engine_session(args.engine, args.depth, args.cache) as session:
        print(f"checking {corpus.n_games} games at depth {args.depth}...", flush=True)
        observations = analyse_corpus(corpus, games, session.analyser)

    flawed = [o for o in observations if o.mover == FLAWED_PLAYER]
    planted = [o for o in flawed if o.ply in spoiled.get(o.game_id, set())]
    clean = [o for o in flawed if o.ply not in spoiled.get(o.game_id, set())]

    planted_rate = _error_rate(planted)
    clean_rate = _error_rate(clean)
    print(f"\nplanted moves  {len(planted):>5}  error rate {planted_rate:.1%}")
    print(f"other moves    {len(clean):>5}  error rate {clean_rate:.1%}")
    if clean_rate > 0:
        print(f"lift           {planted_rate / clean_rate:.2f}x")

    usable = planted_rate > clean_rate
    print("\nfixture is usable" if usable else "\nFIXTURE PROBLEM: planted moves are not worse")
    return 0 if usable else 1


def _error_rate(observations: list[Observation]) -> float:
    if not observations:
        return 0.0
    return sum(1 for o in observations if o.is_error) / len(observations)


def score_agent(args: argparse.Namespace) -> int:
    """Run a section agent against a planted weakness and score it.

    Both halves count: did it find the flaw that was planted, and did it assert
    anything else? A detector that reports everything finds every planted
    weakness and is worthless.
    """
    import json

    from chesscoach.evaluation.planted import FLAWED_PLAYER, WeaknessSpec
    from chesscoach.evaluation.scoring import score_findings
    from chesscoach.sections.base import SectionContext
    from chesscoach.sections.s2_decision_process import S2DecisionProcess

    directory = Path(args.eval_set)
    truth = json.loads((directory / "ground_truth.json").read_text(encoding="utf-8"))
    spec = WeaknessSpec(**truth["spec"])

    games = load_games(directory / "planted.pgn")
    corpus = build_corpus(FLAWED_PLAYER, games)

    with engine_session(args.engine, args.depth, args.cache) as session:
        print(f"analysing {corpus.n_games} games at depth {args.depth}...", flush=True)
        observations = analyse_corpus(corpus, games, session.analyser)
        provenance = session.provenance(corpus.corpus_id)

    agent = S2DecisionProcess()
    report = agent.report(SectionContext(observations, corpus, provenance))
    card = score_findings(report.findings, spec, insufficient_data=report.insufficient_data)

    print(f"\nplanted        {spec.kind} (severity {spec.severity})")
    print(f"agent          {agent.section}")
    print(f"findings       {len(report.findings)}")
    for finding in report.findings:
        measurement = finding.measurement
        lift = measurement.lift_vs_baseline
        print(
            f"  [{finding.confidence.tier.value:>8}] {finding.claim.kind:<20}"
            f" rate {measurement.rate:.1%} vs baseline {measurement.baseline_rate:.1%}"
            f"{f' ({lift:.2f}x)' if lift else ''}"
            f"  {measurement.distinct_games} games"
        )
    if report.insufficient_data:
        print("  (insufficient data — the agent declined to assess)")

    print(f"\n{card.summary()}")
    return 0 if card.detected and card.spurious_count == 0 else 1


def check_progress(args: argparse.Namespace) -> int:
    """Go back and find out whether the plan's predictions came true.

    Measured over the games played **since** the plan only. A rate over the whole
    corpus would be diluted by the very games that produced the diagnosis.
    """
    from chesscoach.progress import check_plan

    previous = load_profile(args.profile)
    if previous.plan is None or not previous.plan.steps:
        print("that profile has no plan to check")
        return 1

    games = load_games(args.pgn)
    corpus = build_corpus(args.player, games)
    already_seen = set(previous.corpus.game_ids)
    new_ids = [game_id for game_id in corpus.game_ids if game_id not in already_seen]

    print(f"plan made   {previous.plan.created} over {previous.corpus.n_games} games")
    print(f"new games   {len(new_ids)}")
    if not new_ids:
        print("\nnothing to check yet: no games since the plan was made")
        return 0

    new_games = [game for game in games if game.game_id in set(new_ids)]
    new_corpus = build_corpus(args.player, new_games)

    with engine_session(args.engine, args.depth, args.cache) as session:
        _prefetch(session, new_games, args)
        observations = analyse_corpus(new_corpus, new_games, session.analyser)
        provenance = session.provenance(new_corpus.corpus_id)

    context = SectionContext(observations, new_corpus, provenance)
    later = {m.claim_key: m for agent in default_agents() for m in agent.measure(context)}
    previous_rates = {f.claim.key(): f.measurement.rate for f in previous.findings}

    report = check_plan(
        previous.plan,
        later,
        previous_rates=previous_rates,
        games_since=len(new_ids),
        checked_at=date.today().isoformat(),
    )
    _print_progress(report, previous.plan)

    if args.out:
        updated = replace(previous, plan=replace(previous.plan, outcomes=report.outcomes))
        save_profile(updated, args.out)
        print(f"\nprofile  {args.out}")
    return 0


def _print_progress(report, plan) -> None:
    """State each verdict, including the ones that did not go our way."""
    signs = {step.finding_id: step.progress_sign for step in plan.steps}
    labels = {
        "met": "MET",
        "not_met": "NOT MET",
        "too_early": "too early",
        "not_measurable": "cannot say",
    }

    print(f"\nprogress  ({report.summary()})")
    for outcome in report.outcomes:
        print(f"\n  [{labels.get(outcome.status, outcome.status)}] {outcome.finding_id}")
        print(f"       predicted  {signs.get(outcome.finding_id, '?')}")
        if outcome.observed_rate is None:
            print(f"       observed   no opportunities in {outcome.games_since} games")
        else:
            print(
                f"       observed   {outcome.observed_rate:.1%} "
                f"(was {outcome.previous_rate:.1%}, target {outcome.target_rate:.1%})"
            )


def build_peer_reference(args: argparse.Namespace) -> int:
    """Build a rating-band reference population from a directory of PGN files.

    Each file is one player, named by its filename — the layout `fetch_games.py`
    produces. Every agent's `measure` is collected, including the unremarkable
    numbers, because a reference made only of interesting players is not a
    reference.
    """
    from chesscoach.peers import build_reference

    directory = Path(args.pgn_dir)
    paths = sorted(directory.glob("*.pgn"))
    if not paths:
        print(f"no PGN files in {directory}")
        return 1

    agents = default_agents()
    collected: list[tuple[str, tuple]] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        # Prefetch across every player at once: openings repeat heavily between
        # players, so the corpus costs far less than the sum of its parts.
        all_games = [game for path in paths for game in load_games(path)]
        _prefetch(session, all_games, args)

        for path in paths:
            player = path.stem
            games = load_games(path)
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                print(f"  {player}: no games, skipped")
                continue

            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id)
            )
            measurements = tuple(m for agent in agents for m in agent.measure(context))
            collected.append((player, measurements))
            print(f"  {player}: {corpus.n_games} games, {len(measurements)} conditions", flush=True)

    reference = build_reference(
        collected, band=args.band, time_control=args.time_control, depth=args.depth
    )
    reference.save(args.out)

    print(f"\nplayers  {len(collected)}")
    print(f"band     {args.band} / {args.time_control} at depth {args.depth}")
    for key in sorted(reference.cells):
        stats = reference.cells[key]
        moves = sum(c.opportunities for c in stats)
        instances = sum(c.instances for c in stats)
        claim = key.split("|")[-1]
        share = instances / moves if moves else 0.0
        print(f"  {claim:<40} {share:6.1%}  ({instances}/{moves} moves, {len(stats)} players)")
    print(f"\nwritten  {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chesscoach")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run = subcommands.add_parser("analyse", help="analyse a player's games into a profile")
    run.add_argument("--pgn", required=True, help="PGN file or directory")
    run.add_argument("--player", required=True, help="username whose games are analysed")
    run.add_argument("--engine", required=True, help="path to the Stockfish binary")
    run.add_argument("--out", required=True, help="where to write the player profile")
    run.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    run.add_argument("--cache", default=None, help="SQLite evaluation cache path")
    run.add_argument("--workers", type=int, default=None, help="parallel engines for prefetch")
    run.add_argument("--observations", default=None, help="optional JSONL dump of every move")
    run.add_argument("--source", default="lichess")
    run.add_argument("--band", default="1400-1800")
    run.add_argument("--time-control", default="rapid")
    run.add_argument(
        "--peers",
        default=None,
        help="peer reference built by build-peer-reference; without it, "
        "selection-confounded conditions stay withheld",
    )
    run.set_defaults(handler=analyse)

    make = subcommands.add_parser("make-eval-set", help="generate games with a known weakness")
    make.add_argument("--engine", required=True)
    make.add_argument("--out", required=True, help="directory for the generated set")
    make.add_argument("--kind", default="time_pressure", choices=["time_pressure", "phase", "uniform"])
    make.add_argument("--severity", type=float, default=0.8)
    make.add_argument(
        "--background",
        type=float,
        default=0.15,
        help="mistake rate outside the planted condition, so the fixture is not unrealistically clean",
    )
    make.add_argument("--games", type=int, default=12)
    make.add_argument("--seed", type=int, default=1)
    make.add_argument("--threshold-seconds", type=float, default=60.0)
    make.add_argument("--phase", default="endgame")
    make.add_argument("--initial-seconds", type=float, default=300.0)
    make.add_argument("--normal-think", type=float, default=6.0)
    make.add_argument(
        "--slow-think",
        type=float,
        default=6.0,
        help="think time during the early slow phase; equal to --normal-think means no slow phase, "
        "which keeps a time-pressure plant from being confounded with a long-think signal",
    )
    make.add_argument("--slow-until-ply", type=int, default=0)
    make.add_argument("--max-plies", type=int, default=120)
    make.add_argument("--gen-depth", type=int, default=8, help="engine depth while generating")
    make.set_defaults(handler=make_eval_set)

    check = subcommands.add_parser(
        "check-eval-set", help="verify a planted weakness is visible to the analysis core"
    )
    check.add_argument("--eval-set", required=True, help="directory written by make-eval-set")
    check.add_argument("--engine", required=True)
    check.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    check.add_argument("--cache", default=None)
    check.set_defaults(handler=check_eval_set)

    score = subcommands.add_parser(
        "score-agent", help="run a section agent against a planted weakness and score it"
    )
    score.add_argument("--eval-set", required=True)
    score.add_argument("--engine", required=True)
    score.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    score.add_argument("--cache", default=None)
    score.set_defaults(handler=score_agent)

    peers = subcommands.add_parser(
        "build-peer-reference", help="build a rating-band reference population from PGN files"
    )
    peers.add_argument("--pgn-dir", required=True, help="directory of PGNs, one file per player")
    peers.add_argument("--engine", required=True)
    peers.add_argument("--out", required=True)
    peers.add_argument("--band", default="1400-1800")
    peers.add_argument("--time-control", default="rapid")
    peers.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    peers.add_argument("--cache", default=None)
    peers.add_argument("--workers", type=int, default=None, help="parallel engines for prefetch")
    peers.set_defaults(handler=build_peer_reference)

    progress = subcommands.add_parser(
        "check-progress", help="did the plan's predictions come true?"
    )
    progress.add_argument("--profile", required=True, help="a profile containing a plan")
    progress.add_argument("--pgn", required=True, help="games, including any played since")
    progress.add_argument("--player", required=True)
    progress.add_argument("--engine", required=True)
    progress.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    progress.add_argument("--cache", default=None)
    progress.add_argument("--workers", type=int, default=None)
    progress.add_argument("--out", default=None, help="write the profile back with its outcomes")
    progress.set_defaults(handler=check_progress)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
