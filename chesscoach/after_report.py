"""What the session does around the report: a summary before it, questions and
practice after it.

Design: docs/notes/design.narrated-session.md

Kept out of `cli.py` so the dialogue is testable without a terminal: every
function takes a `read` and a `write`, and the CLI passes `input` and `print`.
Each part is optional and each degrades to the session as it was before -- no
summary, no questions, no practice -- saying why in one line rather than failing.
"""

from __future__ import annotations

from chesscoach.exercise import check, exercises_for, record
from chesscoach.followup import Source, answer_followup
from chesscoach.narrator import narrate
from chesscoach.profile.models import PlayerProfile

SUMMARY_HEADING = "IN SHORT"
SUMMARY_NOTE = ("   Written by a local language model from the measurements below, and "
                "checked against them.")


def summary_lines(profile: PlayerProfile, *, model: str | None = None,
                  transport=None) -> list[str]:
    """The summary block to print above the report, or one line saying why not."""
    kwargs = {"transport": transport}
    if model:
        kwargs["model"] = model
    narration = narrate(profile, **kwargs)
    if not narration.accepted:
        return [f"(no summary: {narration.reason})", ""]
    lines = [SUMMARY_HEADING, "", _indent(_wrap(narration.text)), "", SUMMARY_NOTE]
    if narration.reason:
        lines.append(f"   ({narration.reason.split(':')[0]}, because the check rejected "
                     "what the model wrote about them.)")
    return lines + [""]


def ask_questions(report: str, read, write, *, store=None, model: str | None = None,
                  transport=None, limit: int = 10) -> int:
    """Answer the player's questions until they stop. Returns how many were asked."""
    write("\nYou can ask about your report, or about a chess idea in it. "
          "An empty line ends the questions.")
    asked = 0
    while asked < limit:
        question = _read(read, "\n  question > ")
        if not question:
            break
        asked += 1
        kwargs = {"store": store, "transport": transport}
        if model:
            kwargs["model"] = model
        reply = answer_followup(question, report, **kwargs)
        write("\n" + _indent(reply.text))
        if reply.source is Source.UNAVAILABLE:
            break
    return asked


def practise(profile: PlayerProfile, read, write) -> PlayerProfile:
    """Offer positions from the player's own games, and record the attempts."""
    exercises = exercises_for(profile)
    if not exercises:
        return profile
    write(f"\nWant to try {len(exercises)} position{'s' if len(exercises) != 1 else ''} "
          "from your own games, where the engine found a better move? (y/n)")
    if _read(read, "  > ").lower() not in ("y", "yes", "d", "da"):
        return profile

    answered = []
    for number, exercise in enumerate(exercises, start=1):
        write(f"\n--- {number}/{len(exercises)}  {exercise.about}")
        write(f"   your game, move {exercise.move}: {exercise.where}")
        write(_board(exercise.fen))
        move = _read(read, "   your move > ")
        write("   " + check(exercise, move).feedback)
        answered.append((exercise, move))
    return record(profile, tuple(answered))


def _board(fen: str) -> str:
    """The position as a board a person can read, from the side to move."""
    import chess

    try:
        board = chess.Board(fen)
    except ValueError:
        return f"   position  {fen}"
    rows = str(board if board.turn else board.transform(chess.flip_vertical)
               .transform(chess.flip_horizontal)).splitlines()
    side = "White" if board.turn else "Black"
    return "\n".join(["", *("      " + row for row in rows), "",
                      f"   {side} to move.  ({fen})"])


def _read(read, prompt: str) -> str:
    try:
        return (read(prompt) or "").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _wrap(text: str, width: int = 92) -> str:
    """Wrap to the report's width, keeping the model's sentences as they are."""
    import textwrap

    return "\n".join(textwrap.wrap(text, width=width))


def _indent(text: str) -> str:
    return "\n".join("   " + line if line.strip() else line for line in text.splitlines())
