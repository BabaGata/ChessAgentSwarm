"""The model may summarise the findings; it may not add to them.

Design: docs/notes/design.narrated-session.md

No model runs here. The transport is injected, so what is tested is the
accept/reject rule -- the property the whole design rests on: a rejected summary
leaves the player with exactly the report they would have had without a model.
"""

from __future__ import annotations

from dataclasses import replace

from chesscoach.narrator import facts, narrate, numbers_in, ungrounded_numbers
from chesscoach.ollama import OllamaUnavailable
from test_explainer import a_finding, a_profile

REPORT = """Report for alice
24 games (2026-05-01 to 2026-07-30), rating band 1400-1800

WHAT STANDS OUT

1. You miss pins more often than players at your level.

   How often   30% of the time, against 12% for players at your level
   Seen in     8 of 24 games
   For example move 20, you played h3 (Bb5 was better)

WHAT TO DO

1. Solve pin puzzles for accuracy, not speed.
"""


def replying(text: str):
    def post(_url, _body):
        return {"response": text}
    return post


def failing():
    def post(_url, _body):
        raise OllamaUnavailable("localhost:11434 -> URLError")
    return post


def recording(*answers: str):
    prompts: list[str] = []
    queue = list(answers)

    def post(_url, body):
        prompts.append(body["prompt"])
        return {"response": queue.pop(0) if len(queue) > 1 else queue[0]}
    return post, prompts


def two_findings():
    pins = a_finding(subject="pin", rate=0.30, peer_rate=0.12)
    forks = a_finding(kind="allowed_motif", subject="fork", rate=0.25, peer_rate=0.10)
    return a_profile(pins, forks)


class TestNumbers:
    def test_it_reads_percentages_and_decimals(self):
        assert numbers_in("30% against 12.5 and 8 of 24") == ("30", "12.5", "8", "24")

    def test_a_decimal_comma_is_the_same_number(self):
        assert ungrounded_numbers("about 12,5 points", "12.5 points") == ()

    def test_a_number_the_report_never_gave_is_caught(self):
        assert ungrounded_numbers("you miss pins 45% of the time", REPORT) == ("45",)


class TestFacts:
    """E92: given the report's own layout, the model read "64% of the time" as "64% of
    the games" and copied its labels ("Target:", "Below 3% ..."). It is given plain
    sentences built from the measurements instead."""

    def test_one_fact_sheet_per_planned_finding(self):
        assert len(facts(two_findings())) == 2

    def test_the_rate_says_what_it_is_a_share_of(self):
        sheet = facts(a_profile(a_finding(rate=0.30, peer_rate=0.12)))[0]

        assert "30% of the times it could have happened" in sheet
        assert "12% for players at your level" in sheet
        assert "8 of 24 games" in sheet

    def test_no_plan_means_nothing_to_summarise(self):
        assert facts(a_profile(a_finding(), with_plan=False)) == ()


class TestAcceptance:
    def test_a_faithful_sentence_is_kept(self):
        said = "You miss pins in 30% of the times it could have happened, against 12%."
        narration = narrate(a_profile(a_finding()), transport=replying(said))

        assert narration.accepted
        assert narration.text == said

    def test_an_invented_number_is_rejected(self):
        narration = narrate(a_profile(a_finding()), transport=replying(
            "You miss pins 45% of the time, in 8 of 24 games."))

        assert not narration.accepted
        assert narration.text is None
        assert "45" in narration.reason

    def test_an_invented_move_is_rejected(self):
        narration = narrate(a_profile(a_finding()), transport=replying(
            "You should have played Nf3 there."))

        assert not narration.accepted
        assert "Nf3" in narration.reason

    def test_chess_advice_of_its_own_is_rejected(self):
        narration = narrate(a_profile(a_finding()), transport=replying(
            "Develop knights before bishops, castle early, control the centre with "
            "pawns and study rook endgames from classical manuals every evening."))

        assert not narration.accepted
        assert "novelty" in narration.reason

    def test_an_empty_answer_is_not_a_summary(self):
        assert not narrate(a_profile(a_finding()), transport=replying("   ")).accepted


class TestOneFindingAtATime:
    """E92: summaries of the whole report mixed findings up -- a cost moved from one
    pattern to another. Each finding is written from its own facts only, so a
    number borrowed from another finding is ungrounded and caught."""

    def test_each_finding_is_written_from_its_own_facts(self):
        post, prompts = recording("You miss pins.")

        narrate(two_findings(), transport=post)

        assert len(prompts) == 2
        assert sorted(("30%" in p, "25%" in p) for p in prompts) == [(False, True), (True, False)]

    def test_a_number_borrowed_from_the_other_finding_drops_that_sentence(self):
        def post(_url, body):
            if "30%" in body["prompt"]:
                return {"response": "You miss pins in 30% of the times it could have happened."}
            return {"response": "You concede forks 30% of the time."}

        narration = narrate(two_findings(), transport=post)

        assert narration.accepted
        assert "forks" not in narration.text
        assert "1 of 2" in narration.reason


class TestNoModel:
    def test_a_stopped_backend_is_said_and_not_raised(self):
        narration = narrate(a_profile(a_finding()), transport=failing())

        assert not narration.accepted
        assert "unavailable" in narration.reason

    def test_a_finding_without_a_plan_step_is_not_summarised(self):
        profile = a_profile(a_finding())
        bare = replace(profile, plan=None)

        assert narrate(bare, transport=replying("x")).reason.startswith("nothing")
