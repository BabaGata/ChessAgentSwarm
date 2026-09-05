"""The author marked four of ten `allows_square` firings wrong, for two reasons.

Both are quoted in `chesscoach.squares` beside the rule they produced:

- *"The piece should be on the black side of the board."* The outpost ranks were
  the classical "knight on its own fourth to sixth rank", which reaches one rank
  past the halfway line, so a knight standing in its **own** half counted as
  settled in the opponent's position.
- *"It lasted there for 1 move because it was taken."* A rook the player can
  simply capture has not established itself on the seventh.

Every position here is from the reviewed games, at the ply pair `allowed` is
actually given: the player's position before their move, and the position after
the opponent's reply.
"""

import chess

from chesscoach.squares import OUTPOST, ROOK_SEVENTH, allowed


def established(before: str, after: str, colour: chess.Color) -> frozenset[str]:
    return allowed(chess.Board(before), chess.Board(after), colour)


class TestARookThatIsSimplyTakenIsNotEstablished:
    def test_wymcy4m1_the_rook_on_e7_falls_at_once(self):
        assert ROOK_SEVENTH not in established(
            "r2q1rk1/1p2npbp/p5p1/2pp4/P2n4/2NP3P/BPP2PP1/R1BQR1K1 b - - 2 14",
            "r4rk1/1p2Rpbp/p2q2p1/2pp4/P2n4/2NP3P/BPP2PP1/R1BQ2K1 b - - 0 15",
            chess.BLACK,
        )

    def test_zc5tdvpr_the_rook_on_d2_falls_at_once(self):
        assert ROOK_SEVENTH not in established(
            "3r2k1/4qpp1/Q1p2b1p/p1p1p3/4P2P/P1P2NP1/1P1R1P2/6K1 w - - 8 26",
            "6k1/4qpp1/2Q2b1p/p1p1p3/4P2P/P1P2NP1/1P1r1P2/6K1 w - - 0 27",
            chess.WHITE,
        )

    def test_a_rook_that_survives_still_counts(self):
        """The author's [y]: Rb7 is safe, and the claim must not be lost with the fix."""
        assert ROOK_SEVENTH in established(
            "2rq1rk1/1p1nbpp1/2npb2p/1R2p3/2P5/2NPPNPP/5PBK/2BQ1R2 b - - 0 16",
            "2rq1rk1/nR1nbpp1/3pb2p/4p3/2P5/2NPPNPP/5PBK/2BQ1R2 b - - 0 17",
            chess.BLACK,
        )


class TestAKnightInItsOwnHalfIsNotAnOutpost:
    def test_qm07j5om_the_knight_on_d4_is_white_side_of_the_board(self):
        assert OUTPOST not in established(
            "rnbq1rk1/1p2bppp/p4n2/2pp4/3P4/2N1P1P1/PP2NPBP/R1BQ1RK1 b - - 0 9",
            "rnbq1rk1/1p2bppp/p4n2/3p4/3N4/2N1P1P1/PP3PBP/R1BQ1RK1 b - - 0 10",
            chess.BLACK,
        )

    def test_hdq7acrq_the_knight_on_c4_is_white_side_of_the_board(self):
        assert OUTPOST not in established(
            "1r1q1rk1/pb3ppp/2n2b2/2ppp3/4P3/P2P1N1P/2PNBPP1/2RQ1RK1 b - - 0 14",
            "1r1q1rk1/pb3ppp/2n2b2/2p1p3/2NpP3/P2P1N1P/2P1BPP1/2RQ1RK1 b - - 1 15",
            chess.BLACK,
        )

    def test_a_knight_that_really_is_in_the_players_half_still_counts(self):
        """The author's [y]: Ne5 sits in Black's half, and must survive the fix."""
        assert OUTPOST in established(
            "rnbq1rk1/ppp3bp/4p1p1/3p1p2/3PnP2/1P1BPN2/PBPN2PP/R2Q1RK1 b - - 1 9",
            "rnbq1rk1/p1p3bp/1p2p1p1/3pNp2/3PnP2/1P1BP3/PBPN2PP/R2Q1RK1 b - - 1 10",
            chess.BLACK,
        )
