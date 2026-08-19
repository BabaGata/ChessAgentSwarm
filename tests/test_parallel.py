"""Pre-evaluating positions in parallel.

E01 measured two things that dictate this design: at a fixed depth a single
engine thread is fastest per position, and parallelising *per game* leaves wall
time hostage to the longest game. So positions are collected across the whole
corpus, deduplicated, evaluated across many single-threaded engines, and written
to the cache in one pass. The ordinary sequential analysis then runs on cache
hits alone.
"""

from __future__ import annotations

from chesscoach.analysis.cache import EvalCache, PositionEval
from chesscoach.analysis import parallel
from chesscoach.analysis.parallel import collect_positions, prefetch
from chesscoach.ingest.pgn import parse_pgn_text

PGN = """[Event "Rapid"]
[Site "https://lichess.org/aaa111"]
[GameId "aaa111"]
[White "alice"]
[Black "bob"]
[Result "1-0"]
[Variant "Standard"]

1. e4 e5 2. Nf3 1-0

[Event "Rapid"]
[Site "https://lichess.org/bbb222"]
[GameId "bbb222"]
[White "alice"]
[Black "carol"]
[Result "1-0"]
[Variant "Standard"]

1. e4 e5 2. Nc3 1-0
"""


class TestCollectPositions:
    def test_collects_every_position_including_the_last(self):
        games = parse_pgn_text(PGN)[:1]

        positions = collect_positions(games)

        assert len(positions) == len(games[0].moves) + 1

    def test_deduplicates_positions_shared_between_games(self):
        # Both games open 1.e4 e5, so their first three positions coincide.
        games = parse_pgn_text(PGN)

        positions = collect_positions(games)

        assert len(positions) == 5  # 3 shared + 1 unique continuation each

    def test_is_deterministic(self):
        games = parse_pgn_text(PGN)

        assert collect_positions(games) == collect_positions(games)

    def test_ignores_illegal_continuations_rather_than_raising(self):
        games = parse_pgn_text(PGN.replace("2. Nf3", "2. Nf6"))

        assert len(collect_positions(games)) > 0


class TestPrefetch:
    def test_writes_every_evaluation_to_the_cache(self, tmp_path):
        games = parse_pgn_text(PGN)
        cache = EvalCache(tmp_path / "c.db")

        written = prefetch(
            games, cache, engine="stub", depth=15, evaluate_batch=_stub_batch
        )

        assert written == 5
        assert cache.size() == 5

    def test_skips_positions_already_cached(self, tmp_path):
        games = parse_pgn_text(PGN)
        cache = EvalCache(tmp_path / "c.db")
        prefetch(games, cache, engine="stub", depth=15, evaluate_batch=_stub_batch)

        written = prefetch(games, cache, engine="stub", depth=15, evaluate_batch=_stub_batch)

        assert written == 0

    def test_a_different_depth_is_a_different_job(self, tmp_path):
        games = parse_pgn_text(PGN)
        cache = EvalCache(tmp_path / "c.db")
        prefetch(games, cache, engine="stub", depth=15, evaluate_batch=_stub_batch)

        written = prefetch(games, cache, engine="stub", depth=20, evaluate_batch=_stub_batch)

        assert written == 5

    def test_does_nothing_without_games(self, tmp_path):
        cache = EvalCache(tmp_path / "c.db")

        assert prefetch((), cache, engine="stub", depth=15, evaluate_batch=_stub_batch) == 0


def _stub_batch(fens, engine, depth, workers=1):
    return {fen: PositionEval(score_cp=len(fen) % 50, best_move="e2e4") for fen in fens}


class TestChunkSizing:
    """A new process pool is built for every chunk, and on Windows that spawns
    rather than forks: each child re-imports the module and launches its own
    Stockfish. What matters is how many positions each worker gets before the
    pool is torn down, not how many the chunk holds.

    The old flat CHUNK_SIZE of 250 gave 18 workers **14 positions each**, so a
    129,000-position corpus paid for ~500 pools. Measured on the real corpus,
    sizing per worker took the prefetch from 6 to 30 positions a second — the
    difference between a 20-hour build and a 2-hour one.
    """

    def size_for(self, workers: int) -> int:
        return max(parallel.MIN_CHUNK_SIZE, workers * parallel.POSITIONS_PER_WORKER)

    def test_each_worker_gets_hundreds_of_positions_not_a_dozen(self):
        assert parallel.POSITIONS_PER_WORKER >= 200

    def test_the_chunk_scales_with_the_worker_count(self):
        # A bigger machine must not mean more pools for the same work.
        assert self.size_for(18) > self.size_for(4)

    def test_a_tiny_corpus_still_gets_one_chunk(self):
        # The floor exists so a handful of positions is not split into slivers.
        assert parallel.MIN_CHUNK_SIZE >= 250
        assert self.size_for(1) >= parallel.MIN_CHUNK_SIZE
