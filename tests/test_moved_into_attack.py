"""A move that puts a piece where it can be won, and not an ordinary trade.

Screen: docs/notes/open-questions.md D23, and the author's marks on
experiments/e46-motif-precision/results/detection-sheet.txt.

The claim scored **0 of 5** on real examples. Every rejection was a capture with
`exchange_value >= 0` — an ordinary trade, or better. The author wrote "exchange"
four times. One of the five, `Bxd8+`, **wins a queen** at +6 and was reported as
"you put the piece you have just moved on a square where it can be won".

The cause was a guard that excluded only *losing* captures, so an even-or-better
capture fell through to a test measuring the recapture **in isolation**, ignoring
what had just been taken. The fix is a clean partition, because `exchange_value`
already nets the whole sequence and for a quiet move equals `-swap` on the
destination:

    moved_into_attack   quiet move, exchange_value < 0
    miscounted_exchange capture,    exchange_value < 0

The five positions below are the author's own counterexamples, replayed from
their games.
"""

from __future__ import annotations

import chess

from chesscoach.material import exchange_value, miscounted_exchange, moved_into_attack

# (fen, uci, san) — every one a capture the author rejected.
REJECTED = [
    ("r2qk1nr/2p2pQp/2p1b3/p7/1pP5/2N3PN/PP1PPP1P/R1B1K2R b KQkq - 0 12", "b4c3", "bxc3"),
    ("rn1qk2r/pb2bppp/1p2p3/2ppP3/3Pn3/2PB1NN1/PP3PPP/R1BQK2R b KQkq - 1 9", "e4g3", "Nxg3"),
    ("rn1q3r/ppk2Bpp/4b3/6B1/1b6/6P1/PP2KP1P/R5NR w - - 0 14", "g5d8", "Bxd8+"),
    ("r4k1r/pb1n1pp1/1p1b1q1p/2p5/3p4/1BPP1N1P/PP1B1PP1/R2QR1K1 b - - 0 14", "b7f3", "Bxf3"),
    ("r4rk1/p3ppbp/2pq2p1/3bN3/2PPn3/1P1B3P/5PP1/R1BQ1RK1 b - - 0 17", "g7e5", "Bxe5"),
]


def played(fen: str, uci: str):
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    assert move in board.legal_moves, f"{uci} illegal in {fen}"
    return board, move


class TestTheReviewersCounterexamples:
    def test_none_of_the_five_rejected_moves_fires(self):
        firing = [
            san for fen, uci, san in REJECTED
            if moved_into_attack(*played(fen, uci))
        ]

        assert firing == []

    def test_winning_a_queen_is_not_moving_into_an_attack(self):
        # Bxd8+ nets +6. It was reported as putting a piece where it can be won.
        board, move = played(*REJECTED[2][:2])

        assert exchange_value(board, move) == 6
        assert not moved_into_attack(board, move)

    def test_an_even_trade_is_not_a_blunder(self):
        board, move = played(*REJECTED[1][:2])

        assert exchange_value(board, move) == 0
        assert not moved_into_attack(board, move)


class TestThePartition:
    def test_captures_belong_to_miscounted_exchange_never_to_this(self):
        for fen, uci, san in REJECTED:
            board, move = played(fen, uci)
            assert board.is_capture(move), san
            assert not moved_into_attack(board, move), san

    def test_a_quiet_move_onto_a_losing_square_still_fires(self):
        # Nd5 walks into exd5: a knight for a pawn, and nothing captured.
        board, move = played(
            "r1bqkbnr/pppp1ppp/4p3/8/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 0 1", "c3d5"
        )

        assert not board.is_capture(move)
        assert moved_into_attack(board, move)

    def test_a_losing_capture_is_a_miscounted_exchange_not_this(self):
        # Nxd5 loses a knight for a pawn — a miscount, not a walk into an attack.
        board, move = played(
            "rnbqkbnr/ppp2ppp/4p3/3p4/8/2N5/PPPPPPPP/R1BQKBNR w KQkq - 0 1", "c3d5"
        )

        assert miscounted_exchange(board, move)
        assert not moved_into_attack(board, move)

    def test_a_safe_quiet_move_fires_neither(self):
        board, move = played(chess.STARTING_FEN, "e2e4")

        assert not moved_into_attack(board, move)
        assert not miscounted_exchange(board, move)
