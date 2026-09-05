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

# ...and three of *what*. Pawns and the king were counted as attackers, so three
# of them round a king in the middle of an endgame board read as an attack. The
# author rejected three of five marked firings on that, twice for the phase:
#
# > *"This is an endgame, a few checks happen regularly in the endgame. King
# > pressure usually happens when king is cornered and there are enough
# > attacking pieces to make potential threat for checkmate."*
#
# and once for the force:
#
# > *"The black king has plenty of space to move away from the attack and the
# > white does not have enough material in the attack compared to the black
# > pieces that can be easily brougth back to the defense."*
#
# So the attackers are counted as pieces, and weighed. Counting alone does not
# separate the marks -- the third rejection had three attackers like both
# accepted cases -- but their weight does: 3, 10 and 11 for the rejected, 15 for
# both accepted. **Calibrated on five hand-marked positions**, so the threshold
# sits in the gap rather than on either edge, and is named so that moving it is
# visible. Weight rather than "a queen must be there": two rooks and two minors
# is a real attack and has no queen in it.
ATTACKER_WEIGHT = {
    chess.PAWN: 0, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0,
}
PRESSURE_WEIGHT = 13


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
    return len(_attacking_pieces(board, colour))


def _attacking_pieces(board: chess.Board, colour: chess.Color) -> set[int]:
    """Squares of the enemy **pieces** bearing on the king zone.

    Pawns and the king are excluded: they cannot carry a mating attack, and
    including them was what made an endgame king look besieged.
    """
    enemy = not colour
    attackers: set[int] = set()
    for square in king_zone(board, colour):
        attackers |= {
            found
            for found in board.attackers(enemy, square)
            if ATTACKER_WEIGHT[board.piece_type_at(found)] > 0
        }
    return attackers


def attack_weight(board: chess.Board, colour: chess.Color) -> int:
    """How much force is actually bearing on `colour`'s king."""
    return sum(
        ATTACKER_WEIGHT[board.piece_type_at(square)]
        for square in _attacking_pieces(board, colour)
    )


def allowed_pressure(before: chess.Board, after: chess.Board, colour: chess.Color) -> bool:
    """Did the opponent cross into a real attack between these two positions?

    `after` is the position following the opponent's **reply**, not the player's
    own move -- an attack arrives on their turn (E09).

    The crossing is what counts, not the state. Pressure that was already there
    is not something this move allowed, and counting it would turn one concession
    into a finding repeated on every move of the attack.
    """
    crossed = (
        zone_attackers(after, colour) >= PRESSURE_ATTACKERS > zone_attackers(before, colour)
    )
    return crossed and attack_weight(after, colour) >= PRESSURE_WEIGHT
