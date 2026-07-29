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
from datetime import date
from pathlib import Path

from chesscoach.analysis.cache import EvalCache
from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.engine import DEFAULT_DEPTH, StockfishAnalyser
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import parse_pgn_dir, parse_pgn_file
from chesscoach.profile.io import save_profile
from chesscoach.profile.models import PlayerProfile, PlayerRef


def analyse(args: argparse.Namespace) -> int:
    source = Path(args.pgn)
    games = parse_pgn_dir(source) if source.is_dir() else parse_pgn_file(source)
    if not games:
        print(f"no standard games found in {source}")
        return 1

    corpus = build_corpus(args.player, games)
    if corpus.n_games == 0:
        print(f"no games found for player {args.player!r} in {source}")
        return 1

    print(f"player   {args.player}")
    print(f"games    {corpus.n_games}")
    print(f"corpus   {corpus.corpus_id}")
    print(f"depth    {args.depth}")

    cache = EvalCache(args.cache) if args.cache else None
    try:
        with StockfishAnalyser(args.engine, depth=args.depth, cache=cache) as analyser:
            print(f"engine   {analyser.engine_name}\nanalysing...", flush=True)
            observations = analyse_corpus(corpus, games, analyser)
    finally:
        if cache is not None:
            cache.commit()

    profile = PlayerProfile(
        player=PlayerRef(source=args.source, username=args.player, band=args.band),
        corpus=corpus.to_ref(),
    )
    save_profile(profile, args.out)

    _report(observations, cache)
    print(f"\nprofile  {args.out}  ({len(profile.findings)} findings — section agents arrive in M4)")

    if args.observations:
        _write_observations(observations, Path(args.observations))
        print(f"moves    {args.observations}")

    if cache is not None:
        cache.close()
    return 0


def _report(observations: tuple[Observation, ...], cache: EvalCache | None) -> None:
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
        looked_up = cache.hits + cache.misses
        share = 100 * cache.hits / max(1, looked_up)
        print(f"cache    {cache.hits} hits / {looked_up} lookups ({share:.1f}%), {cache.size()} rows")


def _write_observations(observations: tuple[Observation, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as sink:
        for observation in observations:
            record = observation.__dict__.copy()
            record["label"] = observation.label.value if observation.label else None
            sink.write(json.dumps(record) + "\n")


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
    run.add_argument("--observations", default=None, help="optional JSONL dump of every move")
    run.add_argument("--source", default="lichess")
    run.add_argument("--band", default="1400-1800")
    run.set_defaults(handler=analyse)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
