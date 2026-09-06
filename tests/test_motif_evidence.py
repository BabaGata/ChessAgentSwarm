"""Evidence must agree with the detector, or the sheet explains a different thing.

The risk this file exists for: `motif_evidence` re-derives the squares a motif
rests on, so it could quietly disagree with `tactics` -- naming pieces for a
motif that did not fire, or falling silent on one that did. Then a reader marking
the sheet would be judging prose rather than the detector.

The corpus test below is the one that matters: **over every legal move of the
reviewed games, evidence is non-empty exactly when the detector fires.**
"""

from __future__ import annotations

import chess
import chess.pgn
import pytest

from chesscoach.motif_evidence import describe, evidence
from chesscoach.tactics import Motif, detect_motifs

GAMES = "expert-review/games"


class TestItNamesTheRightPieces:
    def test_a_fork_names_the_forker_and_both_targets(self):
        board = chess.Board("r3k2r/ppp2ppp/8/3N4/8/8/PPP2PPP/R3K2R w KQkq - 0 1")
        told = describe(board, board.parse_san("Nc7+"), str(Motif.FORK))

        assert "forker" in told and told.count("target") == 2

    def test_capturing_the_defender_shows_the_recapture_and_what_falls(self):
        """The author's own example: Nxf6+ Nd7xf6 Bxe5."""
        board = chess.Board("1r1q1rk1/pp1n1ppp/5b2/2pNn3/2P5/PP2P3/1B2BPPP/R2Q1RK1 w - - 5 16")
        told = describe(board, board.parse_san("Nxf6+"), str(Motif.REMOVING_THE_DEFENDER))

        assert "takes defender on bf6" in told
        assert "they recapture" in told
        assert "then falls ne5" in told

    def test_a_captured_piece_is_named_from_before_the_move(self):
        """It is not on the board afterwards, so naming it from `after` is wrong."""
        board = chess.Board("4k3/8/8/3n4/8/8/8/3RK3 w - - 0 1")
        told = describe(board, board.parse_san("Rxd5"), str(Motif.HANGING_PIECE))

        assert "takes nd5" in told

    def test_nothing_is_said_about_a_motif_that_did_not_fire(self):
        board = chess.Board()
        assert describe(board, board.parse_san("e4"), str(Motif.FORK)) == ""


class TestItCannotDriftFromTheDetector:
    @pytest.mark.parametrize("motif", [str(m) for m in Motif])
    def test_evidence_is_present_exactly_when_the_motif_fires(self, motif):
        """Every legal move of a real game, both directions checked."""
        import pathlib

        pgn = pathlib.Path(GAMES) / "bjagus.pgn"
        if not pgn.exists():
            pytest.skip("review corpus not present")

        checked = disagreements = 0
        with open(pgn, encoding="utf-8", errors="replace") as handle:
            for _ in range(3):
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                board = game.board()
                for played in game.mainline_moves():
                    for move in list(board.legal_moves):
                        fires = motif in {str(m) for m in detect_motifs(board, move)}
                        told = bool(evidence(board, move, motif))
                        checked += 1
                        disagreements += fires != told
                    board.push(played)

        assert checked > 0
        assert disagreements == 0, f"{disagreements} of {checked} disagree for {motif}"
