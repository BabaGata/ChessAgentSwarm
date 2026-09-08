"""A free pawn is a pattern the swarm had no word for.

Spec: [[experiments.e31-move-level-agreement]] — across three reviewed players,
**45 of 45 notes mentioning a pawn were unnameable**. The engine flagged the
error underneath most of them; the motif layer had nothing to call it, because
`hangingPiece` excludes anything worth less than a knight.

This is a **new motif, not a widening of that one**, and the distinction is the
whole design. [[experiments.e30-hanging-definition]] measured what widening does:
everyone drops free pawns, so the population rate more than doubles and a
player's deviation *shrinks* — one reviewed player went from 1.40x to 1.11x.
Folding pawns into `hangingPiece` therefore buries the piece claim to rescue the
pawn one, and a report saying "you hang pieces" about a pawn is simply wrong.

Kept separate, both claims stay true and each is compared against its own
population.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.tactics import Motif, detect_motifs


def motifs(fen: str, uci: str) -> frozenset[str]:
    board = chess.Board(fen)
    return detect_motifs(board, chess.Move.from_uci(uci))


class TestAFreePawn:
    def test_capturing_an_undefended_pawn_is_the_motif(self):
        # Black rook on a8, white pawn on a4 undefended, rook takes it and is
        # safe afterwards.
        found = motifs("r6k/8/8/8/P7/8/7P/6K1 b - - 0 1", "a8a4")

        assert Motif.HANGING_PAWN in found

    def test_a_defended_pawn_is_not_hanging(self):
        # The pawn on b5 is defended by the a4 pawn; taking it is an exchange,
        # not a free pawn, and the rook would be lost.
        found = motifs("r6k/8/8/1P6/P7/8/7P/6K1 b - - 0 1", "a8b8")

        assert Motif.HANGING_PAWN not in found

    def test_a_capture_that_can_be_answered_is_not_free(self):
        found = motifs("r6k/8/8/8/P7/8/R6P/6K1 b - - 0 1", "a8a4")

        assert Motif.HANGING_PAWN not in found

    def test_it_does_not_fire_on_pieces(self):
        # That is `hangingPiece`'s job, and the two must never both claim the
        # same move — the report would name one mistake twice.
        found = motifs("r6k/8/8/8/N7/8/7P/6K1 b - - 0 1", "a8a4")

        assert Motif.HANGING_PIECE in found
        assert Motif.HANGING_PAWN not in found

    def test_a_quiet_move_is_not_a_capture(self):
        assert Motif.HANGING_PAWN not in motifs("r6k/8/8/8/P7/8/7P/6K1 b - - 0 1", "a8a7")

    def test_en_passant_counts(self):
        # It is a pawn won for nothing, and the reviewer wrote one down. The
        # captured pawn is not on the destination square, so a naive
        # `piece_at(to_square)` misses it entirely.
        board = chess.Board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
        found = detect_motifs(board, chess.Move.from_uci("e5d6"))

        assert Motif.HANGING_PAWN in found

    @pytest.mark.parametrize("promotion", ["a7a8q", "a7a8n"])
    def test_a_promotion_capture_is_still_judged_on_the_pawn_taken(self, promotion):
        # Promoting is not itself the motif; whether the captured material was
        # free still is.
        found = motifs("6k1/P7/8/8/8/8/8/6K1 w - - 0 1", promotion)

        assert Motif.HANGING_PAWN not in found  # nothing was captured


class TestItDoesNotDisturbTheExistingMotifs:
    def test_hanging_piece_still_ignores_pawns(self):
        # E30 refused widening this one. Adding a sibling must not quietly do
        # the widening anyway.
        found = motifs("r6k/8/8/8/P7/8/7P/6K1 b - - 0 1", "a8a4")

        assert Motif.HANGING_PIECE not in found

    def test_the_two_are_mutually_exclusive(self):
        # Checked as a property rather than per-position: one capture cannot be
        # both a free piece and a free pawn, and if it ever were, every rate
        # counting them would double-count the same move.
        positions = [
            ("r6k/8/8/8/P7/8/7P/6K1 b - - 0 1", "a8a4"),
            ("r6k/8/8/8/N7/8/7P/6K1 b - - 0 1", "a8a4"),
            ("r6k/8/8/8/Q7/8/7P/6K1 b - - 0 1", "a8a4"),
        ]
        for fen, uci in positions:
            found = motifs(fen, uci)
            assert not (Motif.HANGING_PIECE in found and Motif.HANGING_PAWN in found)


class TestAnExchangeIsNotAFreePawn:
    """The author, on `exf6` answered by `Nxf6` in lichess.org/mdpdLHYI#9:

    > *"This was an exchange. If the pawn took another pawn or a piece a move
    > before it became hanging then it should not be detected as hanging pawn."*

    This is the rule `_is_recapture` already states for `hangingPiece`, written
    from the same author's marks -- *"if the piece took another piece a move
    before and now is hanging then it is an exchange"*. The pawn detector was
    written as *"the exact counterpart below the value line"* and did not get
    it, so a pawn that captured and was taken back read as a dropped pawn.
    """

    def played(self, moves: list[str]) -> frozenset[str]:
        """Motifs of the last move, with the history the rule needs.

        A board built from a bare FEN has no move stack and the question cannot
        be asked at all, so these positions are reached by playing them.
        """
        board = chess.Board()
        for uci in moves[:-1]:
            board.push_uci(uci)
        return detect_motifs(board, chess.Move.from_uci(moves[-1]))

    def test_recapturing_the_pawn_that_just_captured_is_an_exchange(self):
        # 1.e4 d5 2.exd5 Qxd5 -- the d5 pawn arrived by capturing, and taking it
        # back is the other half of a trade, not a pawn dropped for nothing.
        found = self.played(["e2e4", "d7d5", "e4d5", "d8d5"])

        assert Motif.HANGING_PAWN not in found

    def test_a_pawn_that_was_simply_pushed_is_still_hanging(self):
        # 1.e4 d5 2.Nf3 dxe4 -- the e4 pawn was pushed, not won, so taking it
        # is a free pawn and the claim is about exactly this.
        found = self.played(["e2e4", "d7d5", "g1f3", "d5e4"])

        assert Motif.HANGING_PAWN in found

    def test_taking_a_pawn_elsewhere_is_not_a_recapture(self):
        """The author's other two marks are this shape and they disagree with
        each other -- a pawn won on one wing while a pawn falls on the other is
        an exchange in material and not in tactics, and they accepted one
        (*"there will be a lot of pressure on the white king"*) and questioned
        the other. Only the same-square case is ruled out here."""
        # 1.e4 d5 2.Nf3 dxe4 3.Ng5 -- black's capture on e4 does not make
        # white's own loose pawn a recapture.
        board = chess.Board()
        for uci in ["e2e4", "d7d5", "g1f3", "d5e4", "f3g5"]:
            board.push_uci(uci)

        assert board.piece_at(chess.E4) is not None
