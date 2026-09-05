"""A sentence carrying page markup is not a sentence.

Spec: docs/notes/experiments.e89-why-nothing-usable.md

Re-drafting `late_castling` produced this, and it passed every filter because
its prefix reads as prose:

    Castling is permitted provided all of the following conditions are met:
    "}},"i":0}}]}'>

The tail is embedded JSON from the page's own scripts, which the text extraction
did not strip. It would have been shown to the author as a candidate definition
and, if endorsed, to a player.

Natural prose does not contain braces or angle brackets. The test is cheap and
the failure it prevents is visible in the output.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge_swarm import is_broad

DEBRIS = (
    'Castling is permitted provided all of the following conditions are met: '
    '"}},"i":0}}]}\'>'
)


class TestMarkupIsRefused:
    def test_the_sentence_that_was_drafted_is_refused(self):
        assert not is_broad(DEBRIS)

    @pytest.mark.parametrize(
        "sentence",
        [
            'A fork is a move that attacks two pieces {"tracking":1}',
            "An outpost is a square <span class='x'>protected by a pawn</span>.",
            'A pin is a tactic where a piece cannot move.]}]}',
            'Development means bringing pieces out \u003Cbr\u003E quickly.',
        ],
    )
    def test_any_sentence_carrying_markup_is_refused(self, sentence):
        assert not is_broad(sentence)


class TestRealSentencesSurvive:
    @pytest.mark.parametrize(
        "sentence",
        [
            "In chess, an outpost is a square protected by a pawn on the fifth rank "
            "or beyond which cannot be attacked by an enemy pawn.",
            "A fork is a move where a piece attacks two or more opposing pieces "
            "simultaneously, and the defender cannot save both of them.",
            "Castling is a move that allows a player to bring the king to safety "
            "and develop a rook towards the centre at the same time.",
        ],
    )
    def test_ordinary_prose_is_kept(self, sentence):
        assert is_broad(sentence)

    def test_a_colon_is_not_markup(self):
        # Definitions often use one, and the debris case must not take colons
        # with it.
        assert is_broad(
            "There are two kinds of pin: absolute, against the king, and "
            "relative, against a more valuable piece."
        )
