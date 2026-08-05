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
        + _findings_section(profile)
        + _plan_section(profile)
        + _not_assessed(profile)
        + _limits()
    )


def _header(profile: PlayerProfile) -> list[str]:
    corpus = profile.corpus
    span = f" ({corpus.date_range[0]} to {corpus.date_range[1]})" if corpus.date_range else ""
    return [
        f"Report for {profile.player.username}",
        f"{corpus.n_games} games{span}, rating band {profile.player.band or 'unspecified'}",
        "",
    ]


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

    for evidence in finding.evidence[:EVIDENCE_SHOWN]:
        played = f", you played {evidence.move_played}" if evidence.move_played else ""
        better = f" ({evidence.better_move} was better)" if evidence.better_move else ""
        lines.append(f"   For example game {evidence.game_id}, move {move_number(evidence.ply)}"
                     f"{played}{better}")

    meaning = _gap_meaning(finding, probes)
    if meaning:
        lines += ["", f"   {meaning}"]
    return lines + [""]


def _gap_meaning(finding: Finding, probes: tuple[ProbeRecord, ...]) -> str | None:
    """Only said when a probe established it. An inferred gap type is a guess,
    and dressing a guess in an explanation is how a report stops being honest."""
    if finding.gap_type.determined_by is not DeterminedBy.PROBED:
        return None
    return GAP_MEANING.get(finding.gap_type.hypothesis.value)


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


def _limits() -> list[str]:
    return ["WHAT THIS DOES NOT KNOW", ""] + [f" - {limit}" for limit in LIMITS]
