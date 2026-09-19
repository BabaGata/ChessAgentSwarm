"""A short summary of the findings, written by a local model and checked against them.

Design: docs/notes/design.narrated-session.md · Rule:
[[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

The report itself stays templates: every sentence in it is reviewable and every
number is computed. What the model adds is the thing templates do badly -- a few
sentences in one voice that say what matters, addressed to the player.

**How it is given the facts was decided by measuring (E92).** Given the whole
report, the model mixed findings up: a cost moved from one pattern to another,
and every such sentence passed the check because each number was somewhere in
the report. Given one finding's block of report text, it read "64% of the time"
as "64% of the games" and copied labels such as "Target:". So each finding the
plan acts on becomes a short **fact sheet** of plain sentences built from the
measurement -- what the rate is a share of is said in words -- and the model
writes one or two sentences from that sheet alone.

Each sentence is kept only if a deterministic check finds nothing in it that its
own sheet did not say:

  * no move or square absent from the sheet (`grounding.check`);
  * not too many words the sheet never used (`grounding.MAX_NOVELTY`);
  * **no number absent from the sheet.** Added here, because a summary is mostly
    numbers and E50's check was built for opening plans, which are not.

A rejected sentence leaves its finding out of the summary, and the full report
still follows. A stopped model and a rejected answer are reported differently,
never as the same silence (L-046).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chesscoach import grounding, ollama
from chesscoach.arbiter import NEGLIGIBLE_COST_PER_GAME
from chesscoach.phrasing import statement
from chesscoach.profile.models import Finding, PlanStep, PlayerProfile

# E50: the 1.9 GB model beat the 5.2 GB one on acceptance, novelty and time.
MODEL = "qwen2.5:3b"

PROMPT = """You are a chess coach. Below are facts measured from one player's own games about one
pattern in their play, and the advice their report gives about it.

Write one or two sentences to the player about this pattern, speaking to them as "you".
Use only the facts below. Copy every number exactly as it is written.
Do not add advice, chess ideas, moves or numbers of your own.
Plain sentences only: no headings, no labels, no lists.

Facts:
{facts}
"""

# A number standing alone: not the 5 of Bb5, not the 123 of a game id.
_NUMBER = re.compile(r"(?<![A-Za-z0-9.,])\d+(?:[.,]\d+)?(?![A-Za-z0-9])")


@dataclass(frozen=True)
class Narration:
    """The summary if any of it passed, and what was left out and why."""

    text: str | None
    accepted: bool
    reason: str = ""
    model: str = MODEL


def numbers_in(text: str) -> tuple[str, ...]:
    """Every standalone number, decimal commas read as points."""
    return tuple(n.replace(",", ".") for n in _NUMBER.findall(text))


def ungrounded_numbers(text: str, source: str) -> tuple[str, ...]:
    """Numbers in `text` that `source` never states."""
    known = set(numbers_in(source))
    missing: list[str] = []
    for number in numbers_in(text):
        if number not in known and number not in missing:
            missing.append(number)
    return tuple(missing)


def verdict(text: str, source: str) -> str:
    """Empty when `text` says nothing `source` does not; otherwise the reason."""
    if not text.strip():
        return "the model returned nothing"
    checked = grounding.check(text, source)
    if checked.ungrounded_moves:
        return checked.reason
    numbers = ungrounded_numbers(text, source)
    if numbers:
        return "gives numbers the facts do not: " + ", ".join(numbers)
    return checked.reason


def facts(profile: PlayerProfile) -> tuple[str, ...]:
    """One plain fact sheet per finding the plan acts on, in plan order."""
    if profile.plan is None:
        return ()
    by_id = {finding.id: finding for finding in profile.findings}
    return tuple(_sheet(by_id[step.finding_id], step)
                 for step in profile.plan.steps if step.finding_id in by_id)


def narrate(profile: PlayerProfile, *, model: str = MODEL, host: str = ollama.OLLAMA_URL,
            transport=None) -> Narration:
    """A sentence or two per planned finding, each kept only if it checks out."""
    sheets = facts(profile)
    if not sheets:
        return Narration(None, False, "nothing to summarise: the report has no plan", model)

    kept: list[str] = []
    dropped: list[str] = []
    for sheet in sheets:
        try:
            said = ollama.generate(model, PROMPT.format(facts=sheet), host=host,
                                   num_predict=160, temperature=0.2,
                                   transport=transport).strip()
        except ollama.OllamaUnavailable as error:
            return Narration(None, False, f"model unavailable ({error})", model)
        reason = verdict(said, sheet)
        if reason:
            dropped.append(reason)
        else:
            kept.append(said)

    if not kept:
        return Narration(None, False, "; ".join(dropped), model)
    note = (f"{len(dropped)} of {len(sheets)} findings left out: " + "; ".join(dropped)
            if dropped else "")
    return Narration(" ".join(kept), True, note, model)


def _sheet(finding: Finding, step: PlanStep) -> str:
    """The finding as plain sentences, with the same numbers the report prints."""
    m = finding.measurement
    rate = f"This happened in {m.rate:.0%} of the times it could have happened"
    if m.peer_rate is not None:
        rate += f", against {m.peer_rate:.0%} for players at your level"
    lines = [
        statement(finding),
        rate + ".",
        f"It was seen in {m.distinct_games} of {m.games_with_data} games.",
    ]
    cost = m.cost_per_game
    if cost is not None and cost >= NEGLIGIBLE_COST_PER_GAME:
        lines.append(f"It costs you about {cost:.1f} points of win probability a game.")
        if m.peer_cost_per_game is not None:
            lines.append(f"Players at your level lose about {m.peer_cost_per_game:.1f} "
                         "points a game to the same thing.")
    lines.append(f"The advice is: {step.action}")
    return "\n".join(lines)
