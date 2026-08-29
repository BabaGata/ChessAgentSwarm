"""How often a detector is right, from marks a person made.

Design: [[experiments.e55-detector-precision]]

`state.md` has carried the same P0 for a week: *"the deliverable is precision per
detector on hand-verified samples — not a pass/fail."* The sheet that collects
those marks exists (`e46-motif-precision`); this is the half that turns them into
a number, and it exists as library code rather than experiment code because the
measurement will be repeated every time a detector changes.

**Five samples can condemn a detector and cannot exonerate one.** That asymmetry
is the whole design. At n = 5 a score of 0/5 puts the Wilson upper bound near
43 %, which settles it — and 5/5 puts the lower bound near 57 %, which settles
nothing. So the screen runs in two stages: everything at n = 5 to find what is
broken, and only the survivors that actually reach a player at n = 20.

That is the project's usual shape — screen cheaply, measure what survives — and
here it also buys the scarcest resource in the whole thesis, which is the
author's time reading positions.

**The floor is the author's own revealed threshold, not an invented number.**
Marking `allowed_motif.hangingPawn` at 4/5 they wrote *"works, leave alone"*; at
0/5 for `moved_into_attack`, *"broken"*. `PRECISION_FLOOR` sits below the
accepted point estimate and far above the rejected one. It is provisional and
labelled as such: two marks is a weak basis for a constant, and it is a better
basis than a round number chosen because it looked reasonable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from chesscoach.profile.models import wilson_interval

# Below this, a detector is producing advice a player cannot trust. Anchored on
# the author's own two verdicts -- 4/5 accepted, 0/5 rejected -- rather than
# chosen. Provisional until enough detectors are marked to fit it properly.
PRECISION_FLOOR = 0.70

# The screen stage. Enough to condemn, never enough to clear.
SCREEN_SAMPLE = 5

# The measuring stage, for detectors that survive the screen and reach a report.
# At 18/20 the interval is roughly [0.70, 0.97]: the floor is inside it, so even
# this only *supports* a detector rather than proving it.
MEASURE_SAMPLE = 20


class Verdict(str, Enum):
    """What the interval, not the point estimate, permits saying."""

    # The whole interval sits below the floor: broken, whatever the sample size.
    CONDEMNED = "condemned"
    # The whole interval sits above it: trustworthy at this sample size.
    CONFIRMED = "confirmed"
    # The floor is inside the interval. The commonest honest answer.
    INSUFFICIENT = "insufficient"
    # Nobody has marked it.
    UNMARKED = "unmarked"


@dataclass(frozen=True)
class Marks:
    """One detector's marks: right, wrong, and could not tell."""

    detector: str
    right: int = 0
    wrong: int = 0
    unsure: int = 0

    @property
    def judged(self) -> int:
        """Marks that carry a verdict. `[?]` is excluded from the denominator.

        Counting "cannot tell" as wrong would punish a detector for a position
        the reader found hard; counting it as right would flatter it. It is
        reported separately instead, because a detector nobody can adjudicate is
        its own finding.
        """
        return self.right + self.wrong

    @property
    def precision(self) -> float | None:
        return self.right / self.judged if self.judged else None

    @property
    def interval(self) -> tuple[float, float] | None:
        return wilson_interval(self.right, self.judged) if self.judged else None

    @property
    def verdict(self) -> Verdict:
        if not self.judged:
            return Verdict.UNMARKED
        low, high = self.interval
        if high < PRECISION_FLOOR:
            return Verdict.CONDEMNED
        if low >= PRECISION_FLOOR:
            return Verdict.CONFIRMED
        return Verdict.INSUFFICIENT

    @property
    def reason(self) -> str:
        """One line a person can act on."""
        if not self.judged:
            return "nobody has marked it"
        low, high = self.interval
        band = f"{low:.0%}-{high:.0%}"
        if self.verdict is Verdict.CONDEMNED:
            return f"wrong more often than the floor allows ({band}); fix or retire it"
        if self.verdict is Verdict.CONFIRMED:
            return f"right often enough to trust ({band})"
        return (f"the floor sits inside {band} -- "
                f"{MEASURE_SAMPLE - self.judged} more marks would settle it"
                if self.judged < MEASURE_SAMPLE else
                f"the floor sits inside {band} even at {self.judged} marks")


def sample_size(judged: int) -> int:
    """How many more marks this detector needs before it can be cleared."""
    return max(0, MEASURE_SAMPLE - judged)


def condemned(marks) -> tuple[Marks, ...]:
    return tuple(m for m in marks if m.verdict is Verdict.CONDEMNED)


def confirmed(marks) -> tuple[Marks, ...]:
    return tuple(m for m in marks if m.verdict is Verdict.CONFIRMED)


def unsettled(marks) -> tuple[Marks, ...]:
    """Marked, and still undecided — where the next marks should go."""
    return tuple(m for m in marks if m.verdict is Verdict.INSUFFICIENT)


# Which module implements which claim. A mark is evidence about the code that
# was running when it was made, so a detector rebuilt afterwards has no measured
# precision -- however many marks it carries.
#
# This is not bookkeeping pedantry: of the twenty-three marks made on
# 2026-08-23, the motifs were rebuilt on the 24th and `moved_into_attack` fixed
# on the 27th, so reporting them as current would send the author to fix a
# detector twice and would credit a rebuild with a score it never earned.
OWNED_BY: dict[str, str] = {
    "allowed_motif": "chesscoach/tactics.py",
    "missed_motif": "chesscoach/tactics.py",
    "moved_into_attack": "chesscoach/material.py",
    "miscounted_exchange": "chesscoach/material.py",
    "sacrificed_for_attack": "chesscoach/material.py",
    "concedes_weakness": "chesscoach/structure.py",
    "allows_square": "chesscoach/squares.py",
}

# Anything else is a section claim -- early_error, advantage_error,
# endgame_error, time_pressure_error and the rest all come from sections/.
SECTION_CLAIMS = "chesscoach/sections/"


def module_for(detector: str) -> str:
    """The file whose changes invalidate a mark on this detector."""
    return OWNED_BY.get(detector.split(".")[0], SECTION_CLAIMS)


@dataclass(frozen=True)
class Dated(Marks):
    """Marks that know when they were made, and whether the code moved since.

    `stale` is supplied by the caller from version control rather than guessed
    here, so this module stays free of git and the rule stays testable.
    """

    marked_on: str = ""
    changed_on: str = ""

    @property
    def stale(self) -> bool:
        return bool(self.marked_on and self.changed_on
                    and self.changed_on > self.marked_on)

    @property
    def verdict(self) -> Verdict:
        # A stale mark is not a weak verdict, it is no verdict: the thing it
        # measured is gone.
        return Verdict.UNMARKED if self.stale else super().verdict

    @property
    def reason(self) -> str:
        if self.stale:
            return (f"marked {self.marked_on}, but {module_for(self.detector)} "
                    f"changed {self.changed_on} -- must be re-marked")
        return super().reason
