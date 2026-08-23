"""The analysis core: a corpus of games in, typed observations out.

Deterministic and model-free by design (ADR-0002). The analyser is injected
rather than constructed here, which keeps this logic testable without an engine
and leaves the seam a parallel implementation will use.

One evaluation per position, not two per move: the evaluation after a move is
the evaluation before the next one. E01 measured that this is what makes
whole-game analysis affordable.
"""

from __future__ import annotations

from typing import Protocol

import chess

from chesscoach.analysis.cache import PositionEval
from chesscoach.analysis.labels import ErrorLabel, classify, move_loss_wp
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.ingest.pgn import GameRecord, increment_seconds

# Coarse phase boundaries by remaining non-pawn material. E03 found phase
# predicts errors better than any positional feature, so it is recorded on every
# observation rather than derived later.
MIDDLEGAME_PIECES = 10
LATE_MIDDLEGAME_PIECES = 5


class PositionAnalyser(Protocol):
    """Whatever can evaluate a position. Implemented by the engine, stubbed in tests."""

    engine_name: str
    depth: int

    def analyse(self, board: chess.Board) -> PositionEval: ...


def analyse_corpus(
    corpus: Corpus,
    games: tuple[GameRecord, ...] | list[GameRecord],
    analyser: PositionAnalyser,
) -> tuple[Observation, ...]:
    """Analyse every game in the corpus, in a stable order."""
    wanted = set(corpus.game_ids)
    ordered = sorted(
        (game for game in games if game.game_id in wanted), key=lambda game: game.game_id
    )

    observations: list[Observation] = []
    for game in ordered:
        observations.extend(analyse_game(game, analyser))
    return tuple(observations)


def analyse_game(game: GameRecord, analyser: PositionAnalyser) -> tuple[Observation, ...]:
    """Walk one game, evaluating each position once."""
    board = chess.Board()
    observations: list[Observation] = []

    previous = analyser.analyse(board)
    for index, uci in enumerate(game.moves):
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            break  # malformed game; keep what we have rather than guessing

        mover_is_white = board.turn == chess.WHITE
        fen_before = board.fen()
        phase = phase_of(board)
        played_best = previous.best_move == uci

        board.push(move)
        current = analyser.analyse(board)

        observations.append(
            Observation(
                game_id=game.game_id,
                ply=index + 1,
                mover=game.white if mover_is_white else game.black,
                mover_is_white=mover_is_white,
                fen_before=fen_before,
                move_played=uci,
                best_move=previous.best_move,
                score_cp_before=previous.score_cp,
                score_cp_after=current.score_cp,
                loss_wp=_loss(previous, current, mover_is_white, played_best),
                label=_label(previous, current, mover_is_white, played_best),
                phase=phase,
                played_best=played_best,
                clock_before=_clock_before(game, index),
                clock_after=_clock_at(game, index),
                increment=increment_seconds(game.time_control),
                engine=analyser.engine_name,
                depth=analyser.depth,
            )
        )
        previous = current

    return tuple(observations)


def phase_of(board: chess.Board) -> str:
    """Coarse game phase from remaining non-pawn material."""
    pieces = sum(
        len(board.pieces(piece_type, colour))
        for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
        for colour in (chess.WHITE, chess.BLACK)
    )
    if pieces >= MIDDLEGAME_PIECES:
        return "opening_middlegame"
    if pieces >= LATE_MIDDLEGAME_PIECES:
        return "late_middlegame"
    return "endgame"


def _loss(
    before: PositionEval, after: PositionEval, mover_is_white: bool, played_best: bool
) -> float:
    return move_loss_wp(
        before_cp=before.score_cp,
        after_cp=after.score_cp,
        mover_is_white=mover_is_white,
        played_best=played_best,
    )


def _label(
    before: PositionEval, after: PositionEval, mover_is_white: bool, played_best: bool
) -> ErrorLabel | None:
    return classify(_loss(before, after, mover_is_white, played_best))


def _clock_at(game: GameRecord, index: int) -> float | None:
    return game.clocks[index] if index < len(game.clocks) else None


def _clock_before(game: GameRecord, index: int) -> float | None:
    """The mover's own previous clock reading, two plies earlier."""
    return _clock_at(game, index - 2) if index >= 2 else None
