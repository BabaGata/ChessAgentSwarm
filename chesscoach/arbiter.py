"""Choosing what to actually tell the player.

Spec: docs/notes/architecture.orchestration.md § Arbiter

Deterministic, not a model. Given a profile that may contain a dozen measured
weaknesses, pick the **one or two** worth a player's attention.

The cap is a design constraint rather than a tuning parameter. Coaches give one
or two priorities and build the work around them; "here are your nine
weaknesses" is the recorded anti-pattern (docs/notes/domain.coaching.md § 4) and
is precisely what a language model asked to be helpful produces (R-14, R-12).

**On prerequisite ordering.** The spec lists it as a ranking criterion, and it is
deliberately not implemented yet. The prerequisite structure in
docs/notes/domain.chess-concepts.md § C says tactics gate calculation, and that
practical-process skills are cross-cutting and teachable at any level -- so among
the claim kinds that currently exist, tactical and process weaknesses have no
defensible ordering between them. Inventing one would be fabricated pedagogy.
When a section emits a claim that genuinely depends on another, this is where
that goes.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.profile.models import ConfidenceTier, Finding

# One or two. Not a knob.
MAX_PRIORITIES = 2

# Below this a cost is real and not worth reordering anything for -- a fraction
# of a win-probability point per game is noise in the measurement, not a reason
# to prefer one weakness over another.
NEGLIGIBLE_COST_PER_GAME = 0.25

# Only these reach a player at all (architecture.confidence).
ASSERTABLE = (ConfidenceTier.FOCUS, ConfidenceTier.PRIORITY)

_TIER_RANK = {ConfidenceTier.PRIORITY: 0, ConfidenceTier.FOCUS: 1}


@dataclass(frozen=True)
class Priority:
    """A finding chosen to be worked on, and why it was chosen."""

    finding: Finding
    rank: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Selection:
    """What the arbiter decided, including what it set aside."""

    priorities: tuple[Priority, ...] = ()
    considered: int = 0
    not_selected: tuple[str, ...] = ()


def select_priorities(
    findings: tuple[Finding, ...], limit: int = MAX_PRIORITIES
) -> Selection:
    """Rank the assertable findings and take the top one or two."""
    eligible = [f for f in findings if f.confidence.tier in ASSERTABLE]
    if not eligible:
        return Selection(considered=0)

    ordered = sorted(eligible, key=_sort_key)
    chosen = _take_diverse(ordered, limit)

    return Selection(
        priorities=tuple(
            Priority(finding=f, rank=index + 1, reasons=_reasons(f))
            for index, f in enumerate(chosen)
        ),
        considered=len(eligible),
        not_selected=tuple(f.id for f in ordered if f not in chosen),
    )


def _sort_key(finding: Finding) -> tuple:
    """Strength of evidence, then **what it costs**, then how unusual (D5).

    Cost outranks unusualness, and a claim that can state a cost outranks one
    that cannot. That is deliberate: *"this is costing you four points of win
    probability a game"* is a reason to spend a month on something, while *"you
    do this 1.8x more than your peers"* is only a reason to find it interesting.

    A claim whose instances are not mistakes -- conceding a structure, letting a
    rook reach the seventh -- has no cost to state, and sorts below every claim
    that has one. S5's design note argued for exactly that before any of this
    was measurable: a claim that cannot say what it costs should have to work
    harder for one of a player's two slots.
    """
    cost = finding.measurement.cost_per_game
    return (
        _TIER_RANK.get(finding.confidence.tier, 9),
        0 if cost is not None else 1,
        -(cost or 0.0),
        -_unusualness(finding),
        -finding.measurement.distinct_games,
        finding.id,
    )


def _unusualness(finding: Finding) -> float:
    """How far from normal this is: against peers where we have them.

    Falling back to the player's own baseline is weaker -- it overstates by
    however much the behaviour is universal (L-012) -- but it is what exists
    when no reference population covers the claim.
    """
    measurement = finding.measurement
    return measurement.lift_vs_peer or measurement.lift_vs_baseline or 1.0


def _take_diverse(ordered: list[Finding], limit: int) -> list[Finding]:
    """Fill the slots, preferring a second priority about something else.

    Two views of the same pattern -- missing pins and conceding them -- are one
    thing to work on, not two. If nothing else is available the slot is still
    filled rather than wasted.
    """
    chosen: list[Finding] = []
    subjects: set[str] = set()

    for finding in ordered:
        if len(chosen) >= limit:
            break
        if finding.claim.subject in subjects:
            continue
        chosen.append(finding)
        subjects.add(finding.claim.subject)

    if len(chosen) < limit:
        for finding in ordered:
            if len(chosen) >= limit:
                break
            if finding not in chosen:
                chosen.append(finding)

    return chosen


def _reasons(finding: Finding) -> tuple[str, ...]:
    """Plain statements of why this one, in terms of the evidence."""
    measurement = finding.measurement
    reasons = [f"{finding.confidence.tier.value} confidence"]

    if measurement.peer_rate is not None and measurement.lift_vs_peer:
        reasons.append(
            f"{measurement.lift_vs_peer:.1f}x the rate of peers "
            f"({measurement.rate:.1%} against {measurement.peer_rate:.1%})"
        )
    elif measurement.lift_vs_baseline:
        reasons.append(
            f"{measurement.lift_vs_baseline:.1f}x this player's own rate elsewhere"
        )

    cost = measurement.cost_per_game
    if cost is not None and cost >= NEGLIGIBLE_COST_PER_GAME:
        reasons.append(f"costing about {cost:.1f} points of win probability a game")
    elif cost is None:
        # Said plainly rather than left as an absence: this claim lost to any
        # rival that could price itself, and the reader deserves to know that is
        # why.
        reasons.append("no measurable cost — its instances are choices, not mistakes")

    reasons.append(
        f"seen in {measurement.distinct_games} of {measurement.games_with_data} games"
    )
    return tuple(reasons)
