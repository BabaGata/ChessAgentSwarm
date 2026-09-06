"""Every claim kind must have words, or it reaches a player as its own key.

That is the **D8 defect**, and it had returned twice. The five development and
opening claims (E58-E62) shipped with no phrasing at all, so a report headline
read *"pawn_error: any."* and the plan said *"Work on any: review the cited games
and note what you would play instead."* Splitting `out_of_book` per opening
reintroduced it for a second reason: only the pooled subject had a sentence, and
a per-opening subject falls straight past it to the fallback.

Both were found by reading a real report rather than by any test, which is why
these exist.
"""

from __future__ import annotations

import pytest

from chesscoach.planner import _action
from chesscoach.profile.models import (
    Claim,
    Confidence,
    ConfidenceTier,
    DeterminedBy,
    Evidence,
    Finding,
    GapType,
    GapTypeHypothesis,
    Measurement,
    Provenance,
)

PROVENANCE = Provenance(engine="stub", depth=15, corpus_id="c1", analysed_at="2026-09-06")

# Every kind a section can put in front of a player. `executed_motif` is absent
# because `s1_tactical_gaps.NOT_ASSERTED` refuses it, and `plays_queenless`
# because S10 never emits a finding -- it reaches the report as a style line.
KINDS = (
    "allowed_motif", "missed_motif", "opening_disadvantage", "concedes_weakness",
    "allows_square", "allows_pressure", "endgame_error", "long_think_error",
    "time_pressure_error", "time_budget_error", "instant_move_error",
    "moved_into_attack", "miscounted_exchange", "sacrificed_for_attack",
    "out_of_book", "opening_pawn_error", "repeat_move", "late_castling", "slow_development",
)


def a_finding(kind: str, subject: str = "any") -> Finding:
    return Finding(
        section="S1",
        claim=Claim.of(kind=kind, subject=subject),
        measurement=Measurement(
            instances=30, distinct_games=8, games_with_data=24,
            rate=0.30, peer_rate=0.12, baseline_rate=0.12,
        ),
        provenance=PROVENANCE,
        confidence=Confidence(tier=ConfidenceTier.PRIORITY, replicated=True),
        gap_type=GapType(
            hypothesis=GapTypeHypothesis.UNKNOWN, determined_by=DeterminedBy.INFERRED
        ),
        evidence=(Evidence(game_id="g1", ply=21, fen="8/8/8/8/8/8/8/K6k w - - 0 1"),),
    )


@pytest.mark.parametrize("kind", KINDS)
class TestEveryClaimKindHasWords:
    def test_it_has_a_sentence(self, kind):
        from chesscoach.phrasing import STATEMENTS, SUBJECT_STATEMENTS

        assert kind in STATEMENTS or any(k == kind for k, _ in SUBJECT_STATEMENTS), (
            f"{kind} has no sentence and would print as a raw claim key"
        )

    def test_it_has_a_noun_phrase_for_the_plan(self, kind):
        from chesscoach.phrasing import QUANTITIES

        assert kind in QUANTITIES, f"{kind} would print as a raw claim key in the plan"

    def test_it_has_something_for_the_player_to_do(self, kind):
        """A step reading "Work on <key>" is the fallback, and it is not advice."""
        action = _action(a_finding(kind))

        assert not action.startswith("Work on "), f"{kind} has no action of its own"


class TestTheSubjectIsNeverARawKey:
    def test_a_per_opening_out_of_book_names_the_opening(self):
        from chesscoach.phrasing import statement

        said = statement(a_finding("out_of_book", "Bird Opening"))

        assert "Bird Opening" in said
        assert not said.startswith("out_of_book")

    def test_the_two_bases_of_late_castling_say_different_things(self):
        """"By this opening's standard" and "later than you usually are" are
        different evidence, and the design keeps them in separate claim keys."""
        from chesscoach.phrasing import statement

        by_book = statement(a_finding("late_castling", "book"))
        by_own = statement(a_finding("late_castling", "own"))

        assert by_book != by_own
        assert "book" not in by_book and "own" not in by_own.split()


class TestMotifSubjectsThatBreakTheTemplate:
    """Two motif subjects the generic templates could not say properly.

    `capturingDefender`'s friendly name is a **verb phrase**, so
    `"it is often a {subject} that punishes you"` produced *"it is often a
    capturing the defender that punishes you"* -- not a sentence.

    And a hanging piece is not a tactic, for the same reason a hanging pawn is
    not: taking one is looking at the board, not seeing something. `hangingPawn`
    carried that override from the start and `hangingPiece`, written beside it,
    did not -- so the pair said two different kinds of thing about one idea.
    """

    def test_capturing_the_defender_reads_as_a_sentence(self):
        from chesscoach.phrasing import statement

        allowed = statement(a_finding("allowed_motif", "capturingDefender"))
        missed = statement(a_finding("missed_motif", "capturingDefender"))

        assert "a capturing the defender" not in allowed
        assert "capturing the defender tactics" not in missed
        assert allowed.endswith(".") and missed.endswith(".")

    def test_a_hanging_piece_is_not_called_a_tactic(self):
        from chesscoach.phrasing import statement

        assert "tactics" not in statement(a_finding("missed_motif", "hangingPiece"))

    def test_the_piece_and_the_pawn_say_the_same_kind_of_thing(self):
        from chesscoach.phrasing import statement

        piece = statement(a_finding("allowed_motif", "hangingPiece"))
        pawn = statement(a_finding("allowed_motif", "hangingPawn"))

        assert piece.replace("piece", "X") == pawn.replace("pawn", "X")
