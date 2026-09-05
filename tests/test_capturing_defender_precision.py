"""The author rejected three of four `capturingDefender` firings. E86 D-3.

Every rejection was one shape: the capture leaves an enemy piece loose **while
it is not the enemy's turn**, and the piece standing to win it is the capturer
itself, which the recapture removes. `Rxf1+ Kxf1`, `Qxe5 Rxe5`, `Bxc3 bxc3`.

The author's own note on a fourth rejection says the same thing from the other
side:

> *"This was just a normal exchange, no material gain happened because the
> defendor was taken, the rook that was exchanged was not the only piece
> defending any particular piece that was attacked by the oponent."*

The detector now asks whether the defender has a reply that saves the loosened
piece, which is the question `_is_fork` already asks about its targets.
"""

import chess

from chesscoach.tactics import Motif, detect_motifs


def removes_defender(fen: str, san: str) -> bool:
    board = chess.Board(fen)
    return Motif.REMOVING_THE_DEFENDER in detect_motifs(board, board.parse_san(san))


class TestTheRecaptureTakesTheWinnerAway:
    """The three positions the author marked [n], by their own reading."""

    def test_a_rook_that_is_recaptured_cannot_collect_the_knight(self):
        # Rxf1+ leaves Nf5 undefended, but Kxf1 removes the rook that would take it.
        assert not removes_defender(
            "5k1r/1bp5/5p2/p4N1p/2R3p1/2P5/PP4PP/4rRK1 b - - 4 34", "Rxf1+"
        )

    def test_a_queen_that_is_recaptured_cannot_collect_the_pawn(self):
        # Qxe5 leaves c5 loose, but Rxe5 removes the queen that would take it.
        assert not removes_defender(
            "1k1r3r/pp4pp/8/2P1Q3/3q4/P7/5PPP/R3R1K1 b - - 1 21", "Qxe5"
        )

    def test_the_defender_may_simply_defend_again(self):
        # Bxc3 loosens e4 -- and White answers bxc3 and has moves that re-cover it.
        assert not removes_defender(
            "r1bqk2r/pp1p1ppp/2n1pn2/8/1b1NP3/2N5/PPP1BPPP/R1BQ1RK1 b kq - 5 7", "Bxc3"
        )


class TestTheRealOnesStillFire:
    """Two of the author's [y] marks, which the fix must not take with it."""

    def test_hirsican_bxe6(self):
        """`allowed_motif.capturingDefender`, marked [y] at 36.1 wp lost."""
        assert removes_defender(
            "2krr3/ppq3pp/2nbb3/5pB1/2B1Q3/P4N2/1P3PPP/R3R1K1 w - - 0 17", "Bxe6+"
        )

    def test_goydorak_qxg3(self):
        """`allowed_motif.capturingDefender`, marked [y] at 37.2 wp lost."""
        assert removes_defender(
            "r4rk1/ppp2pq1/2np1p1p/2b1p3/2B1P2N/P2P2Pb/1PPQ1P2/RN3RK1 b - - 0 13", "Qxg3+"
        )

    def test_the_king_is_a_target_but_never_a_prize(self):
        """A capture beside the enemy king used to claim the king as loot worth 100.

        `Rxf1+` above is the case: the rook 'defended' g1, and `wins_material`
        answers 100 for a king square, so any capture adjacent to a king fired.
        """
        board = chess.Board("5k1r/1bp5/5p2/p4N1p/2R3p1/2P5/PP4PP/4rRK1 b - - 4 34")
        move = board.parse_san("Rxf1+")
        assert board.piece_at(chess.G1).piece_type == chess.KING
        assert chess.G1 in board.attacks(move.to_square)
        assert Motif.REMOVING_THE_DEFENDER not in detect_motifs(board, move)
