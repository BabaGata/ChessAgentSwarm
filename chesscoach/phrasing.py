"""Plain names for the things the swarm measures.

Extracted because the planner and the explainer both need to say what a claim is
about, in the same words. Two copies would drift, and the failure would be
silent: a plan step and the report explaining it would describe the same
measurement differently, which reads as two different findings.

Nothing here is generated. These are fixed phrasings for a closed set of claim
kinds, so what a player reads is reproducible and reviewable — a language model
writing them would be prose nobody had checked (R-02, R-03).
"""

from __future__ import annotations

from chesscoach.profile.models import Finding

# What is being counted, in the player's terms rather than the schema's.
QUANTITIES: dict[str, str] = {
    "missed_motif": "{subject} missed when available",
    "allowed_motif": "{subject} conceded when you go wrong",
    "long_think_error": "mistakes after a long think",
    "instant_move_error": "mistakes after an instant reply",
    "time_pressure_error": "mistakes when short of time",
}

# The finding as a sentence a person would say. Deliberately flat: no severity
# adjectives, no "worryingly", nothing the evidence does not carry.
STATEMENTS: dict[str, str] = {
    "missed_motif": "You miss {subject} tactics that were available.",
    "allowed_motif": "When you go wrong, it is often a {subject} that punishes you.",
    "long_think_error": "Your long thinks tend to end in a mistake.",
    "instant_move_error": "Moves you play instantly go wrong more often than they should.",
    "time_pressure_error": "Your play falls off when the clock is short.",
}


def quantity(finding: Finding) -> str:
    """The measured quantity, named for a person."""
    template = QUANTITIES.get(finding.claim.kind)
    if template is None:
        return f"{finding.claim.kind} rate ({finding.claim.subject})"
    return template.format(subject=finding.claim.subject)


def statement(finding: Finding) -> str:
    """The finding as one sentence."""
    template = STATEMENTS.get(finding.claim.kind)
    if template is None:
        return f"{finding.claim.kind}: {finding.claim.subject}."
    return template.format(subject=finding.claim.subject)


def move_number(ply: int) -> int:
    """Ply is internal; players count moves."""
    return ply // 2 + 1
