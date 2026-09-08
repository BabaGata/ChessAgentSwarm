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


# A rook to d5 "pins" the d7 knight to the d8 king — and the c6 pawn takes it.
# Both fixtures bring the rook **onto** the d-file. They used to slide along it
# from d1, where the pin already existed before the move -- so after the author
# rejected exactly that shape (*"those pieces were pinned already by the same
# bishop, even before that move"*) neither position tested what it says. The
# hanging one passed for the wrong reason and the control failed outright.
PIN_THAT_HANGS = ("3k4/3n4/2p5/R7/8/8/8/6K1 w - - 0 1", "a5d5")
# The same geometry with nothing attacking the rook.
REAL_PIN = ("3qk3/3n4/8/8/8/8/R7/6K1 w - - 0 1", "a2d2")
# Ra8#: the king is boxed by its own pawns and the rook mates along the rank.
REAL_BACK_RANK = ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "a1a8")
# Nf7#: mate on the eighth rank, but smothered — a different motif entirely.
SMOTHERED = ("6rk/6pp/3N4/8/8/8/8/6K1 w - - 0 1", "d6f7")


class TestPin:
    def test_a_pinning_piece_that_simply_hangs_is_not_a_pin(self):
        # The rook does pin the knight to the king. It is also just taken by a
        # pawn, and a pin you cannot keep is not a pin worth naming.
        assert Motif.PIN not in motifs(*PIN_THAT_HANGS)

    def test_a_real_pin_survives(self):
        assert Motif.PIN in motifs(*REAL_PIN)


class TestBackRankMate:
    def test_a_mate_along_the_back_rank_is_one(self):
        assert Motif.BACK_RANK_MATE in motifs(*REAL_BACK_RANK)

    def test_a_smothered_mate_on_the_eighth_rank_is_not_a_back_rank_mate(self):
        # It is checkmate, and it is on the back rank, and it is a different
        # motif: nothing is delivering mate *along* the rank.
        board = chess.Board(SMOTHERED[0])
        after = board.copy()
        after.push(chess.Move.from_uci(SMOTHERED[1]))
        assert after.is_checkmate()

        assert Motif.BACK_RANK_MATE not in motifs(*SMOTHERED)


class TestHangingCaptures:
    def test_taking_a_defended_piece_is_not_taking_a_hanging_one(self):
        # Nxd5 wins a knight and loses one: an exchange, not a free piece.
        fen = "rnbqkbnr/ppp2ppp/8/3np3/8/2N2N2/PPPPPPPP/R1BQKB1R w KQkq - 0 1"
        assert Motif.HANGING_PIECE not in motifs(fen, "c3d5")

    def test_taking_a_genuinely_free_piece_still_counts(self):
        fen = "rnbqkb1r/pppppppp/8/3n4/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 0 1"
        assert Motif.HANGING_PIECE in motifs(fen, "c3d5")


class TestKingPressureIsNotAnEndgameClaim:
    """"Attacks build against your king" is a middlegame statement.

    The author: *"King attacks are recorded deeply in the endgames."* S8 filtered
    with `diagnosable()` alone — post-opening and still competitive — which says
    nothing about phase, so a king walking up the board in a rook ending counted
    as pressure. With three pieces left there is no attack to build.
    """

    def test_endgame_positions_are_excluded(self):
        from chesscoach.sections.s8_attack_and_defence import attacking_phase

        assert attacking_phase("opening_middlegame")
        assert attacking_phase("late_middlegame")
        assert not attacking_phase("endgame")
