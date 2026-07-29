"""The analysis core, driven by a stub analyser so no engine is required.

The core's job is to turn a corpus into typed observations. Injecting the
analyser keeps that logic testable, deterministic and fast -- and it is the same
seam a parallel implementation will later use.
"""

from __future__ import annotations

import chess

from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.labels import ErrorLabel
from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import parse_pgn_text

from test_ingest import PGN


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
