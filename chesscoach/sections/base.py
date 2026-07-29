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
from chesscoach.profile.models import Finding, Provenance


@dataclass(frozen=True)
class SectionContext:
    """Everything a section agent is given. Read-only."""

    observations: tuple[Observation, ...]
    corpus: Corpus
    provenance: Provenance

    def player_observations(self) -> tuple[Observation, ...]:
        """Only the moves the player made. Their opponents' errors are not theirs."""
        username = self.corpus.username.lower()
        return tuple(o for o in self.observations if o.mover.lower() == username)


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
    """A diagnostic agent for one section of coaching knowledge."""

    section: str

    def report(self, context: SectionContext) -> SectionReport: ...

    def findings(self, context: SectionContext) -> tuple[Finding, ...]: ...
