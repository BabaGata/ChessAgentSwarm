"""Three agents with three roles, and the boundaries between them.

Design: docs/notes/decisions.0014-three-agents-for-the-opening-brief.md, revised
by docs/notes/decisions.0015-a-learned-skip-list-and-a-bullet-brief.md

No model runs here. What these hold is the separation of duties and the failure
behaviour of each role — the part that decides whether a swarm of language models
can be trusted with a player-facing brief:

  the Scout may not make the search worse than not asking it, and never fetches
    what the skip list already refuses;
  the Assessor reads TEXT, keeps the page's own sentences, and may put a site on
    the skip list only when the page was not an article at all;
  the Compiler may not speak when nothing was approved, and each of its bullets
    is kept or dropped on its own.
"""

from __future__ import annotations

import pytest

from chesscoach import ollama
from chesscoach.opening_swarm import (
    Assessor,
    Brief,
    Candidate,
    Compiler,
    OpeningSwarm,
    Scout,
    _bullets,
    _queries,
)
from chesscoach.skiplist import SkipEntry, SkipList

NOTES = (
    "Black allows White to occupy the center with pawns on e4 and d4, aiming to "
    "undermine it later with well timed pawn breaks.",
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break.",
)

ARTICLE = "<p>" + "Black aims to stay flexible and choose a pawn break later. " * 30 + "</p>"


def answering(*replies: str):
    remaining = list(replies)

    def transport(_url, _body):
        return {"response": remaining.pop(0) if len(remaining) > 1 else remaining[0]}
    return transport


def failing(_url, _body):
    raise ollama.OllamaUnavailable("localhost:11434 -> URLError")


class FakeSearcher:
    name = "fake"

    def __init__(self, default=()) -> None:
        self._default = list(default)
        self.queries: list[str] = []

    def search_detailed(self, gap):
        self.queries.append(gap.query)
        return list(self._default)


PAGE_A = ("Pirc plans", "https://a.org/pirc", "a.org", "the plans explained")
TIKTOK = ("Pirc in 60 seconds", "https://www.tiktok.com/@x/video/1", "tiktok.com", "")


class TestTheScoutNeverFetchesWhatIsSkipped:
    def test_a_skipped_domain_never_becomes_a_candidate(self):
        scout = Scout(searcher=FakeSearcher(default=[PAGE_A, TIKTOK]),
                      transport=answering("pirc defense plans"))

        found = scout.find("Pirc Defense")

        assert [c.publisher for c in found] == ["a.org"]
        assert "tiktok.com" in scout.skipped

    def test_both_default_queries_run(self):
        searcher = FakeSearcher(default=[PAGE_A])
        Scout(searcher=searcher, transport=answering("pirc defense plans")).find("Pirc")

        assert len(searcher.queries) == 3

    def test_one_default_query_asks_about_the_opponent(self):
        searcher = FakeSearcher(default=[PAGE_A])
        Scout(searcher=searcher, transport=failing).find("Pirc Defense")

        assert any("against" in q for q in searcher.queries)

    def test_the_defaults_run_even_if_the_model_is_down(self):
        # A model that cannot be reached must not make the search worse than
        # never having asked it.
        searcher = FakeSearcher(default=[PAGE_A])
        scout = Scout(searcher=searcher, transport=failing)

        assert len(scout.find("Pirc Defense")) == 1
        assert len(searcher.queries) == 2

    def test_a_sentence_is_not_a_query(self):
        assert _queries("Here is a good search you could try:", 3) == []

    def test_a_title_cased_heading_is_too_long_to_be_a_query(self):
        assert _queries("Bird Opening Strategy for Club Players Middlegame Guide "
                        "And More Words", 3) == []


class TestTheAssessorReadsText:
    def test_it_keeps_the_pages_own_sentences_by_index(self):
        reading = Assessor(transport=answering("0")).read(
            "Pirc Defense", Candidate(*PAGE_A), ARTICLE
        )

        assert reading.useful
        assert reading.sentences[0] in " ".join(ARTICLE.split())

    def test_prose_in_the_answer_selects_nothing(self):
        # Only indices can reach the output, so nothing the model writes can.
        reading = Assessor(transport=answering(
            "I think Black should break with c5 immediately."
        )).read("Pirc Defense", Candidate(*PAGE_A), ARTICLE)

        assert reading.sentences == ()

    def test_the_veto_still_applies_to_the_models_choice(self):
        page = ("<p>One of the players who has been using it for many years, "
                "producing many convincing wins is Gata Kamsky. </p>" + ARTICLE)

        reading = Assessor(transport=answering("0")).read(
            "Pirc Defense", Candidate(*PAGE_A), page
        )

        assert all("Kamsky" not in s for s in reading.sentences)

    def test_none_means_none(self):
        reading = Assessor(transport=answering("NONE")).read(
            "Pirc Defense", Candidate(*PAGE_A), ARTICLE
        )

        assert reading.sentences == ()
        assert reading.skip_reason == ""


class TestTheAssessorMaintainsTheSkipList:
    def test_a_page_with_no_article_is_classified(self):
        reading = Assessor(transport=answering("video")).read(
            "Pirc Defense", Candidate(*TIKTOK), "<p>Watch now</p>"
        )

        assert reading.skip_reason == "video"
        assert reading.sentences == ()

    def test_a_reason_outside_the_list_is_not_a_reason(self):
        reading = Assessor(transport=answering("it was rubbish")).read(
            "Pirc Defense", Candidate(*TIKTOK), "<p>Watch now</p>"
        )

        assert reading.skip_reason == ""

    def test_an_article_is_never_classified_for_skipping(self):
        # The model is only ever asked about a page that already failed to yield
        # prose, so it cannot condemn a site it merely disliked.
        reading = Assessor(transport=answering("0")).read(
            "Pirc Defense", Candidate(*PAGE_A), ARTICLE
        )

        assert reading.skip_reason == ""

    def test_an_unreachable_model_proposes_no_skip(self):
        reading = Assessor(transport=failing).read(
            "Pirc Defense", Candidate(*TIKTOK), "<p>x</p>"
        )

        assert reading.skip_reason == ""


class TestTheCompilerWritesBullets:
    def test_points_are_produced_under_their_labels(self):
        brief = Compiler(transport=answering(
            "PLAN: Let White build the centre with pawns on e4 and d4.\n"
            "PLAN: Complete development before choosing a pawn break.\n"
            "WATCH: White will occupy the centre and keep the pressure on."
        )).compile("Pirc Defense", NOTES)

        assert len(brief.plans) == 2
        assert len(brief.watches) == 1
        assert brief.accepted is True

    def test_one_bad_point_is_dropped_and_the_rest_survive(self):
        # The reason for bullets: a paragraph fails whole, a point fails alone.
        brief = Compiler(transport=answering(
            "PLAN: Complete development before choosing a pawn break.\n"
            "PLAN: Push c5 and h5 to open the queenside at once."
        )).compile("Pirc Defense", NOTES)

        assert len(brief.plans) == 1
        assert len(brief.dropped) == 1
        assert "c5" in brief.dropped[0].dropped_for

    def test_a_watch_point_repeating_a_plan_point_is_dropped(self):
        brief = Compiler(transport=answering(
            "PLAN: Black aims to stay flexible and choose a pawn break later.\n"
            "WATCH: Black will stay flexible and will choose a pawn break later."
        )).compile("Pirc Defense", NOTES)

        assert len(brief.plans) == 1
        assert brief.watches == ()
        assert "repeats" in brief.dropped[0].dropped_for

    def test_no_opponent_points_is_not_a_failure(self):
        # WATCH is wanted, not required.
        brief = Compiler(transport=answering(
            "PLAN: Complete development before choosing a pawn break."
        )).compile("Pirc Defense", NOTES)

        assert brief.accepted is True
        assert brief.watches == ()

    def test_prose_around_the_points_is_ignored(self):
        brief = Compiler(transport=answering(
            "Here is the brief you asked for:\n"
            "PLAN: Complete development before choosing a pawn break.\n"
            "I hope this helps!"
        )).compile("Pirc Defense", NOTES)

        assert len(brief.plans) == 1

    def test_nothing_approved_means_nothing_said(self):
        asked = []

        def transport(_url, body):
            asked.append(body)
            return {"response": "PLAN: something."}

        assert Compiler(transport=transport).compile("Pirc", ()).accepted is False
        assert asked == []

    def test_a_bullet_needs_words_to_be_a_point(self):
        assert _bullets("PLAN: yes\nWATCH: Black will try to hold the centre.") == [
            ("watch", "Black will try to hold the centre.")
        ]

    def test_list_markers_before_the_label_are_allowed(self):
        assert _bullets("- PLAN: Complete development before the break.") == [
            ("plan", "Complete development before the break.")
        ]


class TestTheSwarmEndToEnd:
    def test_a_skipped_site_is_never_fetched(self):
        fetched: list[str] = []

        def fetch(url):
            fetched.append(url)
            return ARTICLE

        OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A, TIKTOK]), fetch=fetch,
            transport=answering(
                "pirc defense plans", "0",
                "PLAN: Black aims to stay flexible and choose a pawn break later."
            ),
        ).run("Pirc Defense")

        assert fetched == ["https://a.org/pirc"]

    def test_a_site_that_helped_is_protected_from_later_skipping(self):
        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A]), fetch=lambda _u: ARTICLE,
            transport=answering(
                "pirc defense plans", "0",
                "PLAN: Black aims to stay flexible and choose a pawn break later."
            ),
        )

        swarm.run("Pirc Defense")

        assert "a.org" in swarm.skiplist.useful

    def test_an_unreadable_page_teaches_the_skip_list(self):
        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[("Clip", "https://clips.example/x",
                                            "clips.example", "")]),
            fetch=lambda _u: "<p>Watch now</p>",
            skiplist=SkipList((SkipEntry("tiktok.com", "video", "seed"),)),
            transport=answering("pirc defense plans", "video", "PLAN: nothing."),
        )

        swarm.run("Pirc Defense")

        assert swarm.skiplist.skips("https://clips.example/other")
        assert swarm.trace[0]["learned"] == [("clips.example", "video")]

    def test_the_trace_records_what_was_skipped_before_fetching(self):
        swarm = OpeningSwarm(
            searcher=FakeSearcher(default=[PAGE_A, TIKTOK]),
            fetch=lambda _u: ARTICLE,
            transport=answering("pirc defense plans", "0", "PLAN: x y z w."),
        )

        swarm.run("Pirc Defense")

        assert "tiktok.com" in swarm.trace[0]["skipped_before_fetch"]


class TestTheBrief:
    def test_a_brief_with_no_plan_points_is_not_accepted(self):
        assert Brief("Pirc").accepted is False


def test_the_compiler_raises_when_the_model_is_down():
    # Distinct from "it wrote something bad", which returns an empty brief.
    with pytest.raises(ollama.OllamaUnavailable):
        Compiler(transport=failing).compile("Pirc Defense", NOTES)
