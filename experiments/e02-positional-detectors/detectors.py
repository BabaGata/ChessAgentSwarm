"""Positional feature detectors over python-chess (experiment E02).

Open question D4 asks whether the positional taxonomy that already exists in the
literature can be turned into board-feature detectors, the way tactical motifs
already have been in prior art.

Four concepts, chosen because each has a definition precise enough to argue
about: knight outpost, isolated pawn, backward pawn, and rook control of an open
or semi-open file.

Design rules, taken from prior art (lesson L-004):

  * **Conservative.** Prefer missing a real instance to reporting a false one.
    For a coach a false positive is worse than a miss, because it sends the
    player to study something that was never wrong.
  * **Pure functions on a board.** No engine, no database, no side effects.
  * **Every detector states its definition in the docstring**, because these are
    contested terms and an unstated definition cannot be reviewed.

This is experiment code. A detector that survives validation gets reimplemented
for production in M4, with its own design note.
"""

from __future__ import annotations

from dataclasses import dataclass

import chess

# A knight is only an outpost if it has crossed into the opponent's half far
# enough to restrict them. Ranks are 0-indexed: rank index 3 is the 4th rank.
WHITE_OUTPOST_RANKS = (3, 4, 5)
BLACK_OUTPOST_RANKS = (4, 3, 2)

# Classical outposts are knight squares. Bishops benefit far less from being
# unattackable by pawns, so including them would inflate the count.
OUTPOST_PIECES = (chess.KNIGHT,)


@dataclass(frozen=True)
class Feature:
    """One detected positional feature."""

    name: str
    color: chess.Color
    square: int
    detail: str

    @property
    def square_name(self) -> str:
        return chess.square_name(self.square)

    def __str__(self) -> str:
        side = "White" if self.color == chess.WHITE else "Black"
        return f"{side} {self.name} on {self.square_name} ({self.detail})"


def _pawns(board: chess.Board, color: chess.Color) -> list[int]:
    return list(board.pieces(chess.PAWN, color))


def _pawn_files(board: chess.Board, color: chess.Color) -> set[int]:
    return {chess.square_file(sq) for sq in _pawns(board, color)}


def _is_defended_by_pawn(board: chess.Board, square: int, color: chess.Color) -> bool:
    """Is `square` defended by a pawn of `color`?"""
    file_, rank = chess.square_file(square), chess.square_rank(square)
    behind = rank - 1 if color == chess.WHITE else rank + 1
    if not 0 <= behind <= 7:
        return False
    for adjacent in (file_ - 1, file_ + 1):
        if 0 <= adjacent <= 7:
            piece = board.piece_at(chess.square(adjacent, behind))
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                return True
    return False


def _can_be_attacked_by_enemy_pawn(board: chess.Board, square: int, color: chess.Color) -> bool:
    """Could any enemy pawn ever advance to attack `square`?

    An enemy pawn attacks `square` from an adjacent file, one rank further along
    its own direction of travel. It can reach such a position only if it is
    currently at or behind that rank, so we look for enemy pawns on adjacent
    files that have not yet passed the square.
    """
    file_, rank = chess.square_file(square), chess.square_rank(square)
    enemy = not color
    for enemy_pawn in _pawns(board, enemy):
        if abs(chess.square_file(enemy_pawn) - file_) != 1:
            continue
        enemy_rank = chess.square_rank(enemy_pawn)
        # White outpost: black pawns travel downward, so any black pawn still
        # above the square can come down to attack it.
        if color == chess.WHITE and enemy_rank > rank:
            return True
        if color == chess.BLACK and enemy_rank < rank:
            return True
    return False


def detect_outposts(board: chess.Board, color: chess.Color) -> list[Feature]:
    """Knight on an advanced square, pawn-protected, unattackable by enemy pawns.

    All three conditions are required:
      1. the knight stands on the 4th-6th rank from its own side;
      2. a friendly pawn defends the square;
      3. no enemy pawn can ever advance to attack it.

    Condition 3 is what makes an outpost permanent rather than merely nice, and
    it is the one casual definitions omit.
    """
    ranks = WHITE_OUTPOST_RANKS if color == chess.WHITE else BLACK_OUTPOST_RANKS
    found = []
    for piece_type in OUTPOST_PIECES:
        for square in board.pieces(piece_type, color):
            if chess.square_rank(square) not in ranks:
                continue
            if not _is_defended_by_pawn(board, square, color):
                continue
            if _can_be_attacked_by_enemy_pawn(board, square, color):
                continue
            found.append(
                Feature("knight outpost", color, square, "pawn-protected, no enemy pawn can hit it")
            )
    return found


def detect_isolated_pawns(board: chess.Board, color: chess.Color) -> list[Feature]:
    """A pawn with no friendly pawn on either adjacent file.

    It can never be defended by a pawn, so it must be defended by pieces, and the
    square in front of it is a permanent hole. An isolated pawn on the d-file is
    the classical isolated queen's pawn.
    """
    own_files = _pawn_files(board, color)
    found = []
    for square in _pawns(board, color):
        file_ = chess.square_file(square)
        if (file_ - 1) in own_files or (file_ + 1) in own_files:
            continue
        detail = "isolated queen's pawn" if file_ == 3 else "isolated pawn"
        found.append(Feature("isolated pawn", color, square, detail))
    return found


def detect_backward_pawns(board: chess.Board, color: chess.Color) -> list[Feature]:
    """A pawn left behind its neighbours that cannot safely advance.

    All four conditions are required:
      1. it has at least one friendly pawn on an adjacent file (otherwise it is
         isolated, which is a different weakness);
      2. every such neighbour has advanced past it, so it cannot be supported;
      3. no friendly pawn currently defends it;
      4. the square directly in front is attacked by an enemy pawn, so advancing
         loses it.

    Condition 4 is what makes it *backward* rather than merely rearmost, and is
    the most commonly omitted part of the definition.
    """
    found = []
    own_pawns = _pawns(board, color)
    direction = 1 if color == chess.WHITE else -1

    for square in own_pawns:
        file_, rank = chess.square_file(square), chess.square_rank(square)

        neighbours = [
            other
            for other in own_pawns
            if abs(chess.square_file(other) - file_) == 1
        ]
        if not neighbours:
            continue  # isolated, not backward

        # Every neighbour must be further advanced than this pawn.
        if color == chess.WHITE:
            if any(chess.square_rank(other) <= rank for other in neighbours):
                continue
        else:
            if any(chess.square_rank(other) >= rank for other in neighbours):
                continue

        if _is_defended_by_pawn(board, square, color):
            continue

        ahead_rank = rank + direction
        if not 0 <= ahead_rank <= 7:
            continue
        ahead = chess.square(file_, ahead_rank)
        if board.piece_at(ahead) is not None:
            continue  # blocked by a piece: a different problem
        if not _square_attacked_by_pawn(board, ahead, not color):
            continue

        found.append(
            Feature("backward pawn", color, square, "neighbours advanced, cannot advance safely")
        )
    return found


def _square_attacked_by_pawn(board: chess.Board, square: int, by_color: chess.Color) -> bool:
    """Is `square` currently attacked by a pawn of `by_color`?"""
    file_, rank = chess.square_file(square), chess.square_rank(square)
    origin_rank = rank - 1 if by_color == chess.WHITE else rank + 1
    if not 0 <= origin_rank <= 7:
        return False
    for adjacent in (file_ - 1, file_ + 1):
        if 0 <= adjacent <= 7:
            piece = board.piece_at(chess.square(adjacent, origin_rank))
            if piece and piece.piece_type == chess.PAWN and piece.color == by_color:
                return True
    return False


def detect_open_file_rooks(board: chess.Board, color: chess.Color) -> list[Feature]:
    """A rook on a file carrying no pawns at all (open) or none of its own (semi-open).

    Only rooks count. A queen on an open file is not the same positional asset,
    and counting it would inflate the numbers.
    """
    own_files = _pawn_files(board, color)
    enemy_files = _pawn_files(board, not color)
    found = []
    for square in board.pieces(chess.ROOK, color):
        file_ = chess.square_file(square)
        if file_ in own_files:
            continue  # own pawn in the way: file is closed for this rook
        kind = "open file" if file_ not in enemy_files else "semi-open file"
        found.append(
            Feature(
                "rook on " + kind,
                color,
                square,
                f"file {chess.FILE_NAMES[file_]} has no friendly pawns",
            )
        )
    return found


DETECTORS = {
    "outpost": detect_outposts,
    "isolated_pawn": detect_isolated_pawns,
    "backward_pawn": detect_backward_pawns,
    "rook_open_file": detect_open_file_rooks,
}


def detect_all(board: chess.Board) -> list[Feature]:
    """Run every detector for both sides."""
    features: list[Feature] = []
    for detector in DETECTORS.values():
        for color in (chess.WHITE, chess.BLACK):
            features.extend(detector(board, color))
    return features
