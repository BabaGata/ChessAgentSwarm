"""The coaching conversation.

Design: docs/notes/design.coaching-conversation.md

The load-bearing test in this file is `TestTheAgentNeverSuppliesChess`. Everything
else checks the shape of the dialogue; that one checks the rule the design turns
on, and it is the guard against the next person letting a model "phrase it more
naturally" -- which is a fluent sentence with no evidence under it (R-03, hard
rule 7).
"""

from __future__ import annotations

import pytest

from chesscoach.conversation import Conversation, Stage
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    CorpusRef,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    Plan,
    PlanStep,
    PlayerProfile,
    PlayerRef,
    Provenance,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-09-08")


def a_finding(kind: str = "missed_motif", subject: str = "pin", rate: float = 0.31) -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=12,
            distinct_games=6,
            games_with_data=20,
            rate=rate,
            peer_rate=0.09,
            baseline_rate=0.09,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.FOCUS, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(
            Evidence(game_id="g1", ply=14, fen="8/8/8/8/8/8/8/K6k w - - 0 1",
                     move_played="e6e5"),
        ),
    )


def a_profile(*findings: Finding, with_plan: bool = True) -> PlayerProfile:
    steps = tuple(
        PlanStep(
            finding_id=f.id,
            action=f"do something about {f.claim.subject}",
            why="because the games say so",
            progress_sign=f"{f.claim.subject} below 17% over the next 78 games "
                          "(measured 31%, and a parenthetical nobody needs)",
            check_after_games=78,
            target_rate=0.17,
        )
        for f in findings
    )
    return PlayerProfile(
        player=PlayerRef(source="lichess", username="alice", band="1400-1800"),
        corpus=CorpusRef(corpus_id="c1", n_games=20),
        findings=tuple(findings),
        plan=Plan(created="2026-09-08", steps=steps) if with_plan and steps else None,
    )


def opened(*findings: Finding, knowledge=None) -> Conversation:
    talker = Conversation(knowledge=knowledge)
    talker.open()
    talker.reply("alice")
    talker.present(a_profile(*findings))
    return talker


class TestTheOpening:
    def test_it_asks_for_a_username_first(self):
        talker = Conversation()

        turn = talker.open()

        assert "username" in turn.say.lower()
        assert turn.stage is Stage.AWAITING_USERNAME

    def test_a_username_is_handed_back_for_the_caller_to_analyse(self):
        """The agent does no I/O: it says *who* to analyse and stops."""
        talker = Conversation()
        talker.open()

        turn = talker.reply("alice")

        assert turn.analyse == "alice"
        assert turn.stage is Stage.ANALYSING

    def test_a_name_with_spaces_is_refused_rather_than_guessed(self):
        talker = Conversation()
        talker.open()

        turn = talker.reply("my name is alice")

        assert turn.analyse is None
        assert turn.stage is Stage.AWAITING_USERNAME


class TestWhatItSaysFirst:
    def test_it_names_the_weaknesses_with_one_comparison_each(self):
        talker = opened(a_finding())

        said = talker.present(a_profile(a_finding())).say

        assert "You miss pin tactics" in said
        assert "31% of the time, against 9%" in said

    def test_it_does_not_recite_the_statistics_the_report_carries(self):
        """The author's complaint: *"There shouldnt be to many statistics."*"""
        said = opened(a_finding()).present(a_profile(a_finding())).say

        for unwanted in ("win probability", "confidence", "tier", "ci95",
                         "cost", "recoverable"):
            assert unwanted not in said.lower()

    def test_only_what_the_plan_is_built_on(self):
        """R-12: a list of nine weaknesses is the anti-pattern, and the
        conversation is where the cap is felt rather than merely enforced."""
        many = [a_finding(subject=s) for s in ("pin", "fork", "skewer")]
        talker = Conversation()
        talker.open()
        talker.reply("alice")

        said = talker.present(a_profile(*many)).say

        assert said.count("You miss") == 3  # the plan has a step for each here
        assert "4." not in said

    def test_nothing_found_is_said_as_a_result_not_as_silence(self):
        talker = Conversation()
        talker.open()
        talker.reply("alice")

        said = talker.present(a_profile()).say

        assert "real answer" in said


class TestExplainingOnRequest:
    """Shape D's *"expand on request"*, which the by-area map could not do."""

    class _Knowledge:
        def __init__(self, entries):
            self.entries = entries

        def for_player(self, key):
            return self.entries.get(key)

    def test_it_serves_the_endorsed_entry_and_its_source(self):
        knowledge = self._Knowledge({
            "pin": {"what": "A pin is when a piece cannot move without exposing a better one.",
                    "why": "It wins material because the pinned piece is stuck.",
                    "links": [{"url": "u", "publisher": "Lichess"}]}
        })
        talker = opened(a_finding(), knowledge=knowledge)

        said = talker.reply("explain 1").say

        assert "cannot move without exposing" in said
        assert "Source: Lichess" in said

    def test_the_lookup_is_by_the_thing_not_by_the_claim_key(self):
        """The knowledge base is keyed `pin`, not `missed_motif.pin.own`, so a
        lookup by claim key misses every time and the agent then claims to have
        no explanation for something the project has endorsed."""
        knowledge = self._Knowledge({"pin": {"what": "definition"}})

        said = opened(a_finding(), knowledge=knowledge).reply("explain 1").say

        assert "definition" in said

    def test_with_nothing_endorsed_it_says_so_and_shows_the_games(self):
        """Hard rule 7: better to say there is nothing checked than to invent."""
        said = opened(a_finding(), knowledge=None).reply("explain 1").say

        assert "do not have a checked explanation" in said
        assert "lichess.org/g1#13" in said

    def test_a_number_anywhere_in_the_reply_is_understood(self):
        """"explain 1" is the ordinary way to ask; matching a leading digit
        only sent it to the "which one?" branch."""
        said = opened(a_finding()).reply("can you explain 1 for me").say

        assert "Which one?" not in said

    def test_endorsed_practice_is_offered_as_context_and_attributed(self):
        """The knowledge base carries a `practice` field, so where it is filled
        the player should see it -- attributed, so it reads as one source's
        suggestion rather than as the system's instruction."""
        knowledge = self._Knowledge({
            "pin": {"what": "definition", "practice": ["look for lined-up pieces"]}
        })

        said = opened(a_finding(), knowledge=knowledge).reply("explain 1").say

        assert "One source suggests: look for lined-up pieces" in said

    def test_the_exercise_is_still_the_plans_and_not_the_entrys(self):
        """Practice from the knowledge base is written for a *topic*; the plan
        step is written for *this player's* finding, with the target rate the
        progress check will read. So the entry informs, and the plan instructs
        -- `late_castling` carries practice about the rules of castling, which
        would be a nonsense exercise for that claim."""
        knowledge = self._Knowledge({
            "pin": {"what": "definition", "practice": ["do the entry's thing"]}
        })
        talker = opened(a_finding(), knowledge=knowledge)
        talker.reply("explain 1")

        said = talker.reply("1").say

        assert "do something about pin" in said
        assert "do the entry's thing" not in said

    def test_asking_without_naming_one_asks_back(self):
        said = opened(a_finding()).reply("explain that").say

        assert "Which one?" in said


class TestCommittingToOne:
    def test_choosing_one_gives_the_exercise_for_it(self):
        turn = opened(a_finding()).reply("1")

        assert "do something about pin" in turn.say
        assert turn.focus == "missed_motif.pin.own"

    def test_the_horizon_is_a_duration_and_a_standard_not_a_deadline(self):
        """The author's framing: *"Keep this a week or two, until you feel
        confident in finding the pins easily."* A duration says when to stop
        thinking about anything else; the standard says what finished looks
        like. Neither is a date, and the player is not asked to count."""
        said = opened(a_finding()).reply("1").say

        assert "a week or two" in said
        assert "easily" in said

    def test_the_game_count_never_reaches_the_player(self):
        """`check_after_games` reached **78** for a real player. It is the
        number the *measurement* needs before a rate means anything, not an
        instruction -- *"78 is too much, nobody would do that."* It stays in the
        plan for `check-progress` to read and is not said out loud."""
        said = opened(a_finding()).reply("1").say

        assert "78" not in said
        assert "games" not in said.lower()

    def test_the_progress_sign_drops_its_bookkeeping(self):
        said = opened(a_finding()).reply("1").say

        assert "parenthetical nobody needs" not in said
        assert "below 17%" in said

    def test_the_others_are_deferred_rather_than_listed_again(self):
        said = opened(a_finding(), a_finding(subject="fork")).reply("1").say

        assert "can wait" in said
        assert "two things at once" in said

    def test_with_only_one_finding_nothing_is_deferred(self):
        said = opened(a_finding()).reply("1").say

        assert "can wait" not in said


class TestTheAgentNeverSuppliesChess:
    """The rule the design turns on, and the reason this file exists.

    Every sentence the agent can produce comes from `phrasing`, `planner`, the
    knowledge base, or the player's own games. Nothing about chess originates
    here. The risk is the next person letting a model paraphrase a finding "more
    naturally", which is a fluent sentence with no evidence under it.
    """

    def test_no_chess_vocabulary_is_hard_coded_in_the_module(self):
        import inspect

        from chesscoach import conversation

        import ast

        tree = ast.parse(inspect.getsource(conversation))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc is not None:
                    docstrings.add(doc)

        # Only the strings the module can actually **print**. Its own prose is
        # allowed to name claims -- explaining why the knowledge lookup is keyed
        # the way it is requires saying `endgame_error` out loud, and a test that
        # forbade that would be policing comments rather than behaviour.
        sayable = [
            node.value.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value not in docstrings
        ]
        for term in ("pawn", "bishop", "knight", "rook", "queen", "castl",
                     "endgame", "tempo", "outpost", "sacrifice", "fork", "pin"):
            offenders = [text for text in sayable if term in text]
            assert not offenders, (
                f"{term!r} appears in a string conversation.py can print: "
                f"{offenders[:2]} -- chess vocabulary belongs in phrasing, "
                "planner or the knowledge base, not in the agent"
            )

    def test_every_line_of_a_full_dialogue_traces_to_something_computed(self):
        knowledge = TestExplainingOnRequest._Knowledge(
            {"pin": {"what": "A pin is a pin.", "links": [{"url": "u", "publisher": "P"}]}}
        )
        talker = Conversation(knowledge=knowledge)
        turns = [talker.open().say]
        turns.append(talker.reply("alice").say)
        turns.append(talker.present(a_profile(a_finding())).say)
        turns.append(talker.reply("explain 1").say)
        turns.append(talker.reply("1").say)

        whole = "\n".join(turns)
        # The chess in this dialogue is exactly: the claim's own sentence, the
        # knowledge entry, the planner's action, and the game link.
        assert "You miss pin tactics" in whole      # phrasing
        assert "A pin is a pin." in whole           # knowledge base
        assert "do something about pin" in whole    # planner
        assert "lichess.org/g1#13" in whole         # the player's own game

    def test_it_works_with_no_model_and_no_knowledge_base(self):
        """C1: the conversation must not require anything to be running."""
        talker = Conversation(knowledge=None)
        talker.open()
        talker.reply("alice")
        talker.present(a_profile(a_finding()))

        assert talker.reply("1").focus == "missed_motif.pin.own"


class TestTheDialogueDoesNotLoseTheThread:
    def test_an_unrecognised_reply_offers_the_choices_again(self):
        said = opened(a_finding()).reply("hmm not sure").say

        assert "1)" in said

    def test_after_committing_it_still_explains_if_asked(self):
        talker = opened(a_finding(), knowledge=None)
        talker.reply("1")

        said = talker.reply("explain 1 again").say

        assert "do not have a checked explanation" in said
        assert talker.stage is Stage.COMMITTED

    def test_it_closes_rather_than_looping_forever(self):
        talker = opened(a_finding())
        talker.reply("1")

        talker.reply("thanks")

        assert talker.stage is Stage.CLOSED
