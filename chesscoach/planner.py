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
from chesscoach.peers import PeerReference
from chesscoach.profile.models import Finding, Plan, PlanStep

# Enough games that a rate measured over them means something. Matches the
# confidence policy's own threshold for a claim reaching `focus`.
MIN_CHECK_GAMES = 20

# Opportunities needed before the new rate is worth comparing to the old one.
MIN_OPPORTUNITIES_TO_RECHECK = 40

# A training block should halve the distance to the comparison rate, not close
# it. Used only when there is no peer population to calibrate against.
GAP_CLOSED_PER_BLOCK = 0.5

# How far below the no-change expectation a target has to sit before meeting it
# means something. Calibrated in E05 against 57 predictions from 40 players who
# were never told anything, cross-validated by player at both 2 and 5 folds.
#
# The earlier value of 0.34 was never a fitted value at all: it came from 13
# predictions whose folds disagreed 0.385 against 0.518, then tightened by hand
# on the reasoning that strict is the safe direction. It is not — 1 of 52
# untreated predictions met it, and a target nothing reaches cannot detect
# coaching either.
#
# Measured properly (D9), the same rule fitted to a 30-game measurement period
# gives 0.488, not 0.34. So most of the 0.34 → 0.58 move was replacing a guess
# with a fit; only 0.488 → 0.594 is the genuine depth effect, and it is modest.
NO_CHANGE_RATIO = 0.58

# What the constant above buys, out of sample. Unlike the withdrawn 8 %, this is
# held out — folds fitted independently landed within 0.011–0.067 of each other,
# and 2-fold and 5-fold agree.
#
# A **range**, not a point, because D9 measured it against measurement periods of
# 78/60/45/30 games and got 15 / 18 / 22 / 23 %: a finding resting on fewer games
# regresses more, so one constant is slightly too generous for thin histories.
# Quoting 15 % would be true only at the deep end and would flatter the system
# for most players; quoting a single midpoint would hide a real dependence.
#
# Deliberately *not* a per-depth constant. Four points do not determine a curve,
# and fitting one is the overfitting L-018 warns about — the spread is
# 0.488–0.594, narrow enough that stating the range beats modelling it.
#
# Historical note, because the numeral is loaded: an earlier version of this
# output claimed "about 20 % reach this anyway", and that claim was **withdrawn**
# — it was an in-sample percentile from 13 predictions whose true out-of-sample
# value was 38 %. A test guards against it returning. The figures here are the
# measured out-of-sample rates from 27–57 predictions at each depth, which is a
# different kind of number that happens to overlap the same region.
#
# It is a false-*positive* rate only. Nothing here measures whether a coached
# player can meet the target, because no coached cohort exists yet, so the power
# of this test is unknown (open question D8).
UNTREATED_MET_SHARE_RANGE = (0.15, 0.23)


def build_plan(
    priorities: tuple[Priority, ...],
    created: str,
    peers: PeerReference | None = None,
    band: str | None = None,
    time_control: str | None = None,
    player: str | None = None,
    no_change_ratio: float = NO_CHANGE_RATIO,
) -> Plan | None:
    """One step per priority, in rank order. No priorities, no plan.

    The peer reference is not optional in spirit: without it, targets are set
    from the selected value, and E05 measured 92 % of those met by doing nothing
    — on 60-game histories, where the selection bias is at its worst. Deeper
    histories shrink the effect but do not remove it.
    """
    if not priorities:
        return None

    return Plan(
        created=created,
        steps=tuple(
            _step(
                priority.finding,
                expected_no_change(priority.finding, peers, band, time_control, player),
                no_change_ratio,
            )
            for priority in priorities
        ),
    )


def expected_no_change(
    finding: Finding,
    peers: PeerReference | None,
    band: str | None,
    time_control: str | None,
    player: str | None,
) -> float | None:
    """Where the next measurement lands if nothing about the player changes."""
    if peers is None or band is None or time_control is None:
        return None

    measurement = finding.measurement
    if not measurement.rate:
        return None

    opportunities = round(measurement.instances / measurement.rate)
    return peers.expected_rate(
        band,
        time_control,
        finding.claim.key(),
        instances=measurement.instances,
        opportunities=opportunities,
        excluding=player,
    )


def _step(finding: Finding, expected: float | None, no_change_ratio: float) -> PlanStep:
    target = _target_rate(finding, expected, no_change_ratio)
    games = _check_after_games(finding)

    return PlanStep(
        finding_id=finding.id,
        action=_action(finding),
        why=_why(finding),
        progress_sign=_progress_sign(finding, target, games, expected),
        check_after_games=games,
        # The number the prose describes. Without it the sign is readable and
        # uncheckable, which is only half of falsifiable (schema v3).
        target_rate=round(target, 4),
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


def _target_rate(finding: Finding, expected: float | None, no_change_ratio: float) -> float:
    """Halfway from where the player really is to where the comparison sits.

    "Where they really are" is the shrunk estimate, not the measured rate. E05
    showed why: a finding is selected for being extreme, so the measured rate is
    biased upward, and a target set from it is beaten by regression alone. The
    estimate is also the no-change prediction, so a target below it is a claim
    about the coaching rather than about the arithmetic.
    """
    if expected is None:
        # No population to calibrate against: fall back to halving the gap, and
        # accept that such a target is weak. E05 measured how weak.
        rate = finding.measurement.rate
        comparison = _comparison(finding)
        return rate if comparison >= rate else rate - (rate - comparison) * GAP_CLOSED_PER_BLOCK

    return expected * no_change_ratio


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


def _progress_sign(finding: Finding, target: float, games: int, expected: float | None) -> str:
    """The observable claim this step is making, stated so it can be checked.

    Where the no-change expectation is known it is stated too. Without it a
    reader cannot tell a real improvement from regression, and E05 showed that
    is most of what there is to see.
    """
    sign = f"{_quantity(finding)} below {target:.1%} over the next {games} games"
    if expected is not None:
        return (
            f"{sign} (measured {finding.measurement.rate:.1%}, ~{expected:.1%} if nothing changes; "
            f"{UNTREATED_MET_SHARE_RANGE[0]:.0%}–{UNTREATED_MET_SHARE_RANGE[1]:.0%} of players "
            "reach this target without changing anything)"
        )
    return f"{sign} (currently {finding.measurement.rate:.1%})"


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
