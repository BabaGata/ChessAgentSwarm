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
from chesscoach.analysis.labels import ErrorLabel, classify, move_loss_wp, win_probability
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.ingest.pgn import GameRecord, increment_seconds
from chesscoach.material import moved_into_attack
from chesscoach.punishment import WORTH_PLAYING_WP, Punishment, candidates_in, qualifying

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
        label = _label(previous, current, mover_is_white, played_best)
        # Every move, not only errors: putting a piece en prise is a habit a
        # move can have without costing anything. The engine is asked only when
        # the static check fires, which the measurement put at about 64 calls a
        # player.
        winnable = _moved_piece_winnable(
            chess.Board(fen_before), move, analyser, after_eval=current
        )

        # Only errors are priced, which is what keeps this affordable: E85
        # measured 1.52 evaluations per error position, because `detect_motifs`
        # removes 93 % of replies for free before anything reaches the engine.
        punishments: tuple[Punishment, ...] = ()
        available: tuple[Punishment, ...] = ()
        if label is not None:
            punishments = _punishments(board, current, mover_is_white, analyser)
            # **The position as it stood**, rebuilt from the FEN rather than by
            # unwinding: these are the player's own alternatives, and `board`
            # has already had their move pushed onto it for the call above.
            available = _available(
                chess.Board(fen_before), previous, mover_is_white, analyser
            )

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
                available=available,
                moved_piece_winnable=winnable,
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


def _moved_piece_winnable(
    board: chess.Board,
    move: chess.Move,
    analyser: PositionAnalyser,
    after_eval: PositionEval | None = None,
) -> bool | None:
    """Can the piece this move put en prise actually be won?

    `board` is the position before the move. `None` when `moved_into_attack`
    does not fire -- nothing is in question, and no engine call is made.

    The author, on `Ng5` at tXOF3X1K#25: *"Taking the knight would result in a
    forced checkmate for white, in this case this was not the issue."* The
    static exchange count cannot see that. Two cheaper answers were measured and
    both failed: the move's own cost (in 46 of 109 costless firings the
    opponent took the piece anyway) and a cost gate (the author's row cost
    1.8 wp).

    What answers it is the question `punishment.qualifying` asks of every
    reply: **is capturing it worth playing?** Some capture of the moved piece
    must be within `WORTH_PLAYING_WP` of the opponent's best. On the author's
    row the only capture reaches 2.5 wp against a best of 79.3. Across 903
    firings, 18.4 % fail this.

    `after_eval` is the evaluation the analysis pass already made of the
    position after the move, passed in so it is not asked for twice.
    """
    if not moved_into_attack(board, move):
        return None

    after = board.copy(stack=False)
    after.push(move)
    here = after_eval if after_eval is not None else analyser.analyse(after)
    opponent_is_white = after.turn == chess.WHITE

    def for_opponent(cp: int) -> float:
        white_wp = win_probability(cp)
        return white_wp if opponent_is_white else 100.0 - white_wp

    best_wp = for_opponent(here.score_cp)
    for capture in after.legal_moves:
        if capture.to_square != move.to_square or not after.is_capture(capture):
            continue
        taken = after.copy(stack=False)
        taken.push(capture)
        if best_wp - for_opponent(analyser.analyse(taken).score_cp) <= WORTH_PLAYING_WP:
            return True
    return False


def _available(
    board: chess.Board,
    here: PositionEval,
    mover_is_white: bool,
    analyser: PositionAnalyser,
) -> tuple[Punishment, ...]:
    """What the player could have played instead: `_punishments`, one ply earlier.

    `board` is the position they faced and `here` is its evaluation, which
    already assumes they play their best -- so `here` *is* the best move's win
    probability, the same equality `_punishments` relies on and which was
    measured at a median 8 cp.

    **The mirror is exact, and that is the point.** The author's *"doesn't have
    to be the very best move"* now holds on both sides by the same code, not by
    two rules that happen to agree. `candidates_in` enumerates every legal move
    executing a motif -- `detect_motifs` removes 93 % of them for nothing -- and
    `qualifying` keeps those within `WORTH_PLAYING_WP` of the best.

    **Complete by construction.** The qualifying set is *"executes the motif and
    is worth playing"*; enumerating all motif-executing moves and testing each
    cannot miss one. The alternative considered here was the engine's top N,
    which is both **truncatable** -- a motif ranked N+1 is invisible, and the
    claim cannot tell -- and dearer: MultiPV costs about N times a single search,
    2.83x at three, against a measured 1.52 evaluations per error position for
    this ([[design.multipv-candidate-moves]]).
    """

    def for_player(cp: int) -> float:
        white_wp = win_probability(cp)
        return white_wp if mover_is_white else 100.0 - white_wp

    best_wp = for_player(here.score_cp)
    best = None
    if here.best_move:
        try:
            candidate = chess.Move.from_uci(here.best_move)
        except ValueError:
            candidate = None
        if candidate is not None and candidate in board.legal_moves:
            best = candidate

    candidates = candidates_in(
        board,
        lambda b: for_player(analyser.analyse(b).score_cp),
        best=best,
        best_wp=best_wp,
    )
    return qualifying(candidates, best_wp)


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
