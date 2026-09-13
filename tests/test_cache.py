"""The position evaluation cache, keyed by (position, engine, depth).

Depth is part of the key, not a column: E01 measured that error labels differ
between depths, so mixing them is a correctness bug and the key prevents it
structurally rather than by discipline.
"""

from __future__ import annotations

from chesscoach.analysis.cache import EvalCache, Line, PositionEval

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class TestSeveralLinesForOnePosition:
    """MultiPV results, stored beside the single-line ones rather than inside.

    `missed_motif` needs the engine's *few good moves*, not only its best one
    ([[design.multipv-candidate-moves]]). The existing `position_eval` table
    holds **283,576 rows** that must keep working, and widening it would mean a
    migration for the sake of a column null on nearly all of them -- so the
    lines go in their own table, keyed the same way.

    The key includes **how many lines were asked for**. Three lines and five
    lines are different questions, and a cache that answered the second with the
    first would silently truncate -- which is exactly the failure the
    completeness check exists to rule out.
    """

    def test_lines_survive_a_round_trip(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            lines = (
                Line(uci="e2e4", score_cp=30, is_mate=False),
                Line(uci="d2d4", score_cp=25, is_mate=False),
            )
            cache.put_lines(FEN, "stub", 15, 2, lines)

            assert cache.get_lines(FEN, "stub", 15, 2) == lines

    def test_a_position_never_asked_about_returns_None(self, tmp_path):
        """Not an empty tuple: *"nothing stored"* and *"the engine returned no
        moves"* are different, and only one of them means run the engine."""
        with EvalCache(tmp_path / "c.db") as cache:
            assert cache.get_lines(FEN, "stub", 15, 3) is None

    def test_asking_for_more_lines_than_were_stored_is_a_miss(self, tmp_path):
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put_lines(FEN, "stub", 15, 3, (Line("e2e4", 30, False),))

            assert cache.get_lines(FEN, "stub", 15, 5) is None

    def test_fewer_lines_than_stored_is_a_hit(self, tmp_path):
        """Storing five and asking for three is answerable -- the top three of
        five are the top three."""
        with EvalCache(tmp_path / "c.db") as cache:
            stored = tuple(Line(f"e2e{i}", 30 - i, False) for i in range(1, 6))
            cache.put_lines(FEN, "stub", 15, 5, stored)

            assert cache.get_lines(FEN, "stub", 15, 3) == stored[:3]

    def test_the_single_line_table_is_untouched(self, tmp_path):
        """The 283,576 existing rows keep working, which is the whole reason
        this is a second table rather than a wider one."""
        with EvalCache(tmp_path / "c.db") as cache:
            cache.put(FEN, "stub", 15, PositionEval(score_cp=40, best_move="e2e4"))
            cache.put_lines(FEN, "stub", 15, 2, (Line("e2e4", 40, False),))

            assert cache.get(FEN, "stub", 15).score_cp == 40


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
