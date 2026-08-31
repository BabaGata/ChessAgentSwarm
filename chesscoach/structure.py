"""Pawn-structure weakness detectors.

Design: docs/notes/capacity.agents.s5-pawn-structure.md

`isolated` and `backward` are ported from `experiments/e02-positional-detectors/`
rather than rewritten: they were hand-verified 16/16 there, and E02 said in its
own docstring that a detector surviving validation gets reimplemented for
production in M4. `doubled` is new.

Definitions live in the docstrings because these are contested terms and an
unstated definition cannot be reviewed (L-004). All three are **conservative**:
prefer missing a real instance to reporting a false one, since a false positive
sends a player to study something that was never wrong.

The unit of comparison is a **count per feature**, not a set of squares. A pawn
that is isolated on d4 and still isolated on d5 after advancing would look like a
brand new weakness under square comparison, and the section would report a
concession that never happened.
"""

from __future__ import annotations

from collections import Counter

import chess

ISOLATED = "isolated"
BACKWARD = "backward"
DOUBLED = "doubled"

FEATURES = (ISOLATED, BACKWARD, DOUBLED)


def _pawns(board: chess.Board, colour: chess.Color) -> list[int]:
    return list(board.pieces(chess.PAWN, colour))


def _pawn_files(board: chess.Board, colour: chess.Color) -> set[int]:
    return {chess.square_file(square) for square in _pawns(board, colour)}


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


def _attacked_by_pawn(board: chess.Board, square: int, by_colour: chess.Color) -> bool:
    file_, rank = chess.square_file(square), chess.square_rank(square)
    origin = rank - 1 if by_colour == chess.WHITE else rank + 1
    if not 0 <= origin <= 7:
        return False
    for adjacent in (file_ - 1, file_ + 1):
        if 0 <= adjacent <= 7:
            piece = board.piece_at(chess.square(adjacent, origin))
            if piece and piece.piece_type == chess.PAWN and piece.color == by_colour:
                return True
    return False


def count_isolated(board: chess.Board, colour: chess.Color) -> int:
    """Pawns with no friendly pawn on either adjacent file.

    Such a pawn can never be defended by a pawn, so it must be held by pieces,
    and the square in front of it is a permanent hole.
    """
    files = _pawn_files(board, colour)
    return sum(
        1
        for square in _pawns(board, colour)
        if (chess.square_file(square) - 1) not in files
        and (chess.square_file(square) + 1) not in files
    )


def count_backward(board: chess.Board, colour: chess.Color) -> int:
    """Pawns left behind their neighbours that cannot safely advance.

    All four conditions are required:
      1. at least one friendly pawn on an adjacent file — otherwise it is
         isolated, which is a different weakness;
      2. every such neighbour has advanced past it, so it cannot be supported;
      3. no friendly pawn currently defends it;
      4. the square in front is attacked by an enemy pawn, so advancing loses it.

    Condition 4 is what makes it *backward* rather than merely rearmost, and is
    the part casual definitions omit.
    """
    own = _pawns(board, colour)
    direction = 1 if colour == chess.WHITE else -1
    found = 0

    for square in own:
        file_, rank = chess.square_file(square), chess.square_rank(square)
        neighbours = [o for o in own if abs(chess.square_file(o) - file_) == 1]
        if not neighbours:
            continue

        advanced = (
            all(chess.square_rank(o) > rank for o in neighbours)
            if colour == chess.WHITE
            else all(chess.square_rank(o) < rank for o in neighbours)
        )
        if not advanced or _defended_by_pawn(board, square, colour):
            continue

        ahead_rank = rank + direction
        if not 0 <= ahead_rank <= 7:
            continue
        ahead = chess.square(file_, ahead_rank)
        if board.piece_at(ahead) is not None:
            continue  # blocked by a piece: a different problem
        if not _attacked_by_pawn(board, ahead, not colour):
            continue

        found += 1
    return found


# How far apart two pawns on a file may be and still be the weakness the claim
# names. The author, marking the old detector wrong:
#
# > *"Doubled pawns are detected for pretty much any capture no matter how far
# > away the pawns are. This should be counted only if they are directly one in
# > front of the other or if there is only 1 square in between... otherwise, the
# > pawn that is much more forward is usually attacking the opponent and trying
# > to break the defense and will probably capture anything and fall soon
# > afterwards."*
#
# So 1 or 2 ranks apart. Their reasoning is about what the position is FOR, not
# about geometry: a far-advanced pawn on the same file is doing a different job.
MAX_DOUBLED_GAP = 2

# How long the pawns must survive to be a weakness rather than a moment.
#
# > *"Also the double pawns should be taken in the account if they are able to
# > last for more then 3 moves, otherwise, they are in that state just until the
# > end of exchange."*
DOUBLED_PERSISTS_MOVES = 3


def count_doubled(board: chess.Board, colour: chess.Color) -> int:
    """Surplus pawns sharing a file **and close enough to obstruct each other**.

    Counting surplus rather than files means a tripled pawn reads as worse than
    a doubled one, which matches how it plays.

    Pawns more than `MAX_DOUBLED_GAP` ranks apart do not count. This is the
    author's correction and it is a claim about purpose: a pawn far up the same
    file is attacking rather than obstructing, and it is usually about to be
    exchanged off.
    """
    by_file: dict[int, list[int]] = {}
    for square in _pawns(board, colour):
        by_file.setdefault(chess.square_file(square), []).append(
            chess.square_rank(square)
        )

    surplus = 0
    for ranks in by_file.values():
        if len(ranks) < 2:
            continue
        ranks.sort()
        # Each pawn that sits within the gap of the one below it is one surplus.
        surplus += sum(
            1
            for lower, upper in zip(ranks, ranks[1:])
            if upper - lower <= MAX_DOUBLED_GAP
        )
    return surplus


def doubled_files(board: chess.Board, colour: chess.Color) -> frozenset[int]:
    """Files carrying a doubled pair close enough to count."""
    by_file: dict[int, list[int]] = {}
    for square in _pawns(board, colour):
        by_file.setdefault(chess.square_file(square), []).append(
            chess.square_rank(square)
        )
    found = set()
    for file_, ranks in by_file.items():
        ranks.sort()
        if any(u - l <= MAX_DOUBLED_GAP for l, u in zip(ranks, ranks[1:])):
            found.add(file_)
    return frozenset(found)


def persistent_doubled(
    boards, colour: chess.Color, persists: int = DOUBLED_PERSISTS_MOVES
) -> frozenset[int]:
    """Files doubled continuously for longer than `persists` of the player's moves.

    **The detector has to see a span, not a position.** A capture that doubles
    pawns which are resolved two moves later leaves the player no worse off, and
    the old detector counted it because it only ever looked at one board.

    `boards` is the positions after each of this player's own moves, in order.
    Counting the player's own moves rather than plies is deliberate: the author
    said "moves", and a player who un-doubles at their next turn has held the
    weakness for one move, not two.
    """
    run: dict[int, int] = {}
    survived: set[int] = set()
    for board in boards:
        current = doubled_files(board, colour)
        for file_ in current:
            run[file_] = run.get(file_, 0) + 1
            if run[file_] > persists:
                survived.add(file_)
        for file_ in list(run):
            if file_ not in current:
                # Resolved. The run resets rather than accumulating across
                # separate episodes on the same file.
                del run[file_]
    return frozenset(survived)


COUNTERS = {ISOLATED: count_isolated, BACKWARD: count_backward, DOUBLED: count_doubled}


def weakness_counts(board: chess.Board, colour: chess.Color) -> dict[str, int]:
    """How many of each weakness `colour` currently has."""
    return {name: counter(board, colour) for name, counter in COUNTERS.items()}


def conceded(before: chess.Board, after: chess.Board, colour: chess.Color) -> frozenset[str]:
    """Weaknesses that `colour` has more of after the move than before it.

    The whole section rests on this being *creation* rather than presence: E02
    found isolated pawns in 96 % of games, so having one says nothing, while
    making one is a choice the player made.
    """
    was = weakness_counts(before, colour)
    now = weakness_counts(after, colour)
    return frozenset(name for name in FEATURES if now[name] > was[name])
