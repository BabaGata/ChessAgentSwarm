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
