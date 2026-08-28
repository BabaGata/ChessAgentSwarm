"""Selecting a page's plan sentences, never writing one.

Design: docs/notes/decisions.0012-quote-the-plans-rather-than-write-them.md

The acceptance case is real. The author read FreeChessTrainer's Pirc page, called
it *"actually just enough for players around 1500"*, and quoted two of its
sentences as the register everything else should match. Both are verbatim page
text, so the selector can be tested against them directly.

**That page is the calibration case and cannot also be the proof.** Recovering
the two sentences shows the rules encode what was endorsed; whether they
generalise is the author's read of other openings, and the note says so.
"""

from __future__ import annotations

from chesscoach.opening_plans import (
    MAX_QUOTES,
    is_usable_note,
    names_a_target,
    MAX_TOTAL_WORDS,
    is_plan_sentence,
    plan_quotes,
    text_blocks,
)

# The shape the real page has: a heading immediately above the sentence it
# introduces, which is what produced "Black's goals Black aims to stay flexible"
# before block boundaries were kept.
PIRC = """
<html><head><title>Pirc</title></head><body>
<nav>Home Openings <a href="/signup">Sign up</a></nav>
<h1>Pirc Defense</h1>
<p>Black allows White to occupy the center with pawns on e4 and d4, aiming to
undermine it later with well timed pawn breaks and piece pressure. It is a
flexible, hypermodern system that can lead to complex middlegames.</p>
<h2>Black's goals</h2>
<p>Black aims to stay flexible, first completing development and only later
choosing a pawn break.</p>
<footer>If you are finding how to improve, I recommend you to check our course.</footer>
</body></html>
"""


class TestTheEndorsedRegister:
    def test_it_recovers_the_sentences_the_author_approved(self):
        assert plan_quotes(PIRC) == (
            "Black allows White to occupy the center with pawns on e4 and d4, "
            "aiming to undermine it later with well timed pawn breaks and piece "
            "pressure.",
            "Black aims to stay flexible, first completing development and only "
            "later choosing a pawn break.",
        )

    def test_a_heading_is_not_glued_to_the_sentence_below_it(self):
        # Arrange / Act
        quotes = plan_quotes(PIRC)

        # Assert -- the bug this catches produced "Black's goals Black aims to..."
        assert not any(q.startswith("Black's goals") for q in quotes)


class TestBlocks:
    def test_block_elements_become_separate_entries(self):
        assert text_blocks("<h2>Plans</h2><p>Play on the queenside.</p>") == [
            "Plans", "Play on the queenside."
        ]

    def test_navigation_and_scripts_are_not_page_text(self):
        blocks = text_blocks("<nav>Menu</nav><script>var x=1</script><p>Real text.</p>")

        assert blocks == ["Real text."]

    def test_entities_are_decoded(self):
        assert text_blocks("<p>Black&#39;s plan is clear.</p>") == ["Black's plan is clear."]


class TestTheAuthorsThreeObjections:
    def test_a_sentence_about_what_to_aim_for_is_kept(self):
        assert is_plan_sentence(
            "Black aims to break with c5 once the pieces are developed."
        )

    def test_a_sentence_describing_what_happened_is_not_a_plan(self):
        # Objection 1: it explains the past instead of naming the target.
        assert not is_plan_sentence(
            "White captured on d5 and the position opened up considerably here."
        )

    def test_a_sentence_assuming_vocabulary_is_dropped_however_good(self):
        # Objection 3, and the reason the Caro-Kann entry was rejected.
        assert not is_plan_sentence(
            "Black aims to meet the minority attack with active piece play."
        )

    def test_a_fragment_is_not_a_sentence(self):
        assert not is_plan_sentence("You should castle.")

    def test_a_paragraph_length_run_is_refused(self):
        # Objection 2: unreadable at 1500, and usually a stripping failure.
        assert not is_plan_sentence("Black aims to " + "play well and ".join(["x"] * 45))

    def test_a_question_is_not_an_instruction(self):
        assert not is_plan_sentence("How do you study the London System and its plans?")


class TestMarketingWearsTheSameGrammar:
    def test_a_recommendation_of_a_product_is_not_a_plan(self):
        # Found by reading, not predicted: this exact sentence scored on the
        # plan metric and inflated a page to the top of the shortlist.
        assert not is_plan_sentence(
            "If you are finding how to improve your chess level, I recommend you "
            "to check the method."
        )

    def test_a_page_speaking_as_itself_is_refused(self):
        assert not is_plan_sentence(
            "In our course we show you how to develop your pieces quickly."
        )


class TestQuotationStaysQuotation:
    def test_never_more_than_the_cap_however_many_are_asked_for(self):
        page = "<p>" + " ".join(
            [f"Black aims to break with c{i} in the middlegame at some point."
             for i in range(20)]
        ) + "</p>"

        assert len(plan_quotes(page, limit=99)) <= MAX_QUOTES

    def test_the_total_word_budget_is_respected(self):
        page = "".join(
            f"<p>Black aims to break with the c pawn and develop your pieces "
            f"toward the kingside in variation number {i} of this line.</p>"
            for i in range(10)
        )

        quotes = plan_quotes(page, limit=MAX_QUOTES)

        assert sum(len(q.split()) for q in quotes) <= MAX_TOTAL_WORDS

    def test_a_page_with_no_plan_sentences_yields_nothing(self):
        # Silence is the correct output. An empty tuple says "this page does not
        # explain plans", which is a finding; inventing one would be folklore.
        assert plan_quotes("<p>The Pirc Defense was named after Vasja Pirc.</p>") == ()

    def test_an_empty_page_is_not_an_error(self):
        assert plan_quotes("") == ()


class TestWhatARealRunLetThrough:
    """Every case here is a verbatim quote the extractor produced on real pages.

    They are kept as sentences rather than as rules because a rule can be
    rewritten to pass its own test; the output cannot (L-044).
    """

    def test_a_sentence_cut_at_an_abbreviation_is_not_quotable(self):
        # From Exeter Chess Club. The splitter broke on "e.g." mid-sentence.
        assert not is_plan_sentence(
            "Nf3 Nf6 either side can try an early break with the d-Pawn (e.g."
        )

    def test_abbreviations_no_longer_split_a_sentence(self):
        blocks = plan_quotes(
            "<p>Both sides will look to break with a pawn, e.g. c5 in the "
            "center, before White develops the pieces to good squares.</p>"
        )

        assert blocks and blocks[0].endswith("squares.")

    def test_named_structures_are_assumed_vocabulary(self):
        # Objection 3, from the source whose provenance looked strongest.
        assert not is_plan_sentence(
            "One popular system for Black is to allow White the Maroczy bind "
            "while retaining a flexible position and aiming for a break."
        )

    def test_an_annotated_variation_is_not_a_sentence(self):
        # From the Chueca blog. Grammatical, and unreadable as advice.
        assert not is_plan_sentence(
            "(this is the key) exf6 5.Nc3 Bg7 6.g3 O-O 7.Bg2 O-O 8.e3 preparing "
            "Nge2 and castle with pressure on the weak square d5."
        )

    def test_naming_two_or_three_squares_is_still_prose(self):
        # The rule above must not eat the good sentences, which do name squares.
        assert is_plan_sentence(
            "Black allows White to occupy the center with pawns on e4 and d4, "
            "aiming to undermine it later with well timed pawn breaks."
        )

    def test_encouragement_that_names_nothing_on_the_board_is_dropped(self):
        # From TheChessWorld. Passes every content rule and says nothing.
        assert not is_plan_sentence(
            "You can one day play a long positional game and the next surprise "
            "your opponent with a much sharper line."
        )

    def test_advice_about_studying_is_not_advice_about_playing(self):
        assert not is_plan_sentence(
            "If you feel comfortable with the positions then you can continue "
            "with the further study of the French Defense and its plans."
        )

    def test_plural_products_are_caught_like_singular_ones(self):
        # "course" matched; "courses" did not, and the sentence shipped.
        assert not is_plan_sentence(
            "The theory has developed and you can already choose from a number "
            "of good courses and books on this system."
        )

    def test_a_black_move_written_with_a_typographic_ellipsis_is_analysis(self):
        # "4…Nf6" is a numbered move; matching only the ASCII "..." missed it.
        assert not is_plan_sentence(
            "Note: If Black plays 4…Nf6, you can try to counter with the "
            "Alien Gambit, just for fun."
        )


class TestWhatTheAssessorMustNotPassOn:
    """Notes are raw material for the Compiler, so they may be hard to read.

    The author's correction: *"this doesn't has to be disregarded, compiler will
    be the one that writes something understandable, more information is better
    than just disregarding it."* So `is_usable_note` drops the readability tests
    and keeps the relevance ones. Every case below is verbatim from a real run.
    """

    def test_hard_vocabulary_is_kept_for_the_compiler_to_translate(self):
        sentence = ("Black allows White the Maroczy bind and aims for counterplay "
                    "on the queenside later.")

        assert is_plan_sentence(sentence) is False   # too advanced to show as-is
        assert is_usable_note(sentence) is True      # ...but worth passing on

    def test_a_win_rate_is_not_information_about_how_to_play(self):
        assert not is_usable_note(
            "Across 50.8 million Lichess games, White wins 50.2% of the time."
        )

    def test_a_rating_table_line_is_refused(self):
        assert not is_usable_note(
            "At 1200 Elo the top reply is d4, and the second is Nf3 for White."
        )

    def test_a_forum_comment_in_lower_case_is_refused(self):
        # FIRST_PERSON was case-sensitive, so this reached the Compiler as a note.
        assert not is_usable_note(
            "Oh me i also play it against d4 and c4 whenever White allows it."
        )

    def test_a_breadcrumb_trail_is_not_a_sentence(self):
        assert not is_usable_note(
            "Home / Articles / Openings / Czech Pirc Complete Guide for Black"
        )

    def test_a_menu_item_with_an_emoji_is_not_a_sentence(self):
        assert not is_usable_note(
            "\U0001F9E0 Fianchetto London vs King's Indian Setup Adapt the London "
            "when Black plays g6"
        )

    def test_a_tag_list_is_refused(self):
        assert not is_usable_note(
            "Tags: Complete Guide , flexible hypermodern opening , for Black , "
            "White pieces"
        )

    def test_a_real_plan_sentence_survives_all_of_it(self):
        assert is_usable_note(
            "Usually the c and e pawns are placed on the third rank, supporting "
            "the d4 pawn."
        )


class TestWhatCountsAsConcrete:
    """A point must name something locatable — not necessarily a square.

    Two corrections from the author, both from reading real output:

      *"white should take d file but still keep track of black attacks on king
      with light squared bishop and a queen ... only some general ideas which is
      still good and useful"*

      *"control the center, challenge White's pawn structure are ok if they are
      explained like control the center with knight and rook"*

    So the rule is a **positive scan over the whole sentence**, never a veto on
    phrases: a point may open generally and qualify on what comes after.
    """

    def test_a_general_opening_clause_does_not_disqualify_a_point(self):
        # The exact question asked: is such a sentence discarded for containing
        # a general phrase anywhere? No -- only if it names nothing anywhere.
        assert names_a_target("control the center with knight and rook")
        assert names_a_target(
            "challenge White's pawn structure on the weaker queen side"
        )

    def test_the_same_phrases_alone_are_discarded(self):
        assert not names_a_target(
            "Control the center and challenge White's pawn structure"
        )

    def test_the_authors_first_example_is_concrete(self):
        assert names_a_target(
            "White should take the d file but still keep track of Black's attacks "
            "on the king with the light squared bishop and a queen."
        )

    def test_files_diagonals_ranks_and_wings_are_locatable(self):
        assert names_a_target("Double rooks on the c file when it opens.")
        assert names_a_target("Push the f-pawn to gain space on that wing.")
        assert names_a_target("Contest the long diagonal before castling.")
        assert names_a_target("Give the king air so the back rank is not weak.")
        assert names_a_target("Play for a break on the queenside.")

    def test_a_square_is_still_locatable(self):
        assert names_a_target("Keep the knight on e5 for as long as possible.")

    def test_collective_nouns_name_nothing(self):
        # Every one of these was produced by the swarm and says nothing.
        assert not names_a_target("Develop pieces in harmony and prepare for counterplay")
        assert not names_a_target("Counter White's development by controlling key squares")

    def test_bare_pawns_locate_nothing_but_a_named_pawn_does(self):
        # There are eight pawns, so "locking pawns" points at none of them.
        assert not names_a_target("Improve by locking pawns and waiting patiently.")
        assert names_a_target("Trade off the d-pawn before it becomes weak.")
