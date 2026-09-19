"""Practice from the player's own games: the prober's move check, without its diagnosis.

Design: docs/notes/design.narrated-session.md · The prober: [[capacity.agents.prober]]

The prober was built to tell a gap in knowledge from a gap in skill, and that use
is still closed: its classifier's agreement rests on answers the author wrote and
labelled (D10). What it does well without a classifier is the first half -- show
a position from the player's own game and check the move they give -- and that is
a useful exercise on its own: *here is the moment it went wrong for you; what do
you play now?*

So an exercise:

  * comes from a finding in the player's plan, one position each, the first
    sampled position where the engine named a better move. Any claim kind
    qualifies, not only motifs, because this is practice rather than diagnosis;
  * is checked deterministically, by the same comparison the prober uses;
  * is recorded on the profile as a probe, **and changes nothing else**. The
    finding, its gap type and the plan stay as they were.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import chess

from chesscoach.humaninput import clean
from chesscoach.phrasing import move_number, quantity
from chesscoach.profile.models import Finding, PlayerProfile, ProbeRecord

ASKS = "What would you play here?"


@dataclass(frozen=True)
class Exercise:
    """One position to try, with the answer already known."""

    finding_id: str
    about: str
    fen: str
    move: int
    played: str | None
    better_move: str
    where: str
    # The engine's move as stored (UCI). `better_move` is it in SAN, for showing.
    better_uci: str = ""


@dataclass(frozen=True)
class Result:
    correct: bool
    feedback: str


def exercises_for(profile: PlayerProfile) -> tuple[Exercise, ...]:
    """One position for each finding the plan acts on, in plan order."""
    if profile.plan is None:
        return ()
    by_id = {finding.id: finding for finding in profile.findings}
    exercises = []
    for step in profile.plan.steps:
        finding = by_id.get(step.finding_id)
        exercise = _exercise(finding) if finding else None
        if exercise is not None:
            exercises.append(exercise)
    return tuple(exercises)


def check(exercise: Exercise, answer: str | None) -> Result:
    """Is it the engine's move? Said with both moves either way."""
    given = clean(answer or "")
    if given and _is_the_move(given, exercise):
        return Result(True, f"Yes. {exercise.better_move} is the engine's choice here.")
    in_game = (f"In the game you played {exercise.played}, and the engine's choice was "
               if exercise.played else "The engine's choice was ")
    opening = "" if not given else "Not the engine's move. "
    return Result(False, f"{opening}{in_game}{exercise.better_move}.")


def record(profile: PlayerProfile, answered) -> PlayerProfile:
    """Store each attempt as a probe. Nothing the system believes changes."""
    records = tuple(_as_probe(exercise, answer) for exercise, answer in answered)
    return replace(profile, probes=(*profile.probes, *records))


def _exercise(finding: Finding) -> Exercise | None:
    evidence = next((e for e in finding.evidence if e.better_move), None)
    if evidence is None:
        return None
    return Exercise(
        finding_id=finding.id,
        about=quantity(finding),
        fen=evidence.fen,
        move=move_number(evidence.ply),
        played=evidence.played_san,
        better_move=evidence.better_san or evidence.better_move,
        where=evidence.citation(),
        better_uci=evidence.better_move,
    )


def _is_the_move(given: str, exercise: Exercise) -> bool:
    """Read the answer on the board, so SAN, UCI and a lower-case piece all count.

    E90: moves are stored as UCI and the report prints SAN, so a plain text
    comparison marked the move the player had just read as wrong.
    """
    if given.casefold() in {exercise.better_move.casefold(), exercise.better_uci.casefold()}:
        return True
    try:
        board = chess.Board(exercise.fen)
    except ValueError:
        return False
    for candidate in (given, given[:1].upper() + given[1:]):
        move = _parse(board, candidate)
        if move is not None and move.uci() == exercise.better_uci:
            return True
    return False


def _parse(board: chess.Board, text: str) -> chess.Move | None:
    try:
        return board.parse_san(text)
    except ValueError:
        pass
    try:
        move = chess.Move.from_uci(text.lower())
    except ValueError:
        return None
    return move if move in board.legal_moves else None


def _as_probe(exercise: Exercise, answer: str | None) -> ProbeRecord:
    given = clean(answer or "") or None
    return ProbeRecord(
        id=f"exercise.{exercise.finding_id}.{exercise.where}",
        finding_id=exercise.finding_id,
        fen=exercise.fen,
        asks=ASKS,
        player_move=given,
        engine_best=exercise.better_uci or exercise.better_move,
        move_correct=check(exercise, answer).correct if given else None,
    )
