"""S8 — attack and defence, and the king-safety measure under it.

Design: docs/notes/capacity.agents.s8-attack-and-defence.md

Two properties carry the section: the comparison runs across the **opponent's
reply**, and it counts the **crossing** into a real attack rather than the state
of being under one. Without the second, a single concession would be re-reported
on every move of the attack that followed.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.kingsafety import PRESSURE_ATTACKERS, allowed_pressure, king_zone, zone_attackers
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.sections.base import SectionContext
from chesscoach.sections.s8_attack_and_defence import ALLOWS_PRESSURE, KING, S8AttackAndDefence

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-05")

# White king on g1 with a normal shield; Black has nothing near it.
CALM = "4k3/8/8/8/8/8/5PPP/6K1 w - - 0 1"
# Three black pieces bearing on the g1 zone: queen h3, rook f8->f1 is blocked, so
# use queen h3, knight e2 and bishop a7.
ATTACKED = "4k3/b7/8/8/8/7q/4n1PP/6K1 w - - 0 1"


def a_board(fen: str) -> chess.Board:
    return chess.Board(fen)


class TestZone:
    def test_the_zone_is_the_king_and_its_neighbours(self):
        assert len(king_zone(a_board(CALM), chess.WHITE)) == 6  # g1 is on an edge

    def test_a_king_in_the_middle_has_the_full_ring(self):
        assert len(king_zone(a_board("4k3/8/8/3K4/8/8/8/8 w - - 0 1"), chess.WHITE)) == 9

    def test_a_calm_position_has_no_attackers(self):
        assert zone_attackers(a_board(CALM), chess.WHITE) == 0

    def test_attackers_are_counted_once_each(self):
        # A queen bearing on several zone squares is still one attacker.
        position = a_board("4k3/8/8/8/8/7q/5PPP/6K1 w - - 0 1")

        assert zone_attackers(position, chess.WHITE) == 1

    def test_it_counts_the_enemy_of_the_asked_colour(self):
        position = a_board(ATTACKED)

        assert zone_attackers(position, chess.WHITE) >= PRESSURE_ATTACKERS
        assert zone_attackers(position, chess.BLACK) == 0


class TestCrossing:
    def test_arriving_at_a_real_attack_counts(self):
        assert allowed_pressure(a_board(CALM), a_board(ATTACKED), chess.WHITE)

    def test_an_attack_that_was_already_there_does_not(self):
        # Otherwise one concession is re-reported on every move that follows it.
        assert not allowed_pressure(a_board(ATTACKED), a_board(ATTACKED), chess.WHITE)

    def test_a_little_pressure_is_not_an_attack(self):
        mild = "4k3/8/8/8/8/7q/5PPP/6K1 w - - 0 1"

        assert not allowed_pressure(a_board(CALM), a_board(mild), chess.WHITE)

    def test_the_opponents_king_is_not_the_players_problem(self):
        assert not allowed_pressure(a_board(CALM), a_board(ATTACKED), chess.BLACK)


def an_observation(
    game_id: str = "g1",
    ply: int = 12,
    fen: str = CALM,
    white: bool = True,
    mover: str = "alice",
    erred: bool = False,
) -> Observation:
    return Observation(
        game_id=game_id,
        ply=ply,
        mover=mover,
        mover_is_white=white,
        fen_before=fen,
        move_played="g1h1",
        best_move="g1h1",
        score_cp_before=0,
        score_cp_after=0,
        loss_wp=0.2 if erred else 0.0,
        label=ErrorLabel.MISTAKE if erred else None,
        phase="opening_middlegame",
        played_best=not erred,
        clock_before=None,
        clock_after=None,
        engine="stub",
        depth=15,
    )


def a_context(observations, peers=None) -> SectionContext:
    return SectionContext(
        tuple(observations),
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


def games(count: int, after: str = ATTACKED):
    observations = []
    for n in range(count):
        observations += [
            an_observation(game_id=f"g{n}", ply=12, fen=CALM),
            an_observation(game_id=f"g{n}", ply=13, fen=CALM, white=False, mover="bob"),
            an_observation(game_id=f"g{n}", ply=14, fen=after),
        ]
    return observations


def measured(observations, peers=None):
    return {m.claim_key: m for m in S8AttackAndDefence().measure(a_context(observations, peers))}


class TestCounting:
    def test_it_looks_through_the_opponents_reply(self):
        result = measured(games(12))

        assert result[Claim.of(kind=ALLOWS_PRESSURE, subject=KING).key()].instances == 12

    def test_a_quiet_game_is_counted_but_not_charged(self):
        result = measured(games(12, after=CALM))
        entry = result[Claim.of(kind=ALLOWS_PRESSURE, subject=KING).key()]

        assert entry.opportunities == 12
        assert entry.instances == 0

    def test_a_move_with_no_following_turn_is_skipped(self):
        assert measured([an_observation()]) == {}

    def test_only_the_players_own_moves(self):
        observations = games(12)
        observations.append(an_observation(game_id="g0", ply=20, mover="bob", white=False))

        result = measured(observations)

        assert result[Claim.of(kind=ALLOWS_PRESSURE, subject=KING).key()].opportunities == 12

    def test_nothing_is_measured_when_no_move_qualifies(self):
        assert S8AttackAndDefence().measure(a_context([an_observation()])) == ()


class TestReporting:
    def peers(self, rate: float = 0.019):
        from chesscoach.peers import ConditionMeasurement, build_reference

        key = Claim.of(kind=ALLOWS_PRESSURE, subject=KING).key()
        return build_reference(
            [
                (f"peer{n}", (ConditionMeasurement(key, round(rate * 600), 600, 20, 40),))
                for n in range(8)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_too_few_games_is_insufficient_data(self):
        report = S8AttackAndDefence().report(a_context(games(3)))

        assert report.insufficient_data

    def test_no_peers_means_no_findings(self):
        report = S8AttackAndDefence().report(a_context(games(20)))

        assert report.findings == ()

    def test_zero_findings_is_valid(self):
        report = S8AttackAndDefence().report(
            a_context(games(20, after=CALM), peers=self.peers())
        )

        assert report.findings == ()
        assert not report.insufficient_data

    def test_an_unusual_player_is_reported(self):
        report = S8AttackAndDefence().report(a_context(games(20), peers=self.peers()))

        assert report.findings

    def test_the_gap_type_is_honestly_unknown(self):
        # Inviting an attack can be provocation or oversight; the position does
        # not say which.
        report = S8AttackAndDefence().report(a_context(games(20), peers=self.peers()))
        gap = report.findings[0].gap_type

        assert gap.hypothesis is GapTypeHypothesis.UNKNOWN
        assert gap.determined_by is DeterminedBy.INFERRED

    def test_evidence_offers_no_better_move(self):
        report = S8AttackAndDefence().report(a_context(games(20), peers=self.peers()))

        assert all(e.better_move is None for e in report.findings[0].evidence)

    def test_evidence_is_spread_across_games(self):
        report = S8AttackAndDefence().report(a_context(games(20), peers=self.peers()))
        evidence = report.findings[0].evidence

        assert len({e.game_id for e in evidence}) == len(evidence)

    def test_only_ever_one_claim(self):
        # No subdivision: ~10 instances per player leaves nothing to split with.
        report = S8AttackAndDefence().report(a_context(games(20), peers=self.peers()))

        assert len(report.findings) == 1


@pytest.mark.parametrize("colour", [chess.WHITE, chess.BLACK])
def test_the_measure_works_from_either_side(colour):
    white = colour == chess.WHITE
    calm = CALM if white else "6k1/5ppp/8/8/8/8/8/4K3 b - - 0 1"
    # The true vertical mirror of ATTACKED. The old one was not: its knight
    # stood on e6 blocking its own bishop, and the g/h pawns had changed colour,
    # so only two pieces bore on the king and the attack rested on the pawns.
    attacked = ATTACKED if white else "6k1/4N1pp/7Q/8/8/8/B7/4K3 b - - 0 1"

    assert allowed_pressure(a_board(calm), a_board(attacked), colour)
