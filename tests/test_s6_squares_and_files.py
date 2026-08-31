"""S6 — squares and files.

Design: docs/notes/capacity.agents.s6-squares-and-files.md

The property that matters is the **window**: what a player concedes is realised
on the opponent's reply, so the comparison runs from the player's move to their
*next* move. E09's first pass compared across the player's own move and reported
both rates as zero — wrong, not interesting.
"""

from __future__ import annotations

import chess

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, DeterminedBy, GapTypeHypothesis, Provenance
from chesscoach.sections.base import SectionContext
from chesscoach.sections.s6_squares_and_files import ALLOWS, S6SquaresAndFiles
from chesscoach.squares import OUTPOST, ROOK_SEVENTH

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-05")

# Closed boards. `rook_seventh` now refuses to fire when three or more files
# are open, because the author's correction is that a rook nobody could have
# stopped is not a finding -- so a bare board would test the screen rather than
# the claim. No white pawn on the c- or e-file, so d3 stays a real outpost.
QUIET = "4k3/pppppppp/8/8/4p3/8/P2P1PPP/4K3 w - - 0 1"
KNIGHT_SETTLED = "4k3/pppppppp/8/8/4p3/3n4/P2P1PPP/4K3 w - - 0 1"
ROOK_ARRIVED = "4k3/pppppppp/8/8/4p3/8/Pr1P1PPP/4K3 w - - 0 1"


def an_observation(
    game_id: str = "g1",
    ply: int = 12,
    fen: str = QUIET,
    white: bool = True,
    mover: str = "alice",
) -> Observation:
    return Observation(
        game_id=game_id,
        ply=ply,
        mover=mover,
        mover_is_white=white,
        fen_before=fen,
        move_played="e1e2",
        best_move="e1e2",
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


def a_turn(game_id: str, ply: int, before: str, after: str):
    """The player's move, the opponent's reply, and the player's next turn.

    The third observation is what carries the position the comparison ends at.
    """
    return [
        an_observation(game_id=game_id, ply=ply, fen=before),
        an_observation(game_id=game_id, ply=ply + 1, fen=before, white=False, mover="bob"),
        an_observation(game_id=game_id, ply=ply + 2, fen=after),
    ]


def games(count: int, after: str = KNIGHT_SETTLED):
    observations = []
    for n in range(count):
        observations += a_turn(f"g{n}", 12, QUIET, after)
    return observations


def measured(observations, peers=None):
    return {m.claim_key: m for m in S6SquaresAndFiles().measure(a_context(observations, peers))}


class TestTheWindow:
    def test_it_looks_through_the_opponents_reply(self):
        result = measured(games(12, after=KNIGHT_SETTLED))

        assert result[Claim.of(kind=ALLOWS, subject=OUTPOST).key()].instances == 12

    def test_a_rook_arriving_is_caught_too(self):
        result = measured(games(12, after=ROOK_ARRIVED))

        assert result[Claim.of(kind=ALLOWS, subject=ROOK_SEVENTH).key()].instances == 12

    def test_nothing_conceded_is_counted_but_not_charged(self):
        result = measured(games(12, after=QUIET))
        key = Claim.of(kind=ALLOWS, subject=OUTPOST).key()

        assert result[key].opportunities == 12
        assert result[key].instances == 0

    def test_a_move_with_no_following_turn_is_skipped(self):
        # Nothing to compare against; guessing would invent a concession.
        assert measured([an_observation(game_id="g1", ply=12)]) == {}

    def test_only_the_players_own_moves(self):
        observations = games(12)
        observations.append(
            an_observation(game_id="g0", ply=20, mover="bob", white=False)
        )

        result = measured(observations)

        assert result[Claim.of(kind=ALLOWS, subject=OUTPOST).key()].opportunities == 12


class TestTheAggregate:
    def test_any_fires_when_a_feature_does(self):
        result = measured(games(12))

        assert result[Claim.of(kind=ALLOWS, subject="any").key()].instances == 12

    def test_any_shares_the_denominator(self):
        result = measured(games(12))
        pooled = result[Claim.of(kind=ALLOWS, subject="any").key()]
        specific = result[Claim.of(kind=ALLOWS, subject=ROOK_SEVENTH).key()]

        assert pooled.opportunities == specific.opportunities


class TestReporting:
    def peers(self, rate: float = 0.008):
        from chesscoach.peers import ConditionMeasurement, build_reference

        keys = [
            Claim.of(kind=ALLOWS, subject=s).key() for s in ("any", OUTPOST, ROOK_SEVENTH)
        ]
        return build_reference(
            [
                (
                    f"peer{n}",
                    tuple(ConditionMeasurement(k, round(rate * 600), 600, 20, 40) for k in keys),
                )
                for n in range(8)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def test_too_few_games_is_insufficient_data(self):
        report = S6SquaresAndFiles().report(a_context(games(3)))

        assert report.insufficient_data

    def test_no_peers_means_no_findings(self):
        report = S6SquaresAndFiles().report(a_context(games(20)))

        assert report.findings == ()

    def test_zero_findings_is_valid(self):
        report = S6SquaresAndFiles().report(
            a_context(games(20, after=QUIET), peers=self.peers())
        )

        assert report.findings == ()
        assert not report.insufficient_data

    def test_an_unusual_player_is_reported(self):
        report = S6SquaresAndFiles().report(a_context(games(20), peers=self.peers()))

        assert report.findings

    def test_the_gap_type_is_honestly_unknown(self):
        report = S6SquaresAndFiles().report(a_context(games(20), peers=self.peers()))
        gap = report.findings[0].gap_type

        assert gap.hypothesis is GapTypeHypothesis.UNKNOWN
        assert gap.determined_by is DeterminedBy.INFERRED

    def test_evidence_offers_no_better_move(self):
        # As in S5: nothing here establishes the concession was the error.
        report = S6SquaresAndFiles().report(a_context(games(20), peers=self.peers()))

        assert all(e.better_move is None for e in report.findings[0].evidence)

    def test_evidence_is_spread_across_games(self):
        report = S6SquaresAndFiles().report(a_context(games(20), peers=self.peers()))
        evidence = report.findings[0].evidence

        assert len({e.game_id for e in evidence}) == len(evidence)


def test_it_works_from_the_black_side():
    white_knight_settled = "4k3/8/3N4/4P3/8/8/8/4K3 b - - 0 1"
    quiet_for_black = "4k3/8/8/4P3/8/8/8/4K3 b - - 0 1"

    observations = []
    for n in range(12):
        observations += [
            an_observation(game_id=f"g{n}", ply=12, fen=quiet_for_black, white=False),
            an_observation(game_id=f"g{n}", ply=13, fen=quiet_for_black, mover="bob"),
            an_observation(game_id=f"g{n}", ply=14, fen=white_knight_settled, white=False),
        ]

    result = measured(observations)

    assert result[Claim.of(kind=ALLOWS, subject=OUTPOST).key()].instances == 12
