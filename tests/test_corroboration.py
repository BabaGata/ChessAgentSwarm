"""Counting agreement without counting ancestry.

Design: docs/notes/design.graph-knowledge-base.md § "The evidence rule"

The author's rule replaces one endorsement per entry with one rule endorsed
once: a concept is confirmed when several sources describe it similarly. What
these tests pin is the three ways that rule can lie to you.

* **One author is one voice.** Edward Lasker wrote two of the seven books on the
  shelf, so a count over files would let him corroborate himself.
* **Mentioning is not describing.** Agreement is similarity between the passages,
  so the same idea in different words counts and two unrelated remarks do not --
  which is the whole reason vectors are here rather than keyword counts.
* **Verbatim agreement is copying.** Pre-1929 chess books borrow from each other,
  and identical phrasing across two books is evidence of a shared ancestor rather
  than of two people having checked.
"""

from __future__ import annotations

from chesscoach.corroboration import (
    AGREEMENT,
    Attestation,
    Corroboration,
    corroborate,
    cosine,
)


def vec(*values) -> list[float]:
    return list(values)


# Two vectors 0.8 apart, and one pointing elsewhere.
NEAR_A = vec(1.0, 0.0, 0.0)
NEAR_B = vec(0.9, 0.436, 0.0)      # cosine ~0.9 with NEAR_A
FAR = vec(0.0, 0.0, 1.0)           # cosine 0.0 with both
IDENTICAL = vec(1.0, 0.0, 0.0)     # cosine 1.0 with NEAR_A


def attest(locator, lineage):
    return Attestation("backward pawn", locator, lineage, f"text at {locator}")


class TestCosine:
    def test_identical_vectors_are_one(self):
        assert cosine(NEAR_A, IDENTICAL) == 1.0

    def test_orthogonal_vectors_are_zero(self):
        assert cosine(NEAR_A, FAR) == 0.0

    def test_an_empty_vector_is_zero_not_an_error(self):
        # A passage with no embedding must not crash a count, and must not
        # silently look like perfect agreement either.
        assert cosine(NEAR_A, []) == 0.0


class TestOneAuthorIsOneVoice:
    def test_two_books_by_one_author_do_not_corroborate_each_other(self):
        # The case on the real shelf: Edward Lasker wrote two of the seven.
        candidates = [attest("book://lasker-a#1", "Edward Lasker"),
                      attest("book://lasker-b#2", "Edward Lasker")]
        vectors = {"book://lasker-a#1": NEAR_A, "book://lasker-b#2": IDENTICAL}

        got = corroborate("backward pawn", candidates, vectors)

        assert got.independent == 0
        assert not got.servable()

    def test_two_authors_agreeing_is_corroboration(self):
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://b#2": NEAR_B}

        got = corroborate("backward pawn", candidates, vectors)

        assert got.independent == 2
        assert got.servable()

    def test_the_count_is_lineages_not_passages(self):
        # Three passages, two voices. The number that matters is two.
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://a#9", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://a#9": NEAR_A, "book://b#2": NEAR_B}

        got = corroborate("backward pawn", candidates, vectors)

        assert len(got.attestations) == 3
        assert got.independent == 2


class TestMentioningIsNotDescribing:
    def test_passages_that_do_not_agree_are_dropped(self):
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://b#2": FAR}

        got = corroborate("backward pawn", candidates, vectors)

        assert got.attestations == ()
        assert not got.servable()

    def test_a_lone_passage_corroborates_nothing(self):
        got = corroborate("outpost", [attest("book://a#1", "Capablanca")],
                          {"book://a#1": NEAR_A})

        assert got.independent == 0
        assert not got.servable()

    def test_no_candidates_is_not_an_error(self):
        # The expected outcome for "skewer": E64 measured zero occurrences of it
        # across the shelf, so silence here is a true report.
        got = corroborate("skewer", [], {})

        assert got.attestations == ()
        assert got.attribution == ""


class TestVerbatimAgreementIsCopying:
    def test_near_identical_passages_are_flagged(self):
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://b#2": IDENTICAL}

        got = corroborate("backward pawn", candidates, vectors)

        assert got.shared_ancestors, "identical wording across books must be flagged"

    def test_a_flag_is_reported_once_per_pair(self):
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://b#2": IDENTICAL}

        got = corroborate("backward pawn", candidates, vectors)

        assert len(got.shared_ancestors) == 1


class TestWhatTheBaseMaySay:
    def test_the_attribution_names_the_voices_and_claims_nothing(self):
        got = Corroboration("backward pawn", (
            attest("book://a#1", "Capablanca"), attest("book://b#2", "Staunton")))

        said = got.attribution

        assert "Capablanca" in said and "Staunton" in said
        # It is a claim about the literature, never about chess. "is" or "means"
        # would be this project asserting a chess fact it cannot support.
        assert "describe it this way" in said

    def test_a_single_voice_is_singular(self):
        got = Corroboration("outpost", (attest("book://a#1", "Capablanca"),))

        assert got.attribution == "Capablanca describes it this way"

    def test_the_threshold_is_a_parameter_not_a_hidden_constant(self):
        candidates = [attest("book://a#1", "Capablanca"),
                      attest("book://b#2", "Staunton")]
        vectors = {"book://a#1": NEAR_A, "book://b#2": NEAR_B}

        strict = corroborate("x", candidates, vectors, agreement=0.99)
        loose = corroborate("x", candidates, vectors, agreement=AGREEMENT)

        assert strict.attestations == ()
        assert loose.attestations != ()
