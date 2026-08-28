"""Pointing at instruction rather than copying it.

Design: docs/notes/design.informative-claims.md

The plan-level material a 1500 needs is all copyrighted, and the public-domain
books predate the openings these players play. So the system links instead of
quoting — which removes the licence problem and the folklore problem at once,
because it then asserts nothing about chess it did not measure.

The property these tests exist to hold: **an unreviewed link never reaches a
player.** Recommending is endorsing, and the author has not endorsed a candidate.
"""

from __future__ import annotations

from chesscoach.opening_guides import Guide, GuideLibrary


def a_library() -> GuideLibrary:
    return GuideLibrary((
        Guide(opening="Scandinavian Defense", title="Plans in the Scandinavian",
              url="https://example.org/scandi", publisher="Example", reviewed=True),
        Guide(opening="Scandinavian Defense: Modern Variation", title="Candidate",
              url="https://example.org/scandi-modern", publisher="Example",
              reviewed=False),
        Guide(opening="French Defense", title="French plans",
              url="https://example.org/french", publisher="Example", reviewed=True),
    ))


class TestOnlyReviewedLinksAreShown:
    def test_an_unreviewed_candidate_is_never_returned(self):
        found = a_library().for_opening("Scandinavian Defense")

        assert [g.title for g in found] == ["Plans in the Scandinavian"]

    def test_candidates_are_still_listed_for_the_author(self):
        # They must be visible to be reviewed — just never to a player.
        assert len(a_library().candidates) == 1

    def test_a_library_of_only_candidates_shows_a_player_nothing(self):
        library = GuideLibrary((
            Guide(opening="Italian Game", title="c", url="https://e.org/i",
                  publisher="E", reviewed=False),
        ))

        assert library.for_opening("Italian Game") == ()


class TestMatching:
    def test_a_subline_gets_its_family_guide(self):
        found = a_library().for_opening("Scandinavian Defense: Mieses-Kotroc Variation")

        assert [g.title for g in found] == ["Plans in the Scandinavian"]

    def test_an_unknown_opening_returns_nothing_rather_than_something_near(self):
        assert a_library().for_opening("Grob Opening") == ()


class TestSilenceIsVisible:
    def test_it_reports_which_openings_have_no_reviewed_guide(self):
        missing = a_library().openings_without_a_guide([
            "French Defense: Advance Variation",
            "Scandinavian Defense",
            "Pirc Defense",
            "Vienna Game: Stanley Variation",
        ])

        assert missing == ("Pirc Defense", "Vienna Game")


class TestRoundTrip:
    def test_a_saved_library_reloads_unchanged(self, tmp_path):
        path = tmp_path / "guides.json"
        a_library().save(path)
        again = GuideLibrary.load(path)

        assert len(again) == 3
        assert len(again.reviewed) == 2
        assert again.for_opening("French Defense")[0].url == "https://example.org/french"


class TestValidationIsAMaintenancePassNotAReadTimeCheck:
    """A dead link must never reach a player; a fetch must never reach a report.

    Screen: docs/notes/experiments.e48-opening-agent.md, which found one dead link
    (Owen Defense, HTTP 410) sitting in the library ready to be printed.

    So liveness is **stamped** onto the library by a maintenance pass, and reads
    filter on the stamp. Putting the check in `for_opening` would be an HTTP call
    in the report's inner loop — slow, flaky, and against C1.
    """

    def test_a_link_confirmed_dead_is_never_returned(self):
        library = GuideLibrary((
            Guide(opening="Owen Defense", title="gone", url="https://e.org/410",
                  publisher="P", reviewed=True, alive=False, checked_on="2026-08-24"),
            Guide(opening="Owen Defense", title="fine", url="https://e.org/ok",
                  publisher="P", reviewed=True, alive=True, checked_on="2026-08-24"),
        ))

        assert [g.title for g in library.for_opening("Owen Defense")] == ["fine"]

    def test_an_unchecked_link_still_shows(self):
        # The author approved it by opening it, so it was alive then. Absence of
        # a check is not evidence of death, and hiding it would silently empty
        # the library the moment the field was added.
        library = GuideLibrary((
            Guide(opening="French Defense", title="never checked",
                  url="https://e.org/f", publisher="P", reviewed=True),
        ))

        assert len(library.for_opening("French Defense")) == 1

    def test_a_dead_link_that_was_never_approved_is_still_not_returned(self):
        library = GuideLibrary((
            Guide(opening="X", title="t", url="https://e.org/x", publisher="P",
                  reviewed=False, alive=False),
        ))

        assert library.for_opening("X") == ()

    def test_the_library_can_report_what_needs_attention(self):
        library = GuideLibrary((
            Guide(opening="A", title="dead", url="https://e.org/1", publisher="P",
                  reviewed=True, alive=False, checked_on="2026-08-24"),
            Guide(opening="B", title="live", url="https://e.org/2", publisher="P",
                  reviewed=True, alive=True, checked_on="2026-08-24"),
            Guide(opening="C", title="unchecked", url="https://e.org/3", publisher="P",
                  reviewed=True),
        ))

        assert [g.title for g in library.dead] == ["dead"]
        assert [g.title for g in library.unchecked] == ["unchecked"]


class TestStamping:
    def test_validation_returns_a_new_library_rather_than_mutating(self):
        original = GuideLibrary((
            Guide(opening="A", title="t", url="https://e.org/1", publisher="P",
                  reviewed=True),
        ))

        class FakeAgent:
            def check(self, guide):
                from chesscoach.opening_agent import Checked
                return Checked(guide=guide, alive=False, status="HTTP 410",
                               summary="")

        stamped = original.validated(FakeAgent(), today="2026-08-24")

        assert original.unchecked and not original.dead      # untouched
        assert [g.title for g in stamped.dead] == ["t"]
        assert stamped._guides[0].checked_on == "2026-08-24"

    def test_a_page_description_is_kept_as_the_summary(self):
        library = GuideLibrary((
            Guide(opening="A", title="t", url="https://e.org/1", publisher="P"),
        ))

        class FakeAgent:
            def check(self, guide):
                from chesscoach.opening_agent import Checked
                return Checked(guide=guide, alive=True, status="200",
                               summary="Learn the plans and pawn breaks.")

        stamped = library.validated(FakeAgent(), today="2026-08-24")

        assert stamped._guides[0].summary == "Learn the plans and pawn breaks."


class TestASublineGuideOnlyReachesThatSubline:
    """Some families are not openings anyone studies.

    Measured: of ten "Indian Defense" games, five became a London and five did
    not. A London guide on the whole family is right for half the players and
    wrong for the other half, which is worse than covering neither
    (docs/notes/experiments.e50-ollama-summaries.md).
    """

    def a_library(self) -> GuideLibrary:
        return GuideLibrary((
            Guide(opening="Indian Defense: Accelerated London System",
                  title="London System guide", url="https://example.org/london",
                  publisher="Example", reviewed=True),
        ))

    def test_a_player_who_reaches_the_subline_gets_the_guide(self):
        found = self.a_library().for_opening("Indian Defense: Accelerated London System")

        assert [g.title for g in found] == ["London System guide"]

    def test_a_player_elsewhere_in_the_family_gets_nothing(self):
        # The defect this exists to stop: a Przepiorka player handed a London
        # guide because both games start 1. d4 Nf6.
        assert self.a_library().for_opening("Indian Defense: Przepiorka Variation") == ()

    def test_the_bare_family_gets_nothing(self):
        assert self.a_library().for_opening("Indian Defense") == ()

    def test_a_deeper_variant_of_the_scope_is_still_covered(self):
        found = self.a_library().for_opening(
            "Indian Defense: Accelerated London System, Modern Variation"
        )

        assert len(found) == 1

    def test_a_name_that_merely_starts_the_same_is_not_covered(self):
        # Without the separator in the comparison, "London System" would claim
        # "London Systematic" and anything else sharing a prefix.
        library = GuideLibrary((
            Guide(opening="Indian Defense: London", title="g",
                  url="https://example.org/x", publisher="E", reviewed=True),
        ))

        assert library.for_opening("Indian Defense: Londonderry Variation") == ()

    def test_a_family_guide_still_covers_every_subline(self):
        library = GuideLibrary((
            Guide(opening="Pirc Defense", title="family", url="https://example.org/p",
                  publisher="E", reviewed=True),
        ))

        assert len(library.for_opening("Pirc Defense: Austrian Attack")) == 1

    def test_the_specific_guide_sorts_ahead_of_the_general_one(self):
        library = GuideLibrary((
            Guide(opening="Sicilian Defense", title="whole family",
                  url="https://example.org/sicilian", publisher="E", reviewed=True),
            Guide(opening="Sicilian Defense: Alapin Variation", title="alapin",
                  url="https://example.org/alapin", publisher="E", reviewed=True),
        ))

        found = library.for_opening("Sicilian Defense: Alapin Variation")

        assert [g.title for g in found] == ["alapin", "whole family"]
