"""Why material was lost: static exchange evaluation and the four causes.

Answers D13. These are the first detectors in the project that read **the move
the player actually played** rather than the engine's best move or the
opponent's reply, which is the structural gap E33 named.

Correctness first, discrimination second: these tests say the arithmetic is
right. Whether any of it earns a place in a report is E34's question, and a
detector that fires accurately on something every player does equally is still
worthless (L-024).
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.material import (
    exchange_value,
    ignored_threat,
    left_hanging,
    miscounted_exchange,
    moved_into_attack,
)


def value(fen: str, uci: str) -> int:
    return exchange_value(chess.Board(fen), chess.Move.from_uci(uci))


class TestExchangeValue:
    def test_taking_a_free_pawn_wins_a_pawn(self):
        assert value("4k3/8/8/8/p7/8/8/R3K3 w - - 0 1", "a1a4") == 1

    def test_taking_a_defended_pawn_with_a_rook_loses_the_exchange(self):
        # Rook takes pawn, pawn recaptures: +1 -5.
        assert value("4k3/8/8/1p6/p7/8/8/R3K3 w - - 0 1", "a1a4") == 1 - 5

    def test_an_even_trade_is_zero(self):
        assert value("4k3/8/8/8/r7/8/8/R2RK3 w - - 0 1", "d1a1") == 0

    def test_a_quiet_move_that_cannot_be_punished_is_zero(self):
        assert value("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1a4") == 0

    def test_a_quiet_move_onto_an_attacked_square_loses_the_piece(self):
        assert value("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1", "a1a4") == -5

    def test_it_uses_the_cheapest_attacker_first(self):
        # A queen also bears on a4, but the pawn must be used, so the rook is
        # lost outright rather than traded for the queen.
        assert value("3qk3/8/8/1p6/8/8/8/R3K3 w - - 0 1", "a1a4") == -5

    def test_en_passant_is_valued_as_a_pawn(self):
        assert value("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2", "e5d6") == 1

    def test_the_board_is_left_untouched(self):
        board = chess.Board("4k3/8/8/8/p7/8/8/R3K3 w - - 0 1")
        before = board.fen()

        exchange_value(board, chess.Move.from_uci("a1a4"))

        assert board.fen() == before

    def test_a_pinned_defender_cannot_recapture(self):
        # The a6 knight defends b4 but is pinned to its king on a8 by the a1
        # rook, so Nxb4 is illegal and the pawn is simply free. A swap list built
        # from raw attackers counts that knight and calls this an even trade —
        # which is why this uses legal_moves and pays for it in speed.
        board = chess.Board("k7/8/n7/8/1p6/8/8/RR2K3 w - - 0 1")

        assert board.is_pinned(chess.BLACK, chess.A6) is True
        assert exchange_value(board, chess.Move.from_uci("b1b4")) == 1


class TestMovedIntoAttack:
    def test_stepping_onto_a_square_a_pawn_covers(self):
        board = chess.Board("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1")

        assert moved_into_attack(board, chess.Move.from_uci("a1a4")) is True

    def test_a_safe_square_is_not_flagged(self):
        board = chess.Board("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1")

        assert moved_into_attack(board, chess.Move.from_uci("a1a3")) is False

    def test_an_adequately_defended_piece_is_not_moved_into_attack(self):
        # Rook to a4 is attacked by the a8 rook and defended by the d4 rook, so
        # the swap is even and there is nothing to win. "Attacked" is not the
        # test; "winnable" is.
        board = chess.Board("r3k3/8/8/8/3R4/8/8/R3K3 w - - 0 1")

        assert moved_into_attack(board, chess.Move.from_uci("a1a4")) is False

    def test_a_losing_capture_is_not_double_counted(self):
        # This is miscounted_exchange's case. Firing both would name one mistake
        # twice and prescribe two different habits for it.
        board = chess.Board("4k3/8/8/1p6/p7/8/8/R3K3 w - - 0 1")
        move = chess.Move.from_uci("a1a4")

        assert miscounted_exchange(board, move) is True
        assert moved_into_attack(board, move) is False


class TestMiscountedExchange:
    def test_a_capture_that_loses_material(self):
        board = chess.Board("4k3/8/8/1p6/p7/8/8/R3K3 w - - 0 1")

        assert miscounted_exchange(board, chess.Move.from_uci("a1a4")) is True

    def test_an_even_trade_is_not_a_miscount(self):
        board = chess.Board("4k3/8/8/8/r7/8/8/R2RK3 w - - 0 1")

        assert miscounted_exchange(board, chess.Move.from_uci("d1a1")) is False

    def test_a_free_capture_is_not_a_miscount(self):
        board = chess.Board("4k3/8/8/8/p7/8/8/R3K3 w - - 0 1")

        assert miscounted_exchange(board, chess.Move.from_uci("a1a4")) is False

    def test_a_quiet_move_is_never_a_miscount(self):
        board = chess.Board("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1")

        assert miscounted_exchange(board, chess.Move.from_uci("a1a4")) is False


class TestLeftHanging:
    def test_it_counts_other_pieces_left_takeable(self):
        # The h1 rook is en prise to the h8 rook; shuffling the a1 rook leaves
        # it standing there.
        board = chess.Board("4k2r/8/8/8/8/8/8/R3K2R w - - 0 1")

        assert left_hanging(board, chess.Move.from_uci("a1a2")) >= 1

    def test_the_moved_piece_itself_is_not_counted(self):
        # That is moved_into_attack — a different habit with a different remedy.
        board = chess.Board("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1")

        assert left_hanging(board, chess.Move.from_uci("a1a4")) == 0

    def test_a_tidy_position_leaves_nothing(self):
        board = chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")

        assert left_hanging(board, chess.Move.from_uci("a1a4")) == 0


class TestIgnoredThreat:
    def test_leaving_attacked_material_where_it_stands(self):
        board = chess.Board("4k2r/8/8/8/8/8/8/R3K2R w - - 0 1")

        assert ignored_threat(board, chess.Move.from_uci("a1a2")) is True

    def test_moving_the_threatened_piece_addresses_it(self):
        board = chess.Board("4k2r/8/8/8/8/8/8/R3K2R w - - 0 1")

        assert ignored_threat(board, chess.Move.from_uci("h1h7")) is False

    def test_nothing_threatened_means_nothing_ignored(self):
        board = chess.Board("4k3/8/8/8/8/8/8/R3K3 w - - 0 1")

        assert ignored_threat(board, chess.Move.from_uci("a1a4")) is False

    def test_a_bigger_counter_capture_is_not_ignoring_it(self):
        # Winning a queen while a rook hangs is good play, and telling a player
        # off for it would be advice against playing well.
        board = chess.Board("q3k2r/8/8/8/8/8/8/R3K2R w - - 0 1")
        move = chess.Move.from_uci("a1a8")

        assert move in board.legal_moves
        assert ignored_threat(board, move) is False


class TestTheFourCausesStayDistinct:
    @pytest.mark.parametrize(
        "fen,uci",
        [
            ("4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1", "a1a4"),
            ("4k3/8/8/1p6/p7/8/8/R3K3 w - - 0 1", "a1a4"),
            ("4k2r/8/8/8/8/8/8/R3K2R w - - 0 1", "a1a2"),
        ],
    )
    def test_moved_into_attack_and_miscounted_never_both_fire(self, fen, uci):
        # They prescribe opposite habits — "look at the destination square"
        # against "count the exchange" — so a move triggering both would produce
        # contradictory advice about a single mistake.
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)

        assert not (moved_into_attack(board, move) and miscounted_exchange(board, move))
