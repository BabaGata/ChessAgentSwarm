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

from chesscoach.overlap import drop_covered_claims
from chesscoach.profile.models import ConfidenceTier, Finding

# Raised from two to three on 2026-08-15, at the thesis author's direction after
# the first expert review. The coaching literature's objection stands and is
# answered by *ordering* rather than by length: step 1 is marked as where to
# start, and the reader is told the rest are sequenced behind it. A ranked three
# is still a plan; an unranked nine is the anti-pattern.
MAX_PRIORITIES = 3

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
    # True when this came from the cost pool rather than the peer comparison:
    # expensive for this player, and **not** shown to be unusual for their level.
    # The report must say so, or it turns a population fact into a personal
    # accusation (E25 condition 2).
    shared: bool = False


@dataclass(frozen=True)
class Selection:
    """What the arbiter decided, including what it set aside."""

    priorities: tuple[Priority, ...] = ()
    considered: int = 0
    not_selected: tuple[str, ...] = ()


def select_priorities(
    findings: tuple[Finding, ...],
    limit: int = MAX_PRIORITIES,
    also: tuple[Finding, ...] = (),
) -> Selection:
    """Rank the assertable findings, then fill any empty slots by cost.

    `also` is the sub-threshold pool: patterns measured, priced, and **not**
    shown to be unusual for the player's level. They can never displace an
    assertable finding — being unusual is what makes the first slots a diagnosis
    rather than a description — and they are ranked among themselves by what they
    cost the player outright, because the excess over peers is precisely the
    comparison that already declined to rank them.

    Without `also` this behaves exactly as it did before, which is what every
    existing caller relies on.

    Before anything is ranked, claims that mostly restate a narrower one are
    removed — **across sections and across both pools**, by measured overlap
    rather than by a table of which claim contains which (`chesscoach.overlap`).
    Sections cannot see each other, so this is the only place that can notice two
    of them describing the same moves. It is a small effect and honestly so: one
    pair in 501 reached the threshold across twelve real players (E42).
    """
    findings, also = drop_covered_claims(tuple(findings), tuple(also))

    eligible = [f for f in findings if f.confidence.tier in ASSERTABLE]
    ordered = sorted(eligible, key=_sort_key)
    chosen = _take_diverse(ordered, limit)

    # Only what unusualness left empty. E17 measured what happens when cost ranks
    # the whole list: one claim is named to 70 % of players.
    costly = _take_diverse(
        [f for f in sorted(also, key=_cost_key) if _worth_a_slot(f)],
        limit - len(chosen),
        taken={f.claim.subject for f in chosen},
    )
    if not chosen and not costly:
        return Selection(considered=0)

    priorities = tuple(
        Priority(
            finding=f,
            rank=index + 1,
            reasons=_reasons(f, shared=f in costly),
            shared=f in costly,
        )
        for index, f in enumerate(chosen + costly)
    )
    return Selection(
        priorities=priorities,
        considered=len(eligible),
        not_selected=tuple(f.id for f in ordered if f not in chosen),
    )


def _worth_a_slot(finding: Finding) -> bool:
    """Two conditions, and the second was learned the hard way.

    **It must have a cost to state.** A claim whose instances are choices rather
    than mistakes — conceding a structure, letting a rook reach the seventh —
    cannot say what it cost, and filling a training slot with one would be
    inventing a priority rather than finding one.

    **And it must be worse than the player's level in at least one of the two
    ways that matter** — a higher rate, or a higher cost.

    An earlier version of this required the rate alone, on the reasoning that a
    thing you do less than your peers is not a thing to work on. That reasoning
    is wrong for a **conditional** rate, and measurement showed how wrong: of 327
    (player, claim) pairs across the twelve review players, 198 sat below the
    peer rate and **21 of those cost more than peers anyway** — six of them in a
    player's top five by cost, two of them a player's single most expensive
    pattern. One player met time pressure **5.4 times a game against a peer's
    0.4** and handled it better than average once there; the rule threw away the
    largest number in their profile.

    So a below-peer rate is no longer disqualifying on its own. What it changes
    is the **wording**, not the eligibility: `Measurement.driven_by_exposure`
    marks these, and the report says the cost comes from meeting the condition
    more often rather than from handling it worse. Ranking still uses cost, so
    nothing here can outrank a claim that is dearer.

    A missing peer rate is not evidence of being better than average, so it
    passes; the alternative silently narrows the pool to whatever the reference
    happens to cover.
    """
    measurement = finding.measurement
    cost = measurement.cost_per_game
    if cost is None or cost < NEGLIGIBLE_COST_PER_GAME:
        return False
    if measurement.peer_rate is None or measurement.rate >= measurement.peer_rate:
        return True
    # Below the peer rate: only worth a slot if it still costs more than it costs
    # them, which can only mean exposure.
    return measurement.driven_by_exposure


def _cost_key(finding: Finding) -> tuple:
    return (-(finding.measurement.cost_per_game or 0.0), finding.id)


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
    cost = _recoverable(finding)
    return (
        _TIER_RANK.get(finding.confidence.tier, 9),
        0 if cost is not None else 1,
        -(cost or 0.0),
        -_unusualness(finding),
        -finding.measurement.distinct_games,
        finding.id,
    )


def _recoverable(finding: Finding) -> float | None:
    """What working on this could actually get back, per game.

    The **excess** over peers where a population can price the claim, and the
    raw cost where it cannot. Falling back keeps a claim rankable rather than
    dropping it to the bottom for want of a reference it never had — the same
    reasoning as `_unusualness` falling back to the player's own baseline, and
    weaker in the same way.
    """
    measurement = finding.measurement
    excess = measurement.excess_cost_per_game
    return excess if excess is not None else measurement.cost_per_game


def _unusualness(finding: Finding) -> float:
    """How far from normal this is: against peers where we have them.

    Falling back to the player's own baseline is weaker -- it overstates by
    however much the behaviour is universal (L-012) -- but it is what exists
    when no reference population covers the claim.
    """
    measurement = finding.measurement
    return measurement.lift_vs_peer or measurement.lift_vs_baseline or 1.0


def _take_diverse(
    ordered: list[Finding], limit: int, taken: set[str] | None = None
) -> list[Finding]:
    """Fill the slots, preferring a second priority about something else.

    Two views of the same pattern -- missing pins and conceding them -- are one
    thing to work on, not two. If nothing else is available the slot is still
    filled rather than wasted.

    `taken` carries subjects already claimed by an earlier pool, so the rule
    holds *across* the assertable and cost-ranked pools and not only within each.
    """
    if limit <= 0:
        return []

    chosen: list[Finding] = []
    subjects: set[str] = set(taken or ())

    for finding in ordered:
        if len(chosen) >= limit:
            break
        if finding.claim.subject in subjects:
            continue
        chosen.append(finding)
        subjects.add(finding.claim.subject)

    # The fallback relaxes diversity *within* this pool rather than across pools:
    # a slot is better filled than wasted, but repeating a subject the reader has
    # already been given a step for is not filling it.
    blocked = set(taken or ())
    if len(chosen) < limit:
        for finding in ordered:
            if len(chosen) >= limit:
                break
            if finding.claim.subject in blocked:
                continue
            if finding not in chosen:
                chosen.append(finding)

    return chosen


def _reasons(finding: Finding, shared: bool = False) -> tuple[str, ...]:
    """Plain statements of why this one, in terms of the evidence."""
    measurement = finding.measurement
    if shared:
        # Never "you do this more than your peers" — the reason this one is here
        # is precisely that it could not be shown to be unusual. Saying so is the
        # difference between a population fact and a personal accusation.
        return (
            "not unusual for your level, and the most expensive pattern left",
            f"costing about {measurement.cost_per_game:.1f} points of win probability a game",
            f"seen in {measurement.distinct_games} of {measurement.games_with_data} games",
        )

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

    cost = _recoverable(finding)
    if cost is not None and cost >= NEGLIGIBLE_COST_PER_GAME:
        if measurement.excess_cost_per_game is not None:
            reasons.append(
                f"costing about {cost:.1f} points of win probability a game more than "
                f"players at this level lose to it"
            )
        else:
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
