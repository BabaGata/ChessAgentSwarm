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
    "endgame_error": "mistakes in {subject} endgames",
    "advantage_error": "mistakes made while you are winning",
    "early_error": "mistakes before move 15 {subject}",
    "opening_disadvantage": "games where you are already worse by move 15",
}

# The finding as a sentence a person would say. Deliberately flat: no severity
# adjectives, no "worryingly", nothing the evidence does not carry.
STATEMENTS: dict[str, str] = {
    "missed_motif": "You miss {subject} tactics that were available.",
    "allowed_motif": "When you go wrong, it is often a {subject} that punishes you.",
    "long_think_error": "Your long thinks tend to end in a mistake.",
    "instant_move_error": "Moves you play instantly go wrong more often than they should.",
    "time_pressure_error": "Your play falls off when the clock is short.",
    "endgame_error": "Your play falls off in {subject} endgames.",
    "advantage_error": "You go wrong more often than most when you are already better.",
    "early_error": "You go wrong early {subject}.",
    "opening_disadvantage": "You come out of the opening worse more often than most.",
}

# Colours read as a phrase rather than a word, so the sentence works either way.
COLOURS: dict[str, str] = {"white": "as White", "black": "as Black"}

# Endgame material classes.
ENDGAME_CLASSES: dict[str, str] = {
    "pawn": "pawn",
    "rook": "rook",
    "minor": "minor-piece",
    "rook_minor": "rook-and-minor",
    "queen": "queen",
}

# The pooled subject. It cannot share the class templates — substituting a name
# into "{subject} endgames" gives "the endgames", which no one would say — so
# the pooled claim gets its own wording rather than a word chosen to fit a slot.
POOLED = "any"

POOLED_QUANTITIES: dict[str, str] = {
    "endgame_error": "mistakes in the endgame",
    "early_error": "mistakes before move 15",
    "opening_disadvantage": "games where you are already worse by move 15",
}
POOLED_STATEMENTS: dict[str, str] = {
    "endgame_error": "Your play falls off in the endgame.",
    "early_error": "You go wrong early, before the middlegame starts.",
    "opening_disadvantage": "You come out of the opening worse more often than most.",
}


def subject_name(subject: str, kind: str | None = None) -> str:
    """A subject's name as a person would write it.

    Which vocabulary applies depends on the claim: motif subjects are Lichess
    theme keys, endgame subjects are material classes. Falls back to the key
    rather than inventing a spacing rule, so an unmapped subject looks
    unfinished instead of looking like a word someone chose.
    """
    if kind == "endgame_error":
        return ENDGAME_CLASSES.get(subject, subject)
    if kind == "early_error":
        return COLOURS.get(subject, subject)
    return MOTIF_NAMES.get(subject, subject)


def quantity(finding: Finding) -> str:
    """The measured quantity, named for a person."""
    kind, subject = finding.claim.kind, finding.claim.subject
    if subject == POOLED and kind in POOLED_QUANTITIES:
        return POOLED_QUANTITIES[kind]

    name = subject_name(subject, kind)
    template = QUANTITIES.get(kind)
    if template is None:
        return f"{kind} rate ({name})"
    return template.format(subject=name)


def statement(finding: Finding) -> str:
    """The finding as one sentence."""
    kind, subject = finding.claim.kind, finding.claim.subject
    if subject == POOLED and kind in POOLED_STATEMENTS:
        return POOLED_STATEMENTS[kind]

    name = subject_name(subject, kind)
    template = STATEMENTS.get(kind)
    if template is None:
        return f"{kind}: {name}."
    return template.format(subject=name)


def move_number(ply: int) -> int:
    """Ply is internal; players count moves."""
    return ply // 2 + 1
