"""The gate that decides whether a passage is about a concept at all.

Design: docs/notes/design.graph-knowledge-base.md § "Extraction"

**Why the gate exists**, and it is the whole lesson of E79: without it,
corroboration reported 19 concepts of 19 confirmed at every threshold from 0.50
to 0.80 -- including `skewer`, which E64 measured as appearing **zero times**
across the shelf. The method was circular. Passages were retrieved for being
similar to a query and then measured for being similar to each other, and every
page of chess prose passes a test like that.

Two more versions were wrong before this one, both measured rather than reasoned
about:

* matching whole `TERMS` phrases refused **every** `pin` passage, because those
  phrases are search queries ("pin chess tactic") and a book writes "the pin";
* matching their content words accepted **every** `skewer` passage, because
  "chess" was among the words and every chess book contains it.

The model half of the gate is tested nowhere here, because it was measured to do
nothing: `qwen3:8b`, given an explicit criterion and a refusal option, kept
**15 of 15** passages that reached it.
"""

from __future__ import annotations

from chesscoach.extraction import _index_of, mentions, sentences_of


class TestMentions:
    def test_a_passage_using_the_term_passes(self):
        assert mentions("pin", "White wins a piece because the knight is pinned "
                               "against the king and cannot move.")

    def test_a_passage_never_using_the_term_is_refused(self):
        # The `skewer` case: chess prose, about chess, not about this.
        assert not mentions(
            "skewer", "The method to follow is to advance the king as far as is "
                      "compatible with the safety of the pawn.")

    def test_generic_chess_words_do_not_admit_a_passage(self):
        # "chess" appears on nearly every page of a chess book, so a filter that
        # accepts on it accepts everything. This is the version that reported
        # skewer as corroborated by four voices.
        assert not mentions(
            "skewer", "This is a game of chess between two players, and the "
                      "position on the board favours the first player.")

    def test_a_concept_written_with_underscores_is_matched_by_its_words(self):
        assert mentions("late_castling",
                        "It is, of course, better to castle before playing P-Q3.")


class TestSentences:
    def test_short_fragments_are_not_offered_as_definitions(self):
        # A definition needs a clause. "1. P-K4" is not one, and a board diagram
        # is made of exactly that.
        assert sentences_of("P-K4. Kt-KB3. B-B4.") == []

    def test_a_real_sentence_is_kept_and_normalised(self):
        got = sentences_of("A pin is a situation in which a piece cannot move\n"
                           "without exposing a more valuable piece behind it.")

        assert len(got) == 1
        assert "\n" not in got[0]

    def test_the_list_is_capped_so_the_numbering_stays_reliable(self):
        from chesscoach.extraction import MAX_SENTENCES
        text = " ".join(
            f"This is a reasonably long sentence about chess, number {n}." * 1
            for n in range(40))

        assert len(sentences_of(text)) <= MAX_SENTENCES


class TestIndexOf:
    def test_a_bare_number(self):
        assert _index_of("3") == 3

    def test_structured_output(self):
        assert _index_of('{"sentence": 2}') == 2

    def test_a_refusal(self):
        assert _index_of("-1") == -1

    def test_prose_around_the_number(self):
        # Structured output should make this unnecessary and does not: a small
        # model asked for an integer will sometimes wrap it anyway.
        assert _index_of("The answer is sentence 4.") == 4

    def test_nothing_usable_is_none_not_zero(self):
        # Zero is a valid sentence index, so returning it for an unparseable
        # reply would silently select the first sentence every time.
        assert _index_of("") is None
        assert _index_of("I cannot tell") is None
