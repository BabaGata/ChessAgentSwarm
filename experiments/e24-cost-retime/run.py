"""Re-time D9, which was measured before blitz joined the corpus.

The old figure -- ~7.6 s warm for 60 games, roughly two minutes cold -- assumed
the swarm looks at rapid and classical only. A fresh player now brings up to 5x
the games (E21) and a returning one up to 300 (E22), so the number needs
remeasuring rather than adjusting.

Cold means **cold**: a throwaway cache file, so nothing this project has already
analysed is available. That is what a genuinely new player costs.

Usage:  python d9_retime.py PLAYER GAMES
"""

import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm")

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.parallel import prefetch  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.explainer import render  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.orchestrator import apply_to_profile, default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.planner import build_plan  # noqa: E402
from chesscoach.profile.models import PlayerProfile, PlayerRef  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ENGINE = r"C:\stockfish\stockfish-windows-x86-64-avx2.exe"
SCRATCH = Path(__file__).resolve().parent
WORKERS = 8
DEPTH = 15

PLAYER = sys.argv[1] if len(sys.argv) > 1 else "Ahmad_bob"
WANTED = int(sys.argv[2]) if len(sys.argv) > 2 else 60


def load_games():
    """The games a fresh fetch would return: the most recent N across every speed."""
    pool = []
    for directory in ("histories-deep", "histories-blitz"):
        path = SCRATCH / directory / f"{PLAYER}.pgn"
        if path.exists():
            pool += [g for g in parse_pgn_file(path) if g.involves(PLAYER)]
    return tuple(sorted(pool, key=lambda g: (g.date or "", g.game_id))[-WANTED:])


def session(cache_path: Path, label: str, games, peers) -> None:
    stages: dict[str, float] = {}
    started = time.perf_counter()

    corpus = build_corpus(PLAYER, games)
    with engine_session(ENGINE, DEPTH, str(cache_path)) as engine:
        mark = time.perf_counter()
        new = prefetch(games, engine.cache, engine=ENGINE, depth=DEPTH, workers=WORKERS)
        stages["engine analysis"] = time.perf_counter() - mark

        mark = time.perf_counter()
        observations = analyse_corpus(corpus, games, engine.analyser)
        stages["reading the cache"] = time.perf_counter() - mark

        context = SectionContext(
            observations, corpus, engine.provenance(corpus.corpus_id),
            band="1400-1800", time_control="rapid", peers=peers,
        )
        mark = time.perf_counter()
        result = diagnose(context, default_agents())
        stages["diagnosis"] = time.perf_counter() - mark

    mark = time.perf_counter()
    profile = apply_to_profile(
        PlayerProfile(
            player=PlayerRef(source="lichess", username=PLAYER, band="1400-1800"),
            corpus=corpus.to_ref(),
        ),
        result,
    )
    selection = select_priorities(profile.findings)
    from dataclasses import replace

    profile = replace(profile, plan=build_plan(selection.priorities, created="2026-08-06"))
    render(profile)
    stages["plan and report"] = time.perf_counter() - mark

    total = time.perf_counter() - started
    print(f"--- {label}")
    print(f"    positions newly evaluated  {new}")
    for name, seconds in stages.items():
        print(f"    {name:<22} {seconds:>7.1f}s")
    print(f"    {'TOTAL':<22} {total:>7.1f}s   "
          f"({len(profile.findings)} findings, {total / len(games):.2f}s per game)\n")


def clear(cache_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{cache_path}{suffix}").unlink(missing_ok=True)


if __name__ == "__main__":
    # Required on Windows: prefetch spawns worker processes, which re-import
    # this module. Without the guard every worker reruns the whole timing.
    games = load_games()
    peers = PeerReference.load(SCRATCH / "peers-pooled-v1.json")
    print(f"{PLAYER}: {len(games)} games, depth {DEPTH}, {WORKERS} workers\n")

    cold_cache = SCRATCH / "d9_cold.db"
    clear(cold_cache)
    session(cold_cache, "COLD -- a genuinely new player, empty cache", games, peers)
    session(cold_cache, "WARM -- the same player again", games, peers)
    clear(cold_cache)
