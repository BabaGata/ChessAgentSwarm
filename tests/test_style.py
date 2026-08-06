"""V3 — style as measured tendency, and the things it refuses to say.

Screen: docs/notes/experiments.e14-style-dimensions.md
Definition: docs/notes/domain.coaching.md § 6

Two refusals carry this module and both are tested here: a tendency is **never a
finding**, so it cannot compete for one of a player's two priorities; and the
report **never says whether the tendency suits them**, because E14 measured that
and found players barely differ.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, Provenance
from chesscoach.sections.base import SectionContext
from chesscoach.style import (
    MIN_MOVES,
    NOTABLE_RATIO,
    TENDENCY,
    S10StyleTendencies,
    describe,
    queens_off,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-06")

WITH_QUEENS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
QUEENLESS = "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"


def an_observation(index: int, fen: str, mover: str = "alice") -> Observation:
    return Observation(
        game_id=f"g{index // 20}",
        ply=20 + index,
        mover=mover,
        mover_is_white=True,
        fen_before=fen,
        move_played="e2e4",
        best_move="e2e4",
        score_cp_before=0,
        score_cp_after=0,
        loss_wp=0.0,
        label=None,
        phase="opening_middlegame",
        played_best=True,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
    )


def moves(total: int, queenless: int, mover: str = "alice"):
    return tuple(
        an_observation(index, QUEENLESS if index < queenless else WITH_QUEENS, mover)
        for index in range(total)
    )


def a_context(observations, peers=None) -> SectionContext:
    return SectionContext(
        observations,
        Corpus(
            username="alice",
            corpus_id="c1",
            game_ids=tuple(sorted({o.game_id for o in observations})),
        ),
        PROVENANCE,
        band="1400-1800",
        time_control="rapid",
        peers=peers,
    )


def peers(rate: float = 0.28):
    from chesscoach.peers import ConditionMeasurement, build_reference

    key = Claim.of(kind=TENDENCY, subject="any").key()
    return build_reference(
        [
            (f"peer{n}", (ConditionMeasurement(key, round(rate * 1000), 1000, 20, 40),))
            for n in range(8)
        ],
        band="1400-1800",
        time_control="rapid",
        depth=15,
    )


class TestDetectingQueenlessPlay:
    def test_both_queens_gone(self):
        assert queens_off(QUEENLESS)

    def test_queens_on(self):
        assert not queens_off(WITH_QUEENS)

    def test_one_queen_left_is_not_queenless(self):
        assert not queens_off("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


class TestItIsNeverAFinding:
    """A tendency is not a weakness. Routing it through findings would set it
    competing for one of the player's two priorities."""

    def test_the_agent_emits_no_findings(self):
        agent = S10StyleTendencies()

        assert agent.findings(a_context(moves(400, 200))) == ()

    def test_and_its_report_is_empty(self):
        report = S10StyleTendencies().report(a_context(moves(400, 200)))

        assert report.findings == ()
        assert not report.insufficient_data

    def test_but_it_still_measures_for_the_peer_reference(self):
        # A preference means nothing without a population to be unusual against.
        measured = S10StyleTendencies().measure(a_context(moves(400, 200)))

        assert len(measured) == 1
        assert measured[0].instances == 200
        assert measured[0].opportunities == 400

    def test_no_moves_measures_nothing(self):
        assert S10StyleTendencies().measure(a_context(())) == ()


class TestDescribing:
    def test_a_player_who_steers_queenless_more_than_peers(self):
        tendency = describe(moves(400, 200), "alice", peers(0.28), "1400-1800", "rapid")

        assert tendency.share == pytest.approx(0.5)
        assert tendency.peer_share == pytest.approx(0.28, abs=0.01)
        assert tendency.direction == "more"
        assert tendency.notable

    def test_a_player_who_avoids_it(self):
        tendency = describe(moves(400, 20), "alice", peers(0.28), "1400-1800", "rapid")

        assert tendency.direction == "less"
        assert tendency.notable

    def test_a_player_in_the_middle_is_not_notable(self):
        tendency = describe(moves(400, 112), "alice", peers(0.28), "1400-1800", "rapid")

        assert not tendency.notable

    def test_too_few_moves_says_nothing(self):
        assert describe(moves(MIN_MOVES - 1, 50), "alice", peers(), "1400-1800", "rapid") is None

    def test_without_peers_it_says_nothing(self):
        # A share with nothing to compare it to is not a tendency.
        assert describe(moves(400, 200), "alice", None, "1400-1800", "rapid") is None

    def test_only_the_players_own_moves(self):
        mixed = moves(400, 200) + moves(400, 400, mover="bob")

        assert describe(mixed, "alice", peers(), "1400-1800", "rapid").moves == 400


class TestWhatTheReportSaysAndRefuses:
    def profile(self, share: float, peer: float = 0.28):
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef, StyleTendency

        return PlayerProfile(
            player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
            style=(StyleTendency(TENDENCY, share, peer, 400),),
        )

    def test_it_states_the_tendency(self):
        from chesscoach.explainer import render

        report = render(self.profile(0.50))

        assert "HOW YOU PLAY" in report
        assert "50% of your moves with the queens off, against 28%" in report

    def test_it_refuses_to_say_whether_it_suits_them(self):
        # The half a reader most wants, and the half E14 could not support.
        from chesscoach.explainer import render

        report = render(self.profile(0.50))

        assert "Nothing here says whether" in report
        assert "any answer would be invented" in report

    def test_it_is_not_called_a_strength_or_a_weakness(self):
        from chesscoach.explainer import render

        assert "not a strength or a weakness" in render(self.profile(0.50))

    def test_an_unremarkable_tendency_is_not_mentioned_at_all(self):
        from chesscoach.explainer import render

        assert "HOW YOU PLAY" not in render(self.profile(0.29))

    def test_a_profile_with_no_style_says_nothing(self):
        from chesscoach.explainer import render
        from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef

        bare = PlayerProfile(
            player=PlayerRef(source="lichess", username="alice"),
            corpus=CorpusRef(corpus_id="c1", n_games=24),
        )

        assert "HOW YOU PLAY" not in render(bare)


def test_the_notable_threshold_is_gentler_than_a_findings_margin():
    # Nothing is being prescribed, so the cost of mentioning a mild preference
    # is a sentence rather than a wasted training block.
    from chesscoach.confidence import FOCUS_MARGIN

    assert NOTABLE_RATIO < FOCUS_MARGIN


def test_style_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef, StyleTendency

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        style=(StyleTendency(TENDENCY, 0.5, 0.28, 400),),
    )

    assert from_dict(to_dict(profile)).style == profile.style
