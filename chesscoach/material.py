"""Why material was lost, as distinct from what won it.

Answers open question D13, raised by the expert reviewer mid-review:

    "Does the system evaluate the reason for why the player is losing
     pawns/pieces — leaving many undefended regularly, does the player move them
     to the attacked spot, does he calculate the exchange badly, doesn't see
     defending moves? This kind of information seems more valuable for the
     advice than just saying that the player is losing the material."

The swarm already names **mechanism** — a fork, a pin, a hanging piece — and the
author ruled that mechanism beats material outcome, because "you dropped a pawn"
names a symptom the player watched happen. These detectors sit one level below
mechanism: not *what won the material*, but *what the player did that made it
winnable*. Each maps to a different habit, which is the whole point:

    moved into it      check the destination square before releasing the piece
    left it hanging    scan your own undefended pieces before choosing
    miscounted         count attackers and defenders on the square
    ignored a threat   when something is attacked, find the defence first

**These read the move the player actually played.** Every other detector in the
project reads the engine's best move or the opponent's best reply, which is the
structural gap E33 identified: a piece placed en prise is currently only visible
through whatever the opponent's reply happens to be.

No engine call is added. Static exchange evaluation is exact arithmetic over the
position, and it uses `legal_moves` rather than an attacker bitboard so that pins
and discovered checks are respected — slower, and right where a raw swap list is
wrong.
"""

from __future__ import annotations

import chess

# Exchange arithmetic only. Deliberately not the engine's evaluation: this asks
# "who ends up with more wood", which is the question a player asks at the board
# when deciding whether a capture is safe.
PIECE_VALUE: dict[int, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 100,
}

# Below this the "loss" is a tempo or a structural choice, not a material error.
# One pawn is the smallest unit a player would call losing material.
MATERIAL_LOSS = 1


def _least_valuable_capture(board: chess.Board, square: int) -> chess.Move | None:
    """The cheapest legal capture of whatever stands on `square`.

    Legality matters: a pinned defender cannot recapture, and a swap list built
    from raw attackers would count it anyway and call a losing capture safe.
    """
    best: chess.Move | None = None
    best_value = None
    for move in board.legal_moves:
        if move.to_square != square:
            continue
        piece = board.piece_at(move.from_square)
        if piece is None:
            continue
        value = PIECE_VALUE[piece.piece_type]
        if best_value is None or value < best_value:
            best, best_value = move, value
    return best


def _swap(board: chess.Board, square: int) -> int:
    """What the side to move nets by capturing on `square`, in pawns.

    Standard swap-off: take with the cheapest piece, then let the opponent do the
    same, and stop whenever continuing is worse than standing still — which is
    what the `max(0, ...)` models.
    """
    capture = _least_valuable_capture(board, square)
    if capture is None:
        return 0

    victim = board.piece_at(square)
    if victim is None:
        return 0
    gain = PIECE_VALUE[victim.piece_type]

    board.push(capture)
    try:
        return max(0, gain - _swap(board, square))
    finally:
        board.pop()


def wins_material(board: chess.Board, square: int, side: chess.Color) -> int:
    """What `side` wins by capturing on `square`, whoever is to move.

    `_swap` answers for the side to move. The motifs need to ask about **either**
    side — "can the opponent take my knight back?" and "can I win that rook?" are
    both questions about a position where it may not be that side's turn — so the
    turn is flipped with a null move first.

    This is the single notion of "safe" the detectors were missing. `tactics.py`
    had its own, built on `is_attacked_by` with no piece values, which called a
    knight on a square attacked by a pawn and defended by a pawn *safe* (D17).
    """
    if board.turn != side:
        board = board.copy(stack=False)
        # A null move only flips the turn and clears en passant. Pushed even when
        # the other side is in check, deliberately: "what could White win on a8?"
        # is exactly the question a fork detector asks after giving check, and
        # refusing to answer it there would blind the detector to every fork that
        # comes with check -- which is most of them.
        board.push(chess.Move.null())
    return _swap(board, square)


def exchange_value(board: chess.Board, move: chess.Move) -> int:
    """Material the mover nets from this move once the exchange plays out.

    Negative means the move loses material against best play. Zero means an even
    trade or a quiet move that cannot be punished materially.
    """
    square = move.to_square
    if board.is_en_passant(move):
        gain = PIECE_VALUE[chess.PAWN]
    else:
        victim = board.piece_at(square)
        gain = PIECE_VALUE[victim.piece_type] if victim else 0

    board.push(move)
    try:
        return gain - _swap(board, square)
    finally:
        board.pop()


def _winnable_squares(board: chess.Board, owner: chess.Color) -> set[int]:
    """Squares where `owner`'s material can be profitably taken, if it were the
    opponent's move.

    The turn is flipped rather than a null move pushed, because pushing a null
    move is illegal in check and this has to work in exactly the positions where
    a threat is most likely.
    """
    probe = board.copy(stack=False)
    probe.turn = not owner
    # A stale en-passant square after a turn flip would invent a capture.
    probe.ep_square = None

    winnable = set()
    for square, piece in board.piece_map().items():
        if piece.color != owner or piece.piece_type == chess.KING:
            continue
        if _swap(probe, square) >= MATERIAL_LOSS:
            winnable.add(square)
    return winnable


def moved_into_attack(board: chess.Board, move: chess.Move) -> bool:
    """The piece just moved can now be won for material.

    Restricted to quiet moves and even-or-better captures, so a deliberate
    sacrifice that also wins material is not double-counted as a blunder into
    an attack; a capture that loses material is `miscounted_exchange` instead.
    """
    if exchange_value(board, move) < 0 and board.is_capture(move):
        return False

    after = board.copy(stack=False)
    after.push(move)
    return _swap(after, move.to_square) >= MATERIAL_LOSS


def miscounted_exchange(board: chess.Board, move: chess.Move) -> bool:
    """A capture that loses material once the recaptures are counted."""
    return board.is_capture(move) and exchange_value(board, move) <= -MATERIAL_LOSS


def left_hanging(board: chess.Board, move: chess.Move) -> int:
    """How many OTHER pieces are left winnable after this move.

    The moved piece is excluded — that is `moved_into_attack`, a different habit
    with a different remedy. This one is about what the player stopped looking
    at.
    """
    after = board.copy(stack=False)
    after.push(move)
    mover = board.turn
    return len(_winnable_squares(after, mover) - {move.to_square})


def ignored_threat(board: chess.Board, move: chess.Move) -> bool:
    """Material was already attacked, and the move neither saved nor traded it.

    The threatened piece must still be winnable afterwards **and still be on the
    square it was threatened on**, so moving it away, defending it enough to
    survive the swap, or capturing the attacker all count as addressing it.

    A move that wins at least as much material as is being lost is not ignoring
    the threat — it is a counter-strike, and telling a player off for that would
    be advice against playing well.
    """
    mover = board.turn
    threatened = _winnable_squares(board, mover)
    if not threatened:
        return False

    if exchange_value(board, move) >= MATERIAL_LOSS:
        return False

    after = board.copy(stack=False)
    after.push(move)
    still = _winnable_squares(after, mover)
    return bool((threatened & still) - {move.to_square})


# How near the enemy king a material-losing capture has to land before it reads
# as an attacking sacrifice rather than a miscount. Two squares, not one: a
# bishop taking on h7 next to the king and a rook taking a knight on f6 that
# defends it are the same idea, and only the first touches the king.
ATTACK_RADIUS = 2


def near_king(board: chess.Board, square: int, defender: chess.Color) -> bool:
    """Is `square` inside the attacking radius of `defender`'s king?"""
    king = board.king(defender)
    if king is None:
        return False
    return max(
        abs(chess.square_file(square) - chess.square_file(king)),
        abs(chess.square_rank(square) - chess.square_rank(king)),
    ) <= ATTACK_RADIUS


def sacrificed_for_attack(board: chess.Board, move: chess.Move) -> bool:
    """Material given up on or beside the enemy king.

    The reviewer's distinction, and it is a real one:

        "a sacrifice is when a player deliberately gives a stronger piece for a
         weaker piece to make opening for attack which is usually on the king...
         something like taking a pawn with a bishop on the kings castle or rook
         for a defending knight"

    Whether the sacrifice was *sound* is not asked here and deliberately so.
    Soundness is the engine's judgement, and conditioning on it drags the claim
    into restating the error rate -- measured at r = +0.682 against +0.125
    unconditioned (E34 follow-up).
    """
    if not board.is_capture(move) or exchange_value(board, move) > -MATERIAL_LOSS:
        return False
    return near_king(board, move.to_square, not board.turn)


def miscounted_exchange_away_from_king(board: chess.Board, move: chess.Move) -> bool:
    """A losing capture that is **not** an attack on the king.

    What is left of `miscounted_exchange` once sacrifices are taken out of it:
    an exchange that simply did not add up, with no attacking idea behind it.
    """
    return miscounted_exchange(board, move) and not near_king(
        board, move.to_square, not board.turn
    )


def material_balance(board: chess.Board, colour: chess.Color) -> int:
    """Material for `colour` minus material against, in pawns. Kings excluded."""
    total = 0
    for _square, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            continue
        value = PIECE_VALUE[piece.piece_type]
        total += value if piece.color == colour else -value
    return total


def best_free_capture(board: chess.Board) -> tuple[chess.Move | None, int]:
    """The most material available for nothing right now, and the move that takes it."""
    best, best_gain = None, 0
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        gain = exchange_value(board, move)
        if gain > best_gain:
            best, best_gain = move, gain
    return best, best_gain


def moved_toward_king(board: chess.Board, move: chess.Move) -> bool:
    """Did this move bring a piece closer to the enemy king?"""
    king = board.king(not board.turn)
    if king is None:
        return False

    def distance(square: int) -> int:
        return max(
            abs(chess.square_file(square) - chess.square_file(king)),
            abs(chess.square_rank(square) - chess.square_rank(king)),
        )

    return distance(move.to_square) < distance(move.from_square)


def declined_material_to_attack(board: chess.Board, move: chess.Move) -> bool:
    """Free material was on offer, and the player went for the king instead.

    The reviewer, on `goydorak`: *"sometimes he does not take free pawn on the
    opposite side just to go with his pieces towards the king."*

    Both halves are required. Passing up material for a quiet move is a
    different habit -- possibly a better one -- and this claim is about the
    trade the player keeps choosing, not about every capture they decline.
    """
    _capture, gain = best_free_capture(board)
    if gain < MATERIAL_LOSS or board.is_capture(move):
        return False
    return moved_toward_king(board, move) or near_king(
        board, move.to_square, not board.turn
    )
