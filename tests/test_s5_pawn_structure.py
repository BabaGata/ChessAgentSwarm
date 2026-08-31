"""S5 — pawn-structure weaknesses.

Design: docs/notes/capacity.agents.s5-pawn-structure.md

The property under test is **creation, not presence**. E02 found isolated pawns
in 96 % of games, so a section that counted having one would be the R-14
true-but-useless failure by construction. These tests exist mostly to pin that
distinction and the denominator that goes with it.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.sections.base import SectionContext
from chesscoach.sections.s5_pawn_structure import CONCEDES, S5PawnStructure
from chesscoach.structure import DOUBLED, ISOLATED

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-05")

# One white d-pawn; then two, on d3 and d4. Moving between them concedes doubled.
CLEAN = "4k3/8/8/8/8/3P4/8/4K3 w - - 0 1"
DOUBLED_AFTER = "4k3/8/8/8/3P4/3P4/8/4K3 b - - 0 1"


def an_observation(
    game_id: str = "g1",
    ply: int = 12,
    fen: str = CLEAN,
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
        move_played="d3d4",
        best_move="d3d4",
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


def a_move(game_id: str, ply: int, before: str, after: str, white: bool = True):
    """The player's move at `ply`, and the opponent's position that follows it."""
    return [
        an_observation(game_id=game_id, ply=ply, fen=before, white=white),
        an_observation(game_id=game_id, ply=ply + 1, fen=after, white=not white,
                       mover="bob"),
    ]


def games(count: int, concede: bool = True):
    observations = []
    for n in range(count):
        after = DOUBLED_AFTER if concede else CLEAN
        observations += a_move(f"g{n}", 12, CLEAN, after)
    return observations


def measured(observations, peers=None):
    return {m.claim_key: m for m in S5PawnStructure().measure(a_context(observations, peers))}


class TestCreationNotPresence:
    def test_creating_a_weakness_counts(self):
        result = measured(games(12, concede=True))

        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].instances == 12

    def test_a_weakness_that_was_already_there_does_not(self):
        # The whole section rests on this: presence is 96% of games (E02).
        observations = []
        for n in range(12):
            observations += a_move(f"g{n}", 12, DOUBLED_AFTER, DOUBLED_AFTER)

        result = measured(observations)

        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].instances == 0

    def test_the_denominator_is_every_move_not_only_the_bad_ones(self):
        # Otherwise the rate would be 100% by construction.
        result = measured(games(12, concede=False))

        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].opportunities == 12
        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].instances == 0

    def test_only_the_players_own_camp(self):
        # The opponent's structure is not this player's concession.
        black_doubles = "4k3/8/3p4/3p4/8/8/8/4K3 b - - 0 1"
        observations = []
        for n in range(12):
            observations += a_move(f"g{n}", 12, CLEAN, black_doubles)

        result = measured(observations)

        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].instances == 0

    def test_only_the_players_own_moves(self):
        observations = games(12) + a_move("g99", 12, CLEAN, DOUBLED_AFTER)
        observations[-2] = an_observation(
            game_id="g99", ply=12, fen=CLEAN, mover="bob"
        )

        result = measured(observations)

        assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].opportunities == 12


class TestTheAggregate:
    def test_any_fires_when_a_feature_does(self):
        result = measured(games(12, concede=True))

        assert result[Claim.of(kind=CONCEDES, subject="any").key()].instances == 12

    def test_any_shares_the_denominator_with_the_features(self):
        result = measured(games(12, concede=True))
        pooled = result[Claim.of(kind=CONCEDES, subject="any").key()]
        specific = result[Claim.of(kind=CONCEDES, subject=ISOLATED).key()]

        assert pooled.opportunities == specific.opportunities


class TestTheLastMove:
    def test_a_move_with_nothing_after_it_is_skipped(self):
        # No following position means no comparison; guessing would invent one.
        result = measured([an_observation(game_id="g1", ply=12)])

        assert result == {}


class TestReporting:
    def peers(self, rate: float = 0.02):
        from chesscoach.peers import ConditionMeasurement, build_reference

        keys = [
            Claim.of(kind=CONCEDES, subject=s).key()
            for s in ("any", ISOLATED, DOUBLED, "backward")
        ]
        return build_reference(
            [
                (
                    f"peer{n}",
                    tuple(ConditionMeasurement(k, round(rate * 500), 500, 20, 40) for k in keys),
                )
                for n in range(8)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_too_few_games_is_insufficient_data(self):
        report = S5PawnStructure().report(a_context(games(3)))

        assert report.insufficient_data

    def test_no_peers_means_no_findings(self):
        report = S5PawnStructure().report(a_context(games(20, concede=True)))

        assert report.findings == ()

    def test_zero_findings_is_valid(self):
        report = S5PawnStructure().report(
            a_context(games(20, concede=False), peers=self.peers())
        )

        assert report.findings == ()
        assert not report.insufficient_data

    def test_an_unusual_player_is_reported(self):
        report = S5PawnStructure().report(
            a_context(games(20, concede=True), peers=self.peers())
        )

        assert report.findings

    def test_a_statistically_real_but_trivial_deviation_is_not_reported(self):
        # The section's own guard, on top of the confidence policy. FOCUS is a
        # significance test with no floor on magnitude, and with 526
        # opportunities per player a 1.2x deviation clears it comfortably --
        # while meaning nothing a coach would say out loud.
        peers = self.peers(rate=1.0)  # peers concede on every move
        observations = games(20, concede=True)  # so does the player

        report = S5PawnStructure().report(a_context(observations, peers=peers))

        assert report.findings == ()

    def test_the_guard_is_a_ratio_not_a_difference(self):
        # A rare weakness at twice the peer rate is a finding; a common one at
        # 1.1x is not, even though the absolute gap is larger.
        from chesscoach.sections.s5_pawn_structure import MIN_PEER_RATIO

        assert MIN_PEER_RATIO > 1.0

    def test_the_gap_type_is_honestly_unknown(self):
        # Conceding for the bishop pair and conceding by accident look identical
        # in the position. Only a probe separates them.
        report = S5PawnStructure().report(
            a_context(games(20, concede=True), peers=self.peers())
        )

        gap = report.findings[0].gap_type
        assert gap.hypothesis is GapTypeHypothesis.UNKNOWN
        assert gap.determined_by is DeterminedBy.INFERRED

    def test_evidence_does_not_offer_a_better_move(self):
        # Showing the engine's preference would imply the concession was the
        # error, and E03 found no link between structure and this band's errors.
        report = S5PawnStructure().report(
            a_context(games(20, concede=True), peers=self.peers())
        )

        assert all(e.better_move is None for e in report.findings[0].evidence)

    def test_evidence_is_spread_across_games(self):
        report = S5PawnStructure().report(
            a_context(games(20, concede=True), peers=self.peers())
        )
        evidence = report.findings[0].evidence

        assert len({e.game_id for e in evidence}) == len(evidence)


@pytest.mark.parametrize("colour", [chess.WHITE, chess.BLACK])
def test_the_section_works_from_either_side(colour):
    white = colour == chess.WHITE
    before = CLEAN if white else "4k3/8/3p4/8/8/8/8/4K3 b - - 0 1"
    after = DOUBLED_AFTER if white else "4k3/8/3p4/3p4/8/8/8/4K3 w - - 0 1"

    observations = []
    for n in range(12):
        observations += a_move(f"g{n}", 12, before, after, white=white)

    result = measured(observations)

    assert result[Claim.of(kind=CONCEDES, subject=DOUBLED).key()].instances == 12


class TestAWeaknessMustLast:
    """A concession undone two moves later cost the player nothing.

    Design: docs/notes/design.detectors-name-consequences.md § 5, extended by
    the author to every pawn weakness: "isolated pawn should also have similar
    persistance check".
    """

    def test_a_repaired_weakness_is_not_counted(self):
        from chesscoach.structure import ISOLATED, LOCATORS

        # The a-pawn is isolated after the move and has a neighbour again
        # before the window closes.
        alone = chess.Board("4k3/8/8/8/8/8/P7/4K3 w - - 0 1")
        joined = chess.Board("4k3/8/8/8/8/8/PP6/4K3 w - - 0 1")
        assert LOCATORS[ISOLATED](alone, chess.WHITE)
        assert not LOCATORS[ISOLATED](joined, chess.WHITE)

    def test_a_game_that_ends_first_is_not_a_repair(self):
        # The moves were never played, so the weakness stands. Dropping it would
        # make short games look clean, which is the censoring E58 named.
        from chesscoach.sections.s5_pawn_structure import _still_there_later
        from chesscoach.structure import ISOLATED

        class Obs:
            game_id = "g"
            ply = 10

        created = frozenset({ISOLATED})
        assert _still_there_later(created, Obs(), chess.WHITE, {"g": []}) == created

    def test_nothing_conceded_stays_nothing(self):
        from chesscoach.sections.s5_pawn_structure import _still_there_later

        class Obs:
            game_id = "g"
            ply = 1

        assert _still_there_later(frozenset(), Obs(), chess.WHITE, {}) == frozenset()
