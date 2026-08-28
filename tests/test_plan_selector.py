"""A model choosing which of a page's sentences are plans.

Design: docs/notes/experiments.e51-llm-selection-and-search.md

**The model answers with indices, never with text.** That is the safety argument
and it is what these tests hold: what comes back is a set of numbers into a list
built from the page, so a selected sentence is verbatim by construction.

It matters because of what E50 measured. The grounding check's false-claim pass
rate goes **3 % -> 76 %** when the source it compares against grows from the
extracted quotes to the whole page. Selection is what keeps that source small and
the page's own words; a selector that could invent a sentence would poison the
ground truth of every later check.
"""

from __future__ import annotations

from chesscoach import ollama
from chesscoach.opening_plans import is_plan_sentence
from chesscoach.plan_selector import LlmSelector, RegexSelector

PAGE = """
<h1>Pirc Defense</h1>
<p>Black allows White to occupy the center with pawns on e4 and d4, aiming to
undermine it later with well timed pawn breaks and piece pressure.</p>
<p>The opening is named after the Slovenian grandmaster Vasja Pirc, who played
it in the middle of the twentieth century.</p>
<p>Black aims to stay flexible, first completing development and only later
choosing a pawn break.</p>
"""


def answering(text: str):
    def transport(_url, _body):
        return {"response": text}
    return transport


class TestTheModelPicksFromThePage:
    def test_the_chosen_sentences_come_back_verbatim(self):
        selector = LlmSelector(transport=answering("0, 2"))

        chosen = selector.select("Pirc Defense", PAGE, limit=2)

        assert len(chosen) == 2
        assert chosen[0].startswith("Black allows White to occupy")
        assert chosen[1].startswith("Black aims to stay flexible")

    def test_it_can_keep_a_sentence_the_regexes_reject(self):
        # The point of the exercise. The filters demand forward-looking phrasing;
        # a model can see that a sentence is a plan without the trigger words.
        page = "<p>The whole point for Black is counterplay against the centre "
        page += "once the pieces are out and the king is safe.</p>"

        assert RegexSelector().select("Pirc", page) == ()
        assert LlmSelector(transport=answering("0")).select("Pirc", page)

    def test_an_out_of_range_index_is_dropped_not_clamped(self):
        # A hallucinated index is not a near miss.
        selector = LlmSelector(transport=answering("0, 99"))

        assert len(selector.select("Pirc Defense", PAGE, limit=3)) == 1

    def test_none_means_none(self):
        # Silence is a real answer: a reference page explains what an opening is
        # and never what to aim for.
        selector = LlmSelector(transport=answering("NONE"))

        assert selector.select("Pirc Defense", PAGE) == ()

    def test_an_answer_with_no_numbers_selects_nothing(self):
        selector = LlmSelector(transport=answering("I think the first one is best"))

        assert selector.select("Pirc Defense", PAGE) == ()

    def test_never_more_than_asked_for(self):
        # Fewer is legitimate: index 1 is "named after the Slovenian grandmaster
        # Vasja Pirc", which the veto drops for naming nothing on the board.
        selector = LlmSelector(transport=answering("0, 1, 2"))

        assert 0 < len(selector.select("Pirc Defense", PAGE, limit=2)) <= 2


class TestTheModelCannotIntroduceText:
    def test_prose_in_the_answer_is_not_treated_as_a_selection(self):
        # If the model writes a sentence instead of numbers, nothing it wrote
        # can reach the output -- only indices can.
        invented = "Black should immediately break with c5 and attack the queenside."
        selector = LlmSelector(transport=answering(invented))

        assert selector.select("Pirc Defense", PAGE) == ()

    def test_every_returned_sentence_is_present_on_the_page(self):
        selector = LlmSelector(transport=answering("0, 1, 2"))

        for sentence in selector.select("Pirc Defense", PAGE, limit=3):
            assert sentence in " ".join(PAGE.split())

    def test_an_empty_page_is_not_a_question_for_the_model(self):
        asked = []

        def transport(_url, body):
            asked.append(body)
            return {"response": "0"}

        assert LlmSelector(transport=transport).select("Pirc", "") == ()
        assert asked == []


class TestTheCandidateList:
    def test_fragments_and_paragraph_runs_are_not_offered(self):
        selector = LlmSelector()
        page = "<p>Too short.</p><p>" + "word " * 60 + "long.</p>"

        assert selector.candidates(page) == []

    def test_the_offer_is_bounded(self):
        selector = LlmSelector(offered=3)
        page = "".join(
            f"<p>Black aims to break with the c pawn in variation {i} of this line.</p>"
            for i in range(20)
        )

        assert len(selector.candidates(page)) == 3


class TestFailure:
    def test_an_unreachable_model_raises_rather_than_selecting_nothing(self):
        # "Ollama is down" and "this page has no plans" must not look identical.
        def failing(_url, _body):
            raise ollama.OllamaUnavailable("localhost:11434 -> URLError")

        selector = LlmSelector(transport=failing)

        try:
            selector.select("Pirc Defense", PAGE)
        except ollama.OllamaUnavailable:
            return
        raise AssertionError("expected OllamaUnavailable")


class TestTheVetoOverTheModelsChoice:
    """The model replaces the recall-limiting rule, not the precision ones.

    Every sentence below is one the model actually picked in a real run
    (docs/notes/experiments.e51-llm-selection-and-search.md).
    """

    def picked(self, sentence: str, veto: bool = True):
        page = f"<p>{sentence}</p>"
        return LlmSelector(transport=answering("0"), veto=veto).select("X", page)

    def test_marketing_the_model_accepted_is_vetoed(self):
        assert self.picked(
            "White's main idea in the Alapin Highlighted course The High Pressure "
            "Alapin Sicilian Discover White is hoping to strike at the center."
        ) == ()

    def test_trivia_the_model_accepted_is_vetoed(self):
        assert self.picked(
            "One of the players who has been using it for many years, producing "
            "many beautiful and convincing wins is Gata Kamsky."
        ) == ()

    def test_an_annotated_line_the_model_accepted_is_vetoed(self):
        assert self.picked(
            "Nxe5 6.d4 with a fork and Black can only get a balanced game if they "
            "know the line and play very accurately in the next moves."
        ) == ()

    def test_a_real_plan_the_regexes_missed_survives_the_veto(self):
        # The reason for doing this at all: the PLAN pattern rejects it and the
        # veto does not, so the model's recall is kept.
        sentence = ("This gives white flexibility to later choose between two "
                    "main plans: strike in the center or start an attack on the "
                    "kingside.")

        assert is_plan_sentence(sentence) is False
        assert self.picked(sentence) == (sentence,)

    def test_prose_naming_four_squares_is_not_an_annotated_line(self):
        sentence = ("The core idea is simple: White develops the dark-squared "
                    "bishop to f4 before blocking it with e3, then builds a solid "
                    "pawn chain with c3 and e3.")

        assert self.picked(sentence) == (sentence,)

    def test_the_veto_can_be_turned_off_to_measure_it(self):
        assert self.picked(
            "One of the players who has been using it for many years, producing "
            "many beautiful and convincing wins is Gata Kamsky.",
            veto=False,
        ) != ()
