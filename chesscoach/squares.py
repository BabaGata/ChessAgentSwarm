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


# Above this many open files, keeping a rook off the seventh is not a thing a
# player can be asked to do. The author, marking the old detector wrong:
#
# > *"Rooks can pretty much always come to the seventh rank if it is a late
# > endgame, not many pieces and pawns to block them. So basically whenever
# > there are 3 or more open files there is not much possibility to block the
# > opponent... This should be counted only if there was a real opportunity to
# > block the rook from coming to the seventh file a move before or 2 moves
# > before."*
#
# Their number, not one chosen here. The precise version of the rule is a
# two-ply search for a move that would have stopped the arrival; this is the
# cheap screen that runs first, so the search is only paid for if it still has
# something left to buy.
OPEN_FILES_UNPREVENTABLE = 3


def open_files(board: chess.Board) -> int:
    """Files with no pawn of either colour on them."""
    occupied = {
        chess.square_file(square)
        for square in board.pieces(chess.PAWN, chess.WHITE)
        | board.pieces(chess.PAWN, chess.BLACK)
    }
    return 8 - len(occupied)


def _rooks_on_seventh(board: chess.Board, colour: chess.Color) -> int:
    """The raw count, with no judgement about whether it could have been stopped."""
    rank = 1 if colour == chess.WHITE else 6
    return sum(
        1
        for square in board.pieces(chess.ROOK, not colour)
        if chess.square_rank(square) == rank
    )


def count_enemy_rooks_on_seventh(board: chess.Board, colour: chess.Color) -> int:
    """Enemy rooks on the seventh, **when arriving there was preventable**.

    A rook standing on the seventh is a state of the board. Whether the player
    could have stopped it is the question that makes it a finding rather than a
    description -- the fault the six corrections share
    ([[design.detectors-name-consequences]]).

    So an open board does not fire at all. With three or more open files the
    rook was going to get there whatever the player did, and telling them to
    prevent it is telling them to do something impossible.
    """
    if open_files(board) >= OPEN_FILES_UNPREVENTABLE:
        return 0
    return _rooks_on_seventh(board, colour)


def rook_seventh_preventable(before: chess.Board, colour: chess.Color) -> bool:
    """Could the player, moving now, stop a rook reaching their seventh?

    The precise half of the author's correction:

        "This should be counted only if there was a real opportunity to block
        the rook from coming to the seventh file a move before or 2 moves
        before."

    The cheap proxy -- three or more open files -- removes 52 % of firings
    ([[experiments.e66-rook-seventh-and-doubled]]), and the design note said the
    search would be unnecessary only if the proxy removed *most*. Half is not
    most, so this asks the question directly: over the player's own legal moves,
    is there one after which **no** enemy reply lands a rook on the seventh?

    Two plies, which is what the design note scoped. The author also mentioned
    *"2 moves before"*; that is a four-ply search and is not attempted here,
    because the cost of a search grows with its depth and this one already runs
    on every arrival in every game.

    **A move that prevents by any means counts** -- interposing, capturing the
    rook, or giving a check that leaves the opponent no time. It is not required
    to be a *good* move, and that is a real limitation rather than an oversight:
    deciding whether the defence was worth playing needs an engine, and this is
    deterministic computation running inside the section (C1). A player who
    could only have stopped the rook by hanging a queen is told they could have
    stopped it.

    **No legal moves is not prevention.** A player with nothing to play could not
    have prevented anything, and reading the empty case as success is the vacuous
    truth that made every checkmate a fork (L-046).
    """
    had = _rooks_on_seventh(before, colour)
    for move in before.legal_moves:
        answered = before.copy(stack=False)
        answered.push(move)
        replies = list(answered.legal_moves)
        if not replies:
            # The opponent has no move at all, so no rook arrives. Checkmate or
            # stalemate is prevention of a sort, and rare enough not to matter.
            return True
        if not any(_lands_on_seventh(answered, reply, colour, had) for reply in replies):
            return True
    return False


def _lands_on_seventh(
    board: chess.Board, reply: chess.Move, colour: chess.Color, had: int
) -> bool:
    """Does this enemy reply put one more rook on the player's seventh?"""
    after = board.copy(stack=False)
    after.push(reply)
    return _rooks_on_seventh(after, colour) > had


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
    established = {name for name in FEATURES if now[name] > was[name]}

    # The cheap screen has already run inside `counts`; this is the precise
    # question it cannot ask. A rook that arrived because nothing could be done
    # about it is a fact about the position, not something the player allowed.
    if ROOK_SEVENTH in established and not rook_seventh_preventable(before, colour):
        established.discard(ROOK_SEVENTH)
    return frozenset(established)
