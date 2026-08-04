"""Reason classifiers — the only place a model is allowed to act.

Spec: docs/notes/capacity.agents.prober.md § 3-4 · docs/notes/experiments.e07-reason-classification.md

Everything here runs without a network. Agreement against real answers is E07's
job and needs Ollama; these tests cover the parts that must not break silently —
refusal handling, verdict parsing, and the promise that an unreachable model
degrades to "cannot tell" rather than to a wrong answer.
"""

from __future__ import annotations

import pytest

from chesscoach.classifiers import (
    EmbeddingBaseline,
    KeywordFloor,
    OllamaClassifier,
    _cosine,
    _verdict,
    declines_to_answer,
)

UNREACHABLE = "http://localhost:1"


class TestDecliningToAnswer:
    @pytest.mark.parametrize(
        "answer",
        ["I don't know", "no idea, I just played it", "?", "", "   ", "intuition",
         "it looked good", "not sure really", "idk", "because the engine said so"],
    )
    def test_a_non_answer_is_recognised(self, answer):
        assert declines_to_answer(answer)

    @pytest.mark.parametrize(
        "answer",
        ["it pins the knight", "the horse is stuck because the king is behind it",
         "it develops my bishop", "free piece"],
    )
    def test_a_real_reason_is_not(self, answer):
        assert not declines_to_answer(answer)

    def test_it_is_asked_before_any_classifier_runs(self):
        # Refusal is a property of the utterance, not of its chess content. E07
        # measured every classifier collapsing "declined" into "wrong" until
        # this was separated out.
        assert KeywordFloor().classify("I don't know", "pin") is None


class TestKeywordFloor:
    def test_it_finds_the_word(self):
        assert KeywordFloor().classify("it pins the knight", "pin") is True

    def test_it_accepts_a_common_synonym(self):
        assert KeywordFloor().classify("double attack on king and rook", "fork") is True

    def test_it_marks_an_understanding_player_ignorant(self):
        # Documented failure, not a bug: this is why the floor is a floor. The
        # player has described a pin exactly and never used the word.
        answer = "his knight can't move or he loses the queen"

        assert KeywordFloor().classify(answer, "pin") is False


class TestVerdictParsing:
    @pytest.mark.parametrize("text", ["yes", "Yes", " YES ", "yes.", "yes, it does"])
    def test_yes_in_its_various_dresses(self, text):
        assert _verdict(text) is True

    @pytest.mark.parametrize("text", ["no", "No.", " no "])
    def test_no(self, text):
        assert _verdict(text) is False

    @pytest.mark.parametrize("text", ["unclear", "", "   ", "maybe", "I think perhaps"])
    def test_anything_else_is_cannot_tell_rather_than_a_guess(self, text):
        assert _verdict(text) is None


class TestDegradingWithoutAModel:
    """The prober promises to degrade, not to fail. A model that is not running
    must not take down a probe session."""

    def test_the_llm_classifier_returns_cannot_tell(self):
        classifier = OllamaClassifier(host=UNREACHABLE)

        assert classifier.classify("it pins the knight", "pin") is None

    def test_the_embedding_baseline_returns_cannot_tell(self):
        classifier = EmbeddingBaseline(host=UNREACHABLE)

        assert classifier.classify("it pins the knight", "pin") is None

    def test_an_unknown_reason_is_not_guessed_at(self):
        assert OllamaClassifier().classify("something", "notAMotif") is None


class TestClassifierIdentity:
    def test_the_name_records_the_model_so_a_verdict_can_be_audited(self):
        assert "llama3.2:3b" in OllamaClassifier(model="llama3.2:3b").name

    def test_the_embedding_name_records_its_threshold(self):
        # The threshold is as much a part of the verdict as the model is.
        assert "0.62" in EmbeddingBaseline(threshold=0.62).name


class TestCosine:
    def test_identical_vectors(self):
        assert _cosine([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert _cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_a_zero_vector_does_not_divide_by_zero(self):
        assert _cosine([0.0, 0.0], [1.0, 1.0]) == 0.0
