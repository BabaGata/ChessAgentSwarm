"""Running section agents and writing their findings to the profile.

Stages B and 4 of docs/notes/architecture.md. Agents are run in isolation and
communicate only through the profile — never with each other
(ADR-0006), so this module has no notion of one agent's output feeding another's.

Two behaviours here are specified rather than incidental:

  * **failure isolation** — an agent that raises is recorded as failed and the
    run continues. Its silence must never be mistaken for "found nothing";
  * **section-scoped replacement** — re-running updates only the sections that
    actually reported, so a crashed agent does not quietly delete a previous
    diagnosis and tell the player a weakness has gone away.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence

from chesscoach.profile.models import Finding, PlayerProfile
from chesscoach.sections.base import SectionAgent, SectionContext, SectionReport


@dataclass(frozen=True)
class SectionFailure:
    """An agent that could not complete. Recorded, never swallowed."""

    section: str
    error: str


@dataclass(frozen=True)
class DiagnosisResult:
    """What the section stage produced, including what it could not."""

    reports: tuple[SectionReport, ...] = ()
    failures: tuple[SectionFailure, ...] = ()

    @property
    def findings(self) -> tuple[Finding, ...]:
        collected = [f for report in self.reports for f in report.findings]
        return tuple(sorted(collected, key=lambda finding: finding.id))

    @property
    def sections_reporting(self) -> tuple[str, ...]:
        return tuple(report.section for report in self.reports)

    @property
    def failed_sections(self) -> tuple[str, ...]:
        return tuple(failure.section for failure in self.failures)

    @property
    def insufficient_sections(self) -> tuple[str, ...]:
        return tuple(r.section for r in self.reports if r.insufficient_data)


def diagnose(context: SectionContext, agents: Sequence[SectionAgent]) -> DiagnosisResult:
    """Run every agent over the same observations, in isolation."""
    reports: list[SectionReport] = []
    failures: list[SectionFailure] = []

    for agent in agents:
        try:
            reports.append(agent.report(context))
        except Exception as error:  # noqa: BLE001 - one agent must not end the run
            failures.append(SectionFailure(section=agent.section, error=str(error)))

    return DiagnosisResult(reports=tuple(reports), failures=tuple(failures))


def apply_to_profile(profile: PlayerProfile, result: DiagnosisResult) -> PlayerProfile:
    """Write the diagnosis onto the profile, replacing only what was re-measured."""
    reporting = set(result.sections_reporting)
    kept = tuple(f for f in profile.findings if f.section not in reporting)
    combined = sorted(kept + result.findings, key=lambda finding: finding.id)
    return replace(profile, findings=tuple(combined))


def default_agents() -> tuple[SectionAgent, ...]:
    """The agents currently in the swarm, in build order.

    Adding a section here is the entire integration step — no wiring, no
    ordering, no agent aware of any other. That is the blackboard design's
    central claim (ADR-0006); S1 was its first test and S3 its second, both
    one-line changes.
    """
    from chesscoach.sections.s1_tactical_gaps import S1TacticalGaps
    from chesscoach.sections.s2_decision_process import S2DecisionProcess
    from chesscoach.sections.s3_endgame_technique import S3EndgameTechnique
    from chesscoach.sections.s4_opening_outcomes import S4OpeningOutcomes
    from chesscoach.sections.s5_pawn_structure import S5PawnStructure
    from chesscoach.sections.s6_squares_and_files import S6SquaresAndFiles
    from chesscoach.sections.s8_attack_and_defence import S8AttackAndDefence

    return (
        S2DecisionProcess(),
        S1TacticalGaps(),
        S3EndgameTechnique(),
        S4OpeningOutcomes(),
        S5PawnStructure(),
        S6SquaresAndFiles(),
        S8AttackAndDefence(),
    )


def summarise(result: DiagnosisResult) -> Iterable[str]:
    """Human-readable lines describing what each section did."""
    for report in result.reports:
        if report.insufficient_data:
            yield f"  {report.section}: insufficient data"
        elif not report.findings:
            yield f"  {report.section}: nothing to report"
        else:
            yield f"  {report.section}: {len(report.findings)} finding(s)"
    for failure in result.failures:
        yield f"  {failure.section}: FAILED — {failure.error}"
