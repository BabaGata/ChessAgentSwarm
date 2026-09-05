"""A pin against a king still has to be worth naming.

Spec: docs/notes/experiments.e55-detector-precision.md

`missed_motif.pin` scored **20% precision** on the author's marked sheet -- one
right, four wrong -- and `allowed_motif.pin` scored 40%. It was the worst
detector in the system, in both directions.

`_is_pin` asked two different questions depending on what stood behind. For a
rook or queen it required `_wins_once_vacated`: the pin has to win something.
For a **king** it asked only `is_pinned`, with **no material test at all**, so
any geometric alignment counted -- and 88 of 288 firings on real games were a
**pawn** pinned to its own king, defended by that king, winning nothing.

The module's own reasoning already covers this. `PIN_TARGET_MIN_VALUE` exists
because *"two minor pieces in a line is geometry, not a pin worth naming"*; a
pawn in front of a king is the same geometry from the other end.
"""

from __future__ import annotations

import chess

from chesscoach.tactics import Motif, detect_motifs


def pins(fen: str, san: str) -> bool:
    board = chess.Board(fen)
    return Motif.PIN.value in {str(m) for m in detect_motifs(board, board.parse_san(san))}


class TestAPawnPinnedToItsKing:
    def test_a_rook_on_a_file_with_a_pawn_and_king_is_not_a_pin(self):
        # Rc8 lines up with the c2 pawn and Kc1 behind it. The pawn is defended
        # by that same king, so Rxc2+ Kxc2 simply loses the rook.
        assert not pins("5rk1/pp3ppp/4p1n1/8/1q1P2Q1/3R4/2P2PPP/2K4R b - - 3 22", "Rc8")

    def test_another_of_the_same_shape(self):
        assert not pins("2b3rk/p3qp1p/5N2/1p2p2B/3pP3/1PbP3P/P5P1/3R1RK1 b - - 0 27", "Rg5")

    def test_a_pawn_in_front_of_a_ROOK_is_not_a_pin_either(self):
        """This test asserted the opposite until the author's marks were read.

        Rb2 lines up on the b4 pawn with an **undefended rook on b7** behind it,
        and the first reading here was that this is a genuine pin because the
        rear piece is winnable. The author rejected exactly this shape twice on
        the sheet -- *"the pawn is pinned because the rook is behind, but this
        will not lead to any material loss"* -- so the rule is the front piece,
        not what stands behind it. Their reading, not this one.
        """
        assert not pins("8/1R4pp/4B3/4p3/1P2k3/6P1/3r2PK/8 b - - 1 34", "Rb2")


class TestRealPinsSurvive:
    def test_a_piece_pinned_to_its_king_is_still_a_pin(self):
        # Bc4 pins the d5 knight against Kg8 on the a2-g8 diagonal. A piece, not
        # a pawn, and the knight cannot move.
        assert pins("5rk1/1pR3pp/8/pB1np3/8/PR2P1P1/1P3rP1/6K1 w - - 1 24", "Bc4")

    def test_a_pin_that_wins_material_is_untouched(self):
        # The other branch, which always required the pin to win something and
        # is not changed here: Bh4 pins the f6 knight against the queen on d8.
        assert pins("r1bqk2r/1pp3pp/p1nb1n2/4p3/8/P1NBP1B1/1P2NPPP/R2QK2R w KQkq - 4 12", "Bh4")
