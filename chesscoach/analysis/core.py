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

from chesscoach.analysis.cache import Line, PositionEval
from chesscoach.analysis.labels import ErrorLabel, classify, move_loss_wp, win_probability
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.ingest.pgn import GameRecord, increment_seconds
from chesscoach.punishment import Punishment, candidates_in, qualifying

# Coarse phase boundaries by remaining non-pawn material. E03 found phase
# predicts errors better than any positional feature, so it is recorded on every
# observation rather than derived later.
MIDDLEGAME_PIECES = 10
LATE_MIDDLEGAME_PIECES = 5


# How many candidate moves to ask for at an error position.
#
# **Three, and the number is a cost decision with a measurement behind it.**
# MultiPV costs roughly N times a single search at a fixed depth -- measured
# 2.83x at three against 5.28x at five -- because finding the second-best move
# means not pruning the branches that prove it is second best. At three, and at
# error positions only, the whole addition is about 38 seconds per player
# ([[design.multipv-candidate-moves]]).
#
# Three is also enough to be *provably* complete much of the time: when the last
# line shown is already more than an inaccuracy below the first, no unshown move
# can qualify, because MultiPV returns its lines in descending order. See
# `s1_tactical_gaps` for where that check is made.
CANDIDATE_MOVES = 3


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
        label = _label(previous, current, mover_is_white, played_best)

        # Only errors are priced, which is what keeps this affordable: E85
        # measured 1.52 evaluations per error position, because `detect_motifs`
        # removes 93 % of replies for free before anything reaches the engine.
        punishments: tuple[Punishment, ...] = ()
        candidates: tuple[Line, ...] = ()
        if label is not None:
            punishments = _punishments(board, current, mover_is_white, analyser)
            # **The position as it stood**, rebuilt from the FEN rather than by
            # unwinding: these are the player's own alternatives, and `board`
            # has already had their move pushed onto it for the punishment call.
            candidates = _candidates(chess.Board(fen_before), analyser)

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
                label=label,
                phase=phase,
                played_best=played_best,
                clock_before=_clock_before(game, index),
                clock_after=_clock_at(game, index),
                increment=increment_seconds(game.time_control),
                opponent=game.black if mover_is_white else game.white,
                played_on=game.date,
                punishments=punishments,
                candidates=candidates,
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


def _candidates(board: chess.Board, analyser: PositionAnalyser) -> tuple[Line, ...]:
    """The engine's few best moves here, or nothing if it cannot say.

    `PositionAnalyser` is a Protocol and `lines` is **not** part of it: the stubs
    in the test suite implement `analyse` alone, and an older cache or a
    different engine wrapper may too. A missing capability costs the candidates
    and never the run (L-046) -- every claim that reads them already treats an
    empty tuple as *"not measured"*.
    """
    asks = getattr(analyser, "lines", None)
    if asks is None:
        return ()
    try:
        return tuple(asks(board, CANDIDATE_MOVES))
    except Exception:  # noqa: BLE001 - one unanswerable position must not end the game
        return ()


def _punishments(
    board: chess.Board,
    after: PositionEval,
    mover_is_white: bool,
    analyser: PositionAnalyser,
) -> tuple[Punishment, ...]:
    """What the opponent could have played to punish the move just made.

    `board` is the position the opponent now faces and `after` is its evaluation,
    which already assumes they play their best -- so `after` *is* the best reply's
    win probability. That equality was measured rather than assumed: over 800
    positions the gap between a position's evaluation and the evaluation after its
    own best move has a median of **8 cp**, against 264 cp for an arbitrary other
    move.

    Evaluations are White-relative, so both sides of the comparison are converted
    to the replying side's view before anything is subtracted (L-046: the arms of
    a comparison must be what the comparison claims).
    """
    replying_is_white = not mover_is_white

    def for_replier(cp: int) -> float:
        white_wp = win_probability(cp)
        return white_wp if replying_is_white else 100.0 - white_wp

    best_wp = for_replier(after.score_cp)
    best = None
    if after.best_move:
        try:
            candidate = chess.Move.from_uci(after.best_move)
        except ValueError:
            candidate = None
        if candidate is not None and candidate in board.legal_moves:
            best = candidate

    candidates = candidates_in(
        board,
        lambda b: for_replier(analyser.analyse(b).score_cp),
        best=best,
        best_wp=best_wp,
    )
    return qualifying(candidates, best_wp)
