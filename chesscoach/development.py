"""How one player got their pieces out, measured and not judged.

Design: docs/notes/design.opening-development-signals.md

The author's proposal, in their own words:

    "Every opening has an approximate number of moves until the player should
    castle the king, until most pieces should be developed... until the castling
    and until every piece is developed, multiple moves by the same piece are not
    recommended, as well as too many moves by the pawns."

**There is no threshold in this module, deliberately.** *"Castle by move 10"* is
a teaching heuristic rather than a fact; its right value differs by opening, and
writing one in would be the folklore laundering R-03 forbids. This reports what
a game contains and leaves every comparison to the peer reference, where the
number comes from players in the same band **playing the same opening**.

Two traps the design names, and both are handled here rather than downstream:

**The window is an event, not a constant.** It ends when the player has castled
*and* every minor has left home. S4's `OPENING_END_PLY = 30` admits in its own
comment that it is conventional; a window that ends when the opening is actually
over for this player scales with the opening by construction.

**Unfinished development is censored, not zero.** A game ending on move 12 says
nothing about how slowly the player develops, so `completed` is reported beside
every count and a caller that averages without reading it will measure game
length instead.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import chess

# The squares a side's minor pieces start on. Development is complete for a
# player once none of these still holds the piece that began there.
HOME_SQUARES: dict[chess.Color, tuple[int, ...]] = {
    chess.WHITE: (chess.B1, chess.C1, chess.F1, chess.G1),
    chess.BLACK: (chess.B8, chess.C8, chess.F8, chess.G8),
}


@dataclass(frozen=True)
class WindowMove:
    """One of the player's opening moves, labelled by the habit it belongs to.

    The labels carry the **"instead of"** condition the author's wording
    requires: *"the same piece was moved repeatedly **instead of developing the
    other piece**"*, *"every pawn move **when the piece should be developed
    instead**"*, *"every move when the player **should castle** the king but he
    did something else"*.

    Without that condition the labels degenerate into "this was a pawn move",
    and summing their cost would re-measure the player's general error rate
    wearing a habit's name.
    """

    ply: int
    # Moved a piece that had already moved, while a minor still sat at home.
    repeat_instead_of_developing: bool
    # A pawn move, while a minor still sat at home.
    pawn_instead_of_developing: bool
    # Castling was legal on this move and the player played something else.
    declined_available_castle: bool


@dataclass(frozen=True)
class Development:
    """One player's opening, as facts. No judgement, no thresholds."""

    # Ply (1-based, counting both sides) at which the player castled. `None` if
    # they never did -- which is a real answer, not a missing one.
    castled_at: int | None
    # Ply at which the last of the four minors left home.
    developed_at: int | None
    # Home squares still holding their original minor when the game ended, by
    # square name. Empty when development finished.
    still_at_home: frozenset[str]

    # Moves the player made inside the window, and what they were spent on.
    moves_in_window: int
    repeat_moves: int
    pawn_moves: int

    # False when the game ended before the player had castled and developed.
    # **Read this before averaging anything above.**
    completed: bool

    # Every move the player made inside the window, labelled. Joined against the
    # observations by ply to price each habit by what its own moves cost.
    window_moves: tuple[WindowMove, ...] = ()

    @property
    def ready_at(self) -> int | None:
        """The ply the opening was over for this player, or `None` if it wasn't.

        The later of castling and development: a player with every piece out and
        a king in the centre has not finished the opening.
        """
        if self.castled_at is None or self.developed_at is None:
            return None
        return max(self.castled_at, self.developed_at)

    def rate(self, count: int) -> float | None:
        """A count as a share of the window, or `None` when there is no window."""
        if self.moves_in_window == 0:
            return None
        return count / self.moves_in_window


def measure_development(
    moves: Sequence[chess.Move],
    mover: chess.Color,
    start: chess.Board | None = None,
) -> Development:
    """Walk a game and report how `mover` brought their pieces out.

    Counting stops at `ready_at`. Everything after it belongs to the middlegame
    and would dilute exactly the rates the claim is built on -- a player who
    develops briskly and then pushes pawns for thirty moves has not made an
    opening mistake.
    """
    board = chess.Board() if start is None else start.copy()

    # Squares currently holding a piece of ours that has moved before. Keyed by
    # square because that is what a move gives us, and remapped on every move --
    # including the opponent's, since a capture removes the piece a record is
    # about. Leaving a stale entry behind would make a RECAPTURING piece's first
    # move read as a repeat.
    has_moved: set[int] = set()

    home = {square for square in HOME_SQUARES[mover]}
    left_home: set[int] = set()

    castled_at: int | None = None
    developed_at: int | None = None
    moves_in_window = repeat_moves = pawn_moves = 0
    window_moves: list[WindowMove] = []

    for index, move in enumerate(moves):
        ply = index + 1
        ours = board.turn == mover

        if ours and _still_open(castled_at, developed_at):
            moves_in_window += 1
            repeat = move.from_square in has_moved
            if repeat:
                repeat_moves += 1
            piece = board.piece_at(move.from_square)
            is_pawn = piece is not None and piece.piece_type == chess.PAWN
            if is_pawn:
                pawn_moves += 1

            # The "instead of" conditions. A repeat move once every piece is out
            # is not this habit, and a pawn move with nothing left to develop is
            # an ordinary opening move.
            undeveloped = any(_minor_at_home(board, sq, mover) for sq in home)
            castling_available = (
                castled_at is None
                and any(board.is_castling(m) for m in board.legal_moves)
            )
            window_moves.append(
                WindowMove(
                    ply=ply,
                    repeat_instead_of_developing=repeat and undeveloped,
                    pawn_instead_of_developing=is_pawn and undeveloped,
                    declined_available_castle=(
                        castling_available and not board.is_castling(move)
                    ),
                )
            )

        if ours and board.is_castling(move):
            castled_at = ply

        _record_move(board, move, mover, has_moved)
        board.push(move)

        # Checked after the push so a piece captured on its home square counts
        # as no longer there: nothing is left to develop, and waiting for it
        # would mean development never completes in such a game.
        left_home |= {square for square in home if not _minor_at_home(board, square, mover)}
        if developed_at is None and left_home == home:
            developed_at = ply

        if castled_at is not None and developed_at is not None:
            break

    return Development(
        castled_at=castled_at,
        developed_at=developed_at,
        still_at_home=frozenset(chess.square_name(s) for s in sorted(home - left_home)),
        moves_in_window=moves_in_window,
        repeat_moves=repeat_moves,
        pawn_moves=pawn_moves,
        completed=castled_at is not None and developed_at is not None,
        window_moves=tuple(window_moves),
    )


def _still_open(castled_at: int | None, developed_at: int | None) -> bool:
    """Is the opening still running for this player?"""
    return castled_at is None or developed_at is None


def _minor_at_home(board: chess.Board, square: int, mover: chess.Color) -> bool:
    """Does this home square still hold one of our minor pieces?"""
    piece = board.piece_at(square)
    return (
        piece is not None
        and piece.color == mover
        and piece.piece_type in (chess.KNIGHT, chess.BISHOP)
    )


def _record_move(
    board: chess.Board, move: chess.Move, mover: chess.Color, has_moved: set[int]
) -> None:
    """Keep `has_moved` pointing at the right squares across this move.

    Three cases that a naive `has_moved.add(to_square)` gets wrong, and all
    three happen in ordinary games:

    - **a capture** must clear the captured piece's record, or the capturing
      piece inherits it and its next move reads as a repeat;
    - **castling** moves a rook the move's own squares do not mention;
    - **en passant** captures on a square the move never names.
    """
    # Whoever is moving, the destination is vacated of its previous occupant.
    has_moved.discard(move.to_square)
    if board.is_en_passant(move):
        captured = move.to_square + (-8 if board.turn == chess.WHITE else 8)
        has_moved.discard(captured)

    if board.turn != mover:
        return

    has_moved.discard(move.from_square)
    has_moved.add(move.to_square)

    if board.is_castling(move):
        # The rook's own move. Both king and rook have now moved, and neither
        # had before -- castling is legal only from untouched squares.
        rook_from, rook_to = _rook_squares(move)
        has_moved.discard(rook_from)
        has_moved.add(rook_to)


def _rook_squares(move: chess.Move) -> tuple[int, int]:
    """Where the rook comes from and goes to in a castling move."""
    kingside = chess.square_file(move.to_square) > chess.square_file(move.from_square)
    rank = chess.square_rank(move.from_square)
    if kingside:
        return chess.square(7, rank), chess.square(5, rank)
    return chess.square(0, rank), chess.square(3, rank)
