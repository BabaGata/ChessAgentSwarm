"""The four questions no amount of analysis can answer.

Spec: docs/notes/architecture.interaction.md step 2 · docs/notes/domain.signals.md § 3

Asked **before** the engine runs, not after: analysis takes minutes, and a person
who has just answered four questions is more willing to wait than one who has
been staring at a progress bar.

Only one answer changes what the swarm decides. `weekly_study_hours` sets how
many priorities the plan carries, because *"a plan that assumes six hours for a
player with two is a plan that fails and teaches the player the system does not
know them"*. The other three change what the report can honestly say, which is a
smaller job and still worth doing — `plays_elsewhere` in particular converts a
silent blind spot into a stated one.

Nothing here interprets free text. Goals and what-you-have-tried are stored
verbatim and shown back; pretending to act on them would need a model reading
them, and a model that misreads a goal would quietly plan for the wrong person.
"""

from __future__ import annotations

from dataclasses import dataclass

from chesscoach.arbiter import MAX_PRIORITIES
from chesscoach.humaninput import clean, is_blank
from chesscoach.profile.models import PlayerContext

# Below this, one thing to work on rather than several. A convention rather than
# a measurement -- nothing in this project links study hours to outcomes, and
# saying so is better than implying the number was derived. It errs toward
# fewer, which is the direction domain.coaching § 4 argues for anyway.
FOCUSED_EFFORT_HOURS = 3.0

# And below this, two rather than the full three. Added when the ceiling rose
# from two to three: without a middle band the question becomes a switch between
# one and three, which is a cruder instrument than the answer deserves. Same
# standard of evidence as the constant above, which is to say none -- both are
# conventions, and both are declared as such rather than dressed up.
STEADY_EFFORT_HOURS = 6.0


@dataclass(frozen=True)
class Question:
    """One thing to ask, and where the answer goes."""

    field: str
    prompt: str
    help: str = ""


QUESTIONS = (
    Question(
        field="goals",
        prompt="What do you want out of your chess?",
        help="Rating, a specific opponent, enjoying it more — anything.",
    ),
    Question(
        field="weekly_study_hours",
        prompt="Realistically, how many hours a week can you give it?",
        help="The honest number, not the aspirational one. It decides how much is planned.",
    ),
    Question(
        field="already_tried",
        prompt="What have you already tried that did not work?",
        help="So the plan does not hand you back something you have done.",
    ),
    Question(
        field="plays_elsewhere",
        prompt="Do you play anywhere these games will not show — over the board, another site?",
        help="Anything invisible here is a gap in what any of this can say.",
    ),
)


def priorities_for(context: PlayerContext | None, ceiling: int = MAX_PRIORITIES) -> int:
    """How many things to work on, given the time the player actually has.

    Never more than the arbiter's own ceiling, and never fewer than one — a
    player who answers "half an hour" still gets something, because the
    alternative is a report that diagnoses and then prescribes nothing.
    """
    if context is None or context.weekly_study_hours is None:
        return ceiling
    if context.weekly_study_hours < FOCUSED_EFFORT_HOURS:
        return 1
    if context.weekly_study_hours < STEADY_EFFORT_HOURS:
        return min(2, ceiling)
    return ceiling


def parse_hours(answer: str) -> float | None:
    """Read a number out of whatever the player typed, or give up honestly.

    "about 4", "4h", "4-5" all mean four-ish. An unparseable answer becomes None
    and the plan falls back to its default, rather than the session failing over
    a formatting question.
    """
    cleaned = clean(answer).lower().replace(",", ".")
    # A leading minus is refused rather than ignored: "-3" scanned for digits
    # gives 3, and sizing a plan on a misread number is worse than falling back
    # to the default. A minus *inside* the answer is fine -- "4-5" means four-ish.
    if cleaned.startswith("-"):
        return None

    number = ""
    for char in cleaned:
        if char.isdigit() or (char == "." and number and "." not in number):
            number += char
        elif number:
            break
    try:
        hours = float(number)
    except ValueError:
        return None
    return hours if 0 <= hours <= 168 else None


def from_answers(answers: dict[str, str]) -> PlayerContext | None:
    """Build the context, or None when the player answered nothing at all."""
    given = {field: clean(text) for field, text in answers.items() if not is_blank(text)}
    if not given:
        return None

    return PlayerContext(
        goals=given.get("goals"),
        weekly_study_hours=parse_hours(given["weekly_study_hours"])
        if "weekly_study_hours" in given
        else None,
        already_tried=given.get("already_tried"),
        plays_elsewhere=given.get("plays_elsewhere"),
    )


def ask(reader=input, writer=print) -> PlayerContext | None:
    """Put the four questions. Every one of them is skippable."""
    writer("\nFour questions first — the games cannot answer these, and every one")
    writer("of them is skippable with Enter.\n")

    answers: dict[str, str] = {}
    for question in QUESTIONS:
        writer(f"  {question.prompt}")
        if question.help:
            writer(f"    ({question.help})")
        answers[question.field] = reader("  > ")
        writer("")
    return from_answers(answers)
