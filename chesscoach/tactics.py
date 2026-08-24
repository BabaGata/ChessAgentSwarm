"""Tactical motif detection: what a move actually does.

Design: docs/notes/capacity.agents.s1-tactical-gaps.md

Given a position and a move, name the tactical patterns the move executes. Pure
board logic -- no engine, no model, no dataset. Motif names are the **Lichess
theme keys**, which is what will let the detectors be validated against the CC0
puzzle database and, later, let a diagnosis select training material by the same
name that described the weakness.

Every detector is deliberately conservative. For a coach a false positive is
worse than a miss, because it sends the player to study something that was never
wrong, and the recorded failure mode of this kind of code is over-firing: prior
art documented a skewer detector firing 10-18x too often before it was
constrained. Where a definition could reasonably be read strictly or loosely,
the strict reading wins.

Prior art (AGPL-3.0) is evidence that the approach works. Nothing here is copied
from it; each detector is written from the definition.
"""

from __future__ import annotations

from enum import StrEnum

import chess

from chesscoach.material import wins_material

# Values used only for "is this worth winning" comparisons, not for evaluation.
# The king is given a sentinel so it always outranks material.
PIECE_VALUE: dict[int, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 100,
}

# A trapped minor piece is a real tactical theme; a trapped pawn is not.
TRAPPABLE_MIN_VALUE = 3

# "You hang pieces" is not a claim about pawns. Measured on real games, free
# pawn grabs were the bulk of this motif's firings.
HANGING_MIN_VALUE = 3

# What must stand behind for a pin or a skewer to be worth the name. Pinning
# against a rook, queen or king is a pin; two minor pieces in a line is geometry.
PIN_TARGET_MIN_VALUE = 5
SKEWER_TARGET_MIN_VALUE = 3

SLIDERS = (chess.BISHOP, chess.ROOK, chess.QUEEN)


class Motif(StrEnum):
    """Motif names, matching the Lichess puzzle-theme vocabulary."""

    FORK = "fork"
    PIN = "pin"
    SKEWER = "skewer"
    DISCOVERED_ATTACK = "discoveredAttack"
    HANGING_PIECE = "hangingPiece"
    # A sibling of the above rather than a widening of it. E31 found 45 of 45
    # reviewer notes mentioning a pawn had no name available; E30 found that
    # folding pawns INTO `hangingPiece` halves that claim's deviation, because
    # everybody drops free pawns. Separate, both stay true and each is compared
    # against its own population rate.
    HANGING_PAWN = "hangingPawn"
    BACK_RANK_MATE = "backRankMate"
    REMOVING_THE_DEFENDER = "capturingDefender"
    TRAPPED_PIECE = "trappedPiece"


def detect_motifs(board: chess.Board, move: chess.Move) -> frozenset[str]:
    """Every motif this move executes. The board is not modified."""
    if move not in board.legal_moves:
        raise ValueError(f"{move.uci()} is not legal in this position")

    after = board.copy(stack=False)
    after.push(move)
    mover = board.turn

    found = {
        motif
        for motif, detector in _DETECTORS.items()
        if detector(board, after, move, mover)
    }
    return frozenset(found)


# --- individual detectors ---------------------------------------------------


def _is_fork(board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color) -> bool:
    """The moved piece attacks two or more things worth winning, and survives.

    "Worth winning" excludes defended pieces no more valuable than the attacker:
    a rook attacking two protected pawns has not forked anything.
    """
    if not _lands_safely(after, move.to_square, mover):
        return False

    attacker = after.piece_at(move.to_square)
    if attacker is None:
        return False

    targets = [
        square
        for square in after.attacks(move.to_square)
        if _is_worth_winning(after, square, attacker, mover)
    ]
    return len(targets) >= 2


def _is_pin(board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color) -> bool:
    """A slider attacks an enemy piece shielding a more valuable one behind it.

    The piece behind must be worth being pinned *against* -- a rook, queen or
    king. Two minor pieces in a line is geometry, not a pin worth naming.
    """
    return any(
        PIECE_VALUE[behind.piece_type] > PIECE_VALUE[front.piece_type]
        and PIECE_VALUE[behind.piece_type] >= PIN_TARGET_MIN_VALUE
        for front, behind in _lined_up_pairs(after, move.to_square, mover)
    )


def _is_skewer(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """The same geometry as a pin, with the valuable piece attacked first.

    The piece behind must be worth winning once the front one moves; a pawn
    behind a knight lines up without threatening anything.
    """
    return any(
        PIECE_VALUE[front.piece_type] > PIECE_VALUE[behind.piece_type]
        and PIECE_VALUE[behind.piece_type] >= SKEWER_TARGET_MIN_VALUE
        for front, behind in _lined_up_pairs(after, move.to_square, mover)
    )


def _is_discovered_attack(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """Vacating a square lets a friendly slider attack something it could not before."""
    for slider in _friendly_sliders(after, mover, exclude=move.to_square):
        revealed = after.attacks(slider) - board.attacks(slider)
        for square in revealed:
            piece = after.piece_at(square)
            if piece is not None and piece.color != mover and PIECE_VALUE[piece.piece_type] >= 3:
                return True
    return False


def _is_hanging_piece(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """A capture of an undefended **piece** that cannot be answered.

    Pawns are excluded. Measured on real games, free pawn grabs were the bulk of
    this motif's firings, and "you hang pieces" is not a claim about pawns —
    dropping pawns is a real weakness and a different one.
    """
    if not board.is_capture(move) or board.is_en_passant(move):
        return False

    captured = board.piece_at(move.to_square)
    if captured is None or PIECE_VALUE[captured.piece_type] < HANGING_MIN_VALUE:
        return False

    return not after.is_attacked_by(not mover, move.to_square)


def _is_hanging_pawn(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """A pawn won for nothing: taken, and the taker cannot be answered.

    The exact counterpart of `_is_hanging_piece` below the value line, and the
    reason it exists is empirical: across three reviewed players, **every one of
    45 notes mentioning a pawn was unnameable** ([[experiments.e31-move-level-agreement]]).
    The engine saw the error; the vocabulary had no word for it.

    En passant is included, unlike in the piece detector, because it wins a pawn
    for nothing exactly as any other free capture does — and the captured pawn is
    not on the destination square, so it has to be handled rather than inherited.
    """
    if not board.is_capture(move):
        return False

    if board.is_en_passant(move):
        return not after.is_attacked_by(not mover, move.to_square)

    captured = board.piece_at(move.to_square)
    if captured is None or PIECE_VALUE[captured.piece_type] >= HANGING_MIN_VALUE:
        return False

    return not after.is_attacked_by(not mover, move.to_square)


def _is_back_rank_mate(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """Checkmate delivered on the enemy king's home rank."""
    if not after.is_checkmate():
        return False

    defender = not mover
    king_square = after.king(defender)
    if king_square is None:
        return False

    home_rank = 7 if defender == chess.BLACK else 0
    return chess.square_rank(king_square) == home_rank


def _is_removing_the_defender(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """Capturing a piece so that something it defended is now loose and attacked."""
    if not board.is_capture(move) or board.is_en_passant(move):
        return False

    defended = [
        square
        for square in board.attacks(move.to_square)
        if (piece := board.piece_at(square)) is not None and piece.color != mover
    ]
    return any(
        after.is_attacked_by(mover, square) and not after.is_attacked_by(not mover, square)
        for square in defended
    )


def _is_trapped_piece(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """An attacked enemy piece whose every escape square we cover.

    Two constraints, both learned from firings on real games:

    * it must **have** escape squares. A piece with no legal moves is boxed in by
      its own side -- an undeveloped rook behind its own knight -- and calling
      that "trapped" fired on 8.7 % of all positions.
    * it must be **winnable**: undefended, or attacked by something cheaper.
      Otherwise we are only describing a piece that has nowhere useful to go.
    """
    for square, piece in after.piece_map().items():
        if piece.color == mover or piece.piece_type == chess.KING:
            continue
        if PIECE_VALUE[piece.piece_type] < TRAPPABLE_MIN_VALUE:
            continue
        if not after.is_attacked_by(mover, square):
            continue
        if not _is_winnable(after, square, piece, mover):
            continue

        escapes = [m for m in after.legal_moves if m.from_square == square]
        if escapes and all(after.is_attacked_by(mover, e.to_square) for e in escapes):
            return True
    return False


def _is_winnable(
    after: chess.Board, square: int, piece: chess.Piece, mover: chess.Color
) -> bool:
    """Can this enemy piece actually be won, once the exchange is counted?"""
    return wins_material(after, square, mover) > 0


# --- shared helpers ---------------------------------------------------------


def _lands_safely(after: chess.Board, square: int, mover: chess.Color) -> bool:
    """Can the piece be taken **profitably**? A fork that drops it is not a fork.

    This used to ask "attacked? then is it defended?", which has no notion of
    what the pieces are worth: a knight on a square attacked by a pawn and
    defended by a pawn passed as safe, and the detector called the resulting
    piece-drop a fork (D17). Defended and safe are different questions, and only
    an exchange answers the second.
    """
    return wins_material(after, square, not mover) <= 0


def _is_worth_winning(
    after: chess.Board, square: int, attacker: chess.Piece, mover: chess.Color
) -> bool:
    """Is this attacked square a target the fork actually threatens to win?"""
    target = after.piece_at(square)
    if target is None or target.color == mover:
        return False
    if target.piece_type == chess.KING:
        return True
    if PIECE_VALUE[target.piece_type] > PIECE_VALUE[attacker.piece_type]:
        return True
    # Not "is it undefended" but "would taking it actually win anything" -- the
    # difference between a target and a square the opponent is happy to trade on.
    return wins_material(after, square, mover) > 0


def _lined_up_pairs(
    after: chess.Board, square: int, mover: chess.Color
) -> list[tuple[chess.Piece, chess.Piece]]:
    """(front, behind) enemy pairs lined up behind one another from `square`.

    Only the piece that just moved is considered, and only if it is a slider:
    attributing a pin to a piece that was already there would report the same
    motif on every subsequent move.
    """
    piece = after.piece_at(square)
    if piece is None or piece.piece_type not in SLIDERS:
        return []

    pairs = []
    for direction in _directions(piece.piece_type):
        found: list[chess.Piece] = []
        current = square
        while True:
            current = _step(current, direction)
            if current is None:
                break
            occupant = after.piece_at(current)
            if occupant is None:
                continue
            if occupant.color == mover:
                break  # own piece blocks the line
            found.append(occupant)
            if len(found) == 2:
                pairs.append((found[0], found[1]))
                break
    return pairs


def _friendly_sliders(after: chess.Board, mover: chess.Color, exclude: int) -> list[int]:
    return [
        square
        for piece_type in SLIDERS
        for square in after.pieces(piece_type, mover)
        if square != exclude
    ]


def _directions(piece_type: int) -> tuple[tuple[int, int], ...]:
    diagonal = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    straight = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if piece_type == chess.BISHOP:
        return diagonal
    if piece_type == chess.ROOK:
        return straight
    return diagonal + straight


def _step(square: int, direction: tuple[int, int]) -> int | None:
    file_ = chess.square_file(square) + direction[0]
    rank = chess.square_rank(square) + direction[1]
    if 0 <= file_ <= 7 and 0 <= rank <= 7:
        return chess.square(file_, rank)
    return None


_DETECTORS = {
    Motif.FORK: _is_fork,
    Motif.PIN: _is_pin,
    Motif.SKEWER: _is_skewer,
    Motif.DISCOVERED_ATTACK: _is_discovered_attack,
    Motif.HANGING_PIECE: _is_hanging_piece,
    Motif.HANGING_PAWN: _is_hanging_pawn,
    Motif.BACK_RANK_MATE: _is_back_rank_mate,
    Motif.REMOVING_THE_DEFENDER: _is_removing_the_defender,
    Motif.TRAPPED_PIECE: _is_trapped_piece,
}
