"""S7 — material safety, the slot E10 emptied and E34 refilled.

Design: docs/notes/experiments.e34-material-causes.md · Answers D13.

S7 was *calculation quality*, screened and not built: the quiet-versus-forcing
contrast did not vary between players, and the rate that did correlated **+0.737**
with another error rate, so it restated how often the player went wrong at all.

E34 refills the slot on a different question — not *how deeply do you calculate*
but *did you check* — and the two claims here passed E10's own test to get in:

    moved_into_attack     r = +0.225 with the overall error rate
    miscounted_exchange   r = +0.123

Two candidates were refused for failing exactly where `missed_quiet` failed:
`left_hanging` at +0.917 and `ignored_threat` at +0.914. A player who errs more
has more loose pieces as a consequence, so those are the error rate renamed.

The section is unusual in two ways, both deliberate and both tested here: it
reads **the move the player actually played**, and it refuses to speak without a
population, because there is no meaningful within-player baseline for "was that
square safe".
"""

from __future__ import annotations

import chess

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.profile.models import Claim, ConfidenceTier, Provenance
from chesscoach.sections.base import SectionContext
from chesscoach.sections.s7_material_safety import (
    MISCOUNTED,
    MOVED_INTO_ATTACK,
    S7MaterialSafety,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-17")

# Rook on a1, black pawn on b5 covering a4. Ra4 walks into it; Ra3 does not.
WALK_IN = "4k3/8/8/1p6/8/8/8/R3K3 w - - 0 1"
# Black pawn a4 defended by b5: Rxa4 loses the rook for a pawn.
BAD_CAPTURE = "4k3/8/8/1p6/p7/8/8/R3K3 w - - 0 1"
# A free pawn on a4, nothing defending it.
GOOD_CAPTURE = "4k3/8/8/8/p7/8/8/R3K3 w - - 0 1"


def an_observation(game_id, ply, fen, move, *, erred=False, mover="alice", white=True):
    return Observation(
        game_id=game_id,
        ply=ply,
        mover=mover,
        mover_is_white=white,
        fen_before=fen,
        move_played=move,
        best_move="a1a3",
        score_cp_before=0,
        score_cp_after=0,
        loss_wp=25.0 if erred else 0.0,
        label=ErrorLabel.MISTAKE if erred else None,
        phase="opening_middlegame",
        played_best=False,
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


def games(count, fen=WALK_IN, move="a1a4", erred=False):
    return [
        an_observation(f"g{n}", 12, fen, move, erred=erred) for n in range(count)
    ]


def measured(observations, peers=None):
    return {m.claim_key: m for m in S7MaterialSafety().measure(a_context(observations, peers))}


def a_reference(rate: float, kind: str = MOVED_INTO_ATTACK):
    from chesscoach.peers import ConditionMeasurement, build_reference

    key = Claim.of(kind=kind, subject="own_move").key()
    return build_reference(
        [
            (f"peer{n}", (ConditionMeasurement(key, round(rate * 400), 400, 18, 40),))
            for n in range(8)
        ],
        band="1400-1800",
        time_control="rapid",
        depth=15,
    )


class TestItReadsThePlayedMove:
    def test_walking_a_piece_onto_a_covered_square_counts(self):
        result = measured(games(12))

        assert result[Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()].instances == 12

    def test_a_safe_square_does_not(self):
        result = measured(games(12, move="a1a3"))

        assert result[Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()].instances == 0

    def test_every_move_is_an_opportunity_to_walk_in(self):
        result = measured(games(12, move="a1a3"))

        assert result[Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()].opportunities == 12

    def test_only_captures_are_opportunities_to_miscount(self):
        # A quiet move cannot miscount an exchange, so it must not sit in the
        # denominator making the rate look better than it is.
        result = measured(games(12, move="a1a3"))

        assert result[Claim.of(kind=MISCOUNTED, subject="own_move").key()].opportunities == 0

    def test_a_losing_capture_counts_as_a_miscount(self):
        result = measured(games(12, fen=BAD_CAPTURE, move="a1a4"))
        key = Claim.of(kind=MISCOUNTED, subject="own_move").key()

        assert result[key].opportunities == 12
        assert result[key].instances == 12

    def test_a_winning_capture_does_not(self):
        result = measured(games(12, fen=GOOD_CAPTURE, move="a1a4"))
        key = Claim.of(kind=MISCOUNTED, subject="own_move").key()

        assert result[key].opportunities == 12
        assert result[key].instances == 0

    def test_the_two_claims_never_both_fire_on_one_move(self):
        # They prescribe different habits — "look at the square" against "count
        # the exchange" — so one move triggering both is contradictory advice.
        result = measured(games(12, fen=BAD_CAPTURE, move="a1a4"))

        walked = result[Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()].instances
        assert walked == 0


class TestCost:
    def test_only_punished_instances_carry_a_cost(self):
        # An unpunished walk into an attack is still a habit worth naming and it
        # cost nothing. Pricing it would inflate every ranking this claim enters.
        clean = measured(games(12))
        key = Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()

        assert clean[key].cost_wp == 0.0

    def test_a_punished_instance_is_priced(self):
        result = measured(games(12, erred=True))
        key = Claim.of(kind=MOVED_INTO_ATTACK, subject="own_move").key()

        assert result[key].cost_wp > 0


class TestItRefusesToSpeakWithoutAPopulation:
    def test_no_peers_means_no_finding(self):
        # There is no within-player baseline for "was that square safe" — no
        # other kind of square to compare against — so a claim without a
        # population would be comparing the player with nothing at all.
        report = S7MaterialSafety().report(a_context(games(30)))

        assert report.findings == ()
        assert report.sub_threshold == ()

    def test_with_a_low_population_rate_it_speaks(self):
        report = S7MaterialSafety().report(
            a_context(games(30), peers=a_reference(rate=0.02))
        )

        assert any(f.claim.kind == MOVED_INTO_ATTACK for f in report.findings)

    def test_a_player_at_the_population_rate_is_not_a_finding(self):
        report = S7MaterialSafety().report(
            a_context(games(30), peers=a_reference(rate=0.99))
        )
        asserted = [f for f in report.findings if f.claim.kind == MOVED_INTO_ATTACK]

        assert asserted == []

    def test_too_few_games_is_insufficient_data(self):
        report = S7MaterialSafety().report(
            a_context(games(4), peers=a_reference(rate=0.02))
        )

        assert report.insufficient_data is True


class TestWhatItReports:
    def report(self):
        return S7MaterialSafety().report(
            a_context(games(30, erred=True), peers=a_reference(rate=0.02))
        )

    def test_a_finding_cites_positions(self):
        finding = next(f for f in self.report().findings if f.claim.kind == MOVED_INTO_ATTACK)

        assert finding.evidence
        assert all(e.fen for e in finding.evidence)

    def test_the_evidence_says_what_went_wrong_on_that_move(self):
        finding = next(f for f in self.report().findings if f.claim.kind == MOVED_INTO_ATTACK)

        assert "could be won" in finding.evidence[0].note

    def test_it_carries_exposure_so_the_report_can_use_it(self):
        finding = next(f for f in self.report().findings if f.claim.kind == MOVED_INTO_ATTACK)

        assert finding.measurement.opportunities == 30

    def test_the_gap_type_stays_unknown(self):
        # "You did not check the square" and "you checked and misjudged it" look
        # identical in a game record and need different remedies. Only a probe
        # separates them, and guessing would be the folklore this project refuses.
        finding = next(f for f in self.report().findings if f.claim.kind == MOVED_INTO_ATTACK)

        assert finding.gap_type.hypothesis.value == "unknown"

    def test_sub_threshold_findings_keep_their_tier(self):
        report = S7MaterialSafety().report(
            a_context(games(30), peers=a_reference(rate=0.028))
        )

        for finding in report.sub_threshold:
            assert finding.confidence.tier is ConfidenceTier.WATCH
