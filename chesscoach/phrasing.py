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
    "hangingPawn": "free pawn",
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
    "time_budget_error": "mistakes after move 15 in games where the clock went early",
    "endgame_error": "mistakes in {subject} endgames",
    "advantage_error": "mistakes made while you are winning",
    "early_error": "mistakes before move 15 {subject}",
    "opening_disadvantage": "games where you are already worse by move 15",
    "concedes_weakness": "moves that leave you with {subject} pawns",
    "allows_square": "moves that let your opponent establish {subject}",
    "allows_pressure": "moves that let an attack build against your king",
    "moved_into_attack": "moves that leave the piece you moved takeable",
    "miscounted_exchange": (
        "exchanges you start that lose material, with no attack on the king behind them"
    ),
    "sacrificed_for_attack": "material given up to attack the king",
    "out_of_book": "moves played outside known theory in the {subject}",
    "pawn_error": "pawn pushes played instead of developing that went wrong",
    "repeat_move": "moves of a piece you had already moved",
    "late_castling": "games where the king stayed in the centre while you drifted",
    "slow_development": "games where your pieces came out late",
}

# The finding as a sentence a person would say. Deliberately flat: no severity
# adjectives, no "worryingly", nothing the evidence does not carry.
STATEMENTS: dict[str, str] = {
    "missed_motif": "You miss {subject} tactics that were available.",
    "allowed_motif": "When you go wrong, it is often a {subject} that punishes you.",
    "long_think_error": "Your long thinks tend to end in a mistake.",
    "instant_move_error": "Moves you play instantly go wrong more often than they should.",
    "time_pressure_error": "Your play falls off when the clock is short.",
    # Says where the cost lands rather than where it was incurred: the long think
    # itself is not the mistake, and telling a player to think less would be the
    # wrong advice drawn from the right measurement.
    "time_budget_error": (
        "When you use up most of your clock before move 15, the rest of that game "
        "goes worse — the cost of a long think lands later, not on the move itself."
    ),
    "endgame_error": "Your play falls off in {subject} endgames.",
    "advantage_error": "You go wrong more often than most when you are already better.",
    "early_error": "You go wrong early {subject}.",
    "opening_disadvantage": "You come out of the opening worse more often than most.",
    # Says what was measured and stops. E03 found no link between structural
    # features and this band's errors, so anything implying cost -- "this is
    # losing you games" -- would be a claim the evidence does not support.
    "concedes_weakness": "You end up with {subject} pawns more often than players at your level.",
    "allows_square": "You let opponents establish {subject} more often than players at your level.",
    "allows_pressure": (
        "Attacks build against your king more readily than against players at your level."
    ),
    # S7. Says what the player DID, not what punished them -- the whole point of
    # the section (D13, E34).
    "moved_into_attack": (
        "You put the piece you have just moved on a square where it can be won, "
        "more often than players at your level."
    ),
    # The five development and opening claims (E58-E62) shipped without any
    # phrasing, so every one of them reached a player as a raw claim key --
    # "pawn_error: any." in the report and "Work on any:" in the plan. That is
    # the **D8 defect** the `out_of_book` note below warns about, and splitting
    # `out_of_book` per opening reintroduced it for the per-opening subjects,
    # which are not POOLED and so fall through the pooled entry.
    "out_of_book": (
        "You leave known theory sooner than players at your level when you play "
        "the {subject}."
    ),
    "pawn_error": (
        "When you push a pawn instead of developing a piece, it goes wrong more "
        "often than it does for players at your level."
    ),
    "repeat_move": (
        "You move the same piece again while another is still at home, more often "
        "than players at your level."
    ),
    # "Away from the kings" was the jargon and the author asked what it meant.
    # It is the half of the old claim that is **not** a sacrifice: a losing
    # capture within `material.ATTACK_RADIUS` of the enemy king is
    # `sacrificed_for_attack`, a deliberate idea whose soundness this project
    # does not judge; the same capture anywhere else is an exchange that simply
    # did not add up. The sentence now says that instead of naming the geometry.
    "miscounted_exchange": (
        "When you start an exchange with no attack on the enemy king behind it, "
        "it turns out to lose material more often than it does for players at "
        "your level."
    ),
    # Stated without a verdict. 43 % of these are sacrifices the engine did
    # not fault, so calling them mistakes would be wrong; the cost line below
    # it in the report is what tells the player whether theirs are working.
    "sacrificed_for_attack": (
        "You give up material to get at the enemy king more often than players "
        "at your level."
    ),
}

SUBJECT_QUANTITIES: dict[tuple[str, str], str] = {
    ("missed_motif", "hangingPawn"): "free pawns left uncaptured",
    ("allowed_motif", "hangingPawn"): "pawns dropped when you go wrong",
}

# Where the generic template would produce something a person would not say.
# "You miss free pawn tactics that were available" is grammatical and wrong:
# taking a free pawn is not a tactic, it is looking at the board.
SUBJECT_STATEMENTS: dict[tuple[str, str], str] = {
    # `late_castling` and `slow_development` are keyed by **basis**, not by a
    # chess subject: "book" is the norm for the opening being played and "own" is
    # the player's own habit. The design keeps them in separate claim keys so the
    # two can never pool, and they are different sentences for the same reason.
    #
    # `late_castling` also carries its gate: it counts only games where the
    # player was **drifting** while the king stayed at home
    # ([[design.castling-under-drift]]), so the sentence says so rather than
    # implying that castling late is a fault by itself.
    ("late_castling", "book"): (
        "In games where you were already drifting, your king stays in the centre "
        "longer than is usual in the openings you play."
    ),
    ("late_castling", "own"): (
        "In games where you were already drifting, your king stays in the centre "
        "longer than you usually leave it."
    ),
    ("slow_development", "book"): (
        "You finish developing later than is usual in the openings you play."
    ),
    ("slow_development", "own"): (
        "You finish developing later than you usually do."
    ),
    ("missed_motif", "hangingPawn"): (
        "You leave free pawns on the board — material that was there for the taking."
    ),
    ("allowed_motif", "hangingPawn"): (
        "When you go wrong, it is often a pawn you simply drop."
    ),
}

STRUCTURE_NAMES: dict[str, str] = {
    "isolated": "isolated",
    "backward": "backward",
    "doubled": "doubled",
}

SQUARE_NAMES: dict[str, str] = {
    "outpost": "a knight you cannot chase away",
    "rook_seventh": "a rook on your second rank",
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
    "allows_square": "moves that let your opponent settle into your position",
    "endgame_error": "mistakes in the endgame",
    "early_error": "mistakes before move 15",
    "opening_disadvantage": "games where you are already worse by move 15",
    "out_of_book": "opening moves played outside known theory",
}
POOLED_STATEMENTS: dict[str, str] = {
    "endgame_error": "Your play falls off in the endgame.",
    # The author's own reason for building this: "It is coaching to tell the
    # player that they don't know the opening". Said in those terms rather than
    # "your out_of_book rate is high" -- a raw claim key reaching a player is
    # the D8 defect, and `statement` falls through to exactly that without an
    # entry here.
    "out_of_book": (
        "You are out of known opening theory sooner than players at your level."
    ),
    "early_error": "You go wrong early, before the middlegame starts.",
    "opening_disadvantage": "You come out of the opening worse more often than most.",
    "concedes_weakness": (
        "Your moves leave weaknesses in your own pawn structure more often than "
        "players at your level."
    ),
    "allows_square": (
        "You let opponents settle pieces into your position more often than players "
        "at your level."
    ),
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
    if kind == "concedes_weakness":
        return STRUCTURE_NAMES.get(subject, subject)
    if kind == "allows_square":
        return SQUARE_NAMES.get(subject, subject)
    return MOTIF_NAMES.get(subject, subject)


def quantity(finding: Finding) -> str:
    """The measured quantity, named for a person."""
    kind, subject = finding.claim.kind, finding.claim.subject
    if subject == POOLED and kind in POOLED_QUANTITIES:
        return POOLED_QUANTITIES[kind]

    override = SUBJECT_QUANTITIES.get((kind, subject))
    if override is not None:
        return override

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

    override = SUBJECT_STATEMENTS.get((kind, subject))
    if override is not None:
        return override

    name = subject_name(subject, kind)
    template = STATEMENTS.get(kind)
    if template is None:
        return f"{kind}: {name}."
    return template.format(subject=name)


def move_number(ply: int) -> int:
    """Ply is internal; players count moves.

    `ply` is **1-based** — `analysis.core.analyse_game` sets `ply = index + 1` —
    so White's first move is ply 1 and Black's is ply 2, and both are move 1.
    The obvious-looking `ply // 2 + 1` gets White right and reports **every Black
    move one too high**, which is what the reviewer caught reading their own
    games against the reports.
    """
    return (ply + 1) // 2
