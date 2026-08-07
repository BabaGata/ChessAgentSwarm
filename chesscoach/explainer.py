"""Turning a profile into something a person can read.

Spec: docs/notes/architecture.interaction.md § 7

**Deterministic, and that is the first version by decision rather than by
laziness.** An explainer's job is to present what the profile contains, with its
evidence. A language model would add fluency and, at this stage, nothing that
can be checked — while adding the one failure this project is most exposed to
(R-03: chess prose that sounds expert and is invented). Templates cannot
hallucinate a reason the detectors never found.

It also becomes the baseline a model-backed explainer has to beat, the way the
embedding baseline forced the prober's classifier to earn its cost (E07). If a
generated report is not measurably better on a rubric, the templates ship.

The constraints in § 7 are enforced here rather than trusted:

* one or two priorities, never a list of nine (R-12 is the anti-pattern);
* every claim cites specific games;
* what could **not** be assessed is stated -- silence implies competence;
* nothing about the player's talent, potential or ceiling.
"""

from __future__ import annotations

from chesscoach.arbiter import NEGLIGIBLE_COST_PER_GAME
from chesscoach.context import FOCUSED_EFFORT_HOURS
from chesscoach.phrasing import move_number, quantity, statement
from chesscoach.profile.models import (
    DeterminedBy,
    Finding,
    GapTypeHypothesis,
    PlayerProfile,
    ProbeRecord,
)

# How many pieces of evidence to cite per finding. Enough to show the pattern is
# a pattern, few enough to read.
EVIDENCE_SHOWN = 3

# What a probed gap type means for what to do about it, in the player's terms.
GAP_MEANING: dict[str, str] = {
    GapTypeHypothesis.KNOWLEDGE.value: (
        "You did not find it with unlimited time either, so this is worth learning "
        "rather than drilling for speed."
    ),
    GapTypeHypothesis.SKILL.value: (
        "You found it and explained it correctly with time to think, so the pattern "
        "is there — what is missing is spotting it during a game."
    ),
    GapTypeHypothesis.FRAGILE.value: (
        "You found the move but gave a different reason for it, which usually means "
        "the idea will not transfer to a position that looks unlike this one."
    ),
    GapTypeHypothesis.PROCESS.value: (
        "This looks like how you use your time rather than what you know."
    ),
}

LIMITS = (
    "This is measured from your own games and nothing else — it says what happened, "
    "not why, except where a probe asked you directly.",
    "Rates are compared with players in your rating band, so they say you are unusual, "
    "not that you are bad.",
    "Nothing here estimates your potential or your ceiling, because nothing here could.",
)


def render(profile: PlayerProfile) -> str:
    """The whole report, as text."""
    return "\n".join(
        _header(profile)
        + _what_you_said(profile)
        + _how_you_play(profile)
        + _findings_section(profile)
        + _plan_section(profile)
        + _not_assessed(profile)
        + _limits(profile)
    )


def _what_you_said(profile: PlayerProfile) -> list[str]:
    """Read the player's own answers back to them.

    Not decoration. A report that never mentions what someone just told it reads
    as a form that was filled in and filed, and the point of asking was to plan
    for *this* person. Their words are quoted rather than paraphrased — nothing
    here interprets them, and pretending otherwise would need a model that could
    misread a goal and then quietly plan for the wrong person.
    """
    context = profile.context
    if context is None:
        return []

    lines = ["WHAT YOU TOLD ME", ""]
    if context.goals:
        lines.append(f"   You want    {context.goals}")
    if context.weekly_study_hours is not None:
        hours = context.weekly_study_hours
        sized = (
            "so this plan has one thing in it, not two"
            if hours < FOCUSED_EFFORT_HOURS
            else "enough for two things at once"
        )
        unit = "hour" if hours == 1 else "hours"
        lines.append(f"   Time        {hours:g} {unit} a week — {sized}")
    if context.already_tried:
        lines.append(f"   Tried       {context.already_tried}")
    return lines + [""]


def _header(profile: PlayerProfile) -> list[str]:
    corpus = profile.corpus
    span = f" ({corpus.date_range[0]} to {corpus.date_range[1]})" if corpus.date_range else ""
    return [
        f"Report for {profile.player.username}",
        f"{corpus.n_games} games{span}, rating band {profile.player.band or 'unspecified'}",
        "",
    ] + _strength(profile)


def _strength(profile: PlayerProfile) -> list[str]:
    """What the moves suggest, always with the spread that qualifies it.

    Never printed as a single number. Held-out error is ±103 points, so a bare
    "you play like 1650" would claim a precision the measurement does not have,
    and D1 is explicit that this project must not promise rating it cannot
    evidence.
    """
    strength = profile.strength
    if strength is None:
        return []

    low, high = strength.rating - strength.typical_error, strength.rating + strength.typical_error
    lines = [
        "HOW STRONG YOUR PLAY LOOKS",
        "",
        f"   About {strength.rating}, and most likely between {low} and {high}.",
        f"   Judged from how often you blunder across {strength.moves} of your own moves,"
        " and nothing else —",
        "   not from your rating, which was never shown to it.",
    ]
    if strength.extrapolated:
        lines.append(
            "   Your blunder rate is outside the range this was calibrated on, so treat"
            " the number as a direction rather than a figure."
        )
    return lines + [""]


TENDENCY_PHRASING = {
    "plays_queenless": "spend {share:.0%} of your moves with the queens off, against {peer:.0%}"
    " for players at your level",
}


def _how_you_play(profile: PlayerProfile) -> list[str]:
    """Tendencies, stated flatly and with no verdict attached.

    Kept away from WHAT STANDS OUT on purpose: those are weaknesses with a plan
    behind them, and this is not one. **It also stops short of saying whether the
    tendency suits the player**, which is the half a reader most wants — E14
    measured it and found every player errs about 20 % less with the queens off,
    differing by too little to tell one from another. Saying "and it suits you"
    would be the personality label domain.coaching § 6 warns against.
    """
    notable = [t for t in profile.style if _notable(t)]
    if not notable:
        return []

    lines = ["HOW YOU PLAY", ""]
    for tendency in notable:
        template = TENDENCY_PHRASING.get(tendency.name)
        if template is None:
            continue
        lines.append(
            "   You " + template.format(share=tendency.share, peer=tendency.peer_share) + "."
        )
    return lines + [
        "",
        "   That is a preference, not a strength or a weakness. Nothing here says whether",
        "   it suits you — players differ in what they steer towards and barely differ in",
        "   how much it helps them, so any answer would be invented.",
        "",
    ]


def _notable(tendency) -> bool:
    from chesscoach.style import NOTABLE_RATIO

    if not tendency.peer_share:
        return False
    ratio = tendency.share / tendency.peer_share
    return ratio >= NOTABLE_RATIO or ratio <= 1 / NOTABLE_RATIO


def _reported(profile: PlayerProfile) -> list[Finding]:
    """Only what the plan acts on, **in the plan's order**.

    The profile may hold more findings than this. Listing them all is the
    coaching anti-pattern R-12 names — a player given nine weaknesses has been
    given none — so the report shows what the arbiter chose and says how many it
    set aside.

    Ordering by the plan rather than by the profile matters more than it looks:
    both sections are numbered, so a reader takes item 1 in one to be item 1 in
    the other. Profile order is insertion order and does not match the arbiter's
    ranking.
    """
    if profile.plan is None:
        return []
    by_id = {f.id: f for f in profile.findings}
    return [by_id[step.finding_id] for step in profile.plan.steps if step.finding_id in by_id]


def _priced_count(profile: PlayerProfile) -> int:
    """How many reported findings actually printed a cost."""
    return sum(
        1
        for finding in _reported(profile)
        if (finding.measurement.cost_per_game or 0.0) >= NEGLIGIBLE_COST_PER_GAME
    )


def _findings_section(profile: PlayerProfile) -> list[str]:
    reported = _reported(profile)
    if not reported:
        return [
            "Nothing reached the confidence needed to report.",
            "That is a real result, not an empty one: either your games do not show a "
            "consistent pattern, or there were too few of them to tell.",
            "",
        ]

    lines = ["WHAT STANDS OUT", ""]
    for index, finding in enumerate(reported, start=1):
        lines += _finding(index, finding, profile.probes)

    set_aside = len(profile.findings) - len(reported)
    if set_aside > 0:
        noun = "pattern was" if set_aside == 1 else "patterns were"
        lines += [
            f"({set_aside} further {noun} found but not prioritised — working on one or "
            "two things at a time is the point.)",
            "",
        ]
    return lines


def _finding(index: int, finding: Finding, probes: tuple[ProbeRecord, ...]) -> list[str]:
    measurement = finding.measurement
    lines = [f"{index}. {statement(finding)}", ""]

    comparison = (
        f"{measurement.rate:.0%} of the time, against {measurement.peer_rate:.0%} "
        "for players at your level"
        if measurement.peer_rate is not None
        else f"{measurement.rate:.0%} of the time"
    )
    lines.append(f"   How often   {comparison}")
    lines.append(
        f"   Seen in     {measurement.distinct_games} of {measurement.games_with_data} games"
    )

    # The line that answers "why should I care?", where it can be answered.
    cost = measurement.cost_per_game
    excess = measurement.excess_cost_per_game
    if cost is not None and cost >= NEGLIGIBLE_COST_PER_GAME:
        lines.append(f"   Costing you about {cost:.1f} points of win probability a game.")
        if excess is not None and measurement.peer_cost_per_game is not None:
            # The honest ceiling is the *excess*, not the whole cost. Playing
            # this perfectly is not on offer; playing it the way players at the
            # same level do is, so that difference is what a plan can promise.
            lines.append(
                f"   Players at your level lose about "
                f"{measurement.peer_cost_per_game:.1f} to the same thing, so roughly"
            )
            lines.append(f"   {excess:.1f} a game is what fixing this could get back.")
        else:
            lines.append(
                "   That is what these moves gave away, and the most you could get back."
            )

    for evidence in finding.evidence[:EVIDENCE_SHOWN]:
        played = f", you played {evidence.move_played}" if evidence.move_played else ""
        # Never "you played c8e6 (c8e6 was better)". A section can legitimately
        # cite a position where the player found the best move — the claim may be
        # about the position rather than the move — and the alternative is only
        # worth printing when it is genuinely an alternative.
        better = (
            f" ({evidence.better_move} was better)"
            if evidence.better_move and evidence.better_move != evidence.move_played
            else ""
        )
        lines.append(f"   For example game {evidence.game_id}, move {move_number(evidence.ply)}"
                     f"{played}{better}")

    for line in _gap_meaning(finding, probes):
        lines += ["", f"   {line}"]
    return lines + [""]


def _gap_meaning(finding: Finding, probes: tuple[ProbeRecord, ...]) -> list[str]:
    """Only said when a probe established it, and never without its provenance.

    An inferred gap type is a guess, and dressing a guess in an explanation is
    how a report stops being honest. A *probed* one is better evidence and still
    thin: one position, read by a classifier whose agreement was measured against
    a rubric its own author wrote (D10). The reader is told both things, because
    a sentence like "the pattern is there" carries more authority than one probe
    can support.
    """
    if finding.gap_type.determined_by is not DeterminedBy.PROBED:
        return []

    meaning = GAP_MEANING.get(finding.gap_type.hypothesis.value)
    if meaning is None:
        return []

    asked = sum(1 for p in probes if p.finding_id == finding.id)
    judged = any(
        p.finding_id == finding.id and p.was_actually_asked for p in probes
    )
    provenance = (
        f"(From {asked} question{'s' if asked != 1 else ''} you answered"
        + (", read by a local model that agrees with its own rubric about three times in four."
           if judged
           else ", where the move was checked but the reason was not read.")
        + " Worth weighing accordingly.)"
    )
    return [meaning, provenance]


def _plan_section(profile: PlayerProfile) -> list[str]:
    if profile.plan is None or not profile.plan.steps:
        return []

    lines = ["WHAT TO DO", ""]
    for index, step in enumerate(profile.plan.steps, start=1):
        lines += [f"{index}. {step.action}", f"   Why    {step.why}", ""]

    lines += ["WHAT WOULD SHOW IT WORKED", ""]
    for step in profile.plan.steps:
        finding = next((f for f in profile.findings if f.id == step.finding_id), None)
        name = quantity(finding) if finding else step.finding_id
        if step.target_rate is None:
            # Plans written before schema v3 carry a progress sign in prose and
            # no number behind it. Saying "below lower" would be pretending to a
            # target; saying so plainly is what the sign is actually worth.
            lines.append(f" - {name}: no checkable target — this plan predates them")
        else:
            lines.append(
                f" - {name}: below {step.target_rate:.0%} "
                f"over your next {step.check_after_games} games"
            )
    return lines + [""]


def _not_assessed(profile: PlayerProfile) -> list[str]:
    """Silence implies competence, so the gaps are named.

    Written from the findings actually present rather than from a fixed list of
    sections, so it cannot claim to have assessed something that was never run.
    """
    declined = [f for f in profile.findings if f.status == "insufficient_data"]
    if not declined:
        return []

    lines = ["WHAT COULD NOT BE ASSESSED", ""]
    for finding in declined:
        lines.append(f" - {quantity(finding)}: too few games where it came up to say anything")
    return lines + [""]


EXCLUSION_WORDING = {
    "berserked": (
        "{count} of your games were left out because you berserked them — with half "
        "your clock, the mistakes are about the handicap rather than about you."
    ),
    "abandoned": "{count} of your games were left out because they were abandoned before a real game happened.",
}


def _limits(profile: PlayerProfile) -> list[str]:
    limits = list(LIMITS)

    for reason, count in profile.corpus.excluded:
        wording = EXCLUSION_WORDING.get(reason)
        if wording and count:
            # Said in the report rather than only in the corpus record: a player
            # who brought 24 games and is being told about 21 can otherwise not
            # tell that anything was dropped.
            limits.insert(0, wording.format(count=count))

    if _priced_count(profile) > 1:
        # Two costs on the page invite the reader to add them, and the sum would
        # be wrong: one blunder under time pressure in a rook endgame is an
        # instance of both claims. The numbers rank against each other; they do
        # not accumulate (E15).
        limits.append(
            "The two costs above should not be added together — a single mistake can "
            "belong to both patterns, so the totals overlap by an unknown amount."
        )

    elsewhere = profile.context.plays_elsewhere if profile.context else None
    if elsewhere:
        # The player named a blind spot. Repeating it here is the difference
        # between a limitation they stated and one the report has quietly
        # inherited without saying so.
        limits.insert(
            0,
            f"You said you also play here: {elsewhere}. None of those games are in "
            "this, so anything that only happens there is invisible to all of it.",
        )
    return ["WHAT THIS DOES NOT KNOW", ""] + [f" - {limit}" for limit in limits]
