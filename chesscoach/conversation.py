"""The conversation the player actually has with the swarm.

Design: docs/notes/design.coaching-conversation.md · Serves **V9**

The author's shape, in order: greet, ask for a username, analyse, say the few
things that matter, offer to explain, take one focus, give the exercise for that
one and defer the rest for a week.

**The agent never supplies chess.** Every sentence it can say is already computed
somewhere deterministic -- the findings by `phrasing`, the comparison by
`Measurement`, an explanation by `KnowledgeBase.for_player`, the evidence by the
player's own games, the exercise by `planner`. A language model is not in the
content path at all, which is the `prober` boundary again and for the same reason
(R-03, hard rule 7): a conversation is exactly where a model produces its most
confident nonsense.

**No I/O lives here.** `reply(text)` takes the player's line and returns what to
say next, so the whole dialogue is testable without a terminal and the terminal
is a thin loop in `cli talk`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from chesscoach.knowledge import KnowledgeBase, NotEndorsed
from chesscoach.phrasing import move_number, quantity, statement
from chesscoach.planner import _action
from chesscoach.profile.models import Finding, PlayerProfile

# How the week is framed. The plan measures **games**, not days, and the two are
# not the same thing -- so both are said and neither is presented as the other.
WEEK_DAYS = 7

EXPLAIN_WORDS = (
    "explain", "what is", "what's", "whats", "why", "more about",
    "tell me more", "mean", "detail",
)


class Stage(str, Enum):
    """Where the conversation is.

    Explicit, because a dialogue that infers its own state from the last thing
    said is a dialogue that loses the thread.
    """

    GREETING = "greeting"
    AWAITING_USERNAME = "awaiting_username"
    ANALYSING = "analysing"
    PRESENTED = "presented"
    COMMITTED = "committed"
    CLOSED = "closed"


@dataclass
class Turn:
    """What to say, and what the caller must do before the next turn."""

    say: str
    stage: Stage
    # Set once, when the player has given a username and the caller should run
    # the pipeline. The agent does no I/O and analyses nothing itself.
    analyse: str | None = None
    # The claim the player committed to, once they have.
    focus: str | None = None


@dataclass
class Conversation:
    """A turn-taking coach over a profile that already exists."""

    profile: PlayerProfile | None = None
    knowledge: KnowledgeBase | None = None
    stage: Stage = Stage.GREETING
    focus: str | None = None
    _offered: tuple[Finding, ...] = field(default_factory=tuple)

    # --- what it says -------------------------------------------------------

    def open(self) -> Turn:
        """The first thing the player sees."""
        self.stage = Stage.AWAITING_USERNAME
        return Turn(
            say=(
                "I look through your recent Lichess games and tell you what keeps "
                "going wrong, using your own games as the evidence.\n"
                "\n"
                "What is your Lichess username?"
            ),
            stage=self.stage,
        )

    def present(self, profile: PlayerProfile) -> Turn:
        """Say the few things that matter. Called once the analysis is done."""
        self.profile = profile
        self._offered = _worth_saying(profile)
        self.stage = Stage.PRESENTED
        return Turn(say=self._presentation(), stage=self.stage)

    def reply(self, text: str) -> Turn:
        """One turn. `text` is whatever the player typed."""
        said = (text or "").strip()
        if self.stage is Stage.AWAITING_USERNAME:
            return self._take_username(said)
        if self.stage is Stage.PRESENTED:
            return self._after_presenting(said)
        if self.stage is Stage.COMMITTED:
            return self._after_committing(said)
        return Turn(
            say="We are done for now. Play some games and come back.",
            stage=Stage.CLOSED,
        )

    # --- stages -------------------------------------------------------------

    def _take_username(self, said: str) -> Turn:
        if not said or " " in said:
            return Turn(
                say="I need a single Lichess username, with no spaces. What is it?",
                stage=Stage.AWAITING_USERNAME,
            )
        self.stage = Stage.ANALYSING
        return Turn(
            say=(
                f"Thanks. Fetching {said}'s recent games and analysing them. This "
                "takes a couple of minutes, and I will not ask you anything while "
                "it runs."
            ),
            stage=self.stage,
            analyse=said,
        )

    def _after_presenting(self, said: str) -> Turn:
        chosen = self._match(said)
        wants_detail = _asks_to_explain(said)
        if chosen is not None and wants_detail:
            return Turn(say=self._explain(chosen), stage=Stage.PRESENTED)
        if chosen is not None:
            return self._commit(chosen)
        if wants_detail:
            return Turn(
                say="Which one? " + self._choices(), stage=Stage.PRESENTED
            )
        return Turn(
            say=(
                "Tell me either which one to explain, or which one you want to "
                "start on. " + self._choices()
            ),
            stage=Stage.PRESENTED,
        )

    def _after_committing(self, said: str) -> Turn:
        chosen = self._match(said)
        if chosen is not None and _asks_to_explain(said):
            return Turn(say=self._explain(chosen), stage=Stage.COMMITTED)
        self.stage = Stage.CLOSED
        return Turn(
            say=(
                "Good. Play your week, then run this again and I will check "
                "whether the sign showed up."
            ),
            stage=self.stage,
        )

    # --- content ------------------------------------------------------------

    def _presentation(self) -> str:
        if not self._offered:
            return (
                "Nothing in these games reached the confidence needed to name a "
                "weakness. That is a real answer: either the games do not show a "
                "consistent pattern, or there were too few of them.\n"
                "\n"
                "Play some more and come back. A wrong diagnosis would cost you "
                "more than waiting does."
            )
        lines = ["Here is what your games show.", ""]
        for index, finding in enumerate(self._offered, start=1):
            lines.append(f"{index}. {statement(finding)}")
            comparison = _comparison(finding)
            if comparison:
                lines.append(f"   {comparison}")
            lines.append(
                f"   Seen in {finding.measurement.distinct_games} of your games."
            )
            lines.append("")
        lines += [
            "I can explain any of these properly, or you can pick one to start on.",
            "Which would you like?",
        ]
        return "\n".join(lines)

    def _explain(self, finding: Finding) -> str:
        """Serve the endorsed entry, and say so plainly when there is none."""
        shown = _entry_for(self.knowledge, finding)
        head = statement(finding)
        if not shown:
            # **Not a paraphrase.** Nothing endorsed exists for this claim, and
            # writing an explanation here is the one thing this agent may not do
            # (hard rule 7). Saying so is better than sounding informed.
            return (
                f"{head}\n"
                "\n"
                "I do not have a checked explanation of this one to give you, and "
                "I would rather say that than make one up. What I can show you is "
                "where it happened:\n" + _evidence(finding)
            )
        parts = [head, "", shown["what"]]
        if shown.get("why"):
            parts += ["", shown["why"]]
        if shown.get("links"):
            source = shown["links"][0]
            parts += ["", f"Source: {source['publisher']}"]
        parts += ["", "In your games:", _evidence(finding)]
        return "\n".join(parts)

    def _commit(self, finding: Finding) -> Turn:
        self.focus = finding.claim.key()
        self.stage = Stage.COMMITTED
        step = _step_for(self.profile, finding)

        # **What the plan says, not a fresh computation of it.** The step was
        # already written by the planner and saved on the profile; recomputing
        # would give a second answer that can drift from the artefact the player
        # keeps. `_action` is the fallback for a finding with no step.
        exercise = step.action if step is not None else _action(finding)
        parts = [
            f"Right, {quantity(finding)}. Here is what to do:",
            "",
            f"   {exercise}",
            "",
            f"Work on this one only for the next {WEEK_DAYS} days.",
        ]
        # **The week and the game count are not the same horizon and are not
        # said as if they were.** `check_after_games` is how many games the
        # measurement needs to be worth re-reading -- it reached 78 for one
        # player -- and nobody plays 78 games in a week. The week is when to stop
        # thinking about anything else; the count is when the sign can be
        # checked.
        if step is not None:
            parts.append(
                f"What would show it worked: {_plainly(step.progress_sign)}"
            )

        deferred = [f for f in self._offered if f is not finding]
        if deferred:
            parts += [
                "",
                "The other "
                + ("one" if len(deferred) == 1 else "ones")
                + " can wait. Working on two things at once is how neither gets "
                "fixed, and they will still be there next week.",
            ]
        return Turn(say="\n".join(parts), stage=self.stage, focus=self.focus)

    # --- matching -----------------------------------------------------------

    def _choices(self) -> str:
        return ", ".join(
            f"{i}) {quantity(f)}" for i, f in enumerate(self._offered, start=1)
        )

    def _match(self, said: str) -> Finding | None:
        """Which finding the player means, by number or by its own words.

        Deliberately literal. A model could read *"the fork thing"*, and it is
        not needed to: the choices are on the screen and numbered, and a menu
        that works with no model is the primary interface rather than a fallback
        (C1, and the design note's boundary).
        """
        lowered = said.lower().strip()
        if not lowered:
            return None
        # A digit anywhere, not only at the start: "explain 1" and "tell me
        # about 2" are the ordinary way to ask, and matching only a leading
        # digit sent both to the "which one?" branch.
        digits = re.findall(r"\d+", lowered)
        for index, finding in enumerate(self._offered, start=1):
            if str(index) in digits:
                return finding
            subject = finding.claim.subject.lower()
            if subject and subject != "any" and subject in lowered:
                return finding
            for word in quantity(finding).lower().split():
                if len(word) > 4 and word in lowered:
                    return finding
        return None


def _entry_for(knowledge: KnowledgeBase | None, finding: Finding) -> dict | None:
    """The endorsed entry for this finding, or None.

    **The knowledge base is keyed by the thing, not by the claim.** Its 18 keys
    are motif names (`fork`, `pin`, `trappedPiece`) and claim kinds
    (`allows_pressure`, `endgame_error`), so looking one up by the full claim key
    -- `allowed_motif.fork.own` -- misses every time and the agent then says it
    has no explanation for a claim the project has an endorsed entry for.

    The subject is tried first because it is the more specific of the two: a fork
    is a fork whether it was missed or allowed.
    """
    if knowledge is None:
        return None
    for key in (finding.claim.subject, finding.claim.kind):
        if not key:
            continue
        try:
            entry = knowledge.for_player(key)
        except NotEndorsed:
            continue
        if entry:
            return entry
    return None


def _plainly(sign: str) -> str:
    """The progress sign without its parenthetical bookkeeping.

    `progress_sign` carries a trailing note about how the number was derived --
    at one point *"the share of players who reach this without changing anything
    has not been recalibrated since the error threshold moved"*. True, and
    written for the record rather than for a person being coached; the author's
    complaint about the report was exactly this kind of thing. The falsifiable
    part is `target_rate` and `check_after_games`, both untouched.
    """
    return sign.split(" (", 1)[0].strip()


def _asks_to_explain(said: str) -> bool:
    lowered = said.lower()
    return any(word in lowered for word in EXPLAIN_WORDS)


def _worth_saying(profile: PlayerProfile) -> tuple[Finding, ...]:
    """The one or two the plan is built on, and nothing else.

    Not every finding: the cap is the whole point (R-12), and the conversation
    is where it is felt rather than merely enforced.
    """
    if profile.plan is not None and profile.plan.steps:
        by_id = {f.id: f for f in profile.findings}
        chosen = [
            by_id[step.finding_id]
            for step in profile.plan.steps
            if step.finding_id in by_id
        ]
        if chosen:
            return tuple(chosen)
    return tuple(
        f for f in profile.findings if f.status != "insufficient_data"
    )[:2]


def _comparison(finding: Finding) -> str:
    """One comparison, in the player's terms. No cost arithmetic, no tiers."""
    measurement = finding.measurement
    rate, baseline = measurement.rate, measurement.baseline_rate
    if rate is None or not baseline:
        return ""
    return (
        f"{rate:.0%} of the time, against {baseline:.0%} for players at your level."
    )


def _evidence(finding: Finding, limit: int = 2) -> str:
    lines = []
    for item in finding.evidence[:limit]:
        played = f", you played {item.move_played}" if item.move_played else ""
        lines.append(
            f"   move {move_number(item.ply)}{played} "
            f"— lichess.org/{item.game_id}#{item.ply}"
        )
    return "\n".join(lines) if lines else "   (no positions were sampled for this one)"


def _step_for(profile: PlayerProfile | None, finding: Finding):
    if profile is None or profile.plan is None:
        return None
    for step in profile.plan.steps:
        if step.finding_id == finding.id:
            return step
    return None
