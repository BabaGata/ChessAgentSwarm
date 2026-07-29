"""Scoring an agent against a planted weakness.

Two questions carry equal weight: did it find the planted flaw, and did it
refrain from inventing others? A detector that reports everything finds every
planted weakness and is useless.
"""

from __future__ import annotations

from chesscoach.evaluation.planted import WeaknessSpec
from chesscoach.evaluation.scoring import matches_spec, score_findings
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


def a_finding(kind: str = "time_pressure_error", subject: str = "clock", **overrides) -> Finding:
    defaults = dict(
        section="S2",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(instances=9, distinct_games=7, games_with_data=30, rate=0.23),
        provenance=Provenance(engine="stub", depth=15, corpus_id="c", analysed_at="2026-07-28"),
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.PROCESS, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=41, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )
    return Finding(**{**defaults, **overrides})


TIME_SPEC = WeaknessSpec(kind="time_pressure", severity=0.8, threshold_seconds=60.0)
PHASE_SPEC = WeaknessSpec(kind="phase", severity=0.8, phase="endgame")


class TestMatching:
    def test_a_time_pressure_finding_matches_a_time_pressure_plant(self):
        assert matches_spec(a_finding(kind="time_pressure_error"), TIME_SPEC) is True

    def test_an_unrelated_finding_does_not_match(self):
        assert matches_spec(a_finding(kind="missed_motif", subject="fork"), TIME_SPEC) is False

    def test_a_phase_finding_must_name_the_planted_phase(self):
        assert matches_spec(a_finding(kind="phase_error_excess", subject="endgame"), PHASE_SPEC)
        assert not matches_spec(a_finding(kind="phase_error_excess", subject="opening"), PHASE_SPEC)


class TestScoring:
    def test_detects_the_planted_weakness(self):
        card = score_findings((a_finding(),), TIME_SPEC)

        assert card.detected is True
        assert card.matched == ("S2.time_pressure_error.clock.own",)

    def test_reports_a_miss_when_nothing_matches(self):
        card = score_findings((a_finding(kind="missed_motif", subject="fork"),), TIME_SPEC)

        assert card.detected is False

    def test_counts_unrelated_asserted_findings_as_spurious(self):
        findings = (a_finding(), a_finding(kind="missed_motif", subject="fork"))

        card = score_findings(findings, TIME_SPEC)

        assert card.spurious_count == 1

    def test_ignores_low_confidence_findings_when_counting_spurious(self):
        # `watch` is internal and never shown to a player, so it cannot mislead one.
        quiet = a_finding(
            kind="missed_motif",
            subject="fork",
            confidence=Confidence(tier=ConfidenceTier.WATCH, replicated=False),
        )

        card = score_findings((a_finding(), quiet), TIME_SPEC)

        assert card.spurious_count == 0

    def test_an_empty_profile_neither_detects_nor_invents(self):
        card = score_findings((), TIME_SPEC)

        assert card.detected is False
        assert card.spurious_count == 0

    def test_summarises_as_a_readable_line(self):
        card = score_findings((a_finding(),), TIME_SPEC)

        assert "time_pressure" in card.summary()
