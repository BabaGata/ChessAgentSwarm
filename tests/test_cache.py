"""The position evaluation cache, keyed by (position, engine, depth).

Depth is part of the key, not a column: E01 measured that error labels differ
between depths, so mixing them is a correctness bug and the key prevents it
structurally rather than by discipline.
"""

from __future__ import annotations

from chesscoach.analysis.cache import EvalCache, PositionEval

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def a_position_eval(**overrides) -> PositionEval:
    defaults = dict(score_cp=30, best_move="e2e4", is_mate=False)
    return PositionEval(**{**defaults, **overrides})


class TestEvalCache:
    def test_returns_none_for_an_unseen_position(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            assert cache.get(FEN, "sf18", 15) is None

    def test_round_trips_a_stored_evaluation(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "sf18", 15, a_position_eval())

            assert cache.get(FEN, "sf18", 15) == a_position_eval()

    def test_a_different_depth_is_a_different_key(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "sf18", 15, a_position_eval(score_cp=30))

            assert cache.get(FEN, "sf18", 20) is None

    def test_a_different_engine_is_a_different_key(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "sf18", 15, a_position_eval())

            assert cache.get(FEN, "sf17", 15) is None

    def test_persists_across_connections(self, tmp_path):
        path = tmp_path / "c.db"
        with EvalCache(path) as cache:
            cache.put(FEN, "sf18", 15, a_position_eval())

        with EvalCache(path) as reopened:
            assert reopened.get(FEN, "sf18", 15) == a_position_eval()

    def test_storing_the_same_key_twice_overwrites_rather_than_duplicating(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "sf18", 15, a_position_eval(score_cp=30))
            cache.put(FEN, "sf18", 15, a_position_eval(score_cp=45))

            assert cache.get(FEN, "sf18", 15).score_cp == 45
            assert cache.size() == 1

    def test_reports_hits_and_misses(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "sf18", 15, a_position_eval())
            cache.get(FEN, "sf18", 15)
            cache.get(FEN, "sf18", 20)

            assert cache.hits == 1
            assert cache.misses == 1
