"""The motifs must agree with an exchange, not with "is it defended?".

Screen: docs/notes/open-questions.md D17.

The author, after reading three reports against the games: *"Forks are wrongly
detected, placing pieces on the attacked spots count piece and pawn normal
exchanges."*

The shared cause is one helper. `_lands_safely` asked *"attacked by the enemy →
is it defended by me?"* with **no piece values and no exchange evaluation**,
while `chesscoach/material.py` already contained a static exchange evaluator the
motifs never called. Two notions of "safe" in one codebase, and the motifs used
the weaker one.

Every position here was verified legal and its exchange hand-checked before the
assertion was written.
"""

from __future__ import annotations

import chess

from chesscoach.material import wins_material
from chesscoach.tactics import Motif, detect_motifs

# Nc3-d5 attacks the c7 rook and the b6 knight. d5 is attacked by the e6 pawn
# and "defended" by the e4 pawn, so the naive test called it safe — but the
# exchange is knight for pawn and the move simply drops a piece.
FALSE_FORK = ("6k1/2r5/1n2p3/8/4P3/2N5/8/6K1 w - - 0 1", "c3d5")

# Nd5-c7 forks the e8 king and the a8 rook, and nothing attacks c7.
REAL_FORK = ("r3k3/8/8/3N4/8/8/8/6K1 w - - 0 1", "d5c7")

# Nc3-d5 with the same pawn geometry and nothing worth forking.
DEFENDED_BUT_LOST = ("r1bqkbnr/pppp1ppp/4p3/8/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "c3d5")


def motifs(fen: str, uci: str) -> set[str]:
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    assert move in board.legal_moves, f"{uci} is not legal in {fen}"
    return {str(m) for m in detect_motifs(board, move)}


class TestWinsMaterial:
    def test_it_reports_what_the_side_can_win_on_a_square(self):
        board = chess.Board(DEFENDED_BUT_LOST[0])
        board.push(chess.Move.from_uci(DEFENDED_BUT_LOST[1]))

        # Black plays exd5 and White recaptures: knight for pawn, so +2.
        assert wins_material(board, chess.D5, chess.BLACK) == 2

    def test_it_answers_for_either_side_regardless_of_whose_turn_it_is(self):
        board = chess.Board(REAL_FORK[0])
        board.push(chess.Move.from_uci(REAL_FORK[1]))

        # It is Black to move, but the question "what can White win on a8?" is
        # still well posed, and White wins the rook.
        assert wins_material(board, chess.A8, chess.WHITE) == 5

    def test_nothing_to_capture_wins_nothing(self):
        assert wins_material(chess.Board(), chess.E5, chess.WHITE) == 0


class TestFork:
    def test_a_move_that_simply_drops_the_piece_is_not_a_fork(self):
        assert Motif.FORK not in motifs(*FALSE_FORK)

    def test_a_genuine_fork_is_still_a_fork(self):
        assert Motif.FORK in motifs(*REAL_FORK)


class TestSafety:
    def test_defended_is_not_the_same_as_safe(self):
        # The whole defect in one assertion: d5 is defended, and landing there
        # loses two points of material.
        board = chess.Board(DEFENDED_BUT_LOST[0])
        board.push(chess.Move.from_uci(DEFENDED_BUT_LOST[1]))

        assert board.is_attacked_by(chess.WHITE, chess.D5)   # "defended"
        assert wins_material(board, chess.D5, chess.BLACK) > 0  # and lost anyway
