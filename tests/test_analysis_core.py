"""The analysis core, driven by a stub analyser so no engine is required.

The core's job is to turn a corpus into typed observations. Injecting the
analyser keeps that logic testable, deterministic and fast -- and it is the same
seam a parallel implementation will later use.
"""

from __future__ import annotations

import chess

from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import increment_seconds, parse_pgn_text
from chesscoach.sections.s2_decision_process import INSTANT_MOVE_SECONDS

from test_ingest import PGN


def an_observation(**overrides) -> Observation:
    """A minimal observation; only the clock fields matter to these tests."""
    defaults = dict(
        game_id="g1", ply=20, mover="p", mover_is_white=True,
        fen_before="8/8/8/8/8/8/8/K6k w - - 0 1", move_played="a1a2",
        best_move="a1a2", score_cp_before=0, score_cp_after=0, loss_wp=0.0,
        label=None, phase="middlegame", played_best=True,
        clock_before=None, clock_after=None, engine="stub", depth=15,
    )
    return Observation(**{**defaults, **overrides})


class StubAnalyser:
    """Returns a fixed evaluation, or a scripted one keyed by ply."""

    engine_name = "stub"
    depth = 15

    def __init__(self, scores: dict[int, int] | None = None, best: str = "a1a2"):
        self.scores = scores or {}
        self.best = best
        self.calls: list[str] = []

    def analyse(self, board: chess.Board):
        from chesscoach.analysis.cache import PositionEval

        self.calls.append(board.fen())
        ply = len(board.move_stack)
        return PositionEval(score_cp=self.scores.get(ply, 0), best_move=self.best, is_mate=False)


class TestAnalyseCorpus:
    def test_produces_one_observation_per_move(self):
        games = parse_pgn_text(PGN)
        corpus = build_corpus("alice", games)

        observations = analyse_corpus(corpus, games, StubAnalyser())

        assert len(observations) == sum(len(g.moves) for g in games)

    def test_records_provenance_on_every_observation(self):
        games = parse_pgn_text(PGN)
        analyser = StubAnalyser()

        observations = analyse_corpus(build_corpus("alice", games), games, analyser)

        assert all(o.engine == "stub" and o.depth == 15 for o in observations)

    def test_labels_an_error_when_the_evaluation_collapses(self):
        games = parse_pgn_text(PGN)[:1]
        # White to move at ply 0 and 2; a large drop after White's second move.
        analyser = StubAnalyser(scores={0: 0, 1: 0, 2: 0, 3: -900, 4: -900})

        observations = analyse_corpus(build_corpus("alice", games), games, analyser)

        assert any(o.label is ErrorLabel.BLUNDER for o in observations)

    def test_is_deterministic(self):
        games = parse_pgn_text(PGN)
        corpus = build_corpus("alice", games)

        first = analyse_corpus(corpus, games, StubAnalyser())
        second = analyse_corpus(corpus, games, StubAnalyser())

        assert first == second

    def test_carries_the_clock_reading_through(self):
        games = parse_pgn_text(PGN)[:1]

        observations = analyse_corpus(build_corpus("alice", games), games, StubAnalyser())

        assert observations[0].clock_after == 600.0

    def test_identifies_the_mover(self):
        games = parse_pgn_text(PGN)[:1]

        observations = analyse_corpus(build_corpus("alice", games), games, StubAnalyser())

        assert observations[0].mover == "alice"
        assert observations[1].mover == "bob"


class TestIncrementInThinkingTime:
    """A move's cost is what the clock lost, plus what the increment gave back.

    Screen: docs/notes/experiments.e44-clock-on-noted-moves.md, question D16.

    `%clk` is written AFTER the increment is credited, so a raw difference of
    clock readings is `spent - increment`. Left uncorrected, a 3.5 s move on a
    180+2 game reads as 1.5 s and trips `INSTANT_MOVE_SECONDS`. 14.7 % of the
    peer corpus carries an increment, so this is a population-level error, not
    an edge case.
    """

    def test_a_game_without_increment_is_unchanged(self):
        move = an_observation(clock_before=100.0, clock_after=97.0, increment=0.0)

        assert move.seconds_spent == 3.0

    def test_the_increment_is_added_back(self):
        # The clock fell by 1 s, but 2 s were credited after the move, so the
        # player actually spent 3.
        move = an_observation(clock_before=100.0, clock_after=99.0, increment=2.0)

        assert move.seconds_spent == 3.0

    def test_a_considered_move_is_no_longer_read_as_instant(self):
        # The exact case from E44: 3.5 s of thought on a 180+2 game.
        move = an_observation(clock_before=100.0, clock_after=98.5, increment=2.0)

        assert move.seconds_spent == 3.5
        assert move.seconds_spent > INSTANT_MOVE_SECONDS

    def test_a_genuinely_instant_move_survives_the_correction(self):
        move = an_observation(clock_before=100.0, clock_after=100.0, increment=2.0)

        assert move.seconds_spent == 2.0
        assert move.seconds_spent <= INSTANT_MOVE_SECONDS

    def test_time_spent_is_never_negative(self):
        # A clock that gained more than the increment means a tag we cannot
        # trust; zero is honest where a negative number would be nonsense.
        move = an_observation(clock_before=100.0, clock_after=110.0, increment=2.0)

        assert move.seconds_spent == 0.0

    def test_no_clock_still_means_no_answer(self):
        assert an_observation(clock_before=None, clock_after=99.0, increment=2.0).seconds_spent is None
        assert an_observation(clock_before=100.0, clock_after=None, increment=2.0).seconds_spent is None


class TestIncrementFromTheTag:
    def test_reads_the_increment_from_a_time_control(self):
        assert increment_seconds("180+2") == 2.0
        assert increment_seconds("600+0") == 0.0

    def test_an_unreadable_or_absent_tag_is_no_increment(self):
        # Never None: an unknown increment must not silently disable the
        # correction for games that do have one, nor crash those that do not.
        assert increment_seconds(None) == 0.0
        assert increment_seconds("-") == 0.0
        assert increment_seconds("300+abc") == 0.0


class TestWhatThePlayerCouldHavePlayed:
    """The motifs the player could have executed by a move worth playing.

    `missed_motif` read `observation.best_move` alone, so a tactic second best
    by a hair was not a missed tactic and not even an opportunity -- it never
    reached the denominator. `allowed_motif` was rebuilt on *"not best, good
    enough"* and this side never was; the author confirmed the rule is
    symmetric.

    **The symmetry is in the mechanism, not only the rule.** This is
    `punishment.candidates_in` pointed one ply earlier: enumerate the moves that
    execute a motif -- `detect_motifs` removes 93 % of them for free -- and
    evaluate only those. The qualifying set is *"executes the motif and is worth
    playing"*, so enumerating every motif-executing move and testing each
    **cannot miss one**. Complete by construction, with no N to truncate and no
    completeness check to write, at a measured 1.52 evaluations per error
    position against MultiPV 3's 2.83x ([[design.multipv-candidate-moves]]).
    """

    # The scores that make ply 3 a blunder, copied from
    # `test_labels_an_error_when_the_evaluation_collapses` so both tests fail
    # together if the labelling changes.
    COLLAPSE = {0: 0, 1: 0, 2: 0, 3: -900, 4: -900}

    def _corpus(self):
        games = parse_pgn_text(PGN)[:1]
        return build_corpus("alice", games), games

    def test_an_error_is_asked_what_was_available(self):
        corpus, games = self._corpus()

        observations = analyse_corpus(corpus, games, StubAnalyser(scores=self.COLLAPSE))
        errored = [o for o in observations if o.label is not None]

        assert errored
        # A tuple either way: this position may offer no motif at all, and
        # "measured, found none" must not look like "never measured".
        assert isinstance(errored[0].available, tuple)

    def test_a_move_that_was_not_an_error_is_not_asked(self):
        """The cost argument: errors are about 4 % of moves, not all of them."""
        corpus, games = self._corpus()

        observations = analyse_corpus(corpus, games, StubAnalyser(scores=self.COLLAPSE))

        assert all(not o.available for o in observations if o.label is None)

    def test_it_asks_about_the_position_before_the_move(self):
        """These are the player's own alternatives, so they belong to the
        position as it stood -- not the one their move produced."""
        corpus, games = self._corpus()
        analyser = StubAnalyser(scores=self.COLLAPSE)

        observations = analyse_corpus(corpus, games, analyser)
        errored = [o for o in observations if o.label is not None][0]

        assert errored.fen_before in analyser.calls


class TestIsTheMovedPieceReallyWinnable:
    """`moved_into_attack` claims a piece can be won; the engine checks the claim.

    The author, on `Ng5` at tXOF3X1K#25:

    > *"Taking the knight would result in a forced checkmate for white, in this
    > case this was not the issue."*

    The detector is a static exchange count and cannot see that. Two cheaper
    answers were measured and **both were wrong**: the move's own cost (46 of 109
    costless firings were taken anyway) and a cost gate (the author's row cost
    1.8 wp). What answers it is the question `punishment.qualifying` asks of the
    opponent's replies -- **is capturing it worth playing?** On the author's row
    the only capture reaches 2.5 wp against a best of 79.3. Across 903 firings,
    **18.4 %** claim an attack whose best capture is not worth playing.

    This detector fires on any move, not only errors, so it cannot ride the
    error-only branch: about 64 engine calls per player.
    """

    WALK_IN = "4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1"   # Ra1-a4, the b5 pawn takes

    class ByPosition:
        """A stub whose evaluation depends on the position, not the ply."""

        engine_name = "stub"
        depth = 15

        def __init__(self, scores: dict[str, int], default: int = 0):
            self.scores = scores
            self.default = default

        def analyse(self, board):
            from chesscoach.analysis.cache import PositionEval

            return PositionEval(score_cp=self.scores.get(board.epd(), self.default))

    def _after(self, fen: str, uci: str) -> tuple[chess.Board, chess.Move]:
        board = chess.Board(fen)
        return board, chess.Move.from_uci(uci)

    def test_a_capture_as_good_as_the_best_makes_it_winnable(self):
        from chesscoach.analysis.core import _moved_piece_winnable

        board, move = self._after(self.WALK_IN, "a1a4")
        analyser = self.ByPosition({}, default=0)   # every position level

        assert _moved_piece_winnable(board, move, analyser) is True

    def test_a_capture_that_loses_for_the_capturer_is_not(self):
        """The author's shape: the capture exists and is terrible to play."""
        from chesscoach.analysis.core import _moved_piece_winnable

        board, move = self._after(self.WALK_IN, "a1a4")
        after = board.copy(stack=False)
        after.push(move)
        taken = after.copy(stack=False)
        taken.push(chess.Move.from_uci("b5a4"))
        # Black to move after Ra4 and level; after bxa4, White is winning outright.
        analyser = self.ByPosition({after.epd(): 0, taken.epd(): 900})

        assert _moved_piece_winnable(board, move, analyser) is False

    def test_a_move_the_detector_does_not_fire_on_is_not_asked(self):
        """None, not False: "not in question" must not read as "checked and
        safe", and it costs no engine call."""
        from chesscoach.analysis.core import _moved_piece_winnable

        board, move = self._after(self.WALK_IN, "a1a3")   # a3 is not attacked

        assert _moved_piece_winnable(board, move, self.ByPosition({})) is None
