"""Converting engine output into an evaluation, without needing an engine.

The mate case is the one that matters: Stockfish encodes mate as roughly
+-30000, which would turn a mate-delivering move into an enormous apparent loss
if it were differenced raw (lesson L-005).
"""

from __future__ import annotations

import chess
import chess.engine

from chesscoach.analysis.engine import to_position_eval
from chesscoach.analysis.labels import CLAMP_CP


def info(score: chess.engine.Score, pv: list[str] | None = None) -> dict:
    payload: dict = {"score": chess.engine.PovScore(score, chess.WHITE)}
    if pv is not None:
        payload["pv"] = [chess.Move.from_uci(uci) for uci in pv]
    return payload


class TestToPositionEval:
    def test_passes_an_ordinary_evaluation_through(self):
        assert to_position_eval(info(chess.engine.Cp(35))).score_cp == 35

    def test_clamps_a_mate_for_white_to_the_upper_bound(self):
        evaluation = to_position_eval(info(chess.engine.Mate(3)))

        assert evaluation.score_cp == CLAMP_CP
        assert evaluation.is_mate is True

    def test_clamps_a_mate_against_white_to_the_lower_bound(self):
        assert to_position_eval(info(chess.engine.Mate(-2))).score_cp == -CLAMP_CP

    def test_clamps_an_extreme_centipawn_score(self):
        assert to_position_eval(info(chess.engine.Cp(28000))).score_cp == CLAMP_CP

    def test_extracts_the_first_move_of_the_principal_variation(self):
        assert to_position_eval(info(chess.engine.Cp(0), ["e2e4", "e7e5"])).best_move == "e2e4"

    def test_tolerates_a_missing_principal_variation(self):
        assert to_position_eval(info(chess.engine.Cp(0))).best_move is None
