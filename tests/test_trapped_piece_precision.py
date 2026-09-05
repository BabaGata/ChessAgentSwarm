"""`trappedPiece` scored 40% on both claims (2y/3n each). E86.

Three of the five rejections were **checks**. Under check the only legal replies
are the ones that answer it, so every other enemy piece appears to have nowhere
to go -- the detector was reading the check's mobility, not the piece's.

This does not make the detector good. It agrees with the author on 6 of 10 marks
where the whole-board scan agreed on 3; the four it still gets wrong are recorded
in [[experiments.e86-detector-audit]], and two of them the author diagnoses as a
different motif ("This is fork").
"""

import chess

from chesscoach.tactics import Motif, detect_motifs


def traps(fen: str, san: str) -> bool:
    board = chess.Board(fen)
    return Motif.TRAPPED_PIECE in detect_motifs(board, board.parse_san(san))


class TestACheckDoesNotTrapEverything:
    def test_zvmw0et3_qf5_is_a_check_not_a_trap(self):
        assert not traps("2kr1bnr/ppp1pp2/8/4P1P1/7p/5QP1/PPqN2K1/R1B2R2 w - - 0 16", "Qf5+")

    def test_hri4cohc_bb4_is_a_check_not_a_trap(self):
        assert not traps("rnbq1b1r/ppk2Bpp/4Q3/6B1/8/6P1/PP2pP1P/R3K1NR b KQ - 4 12", "Bb4+")


class TestARealTrapStillFires:
    def test_pjzgpmwv_f5(self):
        """The author's [y], and a quiet move: the rule must not take it."""
        assert traps("r4r1k/pp2n1pp/1q3p2/4p3/3pB3/P2Q1N1P/1PP2PP1/R3R1K1 b - - 6 19", "f5")
