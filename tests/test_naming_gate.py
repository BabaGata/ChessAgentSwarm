"""Does this sentence define *this* concept, or merely share a word with it?

Spec: docs/notes/design.knowledge-re-extraction.md

The gate caught `fork` defined as a skewer, because that sentence contains none
of fork's words. It did not catch a pawn-ending passage standing as the
definition of "attack on the king", because that passage contains "king".
Presence is not aboutness, and five of the fourteen stored entries passed on one
ordinary word.

Two changes, both stated in the old docstring's own principle -- *broad for
finding, narrow for verifying*:

1. **Verify against the concept's own topic phrase**, not the widened net. The
   extra phrases exist to *find* pages (`allows_square` finds nothing under
   "outpost" and fifty passages under "hole"); they are too loose to confirm
   what a sentence is about.
2. **Discriminate.** Reject a sentence that matches some *other* concept's
   vocabulary strictly better than its own. A definition by contrast -- "a
   skewer is the inverse of a pin" -- names another concept on purpose, so the
   test is which one it matches *more*, not whether another is mentioned.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge_swarm import _names

# The sentence actually stored under `fork`, and the one the gate was written for.
STORED_AS_FORK = (
    "In other words, a skewer happens when a chess piece attacks an opponent's "
    "chessman, which hides a less important piece behind it."
)

# The passage standing as the definition of an attack on the king.
PAWN_ENDING = (
    "The method to follow is to advance the King as far as is compatible with "
    "the safety of the Pawn, and then to advance the Pawn."
)

# The passage standing as the definition of castling too late.
MOVING_INTO_CHECK = (
    "A player moving into check may be required, by the opposing player, either "
    "to move the King elsewhere, or to replace the King and move another piece."
)


class TestItRejectsTheKnownFailures:
    def test_a_skewer_definition_is_not_a_fork_definition(self):
        assert not _names(STORED_AS_FORK, "fork")

    def test_a_pawn_ending_is_not_an_attack_on_the_king(self):
        # Passes a presence test on "king". It is better matched by `opening_pawn_error`,
        # which is what makes it refusable without knowing any chess.
        assert not _names(PAWN_ENDING, "allows_pressure")

    def test_the_rule_on_moving_into_check_is_not_about_castling(self):
        # Passes a presence test on "king", from the widened phrase "king
        # safety". It contains no form of the concept's own name.
        assert not _names(MOVING_INTO_CHECK, "late_castling")

    def test_an_empty_sentence_names_nothing(self):
        assert not _names("", "fork")


class TestItStillAcceptsRealDefinitions:
    @pytest.mark.parametrize(
        "key,sentence",
        [
            ("fork", "A fork is a move where a piece attacks two or more opposing pieces."),
            ("pin", "A pin is a tactic where a piece cannot move without exposing a "
                    "more valuable piece behind it."),
            ("skewer", "A skewer is a motif involving a high value piece being attacked "
                       "and moving out of the way."),
            ("trappedPiece", "A piece is trapped when it is unable to escape capture "
                             "because it has limited moves."),
            ("late_castling", "Castling early is the surest way to bring the king into "
                              "safety before the centre opens."),
        ],
    )
    def test_a_definition_of_the_thing_passes(self, key, sentence):
        assert _names(sentence, key)

    def test_a_definition_by_contrast_survives(self):
        # "The inverse of a pin" names another concept deliberately. The test is
        # which concept the sentence matches *more*, not whether another appears.
        contrast = ("A skewer is the inverse of a pin: the more valuable piece is "
                    "the one attacked first.")

        assert _names(contrast, "skewer")

    def test_the_concept_it_is_contrasted_against_does_not_steal_it(self):
        # The same sentence must not pass as a definition of `pin`.
        contrast = ("A skewer is the inverse of a pin: the more valuable piece is "
                    "the one attacked first.")

        assert not _names(contrast, "pin")
