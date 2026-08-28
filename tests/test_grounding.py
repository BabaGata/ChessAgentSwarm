"""Checking a rewrite against the text it was rewritten from.

Design: docs/notes/decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert.md

The gate that makes a local model admissible here. If it does not hold, the
project is laundering folklore through a checker that does not check (R-03).

The two failure modes are tested separately because they are separate: a wrong
square is a concrete false claim, and imported vocabulary is a model drawing on
its training rather than its input.
"""

from __future__ import annotations

from chesscoach.grounding import MAX_NOVELTY, check, content_words, moves_in

SOURCE = (
    "Black allows White to occupy the center with pawns on e4 and d4, aiming to "
    "undermine it later with well timed pawn breaks and piece pressure. "
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break."
)


class TestFindingConcreteClaims:
    def test_squares_are_found(self):
        assert moves_in("Play e4 and then d4.") == ("e4", "d4")

    def test_piece_moves_are_found(self):
        assert "Nf3" in moves_in("Develop with Nf3 next.")

    def test_castling_is_a_concrete_claim(self):
        assert "O-O" in moves_in("You should play O-O early.")

    def test_captures_are_found(self):
        assert "exd5" in moves_in("After exd5 the file opens.")

    def test_ordinary_words_are_not_moves(self):
        assert moves_in("Black aims to stay flexible and develop.") == ()

    def test_stopwords_carry_no_claim(self):
        assert "the" not in content_words("The plan is the break")
        assert "break" in content_words("The plan is the break")


class TestAWrongSquareIsCaught:
    def test_a_square_not_in_the_source_is_ungrounded(self):
        # The failure this gate exists for: one character between advice and
        # misinformation.
        result = check("Black should break with c5 in the centre.", SOURCE)

        assert result.grounded is False
        assert "c5" in result.ungrounded_moves
        assert "c5" in result.reason

    def test_a_square_that_is_in_the_source_passes(self):
        result = check(
            "White takes the centre with pawns on e4 and d4, and Black "
            "undermines it later with a timed pawn break.",
            SOURCE,
        )

        assert result.ungrounded_moves == ()
        assert result.grounded is True

    def test_an_invented_piece_move_is_caught(self):
        result = check("Develop with Nf3 and then break.", SOURCE)

        assert "Nf3" in result.ungrounded_moves

    def test_a_square_and_a_bishop_move_are_not_confused(self):
        # "Be4" is a move; "e4" is a square. Case-folding them together would
        # let a hallucinated bishop move ground itself on a mentioned square.
        result = check("Play Be4 at once.", SOURCE)

        assert "Be4" in result.ungrounded_moves


class TestImportedVocabulary:
    def test_a_faithful_rewrite_has_low_novelty(self):
        result = check(
            "In this opening Black lets White build the centre with pawns on e4 "
            "and d4, then undermines it later. Complete development first and "
            "choose a pawn break once White has committed.",
            SOURCE,
        )

        assert result.novelty <= MAX_NOVELTY
        assert result.grounded is True

    def test_a_model_writing_from_its_own_knowledge_is_caught(self):
        result = check(
            "The Pirc suits players who enjoy hypermodern counterattack, "
            "prophylaxis, dynamic imbalance, kingside expansion, queenside "
            "majorities, prophylactic manoeuvring, and rich strategic nuance.",
            SOURCE,
        )

        assert result.novelty > MAX_NOVELTY
        assert result.grounded is False
        assert "novelty" in result.reason

    def test_inflections_of_source_words_are_not_novel(self):
        # A rewrite is allowed to say "developing" where the source said
        # "development", or the reader gets a checker that forbids rewriting.
        result = check(
            "Black is developing pieces first and undermines the centre later.",
            SOURCE,
        )

        assert result.grounded is True

    def test_empty_output_is_not_silently_grounded(self):
        result = check("", SOURCE)

        assert result.novelty == 0.0


class TestTheLimitThisCannotReach:
    def test_negation_is_caught_but_only_by_accident(self):
        """Inverting the advice needs words like "avoid" and "never".

        Those are not in the source, so novelty catches them -- which is luck
        rather than design, and is recorded as such so it is not mistaken for a
        semantic check.
        """
        result = check(
            "Black should avoid the pawn break and never undermine the centre "
            "on e4 or d4, staying passive instead.",
            SOURCE,
        )

        assert result.grounded is False
        assert "avoid" in result.novel_words

    def test_swapping_the_colours_passes_both_checks(self):
        """The real hole, pinned so nobody reads `grounded` as "correct".

        Every word and every square is the source's; only who does what has
        changed. Both checks pass and the advice is backwards. This is the
        residue that keeps `reviewed=true` a person's job.
        """
        result = check(
            "White aims to undermine the center with pawns on e4 and d4, "
            "while Black allows the pressure and completes development.",
            SOURCE,
        )

        assert result.ungrounded_moves == ()
        assert result.novelty <= MAX_NOVELTY
        assert result.grounded is True  # ...and the colours are the wrong way round.
