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

from chesscoach.material import exchange_value, wins_material

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


def _is_fork(board: chess.Board, after: chess.Board, move: chess.Move,
             mover: chess.Color) -> bool:
    """Two pieces newly attacked by the piece that just moved, and material lost.

    The author's definition, after marking the old detector wrong:

    > *"Forks are moves that occur when at least 2 pieces were newly (so they
    > weren't attacked before) attacked by one single piece after moving that
    > piece and the result is definite loss of material."*

    Four conditions, and the old detector asked only the third:

    1. the targets are attacked by **the piece that moved** -- a discovered
       attack from a piece standing still is a different motif;
    2. at least two of them were **not attacked before**, so a piece wandering
       into a double attack that already existed is not a fork;
    3. the attacker survives, which `_lands_safely` answers on exchange values;
    4. **material is definitely lost** -- the defender has no reply that saves
       everything.

    Condition 4 is the one that changes the count, and the author gave the case
    that discriminates: a knight attacking a rook and an *undefended* bishop is
    a fork, because moving either loses the other. Attacking a rook and a
    *defended* bishop is **not**: the rook steps away and what follows is an
    exchange, not a loss.
    """
    if not _lands_safely(after, move.to_square, mover):
        return False
    if after.piece_at(move.to_square) is None:
        return False

    targets = _newly_attacked(board, after, move, mover)
    if len(targets) < 2:
        return False
    return _loses_material_whatever_the_defender_does(after, targets, mover)


def _newly_attacked(board: chess.Board, after: chess.Board, move: chess.Move,
                    mover: chess.Color) -> tuple[int, ...]:
    """Enemy pieces this move put under attack that were not under attack before.

    Worth winning is checked here too: a rook "attacking" a defended pawn has
    put nothing at risk, and counting it would make every developing move a
    fork.
    """
    # What the moving piece already hit from where it stood. `board` still has
    # it on its old square, so this is its attack set before the move.
    #
    # **"Newly" means newly by THIS piece**, which is the author's own reading:
    #
    # > *"the 2 newly attacked pieces can be attacked previously by some other
    # > piece, but they both have to be attacked by the piece that was moved...
    # > the piece that was last moved did not create a fork, it newly attacked
    # > just one piece."*
    #
    # The defect this rules out is a move that newly attacks **one** piece while
    # a second target was already attacked by something else -- the mover did not
    # fork anything. Asking `board.is_attacked_by(mover, square)` instead asks
    # whether *anything* friendly attacked the target, which also throws away
    # genuine forks: `Ng4-f6+` hitting a king and a rook stopped being a fork as
    # soon as a friendly rook shared the file (E86 D-1).
    already = board.attacks(move.from_square)

    found = []
    for square in after.attacks(move.to_square):
        piece = after.piece_at(square)
        if piece is None or piece.color == mover:
            continue
        if square in already:
            continue
        # The king counts as a target without being winnable -- it cannot be
        # captured, so `wins_material` says nothing about it. Excluding it would
        # blind the detector to the family fork, which is the commonest fork
        # there is: the check forces the king to move and the other piece falls.
        if piece.piece_type == chess.KING or wins_material(after, square, mover) > 0:
            found.append(square)
    return tuple(found)


def _loses_material_whatever_the_defender_does(
    after: chess.Board, targets: tuple[int, ...], mover: chess.Color
) -> bool:
    """Can the defender save every target? If so, this is not a fork.

    One ply of the defender's legal replies, which is what "definite" means here
    -- a fork wins because *no* answer saves both, not because the obvious
    answer does not.

    Replies that lose material are skipped rather than counted as saves. The
    commonest is capturing the forking piece: `_lands_safely` has already
    established that loses material, and treating it as a rescue would refuse
    every genuine fork.

    **A defender with no reply at all has not lost material -- the game ended.**
    Without this guard the loop is vacuously true and every checkmate is a fork,
    which is exactly what it counted: **104 of 1,779** corpus hits were mate or
    stalemate. Sixth instance of L-046 -- an empty case answering like a real one.
    """
    if not any(after.legal_moves):
        return False

    # A king is a target but never a prize: the loss has to land on something
    # capturable, so the check is made against the other targets only.
    winnable = tuple(
        square for square in targets
        if (piece := after.piece_at(square)) is not None
        and piece.piece_type != chess.KING
    )
    if not winnable:
        return False

    for reply in after.legal_moves:
        if exchange_value(after, reply) < 0:
            continue
        defended = after.copy(stack=False)
        defended.push(reply)
        if not any(wins_material(defended, square, mover) > 0 for square in winnable):
            return False
    return True


def _is_pin(board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color) -> bool:
    """A slider attacks an enemy piece shielding a more valuable one behind it.

    The piece behind must be worth being pinned *against* -- a rook, queen or
    king. Two minor pieces in a line is geometry, not a pin worth naming.

    Two further tests, both missing until D17 and both cheap. **The pinning piece
    must survive**: a rook that pins a knight to a king and is taken by a pawn
    next move has not pinned anything. And the pin must **hold or win
    something** -- against a king that is exact, because python-chess knows
    whether the front piece may legally move; otherwise the piece behind has to
    be winnable once the front one steps aside.
    """
    if wins_material(after, move.to_square, not mover) > 0:
        return False

    for front_square, front, behind_square, behind in _lined_up_pairs(
        after, move.to_square, mover
    ):
        if PIECE_VALUE[behind.piece_type] <= PIECE_VALUE[front.piece_type]:
            continue
        if PIECE_VALUE[behind.piece_type] < PIN_TARGET_MIN_VALUE:
            continue
        if behind.piece_type == chess.KING:
            if after.is_pinned(not mover, front_square):
                return True
            continue
        if _wins_once_vacated(after, front_square, behind_square, mover):
            return True
    return False


def _is_skewer(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """The same geometry as a pin, with the valuable piece attacked first.

    The piece behind must be worth winning once the front one moves; a pawn
    behind a knight lines up without threatening anything. As with the pin, the
    skewering piece must itself survive, and "worth winning" is now settled by an
    exchange rather than by piece values alone (D17).
    """
    if wins_material(after, move.to_square, not mover) > 0:
        return False

    return any(
        PIECE_VALUE[front.piece_type] > PIECE_VALUE[behind.piece_type]
        and PIECE_VALUE[behind.piece_type] >= SKEWER_TARGET_MIN_VALUE
        and _wins_once_vacated(after, front_square, behind_square, mover)
        for front_square, front, behind_square, behind in _lined_up_pairs(
            after, move.to_square, mover
        )
    )


def _is_discovered_attack(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """Vacating a square lets a friendly slider attack something it could not before.

    The revealed attack has to **threaten** something: a slider that now bears
    on a defended knight it cannot profitably take has discovered a line, not an
    attack (D17).
    """
    for slider in _friendly_sliders(after, mover, exclude=move.to_square):
        revealed = after.attacks(slider) - board.attacks(slider)
        for square in revealed:
            piece = after.piece_at(square)
            if piece is None or piece.color == mover:
                continue
            if PIECE_VALUE[piece.piece_type] < 3:
                continue
            if piece.piece_type == chess.KING or wins_material(after, square, mover) > 0:
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

    # "Free" settled by the exchange rather than by "is anything pointing at it":
    # a defender that is pinned cannot actually recapture, and the old test
    # counted it anyway (D17).
    return exchange_value(board, move) >= PIECE_VALUE[captured.piece_type]


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
        return exchange_value(board, move) >= PIECE_VALUE[chess.PAWN]

    captured = board.piece_at(move.to_square)
    if captured is None or PIECE_VALUE[captured.piece_type] >= HANGING_MIN_VALUE:
        return False

    return exchange_value(board, move) >= PIECE_VALUE[captured.piece_type]


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
    if chess.square_rank(king_square) != home_rank:
        return False

    # Mate must be delivered *along* the rank by a rook or queen. Without this a
    # smothered mate on the eighth rank -- a different motif, with a different
    # lesson -- was reported as a back-rank mate (D17).
    return any(
        chess.square_rank(checker) == home_rank
        and (piece := after.piece_at(checker)) is not None
        and piece.piece_type in (chess.ROOK, chess.QUEEN)
        for checker in after.checkers()
    )


def _is_removing_the_defender(
    board: chess.Board, after: chess.Board, move: chess.Move, mover: chess.Color
) -> bool:
    """Capturing a piece so that something it defended is now loose and attacked."""
    if not board.is_capture(move) or board.is_en_passant(move):
        return False

    # A capture that loses material has not removed a defender, it has donated a
    # piece; and the loosened piece has to be winnable rather than merely looked
    # at (D17).
    if exchange_value(board, move) < 0:
        return False

    defended = [
        square
        for square in board.attacks(move.to_square)
        if (piece := board.piece_at(square)) is not None and piece.color != mover
    ]
    return any(wins_material(after, square, mover) > 0 for square in defended)


def _lost_on_arrival(after: chess.Board, escape: chess.Move, mover: chess.Color) -> bool:
    """Would the piece actually be lost on the square it escapes to?

    **Not "is that square attacked"**, which was the defect (E86 D-2). Attacked
    by something and cannot go there are different questions, and D17 replaced
    the first with the second everywhere else in this module -- `_lands_safely`
    asks `wins_material`, and this did not. A knight fleeing to a square its
    king defends is safe however many pieces point at it.

    The escape is played and the exchange is counted on the square it lands on,
    which is the same test the fork detector applies to its own attacker.
    """
    fled = after.copy(stack=False)
    fled.push(escape)
    return wins_material(fled, escape.to_square, mover) > 0


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
        if escapes and all(_lost_on_arrival(after, e, mover) for e in escapes):
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
) -> list[tuple[int, chess.Piece, int, chess.Piece]]:
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
        found: list[tuple[int, chess.Piece]] = []
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
            found.append((current, occupant))
            if len(found) == 2:
                pairs.append((*found[0], *found[1]))
                break
    return pairs


def _wins_once_vacated(
    after: chess.Board, front: int, behind: int, mover: chess.Color
) -> bool:
    """Would the piece behind be won, if the one in front stepped aside?

    That is what makes a relative pin or a skewer worth naming. Without it the
    detector reports geometry: two enemy pieces on a line, one of them nominally
    more valuable, and nothing at stake if either moves.
    """
    probe = after.copy(stack=False)
    probe.remove_piece_at(front)
    return wins_material(probe, behind, mover) > 0


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
