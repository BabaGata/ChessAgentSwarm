"""What counts as "about one position" rather than about the game in general.

Design: docs/notes/design.knowledge-base.md

`is_broad` is the inverse of the opening veto: where that one REQUIRES a
sentence to name something locatable on the board, this REFUSES it, because a
sentence naming `b5` or `Nxf3+` is about one game and a definition is about all
of them.

That makes the SAN pattern load-bearing, and it was written twice before it was
tested. The first version put the capture marker after the piece letter
(`[a-h]x?`) and so missed `Nxf3+` -- the commonest shape there is. These cases
exist so the third version fails loudly rather than quietly letting examples
through.
"""

from __future__ import annotations

import pytest

from chesscoach.knowledge_swarm import _SPECIFIC, is_broad

MOVES = [
    "e4", "d5", "Nf3", "Bb5", "Qd8", "Ke2", "Ra1",
    "Nxf3", "Nxf3+", "Qxd8#", "cxd4", "exd6",
    "Rae1", "R1e2", "Qh4xe1",             # disambiguation, file / rank / both
    "e8=Q", "a1=N+", "b8=R#",             # promotion
    "O-O", "O-O-O", "0-0", "0-0-0",       # castling, letter and digit spellings
    "1-0", "0-1",                          # game results
    "12. Nf3", "5...c5", "1.e4",          # numbered moves
]

PROSE = [
    "A fork is a move that attacks two or more enemy pieces at the same time.",
    "A hanging piece is one that is undefended and can be captured for free.",
    "Because the opponent can only save one of them, a fork usually wins material.",
    "Practice recognising forks by studying tactics puzzles every day.",
    "The knight is the most common forking piece because of its unusual move.",
    "Castling is a move involving the king and one of the rooks.",
    "An outpost is a square that cannot be attacked by an enemy pawn.",
    "Losing a piece this way costs material and is hard to recover from.",
]


class TestItRecognisesMoveNotation:
    @pytest.mark.parametrize("move", MOVES)
    def test_a_move_is_specific(self, move):
        assert _SPECIFIC.search(move), f"{move!r} should read as move notation"

    @pytest.mark.parametrize("move", MOVES)
    def test_a_sentence_containing_a_move_is_not_broad(self, move):
        assert not is_broad(f"White should consider {move} in this position now.")


class TestItLeavesOrdinaryProseAlone:
    @pytest.mark.parametrize("sentence", PROSE)
    def test_a_general_sentence_survives(self, sentence):
        assert is_broad(sentence), f"{sentence!r} should be kept"

    @pytest.mark.parametrize("sentence", PROSE)
    def test_no_move_is_found_in_it(self, sentence):
        found = _SPECIFIC.search(sentence)
        assert not found, f"false positive {found.group(0)!r} in {sentence!r}"


class TestFalsePositives:
    def test_a_longer_number_is_not_a_square(self):
        # "b12" and "e40" contain "b1" and "e4"; an id or an ECO-like token must
        # not make a whole sentence read as analysis.
        assert not _SPECIFIC.search("b12")
        assert not _SPECIFIC.search("e40")

    def test_capitals_are_not_squares(self):
        # SAN squares are lower case. "H1" is a heading, not h1.
        assert not _SPECIFIC.search("H1")

    def test_a_score_line_is_not_prose(self):
        # A result belongs to one game, so it is specific by the same rule.
        assert not is_broad("The game finished 1-0 after a long endgame battle.")
