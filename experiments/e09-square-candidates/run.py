"""E09 — which square-and-file claims could S6 actually make?

L-023, learned the expensive way on S5: a section's claims are worth building
only if players differ on them. S5 was fully built before that was checked, and
most of it had to be suppressed. `state.md` now says to run the check first, so
this is S6's § 9.1 arriving **before** the section rather than after it.

Deliberately engine-free. Every candidate here is a pure board property, so the
screen needs games and nothing else — no evaluations, no cache, seconds rather
than minutes. Approximating `diagnosable()` by skipping the opening grace plies
is good enough to compare players against each other, which is all this asks.

Candidates, all framed as **what goes wrong** rather than what exists
(domain.sections design rule 1), and all as **events** rather than states, since
E02 showed presence carries almost no information:

    concedes_outpost   a move that hands the opponent a permanent knight square
    concedes_hole      a move that creates a square in the player's own half
                       that no pawn of theirs can ever cover again
    cedes_open_file    an open file exists, the player has a rook, and it is
                       somewhere else -- a state, kept as the control: if this
                       one discriminates it is the odd one out

Usage:
    python run.py --pgn DIR
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.sections.base import OPENING_GRACE_PLIES  # noqa: E402

# A hole matters only where a piece would want to sit: the middle ranks of the
# player's own half. A hole on the first rank is not an outpost square.
WHITE_HOLE_RANKS = (2, 3, 4)
BLACK_HOLE_RANKS = (5, 4, 3)

# Every candidate S6 might be built on. Events where the catalogue's topic
# allows one, states where it does not -- the states are controls, since E02
# showed presence carries almost no information.
CANDIDATES = (
    "concedes_hole",
    "concedes_outpost",
    "allows_rook_seventh",
    "cedes_open_file",
    "bad_bishop",
)


def _pawns(board: chess.Board, colour: chess.Color) -> list[int]:
    return list(board.pieces(chess.PAWN, colour))


def _can_ever_be_covered(board: chess.Board, square: int, colour: chess.Color) -> bool:
    """Could any pawn of `colour` ever advance to defend `square`?

    A pawn defends from an adjacent file, one rank behind in its own direction of
    travel, so it must currently be at or behind that rank.
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


def count_holes(board: chess.Board, colour: chess.Color) -> int:
    """Squares in `colour`'s own half that no pawn of theirs can ever cover."""
    ranks = WHITE_HOLE_RANKS if colour == chess.WHITE else BLACK_HOLE_RANKS
    holes = 0
    for rank in ranks:
        for file_ in range(8):
            square = chess.square(file_, rank)
            if board.piece_at(square) is not None:
                continue
            if not _can_ever_be_covered(board, square, colour):
                holes += 1
    return holes


def count_enemy_outposts(board: chess.Board, colour: chess.Color) -> int:
    """Enemy knights settled in `colour`'s half, pawn-backed and unevictable.

    E02's definition, from the other side: advanced, defended by a friendly pawn,
    and no enemy pawn can ever advance to attack it. Condition three is what
    makes it permanent and is the one casual definitions omit.
    """
    enemy = not colour
    ranks = WHITE_HOLE_RANKS if colour == chess.WHITE else BLACK_HOLE_RANKS
    found = 0
    for square in board.pieces(chess.KNIGHT, enemy):
        if chess.square_rank(square) not in ranks:
            continue
        if not _defended_by_pawn(board, square, enemy):
            continue
        if _can_ever_be_covered(board, square, colour):
            continue
        found += 1
    return found


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


def enemy_rooks_on_my_seventh(board: chess.Board, colour: chess.Color) -> int:
    """Enemy rooks on the rank where the player's pawns started.

    "A rook on the seventh" from the other side. Named for the player's own
    second rank so the claim is about what they conceded.
    """
    rank = 1 if colour == chess.WHITE else 6
    return sum(
        1
        for square in board.pieces(chess.ROOK, not colour)
        if chess.square_rank(square) == rank
    )


def has_bad_bishop(board: chess.Board, colour: chess.Color) -> bool:
    """A bishop hemmed in by the player's own pawns on its own square colour.

    Four is the conventional threshold for "bad" rather than merely inconvenient,
    and it is a state rather than an event -- kept as a second control.
    """
    for square in board.pieces(chess.BISHOP, colour):
        light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
        blockers = sum(
            1
            for pawn in _pawns(board, colour)
            if ((chess.square_file(pawn) + chess.square_rank(pawn)) % 2 == 1) == light
        )
        if blockers >= 4:
            return True
    return False


def cedes_open_file(board: chess.Board, colour: chess.Color) -> bool:
    """An open file exists, the player owns a rook, and none of them is on it."""
    files_with_pawns = {
        chess.square_file(square)
        for square in _pawns(board, chess.WHITE) + _pawns(board, chess.BLACK)
    }
    open_files = set(range(8)) - files_with_pawns
    if not open_files:
        return False

    rooks = list(board.pieces(chess.ROOK, colour))
    if not rooks:
        return False
    return not any(chess.square_file(rook) in open_files for rook in rooks)


def screen(path: Path, player: str) -> dict[str, tuple[int, int]]:
    """Instances and opportunities per candidate, for one player.

    Two windows, because the candidates realise at different moments:

    * a **hole** appears the instant the player pushes the pawn, so it is judged
      across the player's own move;
    * an enemy **knight settling** on an outpost, or a **rook reaching** the
      player's second rank, happens on the opponent's reply. Judging those
      across the player's move alone finds almost nothing — which is exactly
      what the first version of this screen reported, and it was wrong rather
      than interesting. Same framing S1 uses for `allowed_motif`: what you
      conceded shows up in their answer.
    """
    tally: Counter[str] = Counter()
    for game in parse_pgn_file(path):
        colour = chess.WHITE if game.player_is_white(player) else chess.BLACK
        board = chess.Board()

        for index, uci in enumerate(game.moves):
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                break
            if board.turn != colour or index + 1 <= OPENING_GRACE_PLIES:
                board.push(move)
                continue

            before_holes = count_holes(board, colour)
            before_outposts = count_enemy_outposts(board, colour)
            before_seventh = enemy_rooks_on_my_seventh(board, colour)
            ceded = cedes_open_file(board, colour)
            bad_bishop = has_bad_bishop(board, colour)

            board.push(move)
            after_my_move_holes = count_holes(board, colour)

            # Look through the opponent's reply for the things they realise.
            reply = board.copy()
            if index + 1 < len(game.moves):
                answer = chess.Move.from_uci(game.moves[index + 1])
                if answer in reply.legal_moves:
                    reply.push(answer)

            for name in CANDIDATES:
                tally[f"{name}.opportunities"] += 1
            if after_my_move_holes > before_holes:
                tally["concedes_hole.instances"] += 1
            if count_enemy_outposts(reply, colour) > before_outposts:
                tally["concedes_outpost.instances"] += 1
            if enemy_rooks_on_my_seventh(reply, colour) > before_seventh:
                tally["allows_rook_seventh.instances"] += 1
            if ceded:
                tally["cedes_open_file.instances"] += 1
            if bad_bishop:
                tally["bad_bishop.instances"] += 1

    return {
        name: (tally[f"{name}.instances"], tally[f"{name}.opportunities"])
        for name in CANDIDATES
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    args = parser.parse_args()

    per_candidate: dict[str, list[float]] = {}
    opportunities: dict[str, list[int]] = {}

    paths = sorted(args.pgn.glob("*.pgn"))
    print(f"screening {len(paths)} players, no engine\n", flush=True)
    for path in paths:
        for name, (instances, chances) in screen(path, path.stem).items():
            if chances < 50:
                continue
            per_candidate.setdefault(name, []).append(instances / chances)
            opportunities.setdefault(name, []).append(chances)

    print(f"{'candidate':<20} {'n':>3} {'median':>8} {'p10':>7} {'p90':>7} "
          f"{'p90/med':>8} {'opps':>6}")
    for name, rates in sorted(per_candidate.items()):
        rates = sorted(rates)
        median = statistics.median(rates)
        p10 = rates[int(0.10 * (len(rates) - 1))]
        p90 = rates[int(0.90 * (len(rates) - 1))]
        spread = p90 / median if median else float("inf")
        print(f"{name:<20} {len(rates):>3} {median:>8.4f} {p10:>7.4f} {p90:>7.4f} "
              f"{spread:>8.2f} {statistics.median(opportunities[name]):>6.0f}")

    print(
        "\nfor comparison, claims already known to discriminate:\n"
        "  early_error.black 1.92 · long_think_error 1.60 · endgame_error.any 1.70\n"
        "and one that does not:\n"
        "  concedes_weakness.any 1.24 · concedes_weakness.doubled 1.20"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
