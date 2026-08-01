"""Choosing what to actually tell the player.

Spec: docs/notes/architecture.orchestration.md § Arbiter

The cap of two is a design constraint, not a tuning parameter. Coaches give one
or two priorities; "here are your nine weaknesses" is the anti-pattern
([[domain.coaching]] § 4) and the default behaviour of a language model asked to
be helpful (R-12).
"""

from __future__ import annotations

from chesscoach.arbiter import MAX_PRIORITIES, select_priorities
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

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-07-31")


def a_finding(
    kind: str = "missed_motif",
    subject: str = "fork",
    tier: ConfidenceTier = ConfidenceTier.FOCUS,
    rate: float = 0.30,
    peer_rate: float | None = 0.15,
    baseline_rate: float | None = 0.15,
    distinct_games: int = 6,
    section: str = "S1",
) -> Finding:
    return Finding(
        section=section,
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=12,
            distinct_games=distinct_games,
            games_with_data=30,
            rate=rate,
            peer_rate=peer_rate,
            baseline_rate=baseline_rate,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=tier, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=21, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


class TestCap:
    def test_never_returns_more_than_two(self):
        findings = tuple(a_finding(subject=f"m{n}") for n in range(6))

        assert len(select_priorities(findings).priorities) == MAX_PRIORITIES

    def test_the_cap_is_two(self):
        # Stated as a test because it is a design constraint, not a knob.
        assert MAX_PRIORITIES == 2

    def test_returns_what_there_is_when_there_are_fewer(self):
        assert len(select_priorities((a_finding(),)).priorities) == 1

    def test_an_empty_profile_yields_no_priorities(self):
        selection = select_priorities(())

        assert selection.priorities == ()
        assert selection.considered == 0


class TestEligibility:
    def test_ignores_findings_below_focus(self):
        watched = a_finding(tier=ConfidenceTier.WATCH)

        assert select_priorities((watched,)).priorities == ()

    def test_counts_only_eligible_findings_as_considered(self):
        findings = (a_finding(), a_finding(subject="pin", tier=ConfidenceTier.WATCH))

        assert select_priorities(findings).considered == 1


class TestRanking:
    def test_priority_tier_outranks_focus(self):
        focus = a_finding(subject="fork", tier=ConfidenceTier.FOCUS, rate=0.9)
        priority = a_finding(subject="pin", tier=ConfidenceTier.PRIORITY, rate=0.2)

        chosen = select_priorities((focus, priority)).priorities[0]

        assert chosen.finding.claim.subject == "pin"

    def test_within_a_tier_the_more_unusual_claim_wins(self):
        ordinary = a_finding(subject="fork", rate=0.20, peer_rate=0.18)
        unusual = a_finding(subject="pin", rate=0.40, peer_rate=0.10)

        chosen = select_priorities((ordinary, unusual)).priorities[0]

        assert chosen.finding.claim.subject == "pin"

    def test_falls_back_to_the_self_baseline_without_a_peer_rate(self):
        findings = (
            a_finding(subject="fork", rate=0.20, peer_rate=None),
            a_finding(subject="pin", rate=0.50, peer_rate=None),
        )

        assert select_priorities(findings).priorities[0].finding.claim.subject == "pin"

    def test_is_deterministic(self):
        findings = tuple(a_finding(subject=f"m{n}", rate=0.3) for n in range(5))

        first = select_priorities(findings).priorities
        second = select_priorities(findings).priorities

        assert [p.finding.id for p in first] == [p.finding.id for p in second]


class TestDiversity:
    def test_the_second_slot_prefers_a_different_weakness(self):
        # Two views of the same pattern are one priority, not two.
        strong_pin = a_finding(kind="missed_motif", subject="pin", rate=0.60, peer_rate=0.10)
        same_pin = a_finding(kind="allowed_motif", subject="pin", rate=0.55, peer_rate=0.10)
        other = a_finding(kind="missed_motif", subject="fork", rate=0.40, peer_rate=0.15)

        chosen = select_priorities((strong_pin, same_pin, other)).priorities

        assert [p.finding.claim.subject for p in chosen] == ["pin", "fork"]

    def test_still_fills_the_second_slot_when_everything_shares_a_subject(self):
        findings = (
            a_finding(kind="missed_motif", subject="pin", rate=0.60),
            a_finding(kind="allowed_motif", subject="pin", rate=0.55),
        )

        assert len(select_priorities(findings).priorities) == 2


class TestExplanation:
    def test_records_why_each_priority_was_chosen(self):
        selection = select_priorities((a_finding(rate=0.4, peer_rate=0.1),))

        assert any("peers" in reason for reason in selection.priorities[0].reasons)

    def test_ranks_are_one_based_and_ordered(self):
        findings = (a_finding(subject="fork"), a_finding(subject="pin"))

        assert [p.rank for p in select_priorities(findings).priorities] == [1, 2]

    def test_names_what_was_left_out(self):
        findings = tuple(a_finding(subject=f"m{n}") for n in range(4))

        selection = select_priorities(findings)

        assert len(selection.not_selected) == 2
