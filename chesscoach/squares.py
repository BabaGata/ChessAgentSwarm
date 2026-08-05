"""Squares and files: what the opponent gets to keep.

Design: docs/notes/capacity.agents.s6-squares-and-files.md
Screen: docs/notes/experiments.e09-square-candidates.md

Two detectors, both read from the **conceding** side. E02 verified outposts as an
asset for the side that owns one; this is the same geometry seen by the player
who has to live with it.

Only two, because E09 screened five candidates against 38 real players and three
of them -- holes in the player's own camp, a bad bishop, a rook missing from an
open file -- turned out not to distinguish players at all (spreads 1.25-1.31,
against 2.15 and 1.82 for these). The failures were all about *what the player's
position looks like*; the survivors are about *what the opponent achieves*
(L-024).
"""

from __future__ import annotations

import chess

OUTPOST = "outpost"
ROOK_SEVENTH = "rook_seventh"

FEATURES = (OUTPOST, ROOK_SEVENTH)

# A knight is only worth calling an outpost where it restricts: the middle ranks
# of the conceding player's half. Rank indices, from that player's point of view.
WHITE_HALF_RANKS = (2, 3, 4)
BLACK_HALF_RANKS = (5, 4, 3)


def _pawns(board: chess.Board, colour: chess.Color) -> list[int]:
    return list(board.pieces(chess.PAWN, colour))


def _defended_by_pawn(board: chess.Board, square: int, colour: chess.Color) -> bool:
    file_, rank = chess.square_file(square), chess.square_rank(square)
    behind = rank - 1 if colour == chess.WHITE else rank + 1
    if not 0 <= behind <= 7:
        return False
    for adjacent in (file_ - 1, file_ + 1):
        if 0 <= adjacent <= 7:
            piece = board.piece_at(chess.square(adjacent, behind))
            if piece and piece.piece_type == chess.PAWN and piece.color == colour:
                return True
    return False


def can_ever_be_covered(board: chess.Board, square: int, colour: chess.Color) -> bool:
    """Could any pawn of `colour` still advance to defend `square`?

    A pawn defends from an adjacent file one rank behind its own direction of
    travel, so it must currently be at or behind that rank. This is the condition
    that separates a permanent outpost from a temporarily annoying knight, and it
    is the one casual definitions omit (E02, L-004).
    """
    file_, rank = chess.square_file(square), chess.square_rank(square)
    for pawn in _pawns(board, colour):
        if abs(chess.square_file(pawn) - file_) != 1:
            continue
        pawn_rank = chess.square_rank(pawn)
        if colour == chess.WHITE and pawn_rank < rank:
            return True
        if colour == chess.BLACK and pawn_rank > rank:
            return True
    return False


def count_enemy_outposts(board: chess.Board, colour: chess.Color) -> int:
    """Enemy knights settled in `colour`'s half where they cannot be evicted."""
    enemy = not colour
    ranks = WHITE_HALF_RANKS if colour == chess.WHITE else BLACK_HALF_RANKS
    return sum(
        1
        for square in board.pieces(chess.KNIGHT, enemy)
        if chess.square_rank(square) in ranks
        and _defended_by_pawn(board, square, enemy)
        and not can_ever_be_covered(board, square, colour)
    )


def count_enemy_rooks_on_seventh(board: chess.Board, colour: chess.Color) -> int:
    """Enemy rooks on the rank where `colour`'s pawns started."""
    rank = 1 if colour == chess.WHITE else 6
    return sum(
        1
        for square in board.pieces(chess.ROOK, not colour)
        if chess.square_rank(square) == rank
    )


COUNTERS = {OUTPOST: count_enemy_outposts, ROOK_SEVENTH: count_enemy_rooks_on_seventh}


def counts(board: chess.Board, colour: chess.Color) -> dict[str, int]:
    return {name: counter(board, colour) for name, counter in COUNTERS.items()}


def allowed(before: chess.Board, after: chess.Board, colour: chess.Color) -> frozenset[str]:
    """What the opponent established between these two positions.

    `after` is the position **following the opponent's reply**, not following the
    player's own move. A knight settles and a rook arrives on the opponent's
    turn; comparing across the player's move alone finds almost nothing, which is
    what E09's first pass did and why it reported two rates of zero.
    """
    was, now = counts(before, colour), counts(after, colour)
    return frozenset(name for name in FEATURES if now[name] > was[name])
