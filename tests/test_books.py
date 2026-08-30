"""Public-domain chess books as a source.

Design: docs/notes/design.knowledge-base.md

The author asked for books. They answer the failure the web kept producing: a
book by a world champion is about chess by construction, so the relevance gate
built to exclude a Beyonce film, a Go wiki and a communism essay is not needed
against it -- and they are strong exactly where the web returned nothing.
"""

from __future__ import annotations

from chesscoach.books import SHELF, BookLibrary, is_book, strip_licence

LICENCED = """
The Project Gutenberg eBook of Chess Fundamentals, by Capablanca
*** START OF THE PROJECT GUTENBERG EBOOK CHESS FUNDAMENTALS ***
Castling is a move in which the King and a Rook move together. It is the
only move in which two pieces are moved at once, and it brings the King
into safety behind its own pawns.
*** END OF THE PROJECT GUTENBERG EBOOK CHESS FUNDAMENTALS ***
This eBook is for the use of anyone anywhere at no cost.
"""


class TestTheGutenbergWrapper:
    def test_the_licence_is_not_part_of_the_book(self):
        # The header alone is hundreds of words of licence terms, long enough to
        # dominate a passage -- and it would be cited as a source if left in.
        text = strip_licence(LICENCED)
        assert "Castling is a move" in text
        assert "PROJECT GUTENBERG" not in text
        assert "no cost" not in text

    def test_a_text_without_a_wrapper_is_returned_whole(self):
        assert strip_licence("A fork attacks two pieces.") == "A fork attacks two pieces."


class TestFindingPassages:
    def library(self) -> BookLibrary:
        return BookLibrary({SHELF[0].slug: LICENCED_BODY})

    def test_it_finds_a_passage_mentioning_the_terms(self):
        found = BookLibrary({SHELF[0].slug: LICENCED_BODY}).passages(["castling"])
        assert found
        book, locator, passage = found[0]
        assert book.author.endswith("Capablanca")
        assert is_book(locator)
        assert "Castling" in passage

    def test_it_finds_nothing_for_a_term_the_books_do_not_use(self):
        # Measured, not assumed: "skewer" appears zero times in all three books,
        # because the word postdates them. The library must say so rather than
        # return the nearest passage.
        assert BookLibrary({SHELF[0].slug: LICENCED_BODY}).passages(["skewer"]) == []

    def test_no_terms_finds_nothing(self):
        assert BookLibrary({SHELF[0].slug: LICENCED_BODY}).passages([]) == []

    def test_an_empty_shelf_is_not_an_error(self):
        assert len(BookLibrary({})) == 0
        assert BookLibrary({}).passages(["castling"]) == []


class TestItRanksProseOverContents:
    def test_a_contents_page_scores_nothing(self):
        # Counting terms put a table of contents at the top of the first run: a
        # contents page names every subject once and explains none.
        contents = ("TABLE OF CONTENTS\n1. CASTLING 12\n2. DEVELOPMENT 28\n"
                    "3. THE PIN 44\n") * 20
        assert BookLibrary({SHELF[0].slug: contents}).passages(["castling"]) == []

    def test_prose_about_the_term_is_found(self):
        assert BookLibrary({SHELF[0].slug: LICENCED_BODY}).passages(["castling"])


class TestCitations:
    def test_a_book_cites_its_author_title_and_year(self):
        assert SHELF[0].publisher == "José Raúl Capablanca, Chess Fundamentals (1921)"

    def test_a_book_is_one_expert_however_eminent(self):
        # `expert-consensus` would be a claim about the field that a single
        # book cannot support, world champion or not.
        assert all(b.evidence_class == "single-expert" for b in SHELF)


LICENCED_BODY = (
    "Castling is a move in which the King and a Rook move together, and it is "
    "the only move in which two pieces are moved at once. It brings the King "
    "into safety behind its own pawns and develops the Rook towards the centre. "
) * 6
