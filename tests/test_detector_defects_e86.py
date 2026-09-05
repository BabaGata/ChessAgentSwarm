"""The two defects E86 demonstrated, fixed.

Spec: docs/notes/experiments.e86-detector-audit.md § D-1, § D-2

Both were found by reading the detectors against Lichess's own theme definitions
and then reproduced on positions, rather than argued from the code.

**D-1 was withdrawn.** The claim was that `fork` misses a fork when a victim was
already attacked. It does, and that is deliberate: the author's definition says
the targets must not have been *attacked before*, and the position offered as
proof had the rook already undefended and already attackable, so it was won
without any fork. `tests/test_fork.py` holds the case that says so. A narrower
gap remains -- a target attacked but *defended*, made winnable only by this
move's second attacker -- and closing it is a chess judgement, not a bug fix.

**D-2 -- `trappedPiece` reported a piece that could escape safely.**
Escape squares were tested with `is_attacked_by`, the naive test D17 replaced
everywhere else in the module with an exchange. `_lands_safely` asks
`wins_material`; this did not.
"""

from __future__ import annotations

import chess

from chesscoach.tactics import Motif, _is_trapped_piece, detect_motifs


def motifs(fen: str, uci: str) -> set[str]:
    board = chess.Board(fen)
    return {str(m) for m in detect_motifs(board, chess.Move.from_uci(uci))}


class TestTrappedPieceWithASafeEscape:
    SAFE = "n2k4/8/8/P7/8/8/7Q/6KB b - - 0 1"
    TRAPPED = "n3k3/8/8/P7/8/8/7Q/6KB b - - 0 1"

    def judged(self, fen: str) -> bool:
        board = chess.Board(fen)
        return _is_trapped_piece(board, board, chess.Move.from_uci("d8c8"), chess.WHITE)

    def test_a_knight_with_a_defended_escape_is_not_trapped(self):
        assert not self.judged(self.SAFE)

    def test_a_knight_whose_escapes_all_lose_it_is_trapped(self):
        assert self.judged(self.TRAPPED)

    def test_the_two_positions_differ_only_in_the_kings_square(self):
        a, b = chess.Board(self.SAFE), chess.Board(self.TRAPPED)
        differing = {sq for sq in chess.SQUARES if a.piece_at(sq) != b.piece_at(sq)}
        assert differing == {chess.D8, chess.E8}
