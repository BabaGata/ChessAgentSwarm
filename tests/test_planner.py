"""Turning priorities into a plan the system can be measured against.

Spec: docs/notes/architecture.md layer 7, docs/notes/decisions.0008-deterministic-planner.md

The point of every test here is the same: a plan step must say something that can
later be checked. A step whose progress sign is prose is a step V7 cannot test,
and unfalsifiable coaching is what this project exists to avoid (R-02).
"""

from __future__ import annotations

import pytest

from chesscoach.arbiter import select_priorities
from chesscoach.planner import MIN_CHECK_GAMES, build_plan
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
    subject: str = "pin",
    rate: float = 0.30,
    peer_rate: float | None = 0.12,
    instances: int = 30,
    distinct_games: int = 8,
    games_with_data: int = 24,
    tier: ConfidenceTier = ConfidenceTier.PRIORITY,
    section: str = "S1",
) -> Finding:
    return Finding(
        section=section,
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=instances,
            distinct_games=distinct_games,
            games_with_data=games_with_data,
            rate=rate,
            peer_rate=peer_rate,
            baseline_rate=0.12,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=tier, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=21, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


def plan_for(*findings, created: str = "2026-07-31"):
    return build_plan(select_priorities(findings).priorities, created=created)


class TestShape:
    def test_one_step_per_priority_in_rank_order(self):
        plan = plan_for(a_finding(subject="pin"), a_finding(subject="fork", rate=0.25))

        assert len(plan.steps) == 2
        assert plan.steps[0].finding_id.endswith("pin.own")

    def test_no_priorities_means_no_plan(self):
        assert build_plan((), created="2026-07-31") is None

    def test_records_when_it_was_made(self):
        assert plan_for(a_finding()).created == "2026-07-31"

    def test_every_step_names_the_finding_it_came_from(self):
        step = plan_for(a_finding()).steps[0]

        assert step.finding_id == "S1.missed_motif.pin.own"


class TestProgressSign:
    def test_states_a_target_rate_that_can_be_measured(self):
        step = plan_for(a_finding(rate=0.30, peer_rate=0.12)).steps[0]

        assert "%" in step.progress_sign
        assert "games" in step.progress_sign

    def test_the_target_halves_the_gap_to_the_comparison(self):
        # Reaching the peer rate in one block is not a fair ask; halving the
        # distance to it is observable and achievable.
        step = plan_for(a_finding(rate=0.30, peer_rate=0.12)).steps[0]

        assert "21.0%" in step.progress_sign

    def test_falls_back_to_the_self_baseline_without_peers(self):
        step = plan_for(a_finding(rate=0.40, peer_rate=None)).steps[0]

        assert "26.0%" in step.progress_sign  # halfway from 40% to the 12% baseline

    def test_states_the_target_as_a_reduction_from_where_they_are(self):
        # The sign carries both numbers on purpose: a target with no starting
        # point is not something a player can judge progress against.
        step = plan_for(a_finding(rate=0.30, peer_rate=0.12)).steps[0]

        assert "below 21.0%" in step.progress_sign
        assert "currently 30.0%" in step.progress_sign


class TestShrunkTargets:
    """E05: a target set from the selected value is beaten by regression alone."""

    def peers(self, rate: float = 0.12, size: int = 300):
        from chesscoach.peers import ConditionMeasurement, build_reference

        key = Claim.of(kind="missed_motif", subject="pin").key()
        return build_reference(
            [
                (
                    f"peer{n}",
                    (ConditionMeasurement(key, round(rate * size), size, 20, 40),),
                )
                for n in range(5)
            ],
            band="1400-1800",
            time_control="rapid",
            depth=15,
        )

    def plan_with_peers(self, finding):
        return build_plan(
            select_priorities((finding,)).priorities,
            created="2026-07-31",
            peers=self.peers(),
            band="1400-1800",
            time_control="rapid",
        )

    def test_the_target_is_set_from_the_estimate_not_the_measured_rate(self):
        # 9 misses in 30 chances reads as 30%, but against peers at 12% with a
        # sample that small, the player's true rate is nearer the population.
        finding = a_finding(rate=0.30, instances=9, distinct_games=8, peer_rate=0.12)

        step = self.plan_with_peers(finding).steps[0]

        assert step.target_rate < 0.21  # what the old rule would have asked for

    def test_the_sign_states_what_happens_if_nothing_changes(self):
        # Without it a reader cannot tell improvement from regression.
        finding = a_finding(rate=0.30, instances=9, distinct_games=8, peer_rate=0.12)

        sign = self.plan_with_peers(finding).steps[0].progress_sign

        assert "if nothing changes" in sign

    def test_the_target_is_calibrated_against_what_happens_anyway(self):
        from chesscoach.planner import NO_CHANGE_RATIO

        finding = a_finding(rate=0.30, instances=600, distinct_games=20, peer_rate=0.12)

        step = self.plan_with_peers(finding).steps[0]

        # Set below what a player reaches on their own, not below where they are.
        assert step.target_rate < 0.30 * NO_CHANGE_RATIO * 1.2

    def test_the_sign_warns_that_the_target_can_be_met_without_changing(self):
        # Without this a "met" verdict reads as proof, and it is not.
        finding = a_finding(rate=0.30, instances=600, distinct_games=20, peer_rate=0.12)

        sign = self.plan_with_peers(finding).steps[0].progress_sign

        assert "without changing anything" in sign

    def test_the_stated_false_positive_rate_is_the_calibrated_one(self):
        # A number here is only allowed because it is now held out: 57
        # predictions, cross-validated by player at 2 and 5 folds. The earlier
        # in-sample 8% was withdrawn for exactly this reason, so the figure the
        # player is shown must track the constant it was calibrated with.
        from chesscoach.planner import UNTREATED_MET_SHARE

        finding = a_finding(rate=0.30, instances=600, distinct_games=20, peer_rate=0.12)

        sign = self.plan_with_peers(finding).steps[0].progress_sign

        assert f"{UNTREATED_MET_SHARE:.0%}" in sign
        assert "20%" not in sign

    def test_without_peers_it_falls_back_to_the_measured_rate(self):
        step = plan_for(a_finding(rate=0.30, peer_rate=0.12)).steps[0]

        assert step.target_rate == pytest.approx(0.21, abs=0.001)


class TestCheckPoint:
    def test_derives_the_check_point_from_how_often_the_chance_arises(self):
        # 30 misses at 30% means 100 opportunities across 24 games -- roughly
        # four a game, so enough evidence accrues quickly.
        step = plan_for(a_finding(instances=30, rate=0.30, games_with_data=24)).steps[0]

        assert step.check_after_games == MIN_CHECK_GAMES

    def test_asks_for_more_games_when_the_chance_is_rare(self):
        # 3 misses at 30% is 10 opportunities across 24 games: far less often.
        step = plan_for(
            a_finding(instances=3, distinct_games=3, rate=0.30, games_with_data=24)
        ).steps[0]

        assert step.check_after_games > MIN_CHECK_GAMES

    def test_never_asks_for_fewer_than_the_floor(self):
        step = plan_for(a_finding(instances=200, rate=0.30, games_with_data=24)).steps[0]

        assert step.check_after_games >= MIN_CHECK_GAMES


class TestTimeEstimate:
    def test_leaves_days_empty_because_we_do_not_know(self):
        # Open question D5 is unresolved. Progress is measured in games, which
        # can be derived, not days, which cannot.
        assert plan_for(a_finding()).steps[0].time_estimate_days is None


class TestAction:
    def test_a_missed_tactic_prescribes_drilling_that_theme(self):
        step = plan_for(a_finding(kind="missed_motif", subject="fork")).steps[0]

        assert "fork" in step.action

    def test_an_allowed_tactic_prescribes_checking_the_reply(self):
        step = plan_for(a_finding(kind="allowed_motif", subject="fork")).steps[0]

        assert "reply" in step.action or "threat" in step.action

    def test_a_process_weakness_prescribes_a_routine_not_puzzles(self):
        step = plan_for(
            a_finding(kind="long_think_error", subject="long_think", section="S2")
        ).steps[0]

        assert "puzzle" not in step.action.lower()

    def test_an_unknown_claim_kind_still_produces_a_usable_step(self):
        step = plan_for(a_finding(kind="brand_new_thing", subject="mystery")).steps[0]

        assert step.action
        assert step.progress_sign


class TestWhy:
    def test_states_the_evidence_behind_the_step(self):
        step = plan_for(a_finding(distinct_games=8, games_with_data=24)).steps[0]

        assert "8" in step.why and "24" in step.why

    def test_names_the_peer_comparison_when_there_is_one(self):
        step = plan_for(a_finding(rate=0.30, peer_rate=0.12)).steps[0]

        assert "peers" in step.why


class TestDeterminism:
    def test_the_same_findings_produce_the_same_plan(self):
        findings = (a_finding(subject="pin"), a_finding(subject="fork", rate=0.25))

        first = plan_for(*findings)
        second = plan_for(*findings)

        assert first == second
