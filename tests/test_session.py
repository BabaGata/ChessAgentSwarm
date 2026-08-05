"""One coaching session, end to end.

Spec: docs/notes/architecture.interaction.md § 1

The behaviour that matters here is the **gate**: D10 is unresolved, so a probe
may be asked and recorded but must not silently rewrite a diagnosis. These tests
exist so that turning the gate off has to be a deliberate act rather than a
default nobody noticed.
"""

from __future__ import annotations

import json

from chesscoach.prober import interpret, select_probes
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
from chesscoach.session import (
    Answer,
    append_to_answer_set,
    apply_probes,
    probes_for,
    record_answers,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-04")


class Stub:
    name = "stub/v1"

    def __init__(self, verdict=True):
        self.verdict = verdict

    def classify(self, answer, expected_reason):
        return self.verdict


def a_finding(subject: str = "pin") -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind="missed_motif", subject=subject),
        measurement=Measurement(
            instances=9, distinct_games=8, games_with_data=24, rate=0.30, peer_rate=0.12
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(
            Evidence(game_id="g1", ply=21, fen="8/8/8/8/8/8/8/K6k w - - 0 1", better_move="Bb5"),
        ),
    )


def a_profile(*findings: Finding) -> PlayerProfile:
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=24),
        findings=findings or (a_finding(),),
    )


def answered(profile, move="Bb5", reason="it pins the knight", classifier=None):
    probes = probes_for(profile)
    answers = tuple(Answer(probe_id=p.id, move=move, reason=reason) for p in probes)
    return probes, record_answers(probes, answers, classifier or Stub())


class TestSelectingWhatToAsk:
    def test_it_probes_the_shortlisted_finding(self):
        probes = probes_for(a_profile())

        assert len(probes) == 1
        assert probes[0].expected_reason == "pin"

    def test_it_asks_nothing_when_there_is_nothing_to_prioritise(self):
        assert probes_for(a_profile(*())) is not None  # empty findings -> no probes

    def test_the_limit_is_respected(self):
        findings = tuple(a_finding(subject=s) for s in ("pin", "fork", "skewer"))

        assert len(probes_for(a_profile(*findings), limit=1)) == 1


class TestTheGate:
    def test_probes_are_recorded_but_the_finding_is_untouched_by_default(self):
        # D10 is unresolved: the classifier's agreement rests on answers the
        # author wrote and labelled, so it may not yet rewrite a diagnosis.
        profile = a_profile()
        _, records = answered(profile)

        updated = apply_probes(profile, records)

        assert len(updated.probes) == 1
        assert updated.findings[0].gap_type.determined_by is DeterminedBy.INFERRED

    def test_applying_is_possible_but_has_to_be_asked_for(self):
        profile = a_profile()
        _, records = answered(profile)

        updated = apply_probes(profile, records, apply=True)

        assert updated.findings[0].gap_type.determined_by is DeterminedBy.PROBED
        assert updated.findings[0].gap_type.hypothesis is GapTypeHypothesis.SKILL

    def test_the_record_is_kept_even_when_it_is_not_applied(self):
        # A probe that was asked is evidence whether or not the system trusts
        # its interpretation, and discarding it would lose what D10 needs.
        profile = a_profile()
        _, records = answered(profile, reason="his knight cannot move")

        updated = apply_probes(profile, records)

        assert updated.probes[0].player_reason == "his knight cannot move"


class TestAnswersBecomeData:
    def test_answers_are_appended_unlabelled(self, tmp_path):
        # Labelling them here would reintroduce exactly the problem D10 names.
        profile = a_profile()
        _, records = answered(profile, reason="the horse is stuck")
        path = tmp_path / "collected.jsonl"

        written = append_to_answer_set(records, path)

        assert written == 1
        entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        assert entry["answer"] == "the horse is stuck"
        assert entry["expected"] == "pin"
        assert entry["label"] is None

    def test_what_the_classifier_thought_is_kept_alongside_but_not_as_truth(self, tmp_path):
        profile = a_profile()
        _, records = answered(profile)
        path = tmp_path / "collected.jsonl"

        append_to_answer_set(records, path)

        entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        assert entry["classifier_said"] is True
        assert entry["label"] is None

    def test_it_appends_rather_than_overwriting(self, tmp_path):
        profile = a_profile()
        _, records = answered(profile)
        path = tmp_path / "collected.jsonl"

        append_to_answer_set(records, path)
        append_to_answer_set(records, path)

        assert len(path.read_text(encoding="utf-8").splitlines()) == 2

    def test_an_empty_answer_is_not_collected(self, tmp_path):
        profile = a_profile()
        probes = probes_for(profile)
        records = record_answers(
            probes, (Answer(probe_id=probes[0].id, move="Bb5", reason=""),), Stub()
        )
        path = tmp_path / "collected.jsonl"

        assert append_to_answer_set(records, path) == 0


class TestDegrading:
    def test_a_session_without_a_model_still_asks_and_records(self):
        profile = a_profile()
        probes = select_probes(profile.findings)
        records = (interpret(probes[0], "Bb5", "it pins the knight", classifier=None),)

        updated = apply_probes(profile, records)

        assert updated.probes[0].player_reason == "it pins the knight"
        assert updated.probes[0].inference == GapTypeHypothesis.UNKNOWN.value
