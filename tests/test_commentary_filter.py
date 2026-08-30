"""Telling a definition from running commentary.

Design: docs/notes/design.knowledge-base.md

`_SPECIFIC` removes sentences about one POSITION. These remove sentences about
one MOMENT -- commentary, which names no square and so passes that filter
untouched. The sentence that forced this was drafted as the definition of a
hanging pawn:

    "Indeed, there is an avalanche of pawns hanging over Black's head!"

Verbatim from a real chess page, about pawns, naming no square, and useless: it
describes a moment in one game rather than saying what the thing is.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge_swarm import is_broad, reads_as_commentary

# Every one of these is a real sentence the Assessor kept in a live run.
COMMENTARY = [
    "Indeed, there is an avalanche of pawns hanging over Black's head!",
    "Here's an example, with the Knight forking 2 Rooks.",
    "They are in a family fork with their Rooks and Queen under threat of capture.",
    "Black sidesteps the fork but falls into something even more dangerous - a checkmate!",
    "However, another equally strong idea is available in the position.",
    "Instead, he plays a move which wastes time.",
    "But it is this immobility that gives the position its character.",
    "These structures have dynamism to them; they can be classified as good or bad.",
    "At right is the game Unzicker versus Taimanov, Stockholm 1952.",
    "As any general knows, this is a recipe for disaster.",
]

DEFINITIONS = [
    "A fork is a move that attacks two or more enemy pieces at the same time.",
    "A hanging piece is an attacked piece not defended by own man exposed to capture.",
    "An absolute fork is when a piece attacks two or more enemy pieces simultaneously.",
    "The most common piece to perform a fork is the knight, due to its unique movement.",
    "An outpost is a square that cannot be attacked by an enemy pawn.",
    # A "why" sentence and a practice suggestion: both are wanted, and both open
    # with a subordinating conjunction rather than a connective reaching back.
    "Because the opponent can only save one of them, a fork usually wins material.",
    "Practice recognising forks by studying tactics puzzles every day.",
    "When a piece is undefended it can simply be taken, costing material.",
]


class TestItDropsCommentary:
    @pytest.mark.parametrize("sentence", COMMENTARY)
    def test_a_moment_is_not_a_definition(self, sentence):
        assert reads_as_commentary(sentence), f"should be dropped: {sentence!r}"

    @pytest.mark.parametrize("sentence", COMMENTARY)
    def test_it_is_therefore_not_broad(self, sentence):
        assert not is_broad(sentence)

    def test_the_reason_is_reported_not_just_a_verdict(self):
        # The author asked what the Assessor discards. "Some sentences" is not
        # an answer, so the filter returns why.
        reason = reads_as_commentary("However, another idea is available.")
        assert "however" in reason.lower()


class TestItKeepsDefinitions:
    @pytest.mark.parametrize("sentence", DEFINITIONS)
    def test_a_general_statement_survives(self, sentence):
        assert not reads_as_commentary(sentence), f"should be kept: {sentence!r}"

    @pytest.mark.parametrize("sentence", DEFINITIONS)
    def test_it_is_therefore_broad(self, sentence):
        assert is_broad(sentence)


class TestTheSubordinatingConjunctions:
    """`Because` and `When` open a definition; `However` and `Instead` do not.

    The difference is whether the opening word subordinates INSIDE the sentence
    or reaches back to the previous one. Getting this wrong in the strict
    direction would drop the best "why" sentences there are.
    """

    @pytest.mark.parametrize("opener", ["Because", "When", "If", "Although", "While"])
    def test_a_subordinator_is_not_a_connective(self, opener):
        assert not reads_as_commentary(
            f"{opener} the piece is undefended, it can be captured for nothing."
        )

    @pytest.mark.parametrize("opener", ["However", "Instead", "Therefore", "Moreover"])
    def test_a_connective_is(self, opener):
        assert reads_as_commentary(
            f"{opener}, the piece is undefended and can be captured."
        )
