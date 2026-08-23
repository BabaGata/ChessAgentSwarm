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
