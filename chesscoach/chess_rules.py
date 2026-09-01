"""The rules of chess, generated rather than written down.

Design: docs/notes/design.graph-knowledge-base.md § "The rules layer"

The author asked for *"recorded patterns on how the pieces can move so that
ollama's llm knows the basics just in case"*, the general rules, and the time
controls. This is that layer, and it is stage 1 of the graph because it is the
only part with **no sourcing problem at all**.

**Nothing here is a claim about chess.** Movement is computed by `python-chess`
on an empty board, so every square listed is arithmetic anyone can re-run. The
outcome rules cite the predicate that implements them, which is a checkable
source in a way an invented FIDE article number would not be -- fabricating a
citation is worse than lacking one. Time controls come from `chesscoach.speed`,
which reimplements Lichess's own published rule.

The human sentences are held to one standard: **checkable against the data stored
beside them.** *"Two squares along one axis and one along the other"* can be
verified against the eight squares in `attacks_from_centre`. *"Knights are strong
in closed positions"* could not be, and this layer does not hold that kind of
sentence -- it is what stages 2 and 3 exist for, with books behind it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import chess

from chesscoach.speed import _BOUNDS, BLITZ, BULLET, CLASSICAL, RAPID, ULTRA_BULLET

# Every non-pawn movement pattern is generated from this square. The centre,
# because it is the only place where every piece has its full, unobstructed
# pattern -- a knight on a1 attacks two squares and would describe itself wrongly.
CENTRE = chess.D4

# White, so the pawn's direction is stated rather than ambiguous.
_SYMBOLS = (
    ("king", "K"), ("queen", "Q"), ("rook", "R"),
    ("bishop", "B"), ("knight", "N"), ("pawn", "P"),
)

_DESCRIPTIONS = {
    "king": "One square in any direction: along a rank, a file, or a diagonal.",
    "queen": "Any distance along a rank, a file or a diagonal, until something blocks it.",
    "rook": "Any distance along a rank or a file, until something blocks it.",
    "bishop": "Any distance along a diagonal, staying on squares of one colour.",
    "knight": ("Two squares along one axis and one along the other, and it is the only "
               "piece that jumps over whatever stands between."),
    "pawn": ("Forward only, one square, or two from its starting rank. It does not "
             "capture the way it moves: a capture is one square diagonally forward."),
}

_SPECIAL = {
    "king": ("Castling: the king moves two squares toward a rook and that rook jumps "
             "to its far side. Only if neither has moved, the squares between are "
             "empty, and the king is not in check on any square it crosses."),
    "pawn": ("Promotion: a pawn reaching the far rank becomes a queen, rook, bishop or "
             "knight. En passant: a pawn that has just advanced two squares may be "
             "captured as though it had advanced one, and only on the very next move."),
}


@dataclass(frozen=True)
class MovementRule:
    """How one piece moves, with the squares that prove it."""

    piece: str
    symbol: str
    description: str
    # Generated, so the description above can be checked against it.
    attacks_from_centre: tuple[str, ...]
    special: str = ""
    generated_by: str = f"python-chess: Board.attacks({chess.square_name(CENTRE)})"


@dataclass(frozen=True)
class OutcomeRule:
    """A way a game ends, or a state it can be in."""

    name: str
    statement: str
    implemented_by: str


@dataclass(frozen=True)
class TimeControlRule:
    """One Lichess speed, and where its boundary falls."""

    name: str
    statement: str
    upper_seconds: float | None
    examples: tuple[str, ...] = field(default_factory=tuple)
    implemented_by: str = "python: chesscoach.speed.speed_class"


def movement_rules() -> tuple[MovementRule, ...]:
    """One rule per piece, with its attacked squares computed from an empty board."""
    board = chess.Board(None)
    rules = []
    for piece, symbol in _SYMBOLS:
        board.clear()
        board.set_piece_at(CENTRE, chess.Piece.from_symbol(symbol))
        squares = tuple(sorted(chess.square_name(s) for s in board.attacks(CENTRE)))
        rules.append(MovementRule(
            piece=piece,
            symbol=symbol,
            description=_DESCRIPTIONS[piece],
            # A pawn's attacks are not its moves, so listing them as though they
            # were would misdescribe the one piece that moves and captures
            # differently. Its description carries the whole answer instead.
            attacks_from_centre=() if piece == "pawn" else squares,
            special=_SPECIAL.get(piece, ""),
        ))
    return tuple(rules)


def outcome_rules() -> tuple[OutcomeRule, ...]:
    """The states and endings a player asks about, each citing its predicate.

    Every statement is the condition the named `python-chess` predicate tests, so
    it can be checked by reading one function rather than trusted.
    """
    return (
        OutcomeRule(
            "check",
            "The king is attacked and the side to move must answer the attack.",
            "python-chess: Board.is_check()",
        ),
        OutcomeRule(
            "checkmate",
            "The side to move is in check and has no legal move. The game ends "
            "and that side loses.",
            "python-chess: Board.is_checkmate()",
        ),
        OutcomeRule(
            "stalemate",
            "The side to move is not in check and has no legal move. The game "
            "is drawn.",
            "python-chess: Board.is_stalemate()",
        ),
        OutcomeRule(
            "insufficient material",
            "Neither side has enough material to deliver checkmate, so the game "
            "is drawn however it is played out.",
            "python-chess: Board.is_insufficient_material()",
        ),
        OutcomeRule(
            "fifty-move rule",
            "Fifty moves by each side with no capture and no pawn move: either "
            "side may claim a draw.",
            "python-chess: Board.can_claim_fifty_moves()",
        ),
        OutcomeRule(
            "threefold repetition",
            "The same position, with the same side to move and the same legal "
            "moves available, has occurred three times: either side may claim a draw.",
            "python-chess: Board.can_claim_threefold_repetition()",
        ),
    )


def time_control_rules() -> tuple[TimeControlRule, ...]:
    """The five Lichess speeds, with bounds read from the classifier itself.

    **Duration decides, not the starting clock**, which is the part players find
    surprising: 3+2 is blitz and 5+5 is rapid, because the estimate is the clock
    plus forty increments. Examples are generated by running `speed_class`, so a
    bound and its example cannot fall out of step.
    """
    from chesscoach.speed import speed_class

    bounds: dict[str, float | None] = {name: bound for bound, name in _BOUNDS}
    bounds[CLASSICAL] = None

    # Candidates, filtered by what the classifier actually says. Nothing here
    # asserts which bucket a control falls into -- the code does.
    candidates = ("15+0", "60+0", "120+1", "180+0", "180+2", "300+0",
                  "300+5", "600+0", "900+10", "1800+0", "3600+0")

    rules = []
    for name in (ULTRA_BULLET, BULLET, BLITZ, RAPID, CLASSICAL):
        upper = bounds[name]
        limit = ("no upper limit" if upper is None
                 else f"under {upper:.0f} seconds")
        rules.append(TimeControlRule(
            name=name,
            statement=(
                f"{name}: estimated duration {limit}. The estimate is the "
                f"starting clock plus forty increments, so a game with a large "
                f"increment counts as slower than its clock suggests."
            ),
            upper_seconds=upper,
            examples=tuple(c for c in candidates if speed_class(c) == name),
        ))
    return tuple(rules)
