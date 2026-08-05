"""How much the opponent is bearing on the player's king.

Design: docs/notes/capacity.agents.s8-attack-and-defence.md
Screen: docs/notes/experiments.e11-attack-candidates.md

One measurement, deliberately. E11 screened four candidates and only this one is
both viable and unambiguous: a broken pawn shield spreads slightly more but
cannot tell "I advanced them" from "they were traded off", and the error-rate
contrast under pressure barely varies between players.
"""

from __future__ import annotations

import chess

# Three attackers is the conventional point at which an attack stops being an
# inconvenience. Named rather than buried, so that tuning it would be visible.
PRESSURE_ATTACKERS = 3


def king_zone(board: chess.Board, colour: chess.Color) -> tuple[int, ...]:
    """The king's square and everything touching it."""
    king = board.king(colour)
    if king is None:
        return ()

    file_, rank = chess.square_file(king), chess.square_rank(king)
    return tuple(
        chess.square(file_ + df, rank + dr)
        for df in (-1, 0, 1)
        for dr in (-1, 0, 1)
        if 0 <= file_ + df <= 7 and 0 <= rank + dr <= 7
    )


def zone_attackers(board: chess.Board, colour: chess.Color) -> int:
    """Distinct enemy pieces bearing on the squares round `colour`'s king.

    Counts pieces, not weight -- a queen and a rook are worth more than two
    knights and this does not know it. Crude on purpose: the claim is about how
    readily a player lets an attack assemble, not about evaluating one.
    """
    enemy = not colour
    attackers: set[int] = set()
    for square in king_zone(board, colour):
        attackers |= set(board.attackers(enemy, square))
    return len(attackers)


def allowed_pressure(before: chess.Board, after: chess.Board, colour: chess.Color) -> bool:
    """Did the opponent cross into a real attack between these two positions?

    `after` is the position following the opponent's **reply**, not the player's
    own move -- an attack arrives on their turn (E09).

    The crossing is what counts, not the state. Pressure that was already there
    is not something this move allowed, and counting it would turn one concession
    into a finding repeated on every move of the attack.
    """
    return zone_attackers(after, colour) >= PRESSURE_ATTACKERS > zone_attackers(before, colour)
