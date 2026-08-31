"""A rook on the seventh only counts when it could have been kept out.

Design: docs/notes/design.detectors-name-consequences.md § 4

    "Rooks can pretty much always come to the seventh rank if it is a late
    endgame, not many pieces and pawns to block them. So basically whenever
    there are 3 or more open files there is not much possibility to block the
    opponent... This should be counted only if there was a real opportunity to
    block the rook from coming to the seventh file a move before or 2 moves
    before."

A rook standing on the seventh is a STATE. Whether the player could have
stopped it is what makes it a finding.
"""

from __future__ import annotations

import chess

from chesscoach.squares import (
    OPEN_FILES_UNPREVENTABLE,
    count_enemy_rooks_on_seventh,
    open_files,
)


class TestCountingOpenFiles:
    def test_the_start_position_has_none(self):
        assert open_files(chess.Board()) == 0

    def test_a_file_with_only_one_side_s_pawn_is_not_open(self):
        # A single pawn still blocks, and the author's threshold is about
        # whether a rook can be stopped -- one pawn can stop it.
        board = chess.Board("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        assert open_files(board) == 7

    def test_a_bare_endgame_is_wide_open(self):
        assert open_files(chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")) == 8


class TestItRefusesWhatCouldNotBePrevented:
    def test_a_late_endgame_does_not_fire(self):
        # Black rook on the seventh, and seven open files. The author's case:
        # it was going to get there whatever White did.
        board = chess.Board("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1")
        assert open_files(board) >= OPEN_FILES_UNPREVENTABLE
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 0

    def test_a_closed_position_still_fires(self):
        # Every file has a pawn, so nothing is open and the rook's arrival was
        # something White could have contested.
        board = chess.Board(
            "4k3/pppppppp/8/8/8/8/PPPPPPPr/4K3 w - - 0 1"
        )
        assert open_files(board) == 0
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 1

    def test_two_open_files_is_still_preventable(self):
        # The threshold is the author's three, so two must still fire.
        board = chess.Board("4k3/pppppp2/8/8/8/8/PPPPPP1r/4K3 w - - 0 1")
        assert open_files(board) == 2
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 1

    def test_three_open_files_is_not(self):
        board = chess.Board("4k3/ppppp3/8/8/8/8/PPPPP2r/4K3 w - - 0 1")
        assert open_files(board) == 3
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 0


class TestItStillSeesTheRook:
    def test_black_s_seventh_is_white_s_second(self):
        # The rank is the one where the player's own pawns started, and getting
        # this backwards would report the claim for the wrong player.
        board = chess.Board("4k3/pppppp1R/8/8/8/8/PPPPPP2/4K3 w - - 0 1")
        assert count_enemy_rooks_on_seventh(board, chess.BLACK) == 1
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 0

    def test_two_rooks_count_twice(self):
        board = chess.Board("4k3/pppppp2/8/8/8/8/PPPPPPrr/4K3 w - - 0 1")
        assert count_enemy_rooks_on_seventh(board, chess.WHITE) == 2
