"""Questions about the player's own positions, answered from the profile without a model.

Design: docs/notes/design.narrated-session.md

Found by the author on her own session. *"Can you tell me from my own games where
I miss pins"* was refused, although her profile held four positions for exactly
that finding: it was measured, and not planned -- half an hour a week buys one
priority -- so the report never printed its positions, and the follow-up model
reads only the report. The positions and the advice are already in the profile.
Showing them needs a lookup, not a model, and a lookup cannot misquote them.

Two kinds of question are recognised, in English and Croatian:

  * **where** -- *"where do I miss pins?"*, *"gdje propuštam vezivanja?"*: the
    finding's own sampled positions, with the move played, the better move and
    a link;
  * **how to practise** -- *"how to practice pins?"*: the planner's advice for
    that finding, the same sentence the plan would print.

Anything else returns None and goes on to the model.
"""

from __future__ import annotations

import re

from chesscoach.exercise import link_before
from chesscoach.phrasing import move_number, statement
from chesscoach.planner import action_for
from chesscoach.profile.models import Finding, PlayerProfile

MAX_POSITIONS = 4

# Motif subjects and the words a player uses for them, English and Croatian stems.
_SUBJECT_WORDS: dict[str, tuple[str, ...]] = {
    "pin": ("pin", "vezivanj", "vezan"),
    "fork": ("fork", "rašlj", "raslj"),
    "skewer": ("skewer", "nabadanj"),
    "discoveredAttack": ("discovered", "otkriven"),
    "hangingPiece": ("hanging piece", "undefended piece", "ostavljen figur", "nebranjen"),
    "hangingPawn": ("free pawn", "hanging pawn", "dropped pawn", "pješak", "pjesak", "pješa"),
    "trappedPiece": ("trapped", "zarobljen"),
    "backRankMate": ("back rank", "back-rank", "zadnjem redu", "zadnji red"),
    "capturingDefender": ("defender", "branitelj"),
}
# Claim kinds with no motif subject, recognised by what they are about.
_KIND_WORDS: dict[str, tuple[str, ...]] = {
    "time_pressure_error": ("short of time", "time trouble", "clock", "vremensk", "stisc"),
    "long_think_error": ("long think", "think long", "dugo razmi"),
    "instant_move_error": ("instant", "too fast", "prebrzo", "odmah"),
}

_WHERE = re.compile(
    r"\b(where|which (games|positions|moves)|show|example|examples|when did|"
    r"gdje|pokaži|pokazi|primjer|primjere|u kojim)", re.IGNORECASE)
_PRACTISE = re.compile(
    r"(practi[cs]|train|drill|get better|improve|vježb|vjezb|trenir|poboljš|popravi)",
    re.IGNORECASE)
_MISSED = re.compile(r"(miss|propu)", re.IGNORECASE)
_ALLOWED = re.compile(r"(allow|concede|punish|dopu|kažnj|kaznj)", re.IGNORECASE)


def from_profile(question: str, profile: PlayerProfile | None) -> str | None:
    """The answer from the profile, or None if the question is not this kind."""
    if profile is None or not question:
        return None
    where = bool(_WHERE.search(question))
    practise = bool(_PRACTISE.search(question))
    if not (where or practise):
        return None
    findings = _matching(question, profile)
    if not findings:
        return None
    planned = {step.finding_id for step in profile.plan.steps} if profile.plan else set()
    if where:
        return "\n\n".join(_positions(f, f.id in planned) for f in findings)
    return "\n\n".join(f"{statement(f)}\n{action_for(f)}" for f in findings)


def _matching(question: str, profile: PlayerProfile) -> list[Finding]:
    text = question.lower()
    subjects = {s for s, words in _SUBJECT_WORDS.items() if any(w in text for w in words)}
    kinds = {k for k, words in _KIND_WORDS.items() if any(w in text for w in words)}
    found = [f for f in profile.findings if f.evidence and (
        f.claim.subject in subjects or f.claim.kind in kinds)]
    missed, allowed = bool(_MISSED.search(question)), bool(_ALLOWED.search(question))
    if missed != allowed:
        wanted = "missed_motif" if missed else "allowed_motif"
        narrowed = [f for f in found if f.claim.kind == wanted]
        found = narrowed or found
    return found


def _positions(finding: Finding, planned: bool) -> str:
    m = finding.measurement
    share = f"{m.rate:.0%} of the times it could have happened"
    if m.peer_rate is not None:
        share += f", against {m.peer_rate:.0%} for players at your level"
    note = "" if planned else " It was measured in your games but is not in your plan this time."
    lines = [f"{statement(finding)} Seen in {m.distinct_games} of {m.games_with_data} games, "
             f"{share}.{note}", "From your games:"]
    for evidence in finding.evidence[:MAX_POSITIONS]:
        played = evidence.played_san
        better = evidence.better_san
        move = f"move {move_number(evidence.ply)}"
        what = (f"you played {played}" if played else "")
        if better:
            what += f" ({better} was better)" if what else f"{better} was better"
        lines.append(f" - {move}, {what}, {link_before(evidence)}".replace(", ,", ","))
    return "\n".join(lines)
