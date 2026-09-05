"""`allows_pressure.king` scored 40% (2y/3n). E86.

Pawns and the king counted as attackers, so three of them round a king in the
middle of an endgame board read as an attack. The author rejected two firings
for the phase and one for the force -- both quotes are in `chesscoach.kingsafety`
beside the rule they produced.

Counting pieces alone does not separate the marks: the third rejection had three
attacking pieces, exactly like both accepted positions. Their **weight** does,
3/10/11 against 15/15, which is why `PRESSURE_WEIGHT` exists. Five hand-marked
positions is a thin calibration and the constant is named so that is visible.

Every position is from the reviewed games, at the ply pair `allowed_pressure` is
given: before the player's move, and after the opponent's reply.
"""

import chess

from chesscoach.kingsafety import allowed_pressure, attack_weight, zone_attackers


def crossed(before: str, after: str, colour: chess.Color) -> bool:
    return allowed_pressure(chess.Board(before), chess.Board(after), colour)


class TestAnEndgameKingIsNotUnderAttack:
    def test_ujquslpa_one_attacking_piece(self):
        assert not crossed(
            "4r1k1/p5pp/2p1p3/1b1pN3/8/1PK5/P4PPP/R3r3 w - - 0 24",
            "4r1k1/p5pp/4p3/1bppN3/8/1PK5/P4PPP/4R3 w - - 0 25",
            chess.WHITE,
        )

    def test_uhtzuk7r_two_rooks_are_not_a_mating_attack(self):
        assert not crossed(
            "8/5bk1/6pR/2R3P1/4Ppr1/4r3/8/4K3 w - - 2 40",
            "8/5bk1/6pR/2R3P1/4rpr1/8/5K2/8 w - - 0 41",
            chess.WHITE,
        )


class TestThreePiecesAreNotEnoughOnTheirOwn:
    def test_ww19j75a_three_attackers_but_only_eleven_points_of_force(self):
        """The case that counting alone cannot reject.

        > *"the white does not have enough material in the attack compared to the
        > black pieces that can be easily brougth back to the defense"*
        """
        before = "5k1r/1bp2p2/1pn1r2p/p3b3/4NBp1/2PB4/PP4PP/R4RK1 b - - 3 23"
        after = "7r/1bp2pk1/1pn1r2p/p3B3/4N1p1/2PB4/PP4PP/R4RK1 b - - 0 24"

        assert zone_attackers(chess.Board(after), chess.BLACK) == 3
        assert attack_weight(chess.Board(after), chess.BLACK) < 13
        assert not crossed(before, after, chess.BLACK)


class TestRealAttacksStillFire:
    def test_b3xwtvvw(self):
        assert crossed(
            "2k2r1r/pp3q1p/2nbbBp1/3Np3/3pP3/6N1/PP3PPP/R2Q1RK1 b - - 5 18",
            "2k2rr1/pp3q1p/2nbbBp1/3Np3/3pP3/1Q4N1/PP3PPP/R4RK1 b - - 7 19",
            chess.BLACK,
        )

    def test_ehpuefz6(self):
        assert crossed(
            "4rrk1/2pq3p/p1nb1ppN/1p1p4/3P3N/2PQ3P/PP3PP1/R3R1K1 b - - 1 18",
            "4rr2/2pq2kp/p1nb1pp1/1p1p4/3P2NN/2PQ3P/PP3PP1/R3R1K1 b - - 3 19",
            chess.BLACK,
        )
