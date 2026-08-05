"""The prober: the first agent in this swarm with a language model in it.

Spec: docs/notes/capacity.agents.prober.md · docs/notes/architecture.interaction.md § 5

The tests that matter here are the ones about **where the model is allowed to
act**. Position selection, the move check and the gap-type decision must all be
deterministic; only the classification of free text is delegated. If that
boundary slips, the diagnosis stops being reproducible and ADR-0002 is broken
without anything failing loudly.
"""

from __future__ import annotations

import pytest

from chesscoach.classifiers import ClassifierUnavailable
from chesscoach.profile.models import (
    Claim,
    ClassifierStatus,
    Confidence,
    ConfidenceTier,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    Provenance,
)
from chesscoach.prober import (
    MAX_PROBES,
    Probe,
    apply_to_findings,
    interpret,
    probeable,
    select_probes,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-08-03")
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def a_finding(
    kind: str = "missed_motif",
    subject: str = "pin",
    evidence: tuple[Evidence, ...] | None = None,
    section: str = "S1",
) -> Finding:
    if evidence is None:
        evidence = (Evidence(game_id="g1", ply=21, fen=START, better_move="Bb5"),)
    return Finding(
        section=section,
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=9, distinct_games=8, games_with_data=24, rate=0.3, peer_rate=0.12
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=evidence,
    )


def a_probe(finding: Finding | None = None) -> Probe:
    return select_probes((finding or a_finding(),))[0]


class TestWhatIsWorthProbing:
    def test_a_motif_finding_with_a_better_move_is_probeable(self):
        assert probeable(a_finding())

    def test_a_process_finding_is_not(self):
        # A clock reading is exogenous, so S2 already knows the gap is process.
        # Asking the player to solve a position untimed tests nothing about it.
        assert not probeable(a_finding(kind="long_think_error", subject="long_think"))

    def test_evidence_without_a_better_move_is_not_probeable(self):
        # Without the right answer there is nothing to check the move against.
        bare = (Evidence(game_id="g1", ply=21, fen=START),)
        assert not probeable(a_finding(evidence=bare))

    def test_unprobeable_findings_produce_no_probes(self):
        assert select_probes((a_finding(kind="long_think_error"),)) == ()


class TestSelection:
    def test_it_asks_for_a_move_and_a_reason(self):
        assert "what would you play" in a_probe().asks.lower()

    def test_it_never_names_the_motif_it_is_testing(self):
        # "Is there a pin here?" teaches the answer and tests nothing.
        probe = a_probe(a_finding(subject="pin"))

        assert "pin" not in probe.asks.lower()

    def test_it_draws_the_position_from_the_players_own_game(self):
        evidence = (Evidence(game_id="g7", ply=13, fen=START, better_move="Nf3"),)

        probe = a_probe(a_finding(evidence=evidence))

        assert probe.fen == START
        assert probe.game_id == "g7"

    def test_it_is_bounded(self):
        many = tuple(
            Evidence(game_id=f"g{n}", ply=n, fen=START, better_move="Bb5") for n in range(20)
        )

        assert len(select_probes((a_finding(evidence=many),))) <= MAX_PROBES

    def test_selection_is_deterministic(self):
        finding = a_finding()

        assert select_probes((finding,)) == select_probes((finding,))


class StubClassifier:
    """Stands in for the model. Records what it was asked, so the tests can
    assert the model is never handed a chess question."""

    def __init__(self, verdict: bool | None):
        self.verdict = verdict
        self.calls: list[tuple[str, str]] = []

    def classify(self, answer: str, expected_reason: str) -> bool | None:
        self.calls.append((answer, expected_reason))
        return self.verdict

    name = "stub/v1"


class TestInference:
    """The table in capacity.agents.prober § 8, which is the whole argument for V9."""

    def test_a_wrong_move_is_a_knowledge_gap(self):
        record = interpret(a_probe(), move="h3", reason="looked fine", classifier=StubClassifier(True))

        assert record.inference == GapTypeHypothesis.KNOWLEDGE.value

    def test_right_move_and_right_reason_is_a_skill_gap(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it pins the knight", classifier=StubClassifier(True)
        )

        assert record.inference == GapTypeHypothesis.SKILL.value

    def test_right_move_for_the_wrong_reason_is_fragile_knowledge(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it develops a piece", classifier=StubClassifier(False)
        )

        assert record.inference == GapTypeHypothesis.FRAGILE.value

    def test_an_unclassifiable_reason_stays_unknown(self):
        # Refusal is data, and guessing here would invent a diagnosis.
        record = interpret(a_probe(), move="Bb5", reason="", classifier=StubClassifier(None))

        assert record.inference == GapTypeHypothesis.UNKNOWN.value

    def test_no_move_at_all_is_unknown(self):
        record = interpret(a_probe(), move=None, reason=None, classifier=StubClassifier(True))

        assert record.inference == GapTypeHypothesis.UNKNOWN.value


class TestTheModelBoundary:
    def test_the_model_is_never_asked_a_chess_question(self):
        classifier = StubClassifier(True)

        interpret(a_probe(), move="Bb5", reason="it pins the knight", classifier=classifier)

        answer, expected = classifier.calls[0]
        assert answer == "it pins the knight"
        assert expected == "pin"  # supplied, not asked for

    def test_the_move_check_does_not_use_the_model(self):
        # A wrong move is decided before the classifier is ever consulted.
        classifier = StubClassifier(True)

        interpret(a_probe(), move="h3", reason="whatever", classifier=classifier)

        assert classifier.calls == []

    def test_without_a_classifier_it_degrades_to_unknown_rather_than_guessing(self):
        record = interpret(a_probe(), move="Bb5", reason="it pins the knight", classifier=None)

        assert record.inference == GapTypeHypothesis.UNKNOWN.value
        assert record.classifier_status == ClassifierStatus.NOT_CONFIGURED.value

    def test_the_answer_is_stored_verbatim(self):
        # The player's words are the evidence; the classification interprets it.
        record = interpret(
            a_probe(), move="Bb5", reason="his hoss cant move", classifier=StubClassifier(True)
        )

        assert record.player_reason == "his hoss cant move"

    def test_the_classifier_is_recorded_so_a_verdict_can_be_audited(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it pins the knight", classifier=StubClassifier(True)
        )

        assert record.classifier == "stub/v1"


class UnreachableClassifier:
    name = "ollama/never-running"

    def classify(self, answer: str, expected_reason: str) -> bool | None:
        raise ClassifierUnavailable("http://localhost:1: refused")


class TestWhyItCouldNotTell:
    """Four different situations all produce `reason_matched: None`.

    Found by running a real session against an Ollama that had stopped: every
    probe recorded a tidy `unknown`, indistinguishable from a player who could
    not explain themselves. One is evidence about the player, the other about
    the infrastructure.
    """

    def test_an_unreachable_model_does_not_end_the_session(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it pins the knight",
            classifier=UnreachableClassifier(),
        )

        assert record.inference == GapTypeHypothesis.UNKNOWN.value

    def test_but_it_is_recorded_as_unavailable(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it pins the knight",
            classifier=UnreachableClassifier(),
        )

        assert record.classifier_status == ClassifierStatus.UNAVAILABLE.value
        assert not record.was_actually_asked

    def test_a_vague_answer_is_recorded_as_unclear_not_unavailable(self):
        record = interpret(
            a_probe(), move="Bb5", reason="hard to say", classifier=StubClassifier(None)
        )

        assert record.classifier_status == ClassifierStatus.UNCLEAR.value
        assert record.was_actually_asked

    @pytest.mark.parametrize("reason", ["   ", "I don't know", "no idea", "intuition"])
    def test_a_player_who_gave_no_reason_is_recorded_as_declining(self, reason):
        # A worded refusal is a refusal, not a model that could not tell. Caught
        # live: "I have no idea honestly" was landing as `unclear`.
        record = interpret(a_probe(), move="Bb5", reason=reason, classifier=StubClassifier(True))

        assert record.classifier_status == ClassifierStatus.DECLINED.value
        assert not record.was_actually_asked

    def test_a_declining_answer_never_reaches_the_model(self):
        classifier = StubClassifier(True)

        interpret(a_probe(), move="Bb5", reason="no idea", classifier=classifier)

        assert classifier.calls == []

    def test_a_wrong_move_records_that_the_reason_was_moot(self):
        record = interpret(a_probe(), move="h3", reason="whatever", classifier=StubClassifier(True))

        assert record.classifier_status == ClassifierStatus.NOT_CONSULTED.value

    def test_a_real_verdict_is_recorded_as_answered(self):
        record = interpret(
            a_probe(), move="Bb5", reason="it pins the knight", classifier=StubClassifier(True)
        )

        assert record.classifier_status == ClassifierStatus.ANSWERED.value
        assert record.was_actually_asked


class TestApplyingToFindings:
    def test_it_rewrites_the_gap_type_and_says_it_was_probed(self):
        finding = a_finding()
        record = interpret(
            a_probe(finding), move="Bb5", reason="it pins the knight", classifier=StubClassifier(True)
        )

        updated = apply_to_findings((finding,), (record,))[0]

        assert updated.gap_type.hypothesis is GapTypeHypothesis.SKILL
        assert updated.gap_type.determined_by is DeterminedBy.PROBED
        assert record.id in updated.gap_type.probe_ids

    def test_an_unprobed_finding_is_left_exactly_as_it_was(self):
        probed, untouched = a_finding(subject="pin"), a_finding(subject="fork")
        record = interpret(
            a_probe(probed), move="Bb5", reason="pins it", classifier=StubClassifier(True)
        )

        result = apply_to_findings((probed, untouched), (record,))

        assert result[1] == untouched

    def test_an_unknown_result_does_not_claim_it_was_probed(self):
        # Recording "we asked and learned nothing" as `probed` would overstate
        # the evidence behind a gap type that is still a guess.
        finding = a_finding()
        record = interpret(a_probe(finding), move=None, reason=None, classifier=StubClassifier(None))

        updated = apply_to_findings((finding,), (record,))[0]

        assert updated.gap_type.determined_by is DeterminedBy.INFERRED

    def test_findings_are_returned_in_their_original_order(self):
        findings = (a_finding(subject="pin"), a_finding(subject="fork"))

        result = apply_to_findings(findings, ())

        assert [f.claim.subject for f in result] == ["pin", "fork"]


class TestOverturning:
    def test_a_probe_can_be_asked_whether_it_overturned_the_finding(self):
        # Probes that can only confirm are theatre (architecture.interaction § 5).
        finding = a_finding()
        solved = interpret(
            a_probe(finding), move="Bb5", reason="it pins the knight", classifier=StubClassifier(True)
        )

        assert solved.overturns_knowledge_gap

    def test_a_failed_probe_does_not_overturn_anything(self):
        record = interpret(a_probe(), move="h3", reason="dunno", classifier=StubClassifier(True))

        assert not record.overturns_knowledge_gap


@pytest.mark.parametrize(
    "move",
    [
        "Bb5",
        "  Bb5  ",
        "bb5",
        "﻿Bb5",  # byte-order mark, from a pasted or piped answer
        "Bb5​",  # zero-width space
        "﻿  Bb5\r\n",
    ],
)
def test_move_matching_ignores_spacing_case_and_invisible_characters(move):
    # Not hypothetical: a BOM survived str.strip() in the first real probe
    # session and turned a correct move into a knowledge gap the player did not
    # have. An invisible character must never cost someone a diagnosis.
    record = interpret(a_probe(), move=move, reason="pins it", classifier=StubClassifier(True))

    assert record.move_correct is True
    assert record.inference != GapTypeHypothesis.KNOWLEDGE.value


@pytest.mark.parametrize("move", ["Bb4", "Nf3", "B b5"])
def test_a_different_move_is_still_a_different_move(move):
    record = interpret(a_probe(), move=move, reason="pins it", classifier=StubClassifier(True))

    assert record.inference == GapTypeHypothesis.KNOWLEDGE.value
