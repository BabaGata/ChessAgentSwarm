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
from chesscoach.ingest.lichess import DIAGNOSTIC_PERF_TYPES
from chesscoach.orchestrator import apply_to_profile, default_agents, diagnose, summarise
from chesscoach.pipeline import CacheStats, engine_session, load_games
from chesscoach.phrasing import move_number
from chesscoach.profile.io import load_profile, save_profile
from chesscoach.profile.models import ClassifierStatus, PlayerProfile, PlayerRef
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


# A ceiling on the accumulated window. Without one, a player with four thousand
# games would trigger a four-thousand-game analysis on their second visit, and C1
# is a constraint rather than an aspiration. Deep enough that the corpus is no
# longer what limits the diagnosis: E12 measured 150-game histories advising 83 %
# of players.
MAX_ACCUMULATED_GAMES = 300


def games_to_fetch(window: int, previous: PlayerProfile | None) -> int:
    """How many games to ask Lichess for, given what was analysed last time.

    At a fixed window the corpus **slides**: twenty new games push the twenty
    oldest out, and a player who returns after a month is diagnosed on no more
    evidence than before, having played more chess in between. Asking for their
    previous corpus *plus* the window means the second assessment is strictly
    better informed than the first, which is what makes coming back worth it.

    No local game store is needed for this, and the plan was wrong to imply one:
    **Lichess is the archive**, complete and free. Only the size of the request
    had to change.
    """
    if previous is None or previous.corpus.n_games <= 0:
        return window
    return min(previous.corpus.n_games + window, MAX_ACCUMULATED_GAMES)


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


def fetch_corpus(args: argparse.Namespace) -> int:
    """Fetch a band's worth of players' games — the input build-peer-reference needs.

    The first step of the chain in README "Running it", and the one that until
    now existed only in an experiments directory. Without it, a third party
    reproducing this project from the vault got as far as `--pgn-dir DIR` and had
    nowhere to get DIR from.

    Which players you get is not reproducible and is not meant to be: discovery
    reads arenas that finish daily. The band is what is fixed, and it is the band
    the rates are attributed to.
    """
    from chesscoach.ingest.lichess import LichessUnavailable
    from chesscoach.ingest.population import fetch_population

    low, high = (int(part) for part in args.band.split("-"))
    out = Path(args.out)
    print(f"band     {low}-{high}\nspeed    {args.speed or 'all diagnostic speeds'}")
    print(f"wanted   {args.players} players x {args.games} games")

    try:
        written = fetch_population(
            out,
            players=args.players,
            games=args.games,
            band=(low, high),
            speed=args.speed,
            exclude=tuple(Path(d) for d in (args.exclude or [])),
            progress=lambda line: print(line, flush=True),
        )
    except LichessUnavailable as error:
        print(f"could not reach Lichess: {error}")
        return 1

    total = sum(f.n_games for f in written)
    print(f"\nplayers  {len(written)} written to {out} ({total} games)")
    if len(written) < args.players:
        # Said plainly rather than left to be inferred from a file count: a
        # reference built from half the players asked for is still usable, and
        # the reader should decide that knowingly.
        print(
            f"fewer than the {args.players} asked for — arenas running now may not hold "
            "enough players in this band. Re-run to top the directory up; players "
            "already fetched are skipped."
        )
    return 0 if written else 1


def build_peer_reference(args: argparse.Namespace) -> int:
    """Build a rating-band reference population from a directory of PGN files.

    Each file is one player, named by its filename — the layout `fetch_games.py`
    produces. Every agent's `measure` is collected, including the unremarkable
    numbers, because a reference made only of interesting players is not a
    reference.
    """
    from chesscoach.peers import (
        build_reference,
        declared_band_is_wrong,
        declared_speed_is_wrong,
    )

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

        # Checked before the engine runs, not after: this takes minutes, and the
        # bad reference it would produce is indistinguishable from a good one.
        mismatch = declared_speed_is_wrong(all_games, args.time_control)
        if mismatch:
            print(f"refusing to build: {mismatch}")
            return 1

        # The other half of the same key. A lookup is (band, time_control,
        # claim); the speed arm has been checked since the stratum guard and the
        # band arm never was, so `--band` could say anything and the reference
        # would be built, used, and read as a statement about the player.
        # Reported for every player before refusing, because a corpus is fetched
        # by band and one stray file means a different fix from thirty.
        strays = [
            problem
            for path in paths
            if (problem := declared_band_is_wrong(load_games(path), path.stem, args.band))
        ]
        if strays:
            print(f"refusing to build: {len(strays)} of {len(paths)} players are "
                  f"not in the {args.band} band")
            for problem in strays:
                print(f"  {problem}")
            return 1

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

    if args.merge_with:
        # A reference has to span every speed a player might bring, because the
        # comparison is per-speed even though the evidence pools (E19). Cells are
        # keyed by time control, so merging adds strata rather than blending
        # them -- and `merged_with` refuses to mix analysis depths.
        from chesscoach.peers import PeerReference

        existing = PeerReference.load(args.merge_with)
        reference = existing.merged_with(reference)
        print(f"merged into {args.merge_with}")

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

    corpus = subcommands.add_parser(
        "fetch-corpus",
        help="fetch games for a band of players — the input build-peer-reference reads",
    )
    corpus.add_argument("--out", required=True, help="directory to write one PGN per player")
    corpus.add_argument("--band", default="1400-1800", help="rating band, as LOW-HIGH")
    corpus.add_argument(
        "--speed",
        default=None,
        choices=list(DIAGNOSTIC_PERF_TYPES),
        help="fetch one speed only. Give this whenever the directory feeds "
        "build-peer-reference, which labels a whole directory with its "
        "--time-control instead of reading each game's; a mixed directory "
        "therefore files blitz games as rapid and the stratum is a lie",
    )
    corpus.add_argument("--players", type=int, default=80)
    corpus.add_argument("--games", type=int, default=60, help="recent games per player")
    corpus.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="a directory whose players must not be fetched; repeatable. Use it to "
        "keep a held-out set held out",
    )
    corpus.set_defaults(handler=fetch_corpus)

    graph = subcommands.add_parser(
        "build-graph", help="build the graph knowledge base from files and code")
    graph.add_argument("--reset", action="store_true",
                       help="wipe first; safe, because nothing is authored in the database")
    graph.set_defaults(handler=build_graph)

    question = subcommands.add_parser(
        "ask", help="ask the knowledge base a chess question")
    question.add_argument("question")
    question.add_argument("--model", default="phi4-mini:3.8b")
    question.set_defaults(handler=ask)

    peers = subcommands.add_parser(
        "build-peer-reference", help="build a rating-band reference population from PGN files"
    )
    peers.add_argument("--pgn-dir", required=True, help="directory of PGNs, one file per player")
    peers.add_argument("--engine", required=True)
    peers.add_argument("--out", required=True)
    peers.add_argument("--band", default="1400-1800")
    peers.add_argument(
        "--time-control",
        default="rapid",
        help="the speed these PGNs were played at; becomes the stratum they are stored under",
    )
    peers.add_argument(
        "--merge-with",
        default=None,
        help="an existing reference to add these strata to, rather than replacing it",
    )
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

    session = subcommands.add_parser(
        "coach", help="one session: fetch a player's games and produce a coaching report"
    )
    session.add_argument("--player", required=True, help="a Lichess username")
    session.add_argument("--engine", required=True)
    session.add_argument("--peers", required=True, help="the reference population")
    session.add_argument("--out", default=None, help="where to write the profile")
    session.add_argument("--games", type=int, default=60, help="how many recent games to fetch")
    session.add_argument(
        "--previous",
        default=None,
        help="a profile from an earlier session. The corpus then grows to cover it "
        "plus the new games, instead of sliding forward and forgetting as much as "
        "it learns. Already-analysed games are free, the engine cache holds them",
    )
    session.add_argument("--pgn", default=None, help="use these games instead of fetching")
    session.add_argument("--cache", default=None)
    session.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    session.add_argument("--workers", type=int, default=None)
    session.add_argument("--band", default="1400-1800")
    session.add_argument("--time-control", default="rapid")
    session.add_argument("--probe", action="store_true", help="ask about the shortlist (V9)")
    session.add_argument("--model", default=None, help="ollama model for reading probe answers")
    session.add_argument("--collect", default=None, help="append probe answers to this JSONL")
    session.add_argument(
        "--no-questions",
        action="store_true",
        help="skip the four context questions (they size the plan, so the default is to ask)",
    )
    session.add_argument(
        "--runs", default=None,
        help="run store to read an approved opening brief from (data/runs.db)",
    )
    session.set_defaults(handler=coach)

    report = subcommands.add_parser("report", help="render a profile for a person to read")
    report.add_argument("--profile", required=True)
    report.add_argument("--out", default=None, help="write to a file instead of the terminal")
    report.set_defaults(handler=write_report)

    probe = subcommands.add_parser(
        "probe", help="ask the player about their shortlisted weaknesses (V9)"
    )
    probe.add_argument("--profile", required=True, help="a profile that already has findings")
    probe.add_argument("--out", required=True, help="where to write the profile with its probes")
    probe.add_argument("--model", default=None, help="ollama model; omitted means no classifier")
    probe.add_argument(
        "--collect",
        default=None,
        help="append answers to this JSONL as unlabelled data for D10",
    )
    probe.add_argument(
        "--apply",
        action="store_true",
        help="let probe results rewrite gap_type. Off by default: see D10",
    )
    probe.set_defaults(handler=run_probes)

    return parser



def _opening_brief(games, runs_path):
    """The approved brief for the opening this player leans on, if there is one.

    Two ways to get nothing, and both are correct rather than errors: no store,
    or no run for this opening that a person has approved. The report simply
    omits the section -- a gap in our curation is not news to the player.

    The opening is the family they play most, which is the same unit the guide
    library and the swarm both key on.
    """
    if not runs_path:
        return None
    path = Path(runs_path)
    if not path.exists():
        return None

    from collections import Counter

    from chesscoach.openings import OpeningBook
    from chesscoach.runstore import RunStore

    try:
        book = OpeningBook.load()
    except (OSError, ValueError):
        # No book downloaded is a setup gap, not a reason to lose the report.
        return None

    played: Counter = Counter()
    for game in games:
        walk = book.walk(list(game.moves))
        if walk.opening:
            played[walk.opening.name.split(":")[0].strip()] += 1
    if not played:
        return None

    with RunStore(path) as store:
        return store.approved_brief(played.most_common(1)[0][0])



def _opening_resource(games):
    """The moves of the opening this player plays, and the ones they reach.

    The deterministic half of the opening section, and it is separate from
    `_opening_brief` for one reason: **it needs no approval**. The brief is a
    model's wording of quoted sentences and cannot reach a player until someone
    endorses it; the moves are CC0 reference data from `lichess-org/chess-openings`
    and are true whether or not anyone has curated the opening
    ([[decisions.0012-quote-the-plans-rather-than-write-them]]).

    `build_resource` had been written, tested and called by nothing since it was
    built. A player whose opening nobody had reviewed was told nothing about it
    at all, when the moves were sitting in a file the repository already ships.

    Every failure here returns None rather than raising: a missing book or guide
    library is a setup gap, and losing the whole report over background reading
    would be the wrong trade.
    """
    from collections import Counter

    from chesscoach.opening_guides import GuideLibrary
    from chesscoach.opening_resource import build_resource
    from chesscoach.openings import OpeningBook

    try:
        book = OpeningBook.load()
        library = GuideLibrary.load()
    except (OSError, ValueError, KeyError):
        return None

    reached = []
    played: Counter = Counter()
    for game in games:
        walk = book.walk(list(game.moves))
        if walk.opening:
            reached.append(walk.opening.name)
            played[walk.opening.name.split(":")[0].strip()] += 1
    if not played:
        return None

    return build_resource(played.most_common(1)[0][0], book, library, reached=reached)


def coach(args: argparse.Namespace) -> int:
    """One coaching session, from a username to something a person can read.

    Implements the session flow in architecture.interaction § 1. Every stage
    already existed and was tested; what did not exist was a way to run them as
    one thing, which meant "using the swarm" started with a script in an
    experiments directory.
    """
    from chesscoach.band import notes_for
    from chesscoach.explainer import render
    from chesscoach.ingest.lichess import LichessUnavailable, fetch_games_pgn
    from chesscoach.ingest.pgn import parse_pgn_text

    print(f"player   {args.player}")

    previous = load_profile(args.previous) if args.previous else None
    if previous is not None:
        print(f"previous {previous.corpus.n_games} games, {previous.plan and len(previous.plan.steps) or 0} steps")

    if args.pgn:
        games = load_games(args.pgn)
        print(f"games    {len(games)} from {args.pgn}")
    else:
        wanted = games_to_fetch(args.games, previous)
        print(f"fetching up to {wanted} rated games...", flush=True)
        try:
            games = parse_pgn_text(fetch_games_pgn(args.player, wanted))
        except LichessUnavailable as error:
            print(f"could not fetch games: {error}")
            return 1
        print(f"games    {len(games)}")

    corpus = build_corpus(args.player, games)
    if corpus.n_games == 0:
        print(f"no rated rapid or classical games found for {args.player!r}")
        return 1

    peers = _load_peers(args)
    if peers is None:
        return 1

    # Asked before the engine runs, not after. Analysis takes minutes, and
    # someone who has just answered four questions waits more willingly than
    # someone who has been watching a progress bar.
    player_context = None if args.no_questions else ask_context()

    with engine_session(args.engine, args.depth, args.cache) as session:
        print(f"engine   {session.analyser.engine_name}\nanalysing {corpus.n_games} games...",
              flush=True)
        _prefetch(session, games, args)
        observations = analyse_corpus(corpus, games, session.analyser)
        provenance = session.provenance(corpus.corpus_id)

    context = SectionContext(
        observations, corpus, provenance,
        band=args.band, time_control=args.time_control, peers=peers,
    )
    diagnosis = diagnose(context, default_agents())
    profile = apply_to_profile(
        PlayerProfile(
            player=PlayerRef(source="lichess", username=args.player, band=args.band),
            corpus=corpus.to_ref(),
            strength=_strength(observations, args.player, games),
            style=_style(observations, args, peers, corpus),
            band_notes=notes_for(context),
            context=player_context,
        ),
        diagnosis,
    )
    profile = _planned(profile, peers, args, also=diagnosis.sub_threshold)

    if args.probe:
        profile = _probe_interactively(profile, peers, args)

    out = args.out or f"{args.player}-profile.json"
    save_profile(profile, out)
    print("\n" + "=" * 68 + "\n")
    print(render(profile, opening=_opening_brief(games, args.runs),
                 resource=_opening_resource(games)))
    print("\n" + "=" * 68)
    print(f"profile  {out}")
    return 0


def _strength(observations, username: str, games=()):
    """V1, as a profile field rather than a finding — it is not a weakness.

    `games` supplies each game's speed, because the estimate is per speed: a
    blitz corpus is read against the blitz fit and says so.
    """
    from chesscoach.profile.models import Strength
    from chesscoach.speed import speed_class
    from chesscoach.strength import estimate

    speeds = {g.game_id: speed_class(g.time_control) for g in games}
    measured = estimate(observations, username, speeds)
    if measured is None:
        return None
    return Strength(
        rating=measured.rating,
        typical_error=measured.typical_error,
        moves=measured.moves,
        method="blunder-rate-ols/e13",
        extrapolated=measured.extrapolated,
        speed=measured.speed,
    )


def _load_peers(args: argparse.Namespace):
    """The reference population, and the depth check that makes it comparable."""
    from chesscoach.peers import PeerReference

    if not args.peers:
        print(
            "no --peers given: without a reference population nothing can be called "
            "unusual, and the swarm will stay silent. Build one with build-peer-reference."
        )
        return None

    peers = PeerReference.load(args.peers)
    if peers.depth != args.depth:
        print(
            f"peer reference was built at depth {peers.depth}, analysis is at {args.depth}; "
            "rates are not comparable across depths (E01)"
        )
        return None
    return peers


# The author withdrew the style measurement on 2026-09-06 as processing time
# spent on something nothing reads. `describe` walks every diagnosable move and
# parses a FEN each time; the report withholds the paragraph and the agent no
# longer runs, so this computed a number for nobody. Kept whole for a future
# upgrade -- returning `()` is the only change.
STYLE_MEASURED = False


def _style(observations, args, peers, corpus) -> tuple:
    """V3 — how the player plays, never as a finding."""
    from chesscoach.profile.models import StyleTendency
    from chesscoach.style import describe

    if not STYLE_MEASURED:
        return ()

    tendency = describe(
        observations, args.player, peers, args.band, args.time_control, corpus.speed_mix
    )
    if tendency is None:
        return ()
    return (
        StyleTendency(
            name=tendency.name,
            share=round(tendency.share, 4),
            peer_share=round(tendency.peer_share, 4),
            moves=tendency.moves,
        ),
    )


def ask_context():
    """Step 2 of the session flow, wrapped so the CLI stays thin."""
    from chesscoach.context import ask

    return ask()


def _planned(profile, peers, args, also=()):
    """Attach a plan, sized to the time the player said they have.

    This is the whole reason the context questions exist: two priorities for
    someone with half an hour a week is a plan that fails and teaches them the
    system does not know them (architecture.interaction step 2).

    `also` carries the sub-threshold pool — patterns that cost this player real
    win probability and could not be shown to be unusual for their level. They
    fill slots the peer comparison left empty, never slots it wanted. The chosen
    ones are merged into `findings` so the report, the progress check and the
    saved profile can all resolve a plan step back to its measurement; they keep
    their `watch` tier, which is what tells the explainer to label them.
    """
    from chesscoach.context import priorities_for

    selection = select_priorities(
        profile.findings, limit=priorities_for(profile.context), also=also
    )
    chosen = {p.finding.id for p in selection.priorities}
    known = {f.id for f in profile.findings}
    profile = replace(
        profile,
        findings=tuple(
            sorted(
                profile.findings + tuple(f for f in also if f.id in chosen and f.id not in known),
                key=lambda finding: finding.id,
            )
        ),
    )
    return replace(
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


def _probe_interactively(profile, peers, args):
    """Ask about the shortlist, then re-plan in case a probe changed it."""
    from chesscoach.session import (
        Answer,
        append_to_answer_set,
        apply_probes,
        probes_for,
        record_answers,
    )

    probes = probes_for(profile)
    if not probes:
        print("\nnothing to probe: no prioritised finding carries a position to ask about")
        return profile

    classifier = None
    if args.model:
        from chesscoach.classifiers import OllamaClassifier

        classifier = OllamaClassifier(model=args.model)

    print(f"\n{len(probes)} position{'s' if len(probes) != 1 else ''}. Untimed — there is no "
          "clock here, and a wrong answer is more useful than a rushed one.\n")

    answers = []
    for index, probe in enumerate(probes, start=1):
        print(f"--- {index}/{len(probes)} " + "-" * 52)
        print(f"position  {probe.fen}")
        print(f"from      your game {probe.game_id}, move {move_number(probe.ply)}")
        print(f"\n{probe.asks}\n")
        move = input("  your move    > ").strip()
        reason = input("  why          > ").strip()
        answers.append(Answer(probe_id=probe.id, move=move or None, reason=reason or None))
        print()

    records = record_answers(probes, tuple(answers), classifier)
    for record in records:
        print(f"  {record.finding_id}: {'right' if record.move_correct else 'not the move'}"
              f"{_classifier_note(record)}")
    if any(r.classifier_status == ClassifierStatus.UNAVAILABLE.value for r in records):
        print("\nWARNING: the classifier could not be reached, so no reason was judged.")

    if args.collect:
        written = append_to_answer_set(records, Path(args.collect))
        print(f"collected {written} answer(s) -> {args.collect}")

    # Probe results are applied here, unlike the standalone `probe` command.
    # D10 is unresolved -- the classifier's agreement rests on answers written
    # and labelled by this project's author -- so the report states where a gap
    # type came from rather than the system pretending it did not.
    profile = apply_probes(profile, records, apply=True)
    return _planned(profile, peers, args)


def write_report(args: argparse.Namespace) -> int:
    """Layer 8 — the profile as prose. Deterministic, so it is reviewable."""
    from chesscoach.explainer import render

    text = render(load_profile(args.profile))
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"report   {args.out}")
        return 0
    print(text)
    return 0


def run_probes(args: argparse.Namespace) -> int:
    """Ask the player about the shortlist, and record what they say.

    Interactive by nature, so the logic lives in `chesscoach.session` where it
    can be tested and only the prompting happens here.
    """
    from chesscoach.session import (
        Answer,
        append_to_answer_set,
        apply_probes,
        probes_for,
        record_answers,
    )

    profile = load_profile(args.profile)
    probes = probes_for(profile)
    if not probes:
        print("nothing to probe: no prioritised finding carries a position with a better move")
        return 1

    classifier = None
    if args.model:
        from chesscoach.classifiers import OllamaClassifier

        classifier = OllamaClassifier(model=args.model)
        print(f"classifier {classifier.name}")
    else:
        print("no --model given: answers are recorded, gap types stay unknown")

    print(f"\n{len(probes)} position{'s' if len(probes) != 1 else ''}. "
          "Take as long as you like — this is not timed, and there is no clock.\n")

    answers = []
    for index, probe in enumerate(probes, start=1):
        print(f"--- {index}/{len(probes)} " + "-" * 52)
        print(f"position  {probe.fen}")
        print(f"from      your game {probe.game_id}, move {move_number(probe.ply)}")
        print(f"\n{probe.asks}\n")
        move = input("  your move    > ").strip()
        reason = input("  why          > ").strip()
        answers.append(Answer(probe_id=probe.id, move=move or None, reason=reason or None))
        print()

    records = record_answers(probes, tuple(answers), classifier)
    profile = apply_probes(profile, records, apply=args.apply)
    save_profile(profile, args.out)

    print("=" * 60)
    for record in records:
        move = "right" if record.move_correct else "not the move"
        why = _classifier_note(record)
        print(f"  {record.finding_id}: {move}, reads as {record.inference}{why}")

    if any(r.classifier_status == ClassifierStatus.UNAVAILABLE.value for r in records):
        print(
            "\nWARNING: the classifier could not be reached, so no reason was actually"
            "\njudged. Those probes are recorded as unavailable rather than as the"
            "\nplayer being unclear — check the model is running and ask again."
        )

    if not args.apply:
        print("\nrecorded but not applied — gap types are unchanged (D10). "
              "Pass --apply to let these rewrite the diagnosis.")

    if args.collect:
        written = append_to_answer_set(records, Path(args.collect))
        print(f"collected {written} answer(s) -> {args.collect}")

    print(f"profile  {args.out}")
    return 0


def _classifier_note(record) -> str:
    """Say why a verdict is missing, when it is missing for a reason worth knowing."""
    notes = {
        ClassifierStatus.UNAVAILABLE.value: "  (classifier unreachable — not judged)",
        ClassifierStatus.DECLINED.value: "  (no reason given)",
        ClassifierStatus.UNCLEAR.value: "  (reason did not read either way)",
        ClassifierStatus.NOT_CONFIGURED.value: "  (no --model, so reasons are not judged)",
    }
    return notes.get(record.classifier_status, "")



def build_graph(args: argparse.Namespace) -> int:
    """Build the graph knowledge base from files and code.

    Stage 1 of [[design.graph-knowledge-base]]: the rules of chess, generated
    from `python-chess`, and the Lichess speeds, read from the classifier that
    decides them. Nothing authored, so nothing to endorse.

    `--reset` is an ordinary operation rather than a dangerous one, and that is
    the point of Neo4j being a derived index: everything here is rebuilt from
    sources this repository versions.
    """
    from chesscoach.graph import GraphStore, GraphUnavailable, settings_from_env

    settings = settings_from_env()
    try:
        store = GraphStore.connect(settings)
    except GraphUnavailable as error:
        # Named loudly, because "no results" and "no database" must never look
        # the same to whoever reads the output (L-046).
        print(f"cannot reach the graph at {settings.uri}: {error}")
        print("start it with:  docker compose up -d")
        return 1

    with store:
        if args.reset:
            store.wipe()
            print("  wiped")
        store.ensure_schema()
        written = store.load_rules()
        print(f"  rules layer: {written} nodes")
        print(f"  domains and prerequisites: {store.load_domains()} nodes and edges")
        for label, n in sorted(store.counts().items()):
            print(f"    {label:<16}{n:>7}")
    return 0



def ask(args: argparse.Namespace) -> int:
    """Answer one chess question from the knowledge base.

    The conversational half of [[design.graph-knowledge-base]], and the reason
    the graph exists at all: the coach should be able to discuss a report rather
    than only hand one over.

    **A rules question is answered from the generated layer**, which is exact:
    piece movement comes from `python-chess` and the speeds from the classifier
    that decides them. Everything else is answered from the books, quoted and
    attributed, or refused.
    """
    from chesscoach.answering import answer
    from chesscoach.graph import GraphStore, GraphUnavailable, settings_from_env

    settings = settings_from_env()
    try:
        store = GraphStore.connect(settings)
    except GraphUnavailable as error:
        # Loudly, because a stopped database and a question nobody can answer
        # must never look the same (L-046).
        print(f"cannot reach the graph at {settings.uri}: {error}")
        print("start it with:  docker compose up -d")
        return 1

    with store:
        # No keyword gate in front of retrieval. A first version answered from
        # the rules layer when the question's **last word** named a rule, which
        # answered "what is a backward pawn?" with how a pawn moves and missed
        # "how does a knight move?" entirely. Rules and passages are indexed
        # together now and similarity decides which is relevant.
        found = answer(args.question, store, model=args.model)
    print(found.rendered())
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
