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

    def test_one_accurate_move_breaks_the_run(self):
        # This asserted the opposite until E68 calibrated the window. A
        # permutation test found that every move of slack lets chance catch up:
        # three-in-three beats a shuffled baseline 1.96 to 1 and no shuffle in
        # 200 reached it, while three-in-four was matched by one shuffle in
        # eight. The author wrote "one move after the other" and the design note
        # softened it; the measurement says the words were right.
        played = [
            move(40, erred=True), move(41, erred=True),
            move(42, erred=False), move(43, erred=True),
        ]
        assert RUN_WINDOW == RUN_LENGTH == 3
        assert _runs_of_imprecision(played) == frozenset()


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

    def test_a_tactical_drop_breaks_a_run_rather_than_joining_it(self):
        # 40, 42, 43 are three non-tactical drops, but the hung piece at 41 sits
        # between them, so they are not consecutive. Under the calibrated rule
        # that is not a run -- and it should not be: the player did not err on
        # three moves in a row, they erred, missed a tactic, then erred twice.
        played = [
            move(40, erred=True),
            move(41, erred=True, fen=TACTICAL, best=TACTICAL_BEST),
            move(42, erred=True),
            move(43, erred=True),
        ]
        assert _runs_of_imprecision(played) == frozenset()

    def test_three_consecutive_non_tactical_drops_after_one_still_count(self):
        played = [
            move(40, erred=True, fen=TACTICAL, best=TACTICAL_BEST),
            move(41, erred=True),
            move(42, erred=True),
            move(43, erred=True),
        ]
        assert _runs_of_imprecision(played) == {("g1", 41), ("g1", 42), ("g1", 43)}


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


ROOK_ENDGAME = "8/5pk1/8/8/8/8/5PK1/R6r w - - 0 40"
PAWN_ENDGAME = "8/5pk1/8/8/8/8/5PK1/6K1 w - - 0 40"


def an_endgame_finding(fens: tuple[str, ...]):
    """A pooled `endgame_error` finding citing positions of the given kinds."""
    from chesscoach.profile.models import (
        Claim, Confidence, ConfidenceTier, DeterminedBy, Evidence, Finding, GapType,
        GapTypeHypothesis, Measurement, Provenance,
    )

    return Finding(
        section="S3",
        claim=Claim.of(kind="endgame_error", subject="any"),
        measurement=Measurement(
            instances=max(len(fens), 1), distinct_games=min(len(fens), 3) or 1,
            games_with_data=20,
            rate=0.2, baseline_rate=0.1, peer_rate=0.1,
        ),
        provenance=Provenance(engine="stub", depth=15, corpus_id="c1",
                              analysed_at="2026-09-13"),
        confidence=Confidence(tier=ConfidenceTier.WATCH, replicated=True),
        gap_type=GapType(hypothesis=GapTypeHypothesis.UNKNOWN,
                         determined_by=DeterminedBy.INFERRED),
        evidence=tuple(
            Evidence(game_id=f"g{i}", ply=60, fen=fen) for i, fen in enumerate(fens)
        ),
    )


class TestThePooledClaimNamesTheEndgamesItSaw:
    """*"Endgames should be separated by the types of the endgames, any is not
    informative."* -- the author, on `endgame_error.any`.

    The separation **already exists**: `_count` files every endgame error under
    `material_class` as well as under `any`, and the peer reference carries all
    five cells in every band. What does not exist is enough evidence per type --
    23 endgame errors across five classes in a sixty-game window, against a
    confidence gate that wants distinct games. So all five per-type claims sit
    in the sheet's NEVER FIRED list.

    **Retiring `any` the way `out_of_book.any` was retired would therefore
    silence endgames completely**, which is the opposite of what the complaint
    asks for: `out_of_book`'s per-family claims fire, and these do not.

    So the pooled claim stays and is made to say what it knows. It counted the
    types on the way past; it simply threw them away. *"Your play falls off in
    the endgame"* is not informative, and *"...and it is rook endgames where it
    happens"* is the same measurement, said usefully.
    """

    def test_the_exercise_names_the_types_the_errors_were_in(self):
        from chesscoach.planner import _action

        finding = an_endgame_finding((ROOK_ENDGAME, ROOK_ENDGAME, PAWN_ENDGAME))

        said = _action(finding)

        assert "rook" in said and "pawn" in said

    def test_an_unreadable_position_still_produces_an_exercise(self):
        """`Finding` guarantees evidence, so there is always something to read
        -- but a FEN that will not parse must cost the advice rather than the
        run (L-046). An older profile is exactly where this shows up."""
        from chesscoach.planner import _action

        said = _action(an_endgame_finding(("not a fen at all",)))

        assert "endgame" in said.lower()
