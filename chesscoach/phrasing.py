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

# Motif subjects are CC0 Lichess theme keys, chosen deliberately so the same name
# identifies a weakness and selects the training material. They are camelCase
# identifiers, and a player has no idea what a `trappedPiece` is — so they are
# translated on the way out and nowhere else. The key stays the key.
MOTIF_NAMES: dict[str, str] = {
    "fork": "fork",
    "pin": "pin",
    "skewer": "skewer",
    "discoveredAttack": "discovered attack",
    "hangingPiece": "hanging piece",
    "trappedPiece": "trapped piece",
    "backRankMate": "back-rank mate",
    "capturingDefender": "capturing the defender",
    "quietMove": "quiet move",
    "defensiveMove": "defensive move",
}

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


def subject_name(subject: str) -> str:
    """A motif's name as a person would write it.

    Falls back to the key rather than inventing a spacing rule, so an unmapped
    motif looks unfinished instead of looking like a word.
    """
    return MOTIF_NAMES.get(subject, subject)


def quantity(finding: Finding) -> str:
    """The measured quantity, named for a person."""
    template = QUANTITIES.get(finding.claim.kind)
    if template is None:
        return f"{finding.claim.kind} rate ({subject_name(finding.claim.subject)})"
    return template.format(subject=subject_name(finding.claim.subject))


def statement(finding: Finding) -> str:
    """The finding as one sentence."""
    template = STATEMENTS.get(finding.claim.kind)
    if template is None:
        return f"{finding.claim.kind}: {subject_name(finding.claim.subject)}."
    return template.format(subject=subject_name(finding.claim.subject))


def move_number(ply: int) -> int:
    """Ply is internal; players count moves."""
    return ply // 2 + 1
