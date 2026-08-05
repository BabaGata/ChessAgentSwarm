"""Asking the player, so a knowledge gap can be told from a skill gap.

Spec: docs/notes/capacity.agents.prober.md · docs/notes/architecture.interaction.md § 5
Decision: docs/notes/decisions.0009-prober-before-breadth.md

Every finding this swarm produces carries `gap_type: unknown`, and no section
agent can do better — a missed pin cannot distinguish *doesn't know the pattern*
from *knew it and didn't see it here* (L-002). That distinction decides the
remedy, so getting it wrong sends the player to study something that was never
wrong.

**This is the first module in the project that uses a language model, and the
boundary is narrow on purpose.** Position selection, the move check and the
gap-type decision are all deterministic. The model is handed one job — does this
sentence name that reason — with the reason already known, because it came from
a detector. It is never asked what the best move is, never asked to evaluate a
position, and never asked to produce chess advice (R-03, ADR-0002).

The consequence worth having: with no model available the move check still runs
and the verdict falls back to `unknown` rather than being guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from chesscoach.arbiter import Priority
from chesscoach.classifiers import ClassifierUnavailable, declines_to_answer
from chesscoach.profile.models import (
    ClassifierStatus,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    ProbeRecord,
)

# The player's attention is the scarcest resource in the system
# (architecture.interaction § 5).
MAX_PROBES = 6

# Only claims naming a pattern can be probed this way. A process claim already
# rests on an exogenous clock reading, so asking the player to solve a position
# untimed would tell us nothing we do not know.
PROBEABLE_KINDS = frozenset({"missed_motif", "allowed_motif"})

# Deliberately open, and deliberately silent about what to look for. "Is there a
# pin here?" teaches the answer and tests nothing.
PROMPT = "What would you play here, and why?"


class ReasonClassifier(Protocol):
    """Judges whether an answer names a reason. The only model in the system.

    Returns True/False, or **None when it cannot tell** — which is a real
    outcome, not an error, and is recorded rather than resolved by guessing.
    """

    name: str

    def classify(self, answer: str, expected_reason: str) -> bool | None: ...


@dataclass(frozen=True)
class Probe:
    """A question ready to put to the player, with its answer already known."""

    id: str
    finding_id: str
    fen: str
    asks: str
    game_id: str
    ply: int
    engine_best: str
    expected_reason: str


def probeable(finding: Finding) -> bool:
    """Is there a pattern here to ask about, and a right answer to check against?"""
    return finding.claim.kind in PROBEABLE_KINDS and any(
        evidence.better_move for evidence in finding.evidence
    )


def select_probes(
    findings: tuple[Finding, ...] | tuple[Priority, ...], limit: int = MAX_PROBES
) -> tuple[Probe, ...]:
    """One position per finding, in rank order, bounded.

    Deterministic: the evidence was already sampled uniformly when the finding
    was made, so taking the first usable position adds no new selection. Probing
    the *worst* blunder would make the probe easier than the weakness.
    """
    probes = []
    for finding in (_finding_of(item) for item in findings):
        if len(probes) >= limit:
            break
        if not probeable(finding):
            continue
        evidence = next((e for e in finding.evidence if e.better_move), None)
        if evidence is None:
            continue
        probes.append(_probe(finding, evidence))
    return tuple(probes)


def interpret(
    probe: Probe,
    move: str | None,
    reason: str | None,
    classifier: ReasonClassifier | None,
) -> ProbeRecord:
    """Turn an answer into a gap type, by the table in the agent note § 8.

    The order matters and is part of the contract: the move is checked first and
    decides the case on its own when it is wrong, so the model is not consulted
    at all for a failed probe.
    """
    if not move:
        return _record(
            probe, move, reason, None, None, None,
            GapTypeHypothesis.UNKNOWN, ClassifierStatus.NOT_CONSULTED,
        )

    if not _same_move(move, probe.engine_best):
        # Untimed, on their own game, with no clock: failing here is the
        # clearest evidence of a knowledge gap this system can obtain.
        return _record(
            probe, move, reason, None, False, None,
            GapTypeHypothesis.KNOWLEDGE, ClassifierStatus.NOT_CONSULTED,
        )

    matched, status = _classify(classifier, reason, probe.expected_reason)
    hypothesis = {
        True: GapTypeHypothesis.SKILL,
        False: GapTypeHypothesis.FRAGILE,
        None: GapTypeHypothesis.UNKNOWN,
    }[matched]
    name = classifier.name if classifier is not None else None
    return _record(probe, move, reason, name, True, matched, hypothesis, status)


def apply_to_findings(
    findings: tuple[Finding, ...], probes: tuple[ProbeRecord, ...]
) -> tuple[Finding, ...]:
    """Write the probe results back, leaving unprobed findings untouched.

    A probe that concluded nothing does **not** mark the finding as probed:
    recording "we asked and learned nothing" as `determined_by: probed` would
    overstate the evidence behind what is still a guess.
    """
    by_finding: dict[str, ProbeRecord] = {}
    for probe in probes:
        if probe.inference and probe.inference != GapTypeHypothesis.UNKNOWN.value:
            by_finding[probe.finding_id] = probe

    return tuple(_probed(finding, by_finding.get(finding.id)) for finding in findings)


# --- internals --------------------------------------------------------------


def _finding_of(item: Finding | Priority) -> Finding:
    return item.finding if isinstance(item, Priority) else item


def _probe(finding: Finding, evidence: Evidence) -> Probe:
    return Probe(
        id=f"probe.{finding.id}.{evidence.game_id}.{evidence.ply}",
        finding_id=finding.id,
        fen=evidence.fen,
        asks=PROMPT,
        game_id=evidence.game_id,
        ply=evidence.ply,
        engine_best=evidence.better_move or "",
        # The motif name *is* the reason, and it came from a detector rather
        # than from a model. This is what keeps the agent clear of R-03.
        expected_reason=finding.claim.subject,
    )


# Characters that carry no meaning and survive `str.strip()`, because Python
# does not classify them as whitespace. A byte-order mark on the front of a
# pasted or piped answer is invisible, and without this it turns a correct move
# into a wrong one -- which manufactures a knowledge gap the player does not
# have. Found exactly that way, in the first real probe session.
INVISIBLE = "﻿​‌‍⁠"


def _same_move(played: str, best: str) -> bool:
    """Tolerant of spacing, case and invisible characters; never of content.

    Deliberately not a chess-aware comparison: `better_move` and the answer are
    both notation for the same position, and a looser match would start
    accepting moves the engine did not name.
    """
    return _normalise(played) == _normalise(best)


def _normalise(move: str) -> str:
    return move.strip(INVISIBLE + " \t\r\n").casefold()


def _classify(
    classifier: ReasonClassifier | None, reason: str | None, expected: str
) -> tuple[bool | None, ClassifierStatus]:
    """The verdict, and why it is that verdict.

    The status is the point: all four cases below produce `None`, and without it
    a profile cannot say whether the player was vague or the model was never
    running. A probe session against a stopped backend used to look identical to
    one where nobody could explain themselves.
    """
    if classifier is None:
        return None, ClassifierStatus.NOT_CONFIGURED
    if reason is None or declines_to_answer(reason):
        # Checked here rather than left to the classifier so that "I don't know"
        # is recorded as the player declining, not as the model failing to tell.
        # Whether a reason was offered at all is a property of the utterance
        # (E07), so it belongs with the inference table, not inside a model.
        return None, ClassifierStatus.DECLINED

    try:
        matched = classifier.classify(reason, expected)
    except ClassifierUnavailable:
        # Degrade, do not fail: one unreachable model must not end a session the
        # player is part way through. But say so in the record.
        return None, ClassifierStatus.UNAVAILABLE

    if matched is None:
        return None, ClassifierStatus.UNCLEAR
    return matched, ClassifierStatus.ANSWERED


def _record(
    probe: Probe,
    move: str | None,
    reason: str | None,
    classifier_name: str | None,
    move_correct: bool | None,
    reason_matched: bool | None,
    hypothesis: GapTypeHypothesis,
    status: ClassifierStatus,
) -> ProbeRecord:
    return ProbeRecord(
        id=probe.id,
        finding_id=probe.finding_id,
        fen=probe.fen,
        asks=probe.asks,
        player_move=move,
        player_reason=reason,
        engine_best=probe.engine_best,
        inference=hypothesis.value,
        expected_reason=probe.expected_reason,
        move_correct=move_correct,
        reason_matched=reason_matched,
        classifier=classifier_name,
        classifier_status=status.value,
    )


def _probed(finding: Finding, probe: ProbeRecord | None) -> Finding:
    if probe is None:
        return finding

    return replace(
        finding,
        gap_type=GapType(
            hypothesis=GapTypeHypothesis(probe.inference),
            determined_by=DeterminedBy.PROBED,
            probe_ids=(*finding.gap_type.probe_ids, probe.id),
        ),
    )
