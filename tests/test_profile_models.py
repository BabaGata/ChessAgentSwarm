"""Profile model invariants: deterministic identity, immutability, validation."""

from __future__ import annotations

import pytest

from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    Provenance,
)


def a_claim(**overrides) -> Claim:
    defaults = dict(kind="missed_motif", subject="fork", direction="own", context={"phase": "middlegame"})
    return Claim.of(**{**defaults, **overrides})


def a_finding(**overrides) -> Finding:
    defaults = dict(
        section="S1",
        claim=a_claim(),
        measurement=Measurement(instances=14, distinct_games=9, games_with_data=47, rate=0.19),
        provenance=Provenance(engine="Stockfish 18", depth=15, corpus_id="abc", analysed_at="2026-07-28"),
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True, reasons=("distinct_games>=5",)),
        gap_type=GapType(hypothesis=GapTypeHypothesis.SKILL, determined_by=DeterminedBy.PROBED),
        evidence=(Evidence(game_id="g1", ply=47, fen="8/8/8/8/8/8/8/K6k w - - 0 1", loss_wp=34.2),),
    )
    return Finding(**{**defaults, **overrides})


class TestClaimIdentity:
    def test_key_is_deterministic(self):
        assert a_claim().key() == a_claim().key()

    def test_context_order_does_not_change_the_key(self):
        one = a_claim(context={"phase": "middlegame", "time_control": "rapid"})
        other = a_claim(context={"time_control": "rapid", "phase": "middlegame"})

        assert one.key() == other.key()

    def test_different_context_is_a_different_claim(self):
        # E03: relevance is conditional, so context is part of the claim's identity.
        middlegame = a_claim(context={"phase": "middlegame"})
        endgame = a_claim(context={"phase": "endgame"})

        assert middlegame.key() != endgame.key()

    def test_direction_is_part_of_the_claim(self):
        assert a_claim(direction="own").key() != a_claim(direction="opponent").key()


class TestFindingIdentity:
    def test_id_is_derived_from_section_and_claim(self):
        assert a_finding().id == f"S1.{a_claim().key()}"

    def test_same_inputs_give_the_same_id(self):
        assert a_finding().id == a_finding().id


class TestImmutability:
    def test_a_finding_cannot_be_mutated(self):
        with pytest.raises(Exception):
            a_finding().section = "S2"

    def test_status_change_returns_a_new_finding(self):
        original = a_finding()

        updated = original.with_status("addressed")

        assert original.status == "candidate"
        assert updated.status == "addressed"
        assert updated.id == original.id


class TestValidation:
    def test_rejects_a_finding_with_no_evidence(self):
        # V8: a claim without positions attached cannot be made.
        with pytest.raises(ValueError, match="evidence"):
            a_finding(evidence=())

    def test_rejects_a_nonsensical_depth(self):
        with pytest.raises(ValueError, match="depth"):
            a_finding(
                provenance=Provenance(engine="x", depth=0, corpus_id="a", analysed_at="2026-07-28")
            )

    def test_rejects_more_distinct_games_than_instances(self):
        with pytest.raises(ValueError, match="distinct_games"):
            a_finding(
                measurement=Measurement(instances=2, distinct_games=5, games_with_data=40, rate=0.1)
            )

    def test_rejects_a_rate_outside_zero_to_one(self):
        with pytest.raises(ValueError, match="rate"):
            a_finding(
                measurement=Measurement(instances=5, distinct_games=5, games_with_data=40, rate=1.4)
            )


class TestMeasurement:
    def test_computes_a_wilson_interval_when_not_supplied(self):
        measurement = Measurement(instances=9, distinct_games=9, games_with_data=47, rate=0.19)

        low, high = measurement.ci95

        assert 0.0 <= low < 0.19 < high <= 1.0

    def test_peer_lift_is_none_without_a_peer_rate(self):
        assert Measurement(instances=9, distinct_games=9, games_with_data=47, rate=0.19).lift_vs_peer is None

    def test_peer_lift_compares_against_the_reference_population(self):
        measurement = Measurement(
            instances=9, distinct_games=9, games_with_data=47, rate=0.20, peer_rate=0.10
        )

        assert measurement.lift_vs_peer == pytest.approx(2.0)
