"""Going back to find out whether the coaching worked.

Spec: docs/notes/architecture.interaction.md step 8

The rule that shapes every test here: **a failed prediction is information about
the plan, not about the player**, and it is recorded either way. A system that
quietly drops its failed predictions is unfalsifiable, which is the one thing
this project must not be.
"""

from __future__ import annotations

import pytest

from chesscoach.peers import ConditionMeasurement
from chesscoach.profile.models import Plan, PlanStep
from chesscoach.progress import check_plan


def a_step(
    finding_id: str = "S1.missed_motif.pin.own",
    target: float = 0.21,
    check_after: int = 20,
) -> PlanStep:
    return PlanStep(
        finding_id=finding_id,
        action="drill pins",
        why="seen in 8 of 24 games",
        progress_sign=f"pin missed below {target:.1%} over the next {check_after} games",
        check_after_games=check_after,
        target_rate=target,
    )


def a_plan(*steps: PlanStep) -> Plan:
    return Plan(created="2026-07-01", steps=steps or (a_step(),))


def measured(rate: float, opportunities: int = 100, key: str = "missed_motif.pin.own"):
    return {
        key: ConditionMeasurement(
            claim_key=key,
            instances=round(rate * opportunities),
            opportunities=opportunities,
            distinct_games=6,
            games_with_data=25,
        )
    }


class TestVerdicts:
    def test_a_target_reached_is_met(self):
        report = check_plan(a_plan(), measured(0.15), previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=25, checked_at="2026-08-15")

        assert report.outcomes[0].status == "met"

    def test_a_target_missed_is_recorded_as_missed(self):
        report = check_plan(a_plan(), measured(0.28), previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=25, checked_at="2026-08-15")

        assert report.outcomes[0].status == "not_met"

    def test_exactly_on_target_counts_as_met(self):
        report = check_plan(a_plan(), measured(0.21),
                            previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=25, checked_at="2026-08-15")

        assert report.outcomes[0].status == "met"

    def test_too_few_games_is_not_a_verdict(self):
        # Judging early would let the system claim success it has not earned.
        report = check_plan(a_plan(), measured(0.10), previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=5, checked_at="2026-08-15")

        assert report.outcomes[0].status == "too_early"

    def test_a_claim_with_no_new_opportunities_cannot_be_judged(self):
        report = check_plan(
            a_plan(), measured(0.0, opportunities=0),
            previous_rates={"missed_motif.pin.own": 0.30},
            games_since=25, checked_at="2026-08-15",
        )

        assert report.outcomes[0].status == "not_measurable"

    def test_a_claim_absent_from_the_new_measurements_cannot_be_judged(self):
        report = check_plan(a_plan(), {}, previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=25, checked_at="2026-08-15")

        assert report.outcomes[0].status == "not_measurable"


class TestRecording:
    def test_keeps_the_numbers_behind_the_verdict(self):
        report = check_plan(a_plan(), measured(0.28), previous_rates={"missed_motif.pin.own": 0.30},
                            games_since=25, checked_at="2026-08-15")
        outcome = report.outcomes[0]

        assert outcome.previous_rate == pytest.approx(0.30)
        assert outcome.observed_rate == pytest.approx(0.28)
        assert outcome.target_rate == pytest.approx(0.21)
        assert outcome.games_since == 25
        assert outcome.checked_at == "2026-08-15"

    def test_records_an_outcome_for_every_step(self):
        plan = a_plan(a_step(), a_step(finding_id="S1.allowed_motif.fork.own", target=0.05))

        report = check_plan(plan, measured(0.10), previous_rates={}, games_since=25,
                            checked_at="2026-08-15")

        assert len(report.outcomes) == 2

    def test_a_step_without_a_target_cannot_be_checked(self):
        # Plans written before schema v3 carry prose and no number.
        plan = Plan(created="2026-07-01", steps=(
            PlanStep(finding_id="S1.missed_motif.pin.own", action="a", why="w",
                     progress_sign="vaguely better", check_after_games=20),
        ))

        report = check_plan(plan, measured(0.10), previous_rates={}, games_since=25,
                            checked_at="2026-08-15")

        assert report.outcomes[0].status == "not_measurable"


class TestSummary:
    def test_counts_the_verdicts(self):
        plan = a_plan(a_step(), a_step(finding_id="S1.allowed_motif.fork.own", target=0.05))
        later = measured(0.10) | measured(0.50, key="allowed_motif.fork.own")

        report = check_plan(plan, later, previous_rates={}, games_since=25,
                            checked_at="2026-08-15")

        assert report.met == 1
        assert report.not_met == 1

    def test_reads_as_a_line(self):
        report = check_plan(a_plan(), measured(0.15), previous_rates={}, games_since=25,
                            checked_at="2026-08-15")

        assert "1 met" in report.summary()

    def test_an_empty_plan_checks_nothing(self):
        report = check_plan(Plan(created="2026-07-01"), {}, previous_rates={}, games_since=25,
                            checked_at="2026-08-15")

        assert report.outcomes == ()
        assert "nothing to check" in report.summary()
