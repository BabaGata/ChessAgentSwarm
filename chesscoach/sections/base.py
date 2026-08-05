"""The contract every section agent obeys.

From docs/notes/architecture.orchestration.md. Section agents run in parallel and
in isolation, communicating only through the player profile. Two rules here are
the ones most likely to be violated under pressure to make a demo look good:

  * an agent **may return zero findings**, and must when the evidence does not
    support one — "always produce something" is how filler is born;
  * an agent **never calls a language model**. Diagnosis is deterministic; the
    language layer runs later, on the profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chesscoach.analysis.observations import Observation
from chesscoach.ingest.corpus import Corpus
from chesscoach.peers import ConditionMeasurement, PeerReference
from chesscoach.profile.models import Finding, Provenance


# Which moves are worth diagnosing at all. Shared by every section so the answer
# cannot drift between them.
#
# Book moves carry little information and structures have not formed, so the
# opening is skipped. And beyond DECIDED_CP the game is effectively over: win
# probability compresses at the extremes (L-009), making errors there both cheap
# to commit and nearly invisible to measure -- and no coach diagnoses a player
# from an already-lost position.
OPENING_GRACE_PLIES = 8
DECIDED_CP = 500


def diagnosable(observations: tuple[Observation, ...]) -> tuple[Observation, ...]:
    """Post-opening moves played while the game was still competitive."""
    return tuple(
        o
        for o in observations
        if o.ply > OPENING_GRACE_PLIES and abs(o.score_cp_before) <= DECIDED_CP
    )


# The pooled subject a section uses when it needs a denominator big enough to
# clear the confidence gate at all (L-022).
POOLED_SUBJECT = "any"


def drop_redundant_aggregates(findings: tuple[Finding, ...]) -> tuple[Finding, ...]:
    """Keep the specific claim when both it and its pooled parent survive.

    A section carrying an aggregate plus subdivisions can assert both for one
    player, and "you go wrong early" next to "you go wrong early as Black" has
    said one thing twice. The arbiter prefers diversity **across** claim kinds
    and cannot see inside one.

    The specific claim wins because it is strictly more useful: it names the
    same problem and says where to look. Measured in E08 on real players --
    2 of 16 advised players were getting the pair.
    """
    subdivided = {
        f.claim.kind for f in findings if f.claim.subject != POOLED_SUBJECT
    }
    return tuple(
        f
        for f in findings
        if not (f.claim.subject == POOLED_SUBJECT and f.claim.kind in subdivided)
    )


@dataclass(frozen=True)
class SectionContext:
    """Everything a section agent is given. Read-only.

    `band`, `time_control` and `peers` are optional because a reference
    population may not exist yet. An agent that needs one to speak honestly must
    stay silent without it rather than fall back to a weaker comparison.
    """

    observations: tuple[Observation, ...]
    corpus: Corpus
    provenance: Provenance
    band: str | None = None
    time_control: str | None = None
    peers: PeerReference | None = None

    def player_observations(self) -> tuple[Observation, ...]:
        """Only the moves the player made. Their opponents' errors are not theirs."""
        username = self.corpus.username.lower()
        return tuple(o for o in self.observations if o.mover.lower() == username)

    def peer_rate(self, claim_key: str) -> float | None:
        """Population rate for a claim, with this player left out of it."""
        if self.peers is None or self.band is None or self.time_control is None:
            return None
        stats = self.peers.lookup(
            self.band, self.time_control, claim_key, excluding=self.corpus.username
        )
        return stats.rate if stats else None


@dataclass(frozen=True)
class SectionReport:
    """What an agent returns.

    `insufficient_data` is separate from an empty finding list on purpose:
    "we could not assess this" and "we assessed this and it is fine" are
    different statements, and collapsing them tells the player their endgames
    are fine when four of their games reached one.
    """

    section: str
    findings: tuple[Finding, ...] = ()
    insufficient_data: bool = False
    notes: tuple[str, ...] = ()


class SectionAgent(Protocol):
    """A diagnostic agent for one section of coaching knowledge.

    Measuring and asserting are separate methods on purpose. `measure` returns
    raw rates with no judgement applied, which is what building a peer reference
    needs — every player's numbers, including the unremarkable ones. `report`
    is `measure` plus the confidence policy.
    """

    section: str

    def measure(self, context: SectionContext) -> tuple[ConditionMeasurement, ...]: ...

    def report(self, context: SectionContext) -> SectionReport: ...

    def findings(self, context: SectionContext) -> tuple[Finding, ...]: ...
