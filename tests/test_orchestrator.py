"""Running section agents and collecting their findings into the profile.

Implements the stage-B fan-out and stage-4 blackboard write from
docs/notes/architecture.orchestration.md. Agents run in isolation: one failing
must not take the run with it, and must not be silently reported as having found
nothing, which would read as a clean bill of health.
"""

from __future__ import annotations

import pytest

from chesscoach.ingest.corpus import Corpus
from chesscoach.orchestrator import apply_to_profile, diagnose
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    CorpusRef,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    PlayerProfile,
    PlayerRef,
    Provenance,
)
from chesscoach.sections.base import SectionContext, SectionReport

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-07-28")


def a_finding(section: str, kind: str = "time_pressure_error") -> Finding:
    return Finding(
        section=section,
        claim=Claim.of(kind=kind, subject="clock"),
        measurement=Measurement(instances=9, distinct_games=7, games_with_data=30, rate=0.2),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.PROCESS, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=31, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


class StubAgent:
    def __init__(self, section: str, findings=(), insufficient: bool = False):
        self.section = section
        self._findings = findings
        self._insufficient = insufficient

    def report(self, context: SectionContext) -> SectionReport:
        return SectionReport(
            section=self.section,
            findings=self._findings,
            insufficient_data=self._insufficient,
        )

    def findings(self, context: SectionContext):
        return self.report(context).findings


class ExplodingAgent:
    section = "S9"

    def report(self, context: SectionContext) -> SectionReport:
        raise RuntimeError("engine unavailable")

    def findings(self, context: SectionContext):
        return self.report(context).findings


def a_context() -> SectionContext:
    corpus = Corpus(username="alice", corpus_id="c1", game_ids=("g1", "g2"))
    return SectionContext(observations=(), corpus=corpus, provenance=PROVENANCE)


def a_profile(findings=()) -> PlayerProfile:
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=2),
        findings=findings,
    )


class TestDiagnose:
    def test_collects_findings_from_every_agent(self):
        agents = [
            StubAgent("S1", (a_finding("S1", "missed_motif"),)),
            StubAgent("S2", (a_finding("S2"),)),
        ]

        result = diagnose(a_context(), agents)

        assert len(result.findings) == 2

    def test_an_agent_may_report_nothing(self):
        result = diagnose(a_context(), [StubAgent("S2", ())])

        assert result.findings == ()
        assert result.failures == ()

    def test_one_agent_failing_does_not_stop_the_others(self):
        agents = [ExplodingAgent(), StubAgent("S2", (a_finding("S2"),))]

        result = diagnose(a_context(), agents)

        assert len(result.findings) == 1
        assert [f.section for f in result.failures] == ["S9"]

    def test_a_failure_records_why(self):
        result = diagnose(a_context(), [ExplodingAgent()])

        assert "engine unavailable" in result.failures[0].error

    def test_a_failed_agent_is_not_reported_as_having_found_nothing(self):
        # Silence from a crash must not read as a clean bill of health.
        result = diagnose(a_context(), [ExplodingAgent()])

        assert result.sections_reporting == ()
        assert result.failed_sections == ("S9",)

    def test_records_which_sections_lacked_data(self):
        result = diagnose(a_context(), [StubAgent("S3", (), insufficient=True)])

        assert result.insufficient_sections == ("S3",)

    def test_findings_are_ordered_deterministically(self):
        agents = [StubAgent("S2", (a_finding("S2"),)), StubAgent("S1", (a_finding("S1"),))]

        first = diagnose(a_context(), agents)
        second = diagnose(a_context(), agents)

        assert [f.id for f in first.findings] == [f.id for f in second.findings]


class TestApplyToProfile:
    def test_writes_findings_into_the_profile(self):
        result = diagnose(a_context(), [StubAgent("S2", (a_finding("S2"),))])

        updated = apply_to_profile(a_profile(), result)

        assert len(updated.findings) == 1

    def test_replaces_only_the_sections_that_reported(self):
        existing = (a_finding("S1", "missed_motif"), a_finding("S2"))
        result = diagnose(a_context(), [StubAgent("S2", ())])

        updated = apply_to_profile(a_profile(existing), result)

        assert [f.section for f in updated.findings] == ["S1"]

    def test_keeps_findings_from_a_section_that_failed(self):
        # Losing a previous diagnosis because an agent crashed would quietly
        # tell the player a weakness had gone away.
        existing = (a_finding("S9", "missed_motif"),)
        result = diagnose(a_context(), [ExplodingAgent()])

        updated = apply_to_profile(a_profile(existing), result)

        assert len(updated.findings) == 1

    def test_does_not_mutate_the_original_profile(self):
        original = a_profile()
        result = diagnose(a_context(), [StubAgent("S2", (a_finding("S2"),))])

        apply_to_profile(original, result)

        assert original.findings == ()
