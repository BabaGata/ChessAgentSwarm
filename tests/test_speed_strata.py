"""Step 5 — pooling evidence across speeds without blending the comparison.

Spec: docs/notes/design.short-history-prioritisation.md § layer 1, and
      docs/notes/experiments.e19-blitz-stratum.md

E19 settled the shape: blitz predicts a player's rapid behaviour as well as rapid
predicts itself (93 % of the reliability ceiling), so the two speeds measure the
same thing and their **evidence** may be pooled. Their **rates** may not be
compared across speeds — E01's finding, unchanged — because a blitz move and a
rapid move do not go wrong equally often (1.06x, and larger at constant
opposition).

The resolution is direct standardisation: the player's rate is pooled, and the
baseline is rebuilt for **the speed mix this player actually plays**. Someone who
plays three blitz games for every rapid one is compared against what peers do at
that mix, not against a rapid-only population.

Weighted by *games* rather than by opportunities, which is an approximation: it
assumes a game offers about as many chances to go wrong at either speed. Stated
rather than hidden, and cheap to revisit if a section ever tracks its
opportunities per speed.
"""

from __future__ import annotations

import pytest

from chesscoach.ingest.corpus import build_corpus
from chesscoach.ingest.pgn import GameRecord
from chesscoach.speed import BLITZ, BULLET, CLASSICAL, RAPID, speed_class

BAND = "1400-1800"


class TestNamingTheSpeed:
    """Lichess classifies by estimated duration: initial + 40 x increment."""

    @pytest.mark.parametrize(
        "control,expected",
        [
            ("600+0", RAPID),       # 600s, the corpus's most common control
            ("900+10", RAPID),      # 1300s
            ("1800+0", CLASSICAL),  # 1800s
            ("300+0", BLITZ),       # 300s
            ("180+2", BLITZ),       # 260s -- the author's 3+2 example
            ("300+5", RAPID),       # 500s: increment lifts it over the line
            ("60+0", BULLET),       # 60s
            ("120+1", BULLET),      # 160s
        ],
    )
    def test_the_thresholds_are_lichess_thresholds(self, control, expected):
        assert speed_class(control) == expected

    def test_the_boundaries_land_on_the_documented_side(self):
        assert speed_class("479+0") == BLITZ
        assert speed_class("480+0") == RAPID
        assert speed_class("1499+0") == RAPID
        assert speed_class("1500+0") == CLASSICAL

    @pytest.mark.parametrize("control", [None, "", "-", "unlimited", "nonsense"])
    def test_an_unreadable_control_has_no_speed(self, control):
        assert speed_class(control) is None


def a_game(game_id: str, time_control: str, white: str = "alice") -> GameRecord:
    return GameRecord(
        game_id=game_id,
        white=white,
        black="bob",
        result="1-0",
        moves=("e2e4", "e7e5"),
        clocks=(600.0, 600.0),
        time_control=time_control,
    )


class TestTheCorpusKnowsItsMix:
    def test_one_speed_is_the_whole_mix(self):
        corpus = build_corpus("alice", [a_game("g1", "600+0"), a_game("g2", "600+0")])

        assert corpus.speed_mix == ((RAPID, 1.0),)

    def test_a_mixed_corpus_is_split_by_share_of_games(self):
        games = [a_game("g1", "600+0"), a_game("g2", "180+2"), a_game("g3", "180+2")]

        mix = dict(build_corpus("alice", games).speed_mix)

        assert mix[BLITZ] == pytest.approx(2 / 3)
        assert mix[RAPID] == pytest.approx(1 / 3)

    def test_the_shares_sum_to_one(self):
        games = [a_game(f"g{i}", c) for i, c in enumerate(["600+0", "180+2", "60+0", "1800+0"])]

        assert sum(share for _, share in build_corpus("alice", games).speed_mix) == pytest.approx(1.0)

    def test_games_with_no_readable_control_are_left_out_of_the_mix(self):
        games = [a_game("g1", "600+0"), a_game("g2", "unlimited")]

        assert build_corpus("alice", games).speed_mix == ((RAPID, 1.0),)

    def test_a_corpus_with_no_readable_controls_has_no_mix(self):
        assert build_corpus("alice", [a_game("g1", "unlimited")]).speed_mix == ()

    def test_it_is_ordered_so_a_corpus_id_is_reproducible(self):
        first = build_corpus("alice", [a_game("g1", "180+2"), a_game("g2", "600+0")])
        second = build_corpus("alice", [a_game("g2", "600+0"), a_game("g1", "180+2")])

        assert first.speed_mix == second.speed_mix


# The example claim is `allowed_motif.hangingPiece`, and it has to be one that
# **separates players**: `peer_rate` returns None for a claim in
# `chesscoach.separation.DOES_NOT_SEPARATE`, so a registered claim would make
# every assertion here read None whatever the speed mixture did. These tests are
# about the mixture, not about the claim; `missed_motif.pin` was used until the
# register was regenerated against the corrected detectors and it became flat.
class TestTheBaselineFollowsTheMix:
    def reference(self, rapid_rate: float, blitz_rate: float):
        from chesscoach.peers import ConditionMeasurement, build_reference

        def measurement(rate):
            return (
                ConditionMeasurement(
                    claim_key="allowed_motif.hangingPiece.own",
                    instances=int(rate * 1000),
                    opportunities=1000,
                    distinct_games=10,
                    games_with_data=40,
                ),
            )

        rapid = build_reference(
            [("bob", measurement(rapid_rate)), ("carol", measurement(rapid_rate))],
            band=BAND, time_control=RAPID, depth=15,
        )
        blitz = build_reference(
            [("bob", measurement(blitz_rate)), ("carol", measurement(blitz_rate))],
            band=BAND, time_control=BLITZ, depth=15,
        )
        return rapid.merged_with(blitz)

    def context(self, games, peers):
        from chesscoach.profile.models import Provenance
        from chesscoach.sections.base import SectionContext

        corpus = build_corpus("alice", games)
        return SectionContext(
            observations=(),
            corpus=corpus,
            provenance=Provenance(
                engine="stub", depth=15, corpus_id=corpus.corpus_id, analysed_at="2026-08-06"
            ),
            band=BAND,
            time_control=RAPID,
            peers=peers,
        )

    def test_an_all_rapid_player_gets_the_rapid_rate(self):
        context = self.context([a_game("g1", "600+0")], self.reference(0.10, 0.30))

        assert context.peer_rate("allowed_motif.hangingPiece.own") == pytest.approx(0.10)

    def test_an_all_blitz_player_gets_the_blitz_rate(self):
        # The whole point: a blitz player is not judged against rapid peers.
        context = self.context([a_game("g1", "180+2")], self.reference(0.10, 0.30))

        assert context.peer_rate("allowed_motif.hangingPiece.own") == pytest.approx(0.30)

    def test_a_mixed_player_gets_the_mixture(self):
        games = [a_game("g1", "600+0"), a_game("g2", "180+2")]

        context = self.context(games, self.reference(0.10, 0.30))

        assert context.peer_rate("allowed_motif.hangingPiece.own") == pytest.approx(0.20)

    def test_a_speed_the_population_has_never_played_is_skipped(self):
        # Bullet has no cell here. The player's other games still get a
        # comparison rather than the claim going silent.
        games = [a_game("g1", "600+0"), a_game("g2", "60+0")]

        context = self.context(games, self.reference(0.10, 0.30))

        assert context.peer_rate("allowed_motif.hangingPiece.own") == pytest.approx(0.10)

    def test_no_speed_the_population_knows_means_no_comparison(self):
        context = self.context([a_game("g1", "60+0")], self.reference(0.10, 0.30))

        assert context.peer_rate("allowed_motif.hangingPiece.own") is None

    def test_a_corpus_without_controls_falls_back_to_the_stated_time_control(self):
        # Every test fixture in this project builds games without a TimeControl
        # tag; they must keep behaving exactly as before.
        context = self.context(
            [GameRecord(
                game_id="g1", white="alice", black="bob", result="1-0",
                moves=("e2e4",), clocks=(None,),
            )],
            self.reference(0.10, 0.30),
        )

        assert context.peer_rate("allowed_motif.hangingPiece.own") == pytest.approx(0.10)
