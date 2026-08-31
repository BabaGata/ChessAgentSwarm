"""An endgame error is a run the tactics do not explain.

Design: docs/notes/design.detectors-name-consequences.md § 6

    "Endgame error should be calculated just when there are big drops of the
    advantage in a few consecutive moves. So that it can be seen that the player
    is imprecise one move after the other and lacks knowledge of how to play the
    endgame. Also, if the sudden loss of the advantage of the one move is
    detected by other motif tests this should not be taken in the account
    because those are tactical losses and this is lack of knowledge of the
    endgames."

The author's own three cases: a single blunder must not fire, three consecutive
inaccuracies must, and a run whose first drop is tactical must count only the
rest.
"""

from __future__ import annotations

from chesscoach.analysis.observations import ErrorLabel, Observation
from chesscoach.sections.s3_endgame_technique import (
    RUN_LENGTH,
    RUN_WINDOW,
    _is_tactical,
    _runs_of_imprecision,
)

# A quiet rook ending. The engine's preference here executes no motif, so a
# drop in it is a matter of technique rather than of missing a threat.
QUIET = "8/8/4k3/8/8/4K3/8/R7 w - - 0 1"
QUIET_BEST = "a1a8"

# White to move with a knight fork of king and rook available on c7. A player
# who misses this has missed a TACTIC, and saying "you do not understand
# endgames" to them names the wrong weakness.
TACTICAL = "r3k3/8/8/1N6/8/8/8/4K3 w - - 0 1"
TACTICAL_BEST = "b5c7"


def move(ply: int, *, erred: bool, fen: str = QUIET, best: str = QUIET_BEST,
         game_id: str = "g1", phase: str = "endgame") -> Observation:
    return Observation(
        game_id=game_id,
        ply=ply,
        mover="alice",
        mover_is_white=True,
        fen_before=fen,
        move_played="e3e4",
        best_move=best,
        score_cp_before=0,
        score_cp_after=0,
        loss_wp=0.2 if erred else 0.0,
        label=ErrorLabel.MISTAKE if erred else None,
        phase=phase,
        played_best=not erred,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
    )


class TestTellingATacticFromTechnique:
    def test_a_quiet_position_is_not_tactical(self):
        assert not _is_tactical(move(40, erred=True))

    def test_a_missed_fork_is(self):
        assert _is_tactical(move(40, erred=True, fen=TACTICAL, best=TACTICAL_BEST))

    def test_a_move_with_no_engine_opinion_is_not_called_tactical(self):
        # An absent answer must not read as a positive one: refusing it would
        # drop the drop entirely rather than counting it as technique.
        assert not _is_tactical(move(40, erred=True, best=""))


class TestARunNotAPoint:
    def test_one_blunder_in_a_rook_ending_does_not_fire(self):
        # The author's first case. A mistake is a mistake; it is not a gap in
        # endgame knowledge.
        played = [move(40, erred=True)] + [move(41 + i, erred=False) for i in range(3)]
        assert _runs_of_imprecision(played) == frozenset()

    def test_two_in_a_row_is_still_not_a_run(self):
        played = [move(40, erred=True), move(41, erred=True), move(42, erred=False)]
        assert _runs_of_imprecision(played) == frozenset()

    def test_three_consecutive_inaccuracies_do_fire(self):
        played = [move(40 + i, erred=True) for i in range(RUN_LENGTH)]
        found = _runs_of_imprecision(played)
        assert len(found) == RUN_LENGTH

    def test_every_move_of_the_run_is_returned_not_only_the_last(self):
        # The claim is about the run, so its evidence should be able to show one.
        played = [move(40 + i, erred=True) for i in range(RUN_LENGTH)]
        assert _runs_of_imprecision(played) == {("g1", 40), ("g1", 41), ("g1", 42)}

    def test_drops_spread_too_far_apart_are_not_a_run(self):
        # Three errors, but with good moves between them: imprecise sometimes,
        # not imprecise one move after the other.
        played = [
            move(40, erred=True), move(41, erred=False), move(42, erred=False),
            move(43, erred=False), move(44, erred=True), move(45, erred=False),
            move(46, erred=False), move(47, erred=False), move(48, erred=True),
        ]
        assert _runs_of_imprecision(played) == frozenset()

    def test_the_window_allows_one_good_move_inside_a_run(self):
        # RUN_LENGTH errors inside RUN_WINDOW moves: a single accurate move does
        # not rescue a stretch of imprecision.
        played = [
            move(40, erred=True), move(41, erred=True),
            move(42, erred=False), move(43, erred=True),
        ]
        assert RUN_WINDOW == 4
        assert len(_runs_of_imprecision(played)) == RUN_LENGTH


class TestTacticalDropsDoNotJoinRuns:
    def test_a_run_whose_middle_is_tactical_does_not_count(self):
        # The author's third case. A hung piece between two inaccuracies does
        # not make three of a kind, because it is a different failure.
        played = [
            move(40, erred=True),
            move(41, erred=True, fen=TACTICAL, best=TACTICAL_BEST),
            move(42, erred=True),
        ]
        assert _runs_of_imprecision(played) == frozenset()

    def test_the_other_two_still_count_when_a_third_joins_them(self):
        played = [
            move(40, erred=True),
            move(41, erred=True, fen=TACTICAL, best=TACTICAL_BEST),
            move(42, erred=True),
            move(43, erred=True),
        ]
        # 40, 42 and 43 are three non-tactical drops within the window.
        assert _runs_of_imprecision(played) == {("g1", 40), ("g1", 42), ("g1", 43)}


class TestScope:
    def test_middlegame_moves_are_not_endgame_errors(self):
        played = [move(40 + i, erred=True, phase="middlegame") for i in range(4)]
        assert _runs_of_imprecision(played) == frozenset()

    def test_runs_do_not_span_two_games(self):
        # Two games with two drops each is not a run, and pooling them would
        # invent one out of separate evenings.
        played = [
            move(40, erred=True, game_id="a"), move(41, erred=True, game_id="a"),
            move(40, erred=True, game_id="b"), move(41, erred=True, game_id="b"),
        ]
        assert _runs_of_imprecision(played) == frozenset()
