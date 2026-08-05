"""One coaching session, end to end.

Spec: docs/notes/architecture.interaction.md § 1

    analyse -> diagnose -> shortlist -> PROBE -> plan -> report

Steps 1-4 and 6-7 already existed as separate commands; this is the step that
was missing and the wiring that makes them one thing.

**The probe gate.** [[capacity.agents.prober]] § 4 forbids a probe result
changing a finding until the classifier's agreement is measured against answers
the author did not write and label (D10). That is unresolved, so probes run,
their answers are recorded, and `apply` defaults to **off**. The mechanism is
demonstrable; the diagnosis is not yet altered by it.

**Answers are appended to a dataset as a side effect.** D10 needs real phrasings
and collecting them as an exercise is expensive; collecting them as a by-product
of using the tool is free. What that fixes is *constructed rather than
collected* — it does not fix the labelling, which still needs a second person.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from chesscoach.arbiter import Selection, select_priorities
from chesscoach.planner import build_plan
from chesscoach.prober import ReasonClassifier, apply_to_findings, interpret, select_probes
from chesscoach.profile.models import PlayerProfile, ProbeRecord


@dataclass(frozen=True)
class Answer:
    """What the player said, before anything interprets it."""

    probe_id: str
    move: str | None
    reason: str | None


def probes_for(profile: PlayerProfile, limit: int | None = None):
    """The positions worth asking about, drawn from the shortlist."""
    selection = _selection(profile)
    if limit is None:
        return select_probes(selection.priorities)
    return select_probes(selection.priorities, limit=limit)


def record_answers(
    probes: tuple,
    answers: tuple[Answer, ...],
    classifier: ReasonClassifier | None,
) -> tuple[ProbeRecord, ...]:
    """Interpret each answer against the probe it belongs to."""
    by_id = {answer.probe_id: answer for answer in answers}
    return tuple(
        interpret(probe, by_id[probe.id].move, by_id[probe.id].reason, classifier)
        for probe in probes
        if probe.id in by_id
    )


def apply_probes(
    profile: PlayerProfile, records: tuple[ProbeRecord, ...], apply: bool = False
) -> PlayerProfile:
    """Store the probes; change the findings only when explicitly allowed.

    The records are kept either way. A probe that was asked is evidence about
    the player whether or not the system currently trusts its interpretation,
    and discarding it would lose the very data D10 needs.
    """
    findings = apply_to_findings(profile.findings, records) if apply else profile.findings
    return replace(profile, findings=findings, probes=(*profile.probes, *records))


def replan(profile: PlayerProfile, **plan_args) -> PlayerProfile:
    """Rebuild the plan after probing, since a probe may have changed the picture."""
    selection = _selection(profile)
    return replace(
        profile,
        plan=build_plan(
            selection.priorities, created=date.today().isoformat(), **plan_args
        ),
    )


def append_to_answer_set(records: tuple[ProbeRecord, ...], path: Path) -> int:
    """Grow the D10 dataset from real use.

    Written **unlabelled**, with `label: null`, because the point is phrasings
    from someone who is not the author — inventing the label here would
    reintroduce exactly the problem it exists to fix.
    """
    usable = [r for r in records if r.player_reason and r.player_reason.strip()]
    if not usable:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in usable:
            handle.write(
                json.dumps(
                    {
                        "answer": record.player_reason,
                        "expected": record.expected_reason,
                        "label": None,
                        "source": "session",
                        "classifier_said": record.reason_matched,
                    }
                )
                + "\n"
            )
    return len(usable)


def _selection(profile: PlayerProfile) -> Selection:
    return select_priorities(profile.findings)
