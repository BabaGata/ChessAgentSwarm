"""What a game says about how one player developed.

Design: docs/notes/design.opening-development-signals.md

The module reports facts and judges nothing. There is no threshold in it,
because a threshold is the part that has to come from the player's peers in the
same opening -- "castle by move 10" is a teaching heuristic, not a fact, and
hard-coding it would be the folklore laundering R-03 forbids.
"""

from __future__ import annotations

import chess

from chesscoach.development import measure_development


def moves(*sans: str, start: str | None = None) -> list[chess.Move]:
    """SAN into moves, so the fixtures read like games."""
    board = chess.Board() if start is None else chess.Board(start)
    played = []
    for san in sans:
        move = board.parse_san(san)
        played.append(move)
        board.push(move)
    return played


ITALIAN = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6", "d3", "d6",
           "Bg5", "Bg4", "Nbd2", "Nd4")


class TestCastling:
    def test_it_finds_the_ply_the_player_castled(self):
        # White castles on their 4th move, which is ply 7 counting from 1.
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.castled_at == 7

    def test_a_player_who_never_castles_has_no_castling_ply(self):
        black = measure_development(moves(*ITALIAN), chess.BLACK)
        assert black.castled_at is None

    def test_walking_the_king_by_hand_is_not_castling(self):
        # Ke2 is not castling however much it resembles getting the king out of
        # the centre, and counting it would flatter exactly the players this
        # claim exists to find.
        game = measure_development(moves("e4", "e5", "Ke2", "Nc6"), chess.WHITE)
        assert game.castled_at is None


class TestDevelopment:
    def test_all_four_minors_must_have_moved(self):
        # White's minors leave on plies 3 (Nf3), 5 (Bc4), 11 (Bg5), 13 (Nbd2).
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.developed_at == 13

    def test_development_is_incomplete_while_a_minor_sits_at_home(self):
        white = measure_development(moves("e4", "e5", "Nf3", "Nc6"), chess.WHITE)
        assert white.developed_at is None

    def test_a_minor_captured_at_home_no_longer_blocks_development(self):
        # Nothing is left to develop on that square, so waiting for it would
        # mean development never completes in any game where a piece is traded
        # on its home square.
        # Black's bishop reaches c1 down the empty h6-c1 diagonal and takes
        # White's dark bishop where it started.
        played = moves("d4", "g6", "Nf3", "Bh6", "c3", "Bxc1")
        white = measure_development(played, chess.WHITE)
        assert "c1" not in white.still_at_home

    def test_ready_is_the_later_of_castling_and_development(self):
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.ready_at == 13
        assert white.completed


class TestRepeatMoves:
    def test_moving_a_piece_that_has_already_moved_is_a_repeat(self):
        # Nf3 then Ng5: the second is a repeat, the first is not.
        played = moves("e4", "e5", "Nf3", "Nc6", "Ng5", "d5")
        white = measure_development(played, chess.WHITE)
        assert white.repeat_moves == 1

    def test_a_piece_returning_home_has_still_moved(self):
        # Nf3, Ng1 -- both count as moves of an already-developed piece from the
        # second onward. A knight that goes home has not become undeveloped.
        played = moves("e4", "e5", "Nf3", "Nc6", "Ng1", "d5")
        white = measure_development(played, chess.WHITE)
        assert white.repeat_moves == 1

    def test_castling_does_not_count_as_moving_the_rook_again(self):
        # Every white move in this line is a different piece's first move, so
        # the honest answer is zero -- and it is only zero if castling did not
        # leave a phantom record on the rook's new square.
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.repeat_moves == 0
        assert white.castled_at == 7

    def test_a_piece_recaptured_on_its_square_does_not_make_the_next_move_a_repeat(self):
        # White's bishop is traded on f2 and Black's king recaptures there. The
        # king has now moved, but the entry that has to be cleared is the
        # BISHOP's -- if a capture left the mover's record in place, the
        # recapturing piece would inherit it.
        played = moves("e4", "e5", "Nf3", "Bc5", "Nc3", "Bxf2+", "Kxf2", "Nc6", "Kg1")
        white = measure_development(played, chess.WHITE)
        # Kxf2 is the king's first move; Kg1 is its second and the only repeat.
        assert white.repeat_moves == 1


class TestPawnMoves:
    def test_it_counts_only_the_players_own_pawn_moves(self):
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.pawn_moves == 2  # e4 and d3
        black = measure_development(moves(*ITALIAN), chess.BLACK)
        assert black.pawn_moves == 2  # e5 and d6


class TestTheWindow:
    def test_counting_stops_once_development_is_complete(self):
        # Three further pawn moves after White is ready must not be counted:
        # the claim is about the opening, and the window ends when the opening
        # is over for this player.
        played = moves(*ITALIAN, "a3", "a6", "b4", "b5", "c3")
        white = measure_development(played, chess.WHITE)
        assert white.ready_at == 13
        assert white.pawn_moves == 2
        assert white.moves_in_window == 7

    def test_an_unfinished_game_reports_what_it_saw_and_says_so(self):
        # Right-censored: development had not finished and could not have. The
        # measurement must not pretend otherwise -- a rate built over this game
        # as though it were complete would report short games as slow
        # development.
        white = measure_development(moves("e4", "e5", "Nf3", "Nc6"), chess.WHITE)
        assert not white.completed
        assert white.ready_at is None
        assert white.moves_in_window == 2
