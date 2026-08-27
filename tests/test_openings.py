"""Naming the opening, and finding where the player left it.

Design: docs/notes/design.informative-claims.md

The book is `lichess-org/chess-openings` (CC0). It is a **naming** database
rather than a theory-depth one: 3,810 named lines, median 5 plies, **maximum 16**.
That cap is a real limit on what can be claimed and is deliberately not hidden —
"you leave theory at move 6" is sayable, "at move 14" is not, because the source
does not know. It happens to cover the range the author identified as the one
that matters at this level.

Keyed by EPD, so transpositions resolve without any move-order matching.
"""

from __future__ import annotations

import chess

from chesscoach.openings import Opening, OpeningBook

ITALIAN = "1. e4 e5 2. Nf3 Nc6 3. Bc4"
KINGS_PAWN = "1. e4 e5"
E4 = "1. e4"


def a_book() -> OpeningBook:
    return OpeningBook.from_rows([
        ("B00", "King's Pawn", E4),
        ("C20", "King's Pawn Game", KINGS_PAWN),
        ("C50", "Italian Game", ITALIAN),
    ])


def board_after(pgn: str) -> chess.Board:
    board = chess.Board()
    for token in pgn.split():
        if not token.endswith("."):
            board.push_san(token)
    return board


class TestBuilding:
    def test_every_line_becomes_an_entry_keyed_by_position(self):
        book = a_book()

        assert len(book) == 3
        assert book.classify(board_after(ITALIAN)).name == "Italian Game"

    def test_a_line_that_cannot_be_replayed_is_skipped_not_fatal(self):
        # One malformed row must not cost the other 3,809.
        book = OpeningBook.from_rows([
            ("C50", "Italian Game", ITALIAN),
            ("XXX", "Nonsense", "1. e4 Qz9"),
        ])

        assert len(book) == 1

    def test_plies_are_recorded_so_depth_can_be_reported(self):
        assert a_book().classify(board_after(ITALIAN)).plies == 5


class TestClassify:
    def test_an_unknown_position_is_not_classified(self):
        board = board_after("1. a3 h6 2. a4 h5 3. Ra3")

        assert a_book().classify(board) is None

    def test_a_transposition_is_recognised(self):
        # 1.Nf3 e5 2.e4 Nc6 3.Bc4 reaches the Italian by another order.
        transposed = board_after("1. Nf3 e5 2. e4 Nc6 3. Bc4")

        assert a_book().classify(transposed).name == "Italian Game"


class TestWalkingAGame:
    def test_it_reports_the_deepest_line_reached_and_where_it_ended(self):
        # Two moves of book, then something not in this small book.
        moves = [m.uci() for m in board_after("1. e4 e5 2. Nf3 Nc6 3. Bc4 h6").move_stack]

        walk = a_book().walk(moves)

        assert walk.opening.name == "Italian Game"
        assert walk.plies_in_book == 5
        assert walk.left_at_ply == 6

    def test_a_game_that_stays_in_book_reports_no_exit(self):
        moves = [m.uci() for m in board_after(ITALIAN).move_stack]

        walk = a_book().walk(moves)

        assert walk.opening.name == "Italian Game"
        assert walk.left_at_ply is None

    def test_a_game_that_never_enters_book_says_so(self):
        moves = [m.uci() for m in board_after("1. a3 h6").move_stack]

        walk = a_book().walk(moves)

        assert walk.opening is None
        assert walk.left_at_ply == 1

    def test_who_left_the_book_is_recorded_because_it_may_be_the_opponent(self):
        # The exit ply is a property of the GAME. Attributing an opponent's
        # sideline to the player would be measuring the wrong person.
        moves = [m.uci() for m in board_after("1. e4 e5 2. Nf3 Nc6 3. Bc4 h6").move_stack]

        walk = a_book().walk(moves)

        assert walk.left_by_white is False  # ply 6 is Black's move
