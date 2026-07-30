"""The engine/cache session shared by every command.

Extracted in M6: the open-cache, open-engine, analyse, close-both sequence was
repeated in three CLI commands, which is both a duplication and the reason those
commands were the least tested code in the project.
"""

from __future__ import annotations

import chess

from chesscoach.analysis.cache import EvalCache, PositionEval
from chesscoach.pipeline import EngineSession, load_games

PGN = """[Event "Rapid"]
[Site "https://lichess.org/aaa111"]
[GameId "aaa111"]
[White "alice"]
[Black "bob"]
[Result "1-0"]
[TimeControl "600+0"]
[Variant "Standard"]

1. e4 { [%clk 0:10:00] } 1... e6 { [%clk 0:09:58] } 1-0
"""


class StubAnalyser:
    engine_name = "Stockfish 18"
    depth = 15

    def analyse(self, board: chess.Board) -> PositionEval:
        return PositionEval(score_cp=0, best_move="e2e4")


class TestProvenance:
    def test_records_the_engine_and_depth_it_actually_used(self):
        session = EngineSession(StubAnalyser(), cache=None)

        provenance = session.provenance("corpus1", analysed_at="2026-07-29")

        assert provenance.engine == "Stockfish 18"
        assert provenance.depth == 15
        assert provenance.corpus_id == "corpus1"

    def test_defaults_the_date_to_today(self):
        from datetime import date

        session = EngineSession(StubAnalyser(), cache=None)

        assert session.provenance("c").analysed_at == date.today().isoformat()


class TestCacheStats:
    def test_reports_nothing_without_a_cache(self):
        assert EngineSession(StubAnalyser(), cache=None).cache_stats() is None

    def test_reports_hits_lookups_and_rows(self, tmp_path):
        cache = EvalCache(tmp_path / "c.db")
        cache.put("fen", "Stockfish 18", 15, PositionEval(score_cp=1))
        cache.get("fen", "Stockfish 18", 15)
        cache.get("other", "Stockfish 18", 15)

        stats = EngineSession(StubAnalyser(), cache=cache).cache_stats()

        assert (stats.hits, stats.lookups, stats.rows) == (1, 2, 1)
        assert stats.hit_rate == 0.5

    def test_stats_survive_the_session_closing(self, tmp_path):
        # Callers report these numbers after the work is done, by which point
        # the connection needed for a row count is gone.
        cache = EvalCache(tmp_path / "c.db")
        cache.put("fen", "Stockfish 18", 15, PositionEval(score_cp=1))
        session = EngineSession(StubAnalyser(), cache=cache)

        session._final_stats = session.cache_stats()
        cache.close()

        assert session.cache_stats().rows == 1


class TestLoadGames:
    def test_reads_a_single_pgn_file(self, tmp_path):
        path = tmp_path / "games.pgn"
        path.write_text(PGN, encoding="utf-8")

        assert len(load_games(path)) == 1

    def test_reads_every_pgn_in_a_directory(self, tmp_path):
        (tmp_path / "a.pgn").write_text(PGN, encoding="utf-8")
        (tmp_path / "b.pgn").write_text(PGN.replace("aaa111", "bbb222"), encoding="utf-8")

        assert len(load_games(tmp_path)) == 2

    def test_returns_nothing_for_an_empty_directory(self, tmp_path):
        assert load_games(tmp_path) == ()
