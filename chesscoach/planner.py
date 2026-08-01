"""Turning priorities into a plan the system can later be measured against.

Spec: docs/notes/architecture.md layer 7 ·
docs/notes/decisions.0008-deterministic-planner.md

Deterministic by decision, not by omission. Every step carries a **progress
sign** and a **check point**, and both are computed from the same measurement
that produced the finding. A language model cannot supply them: "you should
start spotting pins more reliably" is prose, and V7 has nothing to test. What V7
needs is a number and a deadline, and arithmetic is where those come from.

Two honest limits are built in. Progress is measured in **games**, not days,
because how long an intervention takes to show is unresolved (open question D5)
and inventing "two to three weeks" would be the confident folklore this project
refuses elsewhere. And targets **halve the gap** rather than closing it: asking a
player to reach the peer rate in one training block is not a fair expectation.
"""

from __future__ import annotations

import math

from chesscoach.arbiter import Priority
from chesscoach.profile.models import Finding, Plan, PlanStep

# Enough games that a rate measured over them means something. Matches the
# confidence policy's own threshold for a claim reaching `focus`.
MIN_CHECK_GAMES = 20

# Opportunities needed before the new rate is worth comparing to the old one.
MIN_OPPORTUNITIES_TO_RECHECK = 40

# A training block should halve the distance to the comparison rate, not close
# it. Provisional, like every threshold in this project.
GAP_CLOSED_PER_BLOCK = 0.5


def build_plan(priorities: tuple[Priority, ...], created: str) -> Plan | None:
    """One step per priority, in rank order. No priorities, no plan."""
    if not priorities:
        return None

    return Plan(
        created=created,
        steps=tuple(_step(priority.finding) for priority in priorities),
    )


def _step(finding: Finding) -> PlanStep:
    target = _target_rate(finding)
    games = _check_after_games(finding)

    return PlanStep(
        finding_id=finding.id,
        action=_action(finding),
        why=_why(finding),
        progress_sign=_progress_sign(finding, target, games),
        check_after_games=games,
        # Deliberately empty: see D5. Progress is counted in games, which we can
        # derive, rather than days, which we cannot.
        time_estimate_days=None,
    )


def _comparison(finding: Finding) -> float:
    """What the player is being measured against: peers if we have them."""
    measurement = finding.measurement
    if measurement.peer_rate is not None:
        return measurement.peer_rate
    return measurement.baseline_rate or 0.0


def _target_rate(finding: Finding) -> float:
    """Halfway from where they are to where the comparison sits."""
    rate = finding.measurement.rate
    comparison = _comparison(finding)
    if comparison >= rate:
        return rate
    return rate - (rate - comparison) * GAP_CLOSED_PER_BLOCK


def _check_after_games(finding: Finding) -> int:
    """Enough games for the chance to arise often enough to measure again."""
    measurement = finding.measurement
    if not measurement.rate or not measurement.games_with_data:
        return MIN_CHECK_GAMES

    opportunities = measurement.instances / measurement.rate
    per_game = opportunities / measurement.games_with_data
    if per_game <= 0:
        return MIN_CHECK_GAMES

    needed = math.ceil(MIN_OPPORTUNITIES_TO_RECHECK / per_game)
    return max(MIN_CHECK_GAMES, needed)


def _progress_sign(finding: Finding, target: float, games: int) -> str:
    """The observable claim this step is making, stated so it can be checked."""
    return (
        f"{_quantity(finding)} below {target:.1%} over the next {games} games "
        f"(currently {finding.measurement.rate:.1%})"
    )


def _quantity(finding: Finding) -> str:
    """Plain name for the thing being measured."""
    subject = finding.claim.subject
    return {
        "missed_motif": f"{subject} missed when available",
        "allowed_motif": f"{subject} conceded when you go wrong",
    }.get(finding.claim.kind, f"{finding.claim.kind} rate ({subject})")


def _why(finding: Finding) -> str:
    """The evidence, in the terms it was measured in."""
    measurement = finding.measurement
    where = f"seen in {measurement.distinct_games} of {measurement.games_with_data} games"
    if measurement.peer_rate is not None:
        return (
            f"{where}, at {measurement.rate:.1%} against {measurement.peer_rate:.1%} "
            "for peers at your level"
        )
    return f"{where}, at {measurement.rate:.1%} against {measurement.baseline_rate:.1%} elsewhere"


def _action(finding: Finding) -> str:
    """What to do about it.

    Tactical claims map to the Lichess theme vocabulary, so the same name that
    described the weakness selects the training material. Process claims map to
    a change of routine rather than to content, because that is what a process
    gap needs (domain.coaching § 2).
    """
    subject = finding.claim.subject
    actions = {
        "missed_motif": (
            f"Drill `{subject}` puzzles, and solve to be right rather than fast — "
            "review every one you get wrong."
        ),
        "allowed_motif": (
            "Before committing a move, ask what your opponent's best reply threatens; "
            f"`{subject}` is what has been punishing you."
        ),
        "long_think_error": (
            "When a think runs long, stop and choose between your two best candidate moves "
            "rather than searching for a third."
        ),
        "instant_move_error": (
            "In any position that is not forced, make yourself name your opponent's threat "
            "before moving."
        ),
        "time_pressure_error": (
            "Spend less time in the opening so that the clock is not deciding your moves later."
        ),
    }
    return actions.get(
        finding.claim.kind,
        f"Work on `{subject}`: review the cited games and note what you would play instead.",
    )
