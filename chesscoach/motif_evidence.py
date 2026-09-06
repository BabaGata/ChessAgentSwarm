"""Which pieces make a motif true, so a reader can check the name against the board.

The author, on marking the sheet:

> *"If the position detects multiple motifs at the same time it is ok, they are
> valuable input for the general overview. I might not seen the other motif
> because I saw the first one, but now since the detectors should mark the pieces
> involved with the motif I should be able to see if the detector really detected
> the wrong motif instead of the correct one."*

**Two motifs on one move is not a defect** -- it is the position being richer than
one word. What the sheet could not do is show *why* each name was given, so a
reader judging "is this a pin?" had only the move to go on, and for an
`allowed_motif` claim not even that: the move on the line is the player's own
losing move, and the motif belongs to the opponent's reply.

Every function here re-derives its squares from the **same helpers the detector
used**, so the two cannot drift: `tests/test_motif_evidence.py` asserts that
evidence is non-empty exactly when the detector fires, over the reviewed corpus.
"""

from __future__ import annotations

import chess

from chesscoach.material import PIECE_VALUE, wins_material
from chesscoach.tactics import (
    PIN_TARGET_MIN_VALUE,
    SKEWER_TARGET_MIN_VALUE,
    TRAPPABLE_MIN_VALUE,
    Motif,
    _friendly_sliders,
    _is_winnable,
    _lined_up_pairs,
    _lost_on_arrival,
    _newly_attacked,
    _wins_once_vacated,
    detect_motifs,
)

# A square to be read from the board **before** the move rather than after it,
# which is how a captured piece is named: it is not there afterwards.
_BEFORE = 1000

Role = tuple[str, int]


def _named(board: chess.Board, square: int) -> str:
    piece = board.piece_at(square)
    return f"{piece.symbol()}{chess.square_name(square)}" if piece else chess.square_name(square)


def describe(board: chess.Board, move: chess.Move, motif: str) -> str:
    """One line naming the pieces that make `motif` true of `move`.

    Empty when the motif does not hold, so a caller can tell "no evidence" from
    "not this motif" without a second call.
    """
    roles = evidence(board, move, motif)
    if not roles:
        return ""
    after = board.copy(stack=False)
    after.push(move)
    return ", ".join(
        f"{role} {_named(board if square >= _BEFORE else after, square % _BEFORE)}"
        for role, square in roles
    )


def evidence(board: chess.Board, move: chess.Move, motif: str) -> tuple[Role, ...]:
    """The squares that make `motif` true, each with the part it plays.

    **The detector decides, and this only locates.** The first version of this
    module re-stated each detector's conditions in order to find the squares, and
    restated them incompletely -- it missed `_lands_safely` for a fork, the
    surviving-pinner guard for a pin, the value floor for a hanging piece, and
    more, disagreeing on 303 of 5,935 moves in one game for `hangingPawn` alone.

    Asking `detect_motifs` first makes the two agree by construction rather than
    by my copying conditions correctly. What is left to test is the weaker and
    more useful property: that a finder never comes back empty for a motif that
    did fire.
    """
    if move not in board.legal_moves:
        return ()
    if motif not in {str(found) for found in detect_motifs(board, move)}:
        return ()
    after = board.copy(stack=False)
    after.push(move)
    mover = board.turn
    finder = _FINDERS.get(motif)
    return finder(board, after, move, mover) if finder else ()


def _fork(board, after, move, mover) -> tuple[Role, ...]:
    targets = _newly_attacked(board, after, move, mover)
    if len(targets) < 2:
        return ()
    return (("forker", move.to_square),) + tuple(("target", s) for s in targets)


def _pin(board, after, move, mover) -> tuple[Role, ...]:
    for front_square, front, behind_square, behind in _lined_up_pairs(
        after, move.to_square, mover
    ):
        if PIECE_VALUE[behind.piece_type] <= PIECE_VALUE[front.piece_type]:
            continue
        if PIECE_VALUE[behind.piece_type] < PIN_TARGET_MIN_VALUE:
            continue
        if front.piece_type == chess.PAWN:
            continue
        if behind.piece_type == chess.KING:
            if after.is_pinned(not mover, front_square):
                return (("pinner", move.to_square), ("pinned", front_square),
                        ("against", behind_square))
            continue
        if _wins_once_vacated(after, front_square, behind_square, mover):
            return (("pinner", move.to_square), ("pinned", front_square),
                    ("against", behind_square))
    return ()


def _skewer(board, after, move, mover) -> tuple[Role, ...]:
    for front_square, front, behind_square, behind in _lined_up_pairs(
        after, move.to_square, mover
    ):
        if (PIECE_VALUE[front.piece_type] > PIECE_VALUE[behind.piece_type]
                and PIECE_VALUE[behind.piece_type] >= SKEWER_TARGET_MIN_VALUE
                and _wins_once_vacated(after, front_square, behind_square, mover)):
            return (("skewerer", move.to_square), ("front", front_square),
                    ("behind", behind_square))
    return ()


def _discovered(board, after, move, mover) -> tuple[Role, ...]:
    for slider in _friendly_sliders(after, mover, exclude=move.to_square):
        for square in after.attacks(slider) - board.attacks(slider):
            piece = after.piece_at(square)
            if piece is None or piece.color == mover:
                continue
            if PIECE_VALUE[piece.piece_type] < 3:
                continue
            if piece.piece_type == chess.KING or wins_material(after, square, mover) > 0:
                return (("revealed", slider), ("target", square), ("moved", move.to_square))
    return ()


def _hanging(board, after, move, mover) -> tuple[Role, ...]:
    """The piece that was taken is on the *before* board, not the after one."""
    if not board.is_capture(move):
        return ()
    if board.is_en_passant(move):
        taken = chess.square(chess.square_file(move.to_square),
                             chess.square_rank(move.from_square))
    else:
        taken = move.to_square
    return (("takes", _BEFORE + taken), ("with", move.to_square))


def _back_rank(board, after, move, mover) -> tuple[Role, ...]:
    if not after.is_checkmate():
        return ()
    king = after.king(not mover)
    if king is None:
        return ()
    return (("mates with", move.to_square), ("king", king))


def _removing_the_defender(board, after, move, mover) -> tuple[Role, ...]:
    if not board.is_capture(move):
        return ()
    guarded = tuple(
        square
        for square in board.attacks(move.to_square)
        if (piece := board.piece_at(square)) is not None
        and piece.color != mover
        and piece.piece_type not in (chess.PAWN, chess.KING)
    )
    if not guarded:
        return ()

    # Report the piece that actually falls, not every piece the defender
    # touched: the detector concluded on one of them, and a reader checking the
    # name needs to see which.
    answers = [reply for reply in after.legal_moves if reply.to_square == move.to_square]
    for reply in answers or [None]:
        settled = after
        if reply is not None:
            settled = after.copy(stack=False)
            settled.push(reply)
        for square in guarded:
            if settled.piece_at(square) is None:
                continue
            if wins_material(settled, square, mover) > 0:
                roles = [("takes defender on", _BEFORE + move.to_square)]
                if reply is not None:
                    roles.append(("they recapture", reply.from_square))
                roles.append(("then falls", square))
                return tuple(roles)
    return ()


def _trapped(board, after, move, mover) -> tuple[Role, ...]:
    if after.is_check():
        return ()
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
        if escapes and all(_lost_on_arrival(after, e, mover) for e in escapes):
            return (("traps", square), ("with", move.to_square))
    return ()


_FINDERS = {
    str(Motif.FORK): _fork,
    str(Motif.PIN): _pin,
    str(Motif.SKEWER): _skewer,
    str(Motif.DISCOVERED_ATTACK): _discovered,
    str(Motif.HANGING_PIECE): _hanging,
    str(Motif.HANGING_PAWN): _hanging,
    str(Motif.BACK_RANK_MATE): _back_rank,
    str(Motif.REMOVING_THE_DEFENDER): _removing_the_defender,
    str(Motif.TRAPPED_PIECE): _trapped,
}
