"""Going back to find out whether the coaching worked.

Spec: docs/notes/architecture.interaction.md step 8

The plan said what should change and by when. This re-measures the same quantity
over the games played since, and records what happened.

One rule shapes the whole module: **a failed prediction is information about the
plan, not about the player**, and it is recorded either way. A system that
quietly drops its failed predictions cannot be wrong, and a coach who cannot be
wrong is not offering evidence -- it is offering reassurance.

Two verdicts exist for "we cannot say", kept separate from "no":

  * ``too_early``      -- fewer games than the plan asked for. Judging now would
    let the system claim a success it has not earned.
  * ``not_measurable`` -- the chance did not arise, or the step predates the
    schema that recorded a target. Nothing to compare against.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from chesscoach.peers import ConditionMeasurement
from chesscoach.profile.models import Plan, PlanStep, StepOutcome

MET = "met"
NOT_MET = "not_met"
TOO_EARLY = "too_early"
NOT_MEASURABLE = "not_measurable"


@dataclass(frozen=True)
class ProgressReport:
    """What became of a plan's predictions."""

    checked_at: str
    outcomes: tuple[StepOutcome, ...] = ()

    @property
    def met(self) -> int:
        return sum(1 for o in self.outcomes if o.status == MET)

    @property
    def not_met(self) -> int:
        return sum(1 for o in self.outcomes if o.status == NOT_MET)

    @property
    def undecided(self) -> int:
        return sum(1 for o in self.outcomes if o.status in (TOO_EARLY, NOT_MEASURABLE))

    def summary(self) -> str:
        if not self.outcomes:
            return "nothing to check: the plan made no predictions"
        parts = [f"{self.met} met", f"{self.not_met} not met"]
        if self.undecided:
            parts.append(f"{self.undecided} undecided")
        return ", ".join(parts)


def check_plan(
    plan: Plan,
    later: Mapping[str, ConditionMeasurement],
    previous_rates: Mapping[str, float],
    games_since: int,
    checked_at: str,
) -> ProgressReport:
    """Judge every step of a plan against what the player has done since.

    `later` holds measurements taken over the **new** games only -- a rate over
    the whole corpus would be diluted by the games that produced the diagnosis
    in the first place.
    """
    return ProgressReport(
        checked_at=checked_at,
        outcomes=tuple(
            _judge(step, later, previous_rates, games_since, checked_at) for step in plan.steps
        ),
    )


def _judge(
    step: PlanStep,
    later: Mapping[str, ConditionMeasurement],
    previous_rates: Mapping[str, float],
    games_since: int,
    checked_at: str,
) -> StepOutcome:
    previous = previous_rates.get(step.claim_key, 0.0)
    measurement = later.get(step.claim_key)
    observed = measurement.rate if measurement else None

    return StepOutcome(
        finding_id=step.finding_id,
        status=_status(step, observed, games_since),
        target_rate=step.target_rate if step.target_rate is not None else 0.0,
        previous_rate=previous,
        observed_rate=observed,
        games_since=games_since,
        checked_at=checked_at,
    )


def _status(step: PlanStep, observed: float | None, games_since: int) -> str:
    if step.target_rate is None:
        return NOT_MEASURABLE
    if games_since < step.check_after_games:
        return TOO_EARLY
    if observed is None:
        return NOT_MEASURABLE
    return MET if observed <= step.target_rate else NOT_MET
