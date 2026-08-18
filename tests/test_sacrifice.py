"""Telling an attacking sacrifice from an exchange that did not add up.

The reviewer's correction, and it is a chess distinction the first version of
S7 collapsed:

    "a sacrifice is when a player deliberately gives a stronger piece for a
     weaker piece to make opening for attack which is usually on the king. So
     this is not something like giving a good positioned and active bishop for
     an opponent's inactive knight but something like taking a pawn with a
     bishop on the kings castle or rook for a defending knight. Those are
     usually direct material losses while miscalculated exchange can be usually
     seen after 2 or 3 moves."

It matters because the advice differs completely. Telling an attacking player
they "miscount exchanges" when they are deliberately sacrificing is the same
kind of wrong as telling a player to work on time pressure they already handle
well — it prescribes the half they are not doing.
"""

from __future__ import annotations

import chess

from chesscoach.material import (
    ATTACK_RADIUS,
    best_free_capture,
    declined_material_to_attack,
    material_balance,
    miscounted_exchange,
    miscounted_exchange_away_from_king,
    moved_toward_king,
    near_king,
    sacrificed_for_attack,
)

# White bishop on c4, black king castled on g8 with pawns f7/g7/h7. Bxf7+ gives
# a bishop for a pawn on the king's doorstep: the classic sacrifice.
GREEK_GIFT = "r1bq1rk1/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 w - - 0 1"

# The same losing capture, far from the king: a bishop takes a defended pawn on
# a6 while the black king sits on g8.
FAR_SIDE = "r1bq1rk1/1ppp1ppp/p1n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 w - - 0 1"


class TestNearKing:
    def test_the_square_beside_the_king_is_near(self):
        board = chess.Board(GREEK_GIFT)

        assert near_king(board, chess.F7, chess.BLACK) is True

    def test_two_squares_away_is_still_near(self):
        # A rook taking a knight on f6 that defends the king is the same idea as
        # taking on h7, and only one of them touches the king.
        board = chess.Board(GREEK_GIFT)

        assert near_king(board, chess.F6, chess.BLACK) is True

    def test_the_far_side_of_the_board_is_not(self):
        board = chess.Board(GREEK_GIFT)

        assert near_king(board, chess.A6, chess.BLACK) is False

    def test_the_radius_is_two(self):
        assert ATTACK_RADIUS == 2


class TestSacrificeAgainstMiscount:
    def test_a_bishop_for_a_pawn_beside_the_king_is_a_sacrifice(self):
        board = chess.Board(GREEK_GIFT)
        move = chess.Move.from_uci("c4f7")

        assert move in board.legal_moves
        assert sacrificed_for_attack(board, move) is True

    def test_and_it_is_not_counted_as_a_miscount(self):
        # The two must partition the losing captures, or a single move produces
        # two findings with opposite advice.
        board = chess.Board(GREEK_GIFT)
        move = chess.Move.from_uci("c4f7")

        assert miscounted_exchange(board, move) is True
        assert miscounted_exchange_away_from_king(board, move) is False

    def test_the_same_loss_far_from_the_king_is_a_miscount(self):
        board = chess.Board(FAR_SIDE)
        move = chess.Move.from_uci("c4a6")

        assert move in board.legal_moves
        assert miscounted_exchange(board, move) is True
        assert miscounted_exchange_away_from_king(board, move) is True
        assert sacrificed_for_attack(board, move) is False

    def test_a_capture_that_wins_material_is_neither(self):
        # Taking a genuinely free pawn near the king is good play, not a
        # sacrifice, however close to the king it lands. The king is on h8 so it
        # cannot recapture on f7 — with it on g8 this capture really would be a
        # sacrifice, which is the point.
        board = chess.Board("7k/5p2/8/8/2B5/8/8/6K1 w - - 0 1")
        move = chess.Move.from_uci("c4f7")

        assert near_king(board, chess.F7, chess.BLACK) is True

        assert move in board.legal_moves
        assert sacrificed_for_attack(board, move) is False
        assert miscounted_exchange_away_from_king(board, move) is False

    def test_soundness_is_not_asked(self):
        # Deliberately: conditioning on the engine faulting the move measured
        # r = +0.682 with the overall error rate against +0.125 unconditioned,
        # which is the failure that refused two candidates in E34.
        board = chess.Board(GREEK_GIFT)

        assert sacrificed_for_attack(board, chess.Move.from_uci("c4f7")) is True


class TestMaterialBalance:
    def test_the_opening_position_is_level(self):
        assert material_balance(chess.Board(), chess.WHITE) == 0

    def test_a_piece_up_reads_positive(self):
        board = chess.Board("4k3/8/8/8/8/8/8/4K1N1 w - - 0 1")

        assert material_balance(board, chess.WHITE) == 3
        assert material_balance(board, chess.BLACK) == -3

    def test_kings_are_not_counted(self):
        assert material_balance(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1"), chess.WHITE) == 0


class TestDecliningMaterialToAttack:
    def test_the_free_capture_is_found(self):
        # Black pawn on a7 is free; the white rook on a1 can take it.
        board = chess.Board("4k3/p7/8/8/8/8/6B1/R3K3 w - - 0 1")
        move, gain = best_free_capture(board)

        assert gain >= 1
        assert move.to_square == chess.A7

    def test_walking_toward_the_king_while_ignoring_it_counts(self):
        board = chess.Board("4k3/p7/8/8/8/8/6B1/R3K3 w - - 0 1")
        # Bishop steps toward the black king instead of taking on a7.
        move = chess.Move.from_uci("g2c6")

        assert move in board.legal_moves
        assert moved_toward_king(board, move) is True
        assert declined_material_to_attack(board, move) is True

    def test_declining_it_for_a_quiet_move_does_not(self):
        # Passing up material is a different habit, possibly a better one. This
        # claim is about the trade the player keeps choosing.
        board = chess.Board("4k3/p7/8/8/8/8/6B1/R3K3 w - - 0 1")
        move = chess.Move.from_uci("g2h1")

        assert declined_material_to_attack(board, move) is False

    def test_taking_the_material_is_never_declining_it(self):
        board = chess.Board("4k3/p7/8/8/8/8/6B1/R3K3 w - - 0 1")

        assert declined_material_to_attack(board, chess.Move.from_uci("a1a7")) is False

    def test_with_nothing_on_offer_nothing_is_declined(self):
        board = chess.Board("4k3/8/8/8/8/8/6B1/R3K3 w - - 0 1")

        assert declined_material_to_attack(board, chess.Move.from_uci("g2c6")) is False
