"""The moves, the quoted plans, and the link — assembled for one opening.

Design: docs/notes/decisions.0012-quote-the-plans-rather-than-write-them.md

The author approved the Pirc entry and asked for the same shape everywhere:
*"the main lines to be fetched with maybe a few variants. Short summary or
description of the information about the plans and a link for further
references."*

Two properties these tests hold, and they are the ones that could quietly break:

  **an unreviewed page's sentences never reach a player** — quoting is a
    stronger endorsement than linking, not a weaker one;
  **which variants are shown comes from the player's own games** — the
    alternative is this project inventing an editorial opinion about chess.
"""

from __future__ import annotations

from chesscoach.opening_guides import Guide, GuideLibrary
from chesscoach.opening_resource import MAX_VARIANTS, build_resource
from chesscoach.openings import OpeningBook

ROWS = (
    ("B07", "Pirc Defense", "1. e4 d6 2. d4 Nf6 3. Nc3"),
    ("B08", "Pirc Defense: Classical Variation", "1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Nf3"),
    ("B09", "Pirc Defense: Austrian Attack", "1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. f4"),
    ("B07", "Pirc Defense: Byrne Variation", "1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Bg5"),
    ("B06", "Modern Defense", "1. e4 g6"),
)

PLANS = (
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break.",
)


def a_book() -> OpeningBook:
    return OpeningBook.from_rows(ROWS)


def a_library(reviewed: bool = True, plans=PLANS) -> GuideLibrary:
    return GuideLibrary((
        Guide(opening="Pirc Defense", title="Pirc plans",
              url="https://example.org/pirc", publisher="Example Trainer",
              reviewed=reviewed, plans=tuple(plans)),
    ))


class TestTheMoves:
    def test_the_main_line_is_the_one_named_for_the_family(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert resource.main_line.name == "Pirc Defense"
        assert resource.main_line.moves == "1. e4 d6 2. d4 Nf6 3. Nc3"

    def test_variants_are_the_family_sublines(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert [v.variation for v in resource.variants] == [
            "Austrian Attack", "Byrne Variation", "Classical Variation",
        ]

    def test_another_opening_is_not_a_variant_of_this_one(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert all("Modern" not in v.name for v in resource.variants)

    def test_a_subline_name_resolves_to_its_family(self):
        # A player's game is labelled with the subline; the resource is the
        # family's, because that is what they would sit down and study.
        resource = build_resource(
            "Pirc Defense: Austrian Attack", a_book(), a_library()
        )

        assert resource.family == "Pirc Defense"
        assert resource.main_line.name == "Pirc Defense"

    def test_never_more_variants_than_the_cap(self):
        rows = ROWS + tuple(
            ("B08", f"Pirc Defense: Line {i}", f"1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. h{i}")
            for i in range(3, 5)
        )

        resource = build_resource("Pirc Defense", OpeningBook.from_rows(rows), a_library())

        assert len(resource.variants) <= MAX_VARIANTS

    def test_an_opening_the_book_does_not_know_yields_no_line(self):
        resource = build_resource("Grob Opening", a_book(), a_library())

        assert resource.main_line is None
        assert resource.variants == ()


class TestVariantsComeFromThePlayersGames:
    def test_a_line_the_player_actually_reaches_is_shown_first(self):
        reached = ["Pirc Defense: Byrne Variation"] * 6 + ["Pirc Defense"] * 2

        resource = build_resource("Pirc Defense", a_book(), a_library(), reached=reached)

        assert resource.variants[0].variation == "Byrne Variation"
        assert resource.variants[0].games == 6

    def test_with_no_games_the_order_is_the_stated_fallback(self):
        # Shallowest first, and `games` is None so the report can say which
        # rule produced the list rather than implying evidence it does not have.
        resource = build_resource("Pirc Defense", a_book(), a_library(), reached=())

        assert all(v.games is None for v in resource.variants)


class TestQuotingIsEndorsing:
    def test_an_unreviewed_page_contributes_no_sentences(self):
        resource = build_resource("Pirc Defense", a_book(), a_library(reviewed=False))

        assert resource.plans == ()
        assert resource.guide is None
        assert resource.has_plans is False

    def test_a_reviewed_page_contributes_its_own_words(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert resource.plans == PLANS
        assert resource.has_plans is True

    def test_every_quote_travels_with_its_source(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert "Example Trainer" in resource.attribution
        assert "https://example.org/pirc" in resource.attribution

    def test_the_moves_survive_when_no_guide_is_endorsed(self):
        # The CC0 book needs no endorsement, so an opening with no approved
        # guide still gets its lines. Losing them too would be the fallback
        # punishing the player for the library's gap.
        resource = build_resource("Pirc Defense", a_book(), a_library(reviewed=False))

        assert resource.main_line is not None
        assert resource.variants

    def test_a_reviewed_page_with_no_plan_sentences_says_nothing(self):
        resource = build_resource("Pirc Defense", a_book(), a_library(plans=()))

        assert resource.plans == ()
        assert resource.has_plans is False
        # ...but the link still stands: "read this" is what it always was.
        assert resource.guide is not None


class TestTheFamilysOwnRowsAreNotVariations:
    """The book names several rows plainly for the family, at different depths.

    Treating the extra ones as branches printed "Main line" three times beneath
    the main line, which is noise dressed as information.
    """

    def a_book_with_repeated_family_rows(self) -> OpeningBook:
        return OpeningBook.from_rows(ROWS + (
            ("B07", "Pirc Defense", "1. e4 d6"),
            ("B07", "Pirc Defense", "1. e4 d6 2. d4"),
        ))

    def test_the_deepest_plain_row_is_the_main_line(self):
        resource = build_resource(
            "Pirc Defense", self.a_book_with_repeated_family_rows(), a_library()
        )

        assert resource.main_line.moves == "1. e4 d6 2. d4 Nf6 3. Nc3"

    def test_no_variation_is_labelled_as_the_main_line(self):
        resource = build_resource(
            "Pirc Defense", self.a_book_with_repeated_family_rows(), a_library()
        )

        assert "Main line" not in [v.variation for v in resource.variants]

    def test_every_variation_names_itself(self):
        resource = build_resource(
            "Pirc Defense", self.a_book_with_repeated_family_rows(), a_library()
        )

        assert all(":" in v.name for v in resource.variants)

    def test_one_row_per_named_variation(self):
        # The book lists a variation at several depths; showing both reads as
        # two different variations with two different move counts.
        rows = ROWS + (
            ("B08", "Pirc Defense: Classical Variation",
             "1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Nf3 Bg7"),
        )

        resource = build_resource("Pirc Defense", OpeningBook.from_rows(rows), a_library())

        labels = [v.variation for v in resource.variants]
        assert len(labels) == len(set(labels))


class TestTheOptionalRewrite:
    """A summariser can improve the prose and must never degrade it.

    Design: docs/notes/decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert.md
    """

    def test_without_a_summariser_the_prose_is_the_quotes(self):
        resource = build_resource("Pirc Defense", a_book(), a_library())

        assert resource.summary is None
        assert resource.prose == " ".join(PLANS)

    def test_an_accepted_rewrite_becomes_the_prose(self):
        from chesscoach.opening_summary import OllamaSummariser

        summariser = OllamaSummariser(post=lambda _u, _b: {"response": (
            "Stay flexible, complete development first, and choose a pawn break "
            "only later."
        )})

        resource = build_resource("Pirc Defense", a_book(), a_library(),
                                  summariser=summariser)

        assert resource.summary.accepted is True
        assert resource.prose.startswith("Stay flexible")

    def test_a_rejected_rewrite_leaves_the_quotes_standing(self):
        from chesscoach.opening_summary import OllamaSummariser

        summariser = OllamaSummariser(post=lambda _u, _b: {"response": (
            "Black should break with c5 and attack on the queenside at once."
        )})

        resource = build_resource("Pirc Defense", a_book(), a_library(),
                                  summariser=summariser)

        assert resource.summary.accepted is False
        assert resource.prose == " ".join(PLANS)

    def test_an_unreviewed_page_is_never_handed_to_a_model(self):
        # Rephrasing something unendorsed would launder it into prose that no
        # longer looks like an unreviewed quote.
        asked = []

        from chesscoach.opening_summary import OllamaSummariser

        def post(_url, body):
            asked.append(body)
            return {"response": "anything"}

        build_resource("Pirc Defense", a_book(), a_library(reviewed=False),
                       summariser=OllamaSummariser(post=post))

        assert asked == []
