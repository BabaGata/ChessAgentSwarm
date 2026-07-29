"""Section agents: one per section of coaching knowledge.

They run in parallel and in isolation, read the analysis core's observations,
and write typed Findings into the player profile. They never message each other
and never call a language model — see docs/notes/architecture.orchestration.md.

Build order is set in docs/notes/domain.sections.md.
"""

from chesscoach.sections.base import SectionAgent, SectionContext, SectionReport

__all__ = ["SectionAgent", "SectionContext", "SectionReport"]
