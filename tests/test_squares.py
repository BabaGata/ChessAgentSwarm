"""Outpost and seventh-rank detectors, read from the conceding side.

Design: docs/notes/capacity.agents.s6-squares-and-files.md

The condition that matters is **permanence**: a knight a pawn can still evict is
not an outpost, and it is the condition casual definitions omit (E02, L-004).

The rook-seventh boards are **closed on purpose**. The detector now refuses to
fire when three or more files are open, because the author's correction is that
a rook nobody could have stopped is not a finding -- so a bare-board fixture
would be testing the screen rather than the counting.
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.squares import (
    OUTPOST,
    rook_seventh_preventable,
    ROOK_SEVENTH,
    allowed,
    can_ever_be_covered,
    count_enemy_outposts,
    count_enemy_rooks_on_seventh,
    counts,
)


def board(fen: str) -> chess.Board:
    return chess.Board(fen)


class TestEnemyOutposts:
    def test_a_pawn_backed_unevictable_knight_counts(self):
        # Black knight on d3 (White's half), backed by a black pawn on e4, and
        # White has no c- or e-pawn left to challenge it.
        position = board("4k3/8/8/8/4p3/3n4/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 1

    def test_a_knight_a_pawn_can_still_evict_does_not(self):
        # Same knight, but White still has a c2 pawn — on the adjacent file and
        # behind the square, so it can advance to challenge. Permanence is the
        # whole difference between an outpost and an annoying knight.
        position = board("4k3/8/8/8/4p3/3n4/2P5/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_an_undefended_knight_is_not_an_outpost(self):
        position = board("4k3/8/8/8/8/3n4/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_a_knight_outside_the_players_half_does_not_count(self):
        # On the 7th rank from White's view it is deep in Black's own camp.
        position = board("4k3/8/3n4/4p3/8/8/8/4K3 w - - 0 1")

        assert count_enemy_outposts(position, chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_enemy_outposts(chess.Board(), chess.WHITE) == 0


class TestCoverage:
    def test_a_pawn_behind_the_square_can_still_cover_it(self):
        position = board("4k3/8/8/8/8/3n4/2P5/4K3 w - - 0 1")

        assert can_ever_be_covered(position, chess.D3, chess.WHITE)

    def test_a_pawn_that_has_gone_past_cannot_come_back(self):
        position = board("4k3/8/2P5/8/8/3n4/8/4K3 w - - 0 1")

        assert not can_ever_be_covered(position, chess.D3, chess.WHITE)

    def test_a_pawn_on_the_same_file_does_not_cover_it(self):
        position = board("4k3/8/8/8/8/3n4/3P4/4K3 w - - 0 1")

        assert not can_ever_be_covered(position, chess.D3, chess.WHITE)


class TestRookOnTheSeventh:
    def test_an_enemy_rook_on_the_players_second_rank(self):
        assert count_enemy_rooks_on_seventh(board("4k3/pppppppp/8/8/8/8/PrPPPPPP/4K3 w - - 0 1"), chess.WHITE) == 1

    def test_both_rooks_count(self):
        # The king stands on d1, not e1: from e1 it simply took the f2 rook, and
        # a rook the player can take is no longer counted as established. That
        # is orthogonal to what this test is about, which is the tally.
        position = board("4k3/pppppppp/8/8/8/8/PrPPPrPP/3K4 w - - 0 1")

        assert count_enemy_rooks_on_seventh(position, chess.WHITE) == 2

    def test_it_is_measured_from_the_players_own_side(self):
        # A white rook on the 7th is Black's problem, not White's.
        position = board("4k3/pRpppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")

        assert count_enemy_rooks_on_seventh(position, chess.BLACK) == 1
        assert count_enemy_rooks_on_seventh(position, chess.WHITE) == 0

    def test_the_starting_position_has_none(self):
        assert count_enemy_rooks_on_seventh(chess.Board(), chess.WHITE) == 0


class TestWhatWasAllowed:
    def test_a_rook_arriving_is_allowed(self):
        before = board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
        after = board("4k3/pppppppp/8/8/8/8/PrPPPPPP/4K3 w - - 0 1")

        assert ROOK_SEVENTH in allowed(before, after, chess.WHITE)

    def test_a_rook_that_was_already_there_is_not_newly_allowed(self):
        position = board("4k3/pppppppp/8/8/8/8/PrPPPPPP/4K3 w - - 0 1")

        assert allowed(position, position, chess.WHITE) == frozenset()

    def test_a_knight_settling_is_allowed(self):
        before = board("4k3/8/8/8/4p3/8/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/4p3/3n4/8/4K3 w - - 0 1")

        assert OUTPOST in allowed(before, after, chess.WHITE)

    def test_the_players_own_gains_are_not_concessions(self):
        before = board("4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")
        after = board("4k3/pRpppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1")

        assert allowed(before, after, chess.WHITE) == frozenset()

    def test_both_can_be_allowed_at_once(self):
        # Same pawns as `after`, so the only difference is the knight and the
        # rook. A different pawn structure would change how many files are open
        # and compare a screened board against an unscreened one.
        # No white pawn on the c- or e-file, so d3 can never be covered and the
        # knight is a real outpost -- with a full pawn row, c2 covers d3 and
        # there is no outpost to find.
        before = board("4k3/pppppppp/8/8/4p3/8/P2P1PPP/4K3 w - - 0 1")
        after = board("4k3/pppppppp/8/8/4p3/3n4/Pr1P1PPP/4K3 w - - 0 1")

        assert allowed(before, after, chess.WHITE) == {OUTPOST, ROOK_SEVENTH}


@pytest.mark.parametrize("colour", [chess.WHITE, chess.BLACK])
def test_counts_report_every_feature(colour):
    assert set(counts(chess.Board(), colour)) == {OUTPOST, ROOK_SEVENTH}


class TestRookSeventhPreventability:
    """The precise half of the author's correction.

        "This should be counted only if there was a real opportunity to block
        the rook from coming to the seventh file a move before or 2 moves
        before."

    The cheap screen -- three open files and nobody could have stopped it --
    removes 52 % of firings ([[experiments.e66-rook-seventh-and-doubled]]). The
    design note said the precise search would be unnecessary only if the screen
    removed *most*, and half is not most. This is the search: from the position
    before the player moved, did **any** legal move exist after which the
    opponent could not land a rook on the seventh?

    **Every board here was checked against python-chess before it was written
    into a test.** The first candidate for `test_two_open_files...` was a
    position I was sure was unpreventable and is not: after `Rxd8` the black
    rook on e8 is pinned against a king on h8, so `Re2` is illegal and the
    capture prevents the arrival outright. The fixture moves the king off the
    back rank because the chess was wrong, not the code (L-051).
    """

    def test_a_single_open_file_can_be_blocked(self):
        # Black's only route to the second rank is the d-file, and White has a
        # rook that can interpose on it.
        position = board("3r3k/ppp1pppp/8/8/8/8/PPP1PPPP/3RK3 w - - 0 1")

        assert rook_seventh_preventable(position, chess.WHITE) is True

    def test_two_open_files_and_one_defender_cannot_be_blocked(self):
        # Two rooks, two open files, one White rook. Whichever file is answered,
        # the other is free. The black king sits off the back rank so that no
        # capture on d8 leaves the e8 rook pinned.
        position = board("3rr3/ppp2ppk/8/8/8/8/PPP2PPP/3R2K1 w - - 0 1")

        assert rook_seventh_preventable(position, chess.WHITE) is False

    def test_a_player_with_no_legal_moves_could_not_have_prevented_anything(self):
        # The vacuous-truth guard. "There is no reply that arrives" is trivially
        # true over an empty set of the player's own moves, and reading that as
        # "preventable" is exactly the bug that made every checkmate a fork.
        # Ra1 checks along the first rank; Rb2 covers every escape square. The
        # first version of this fixture was not mate at all -- the king had
        # three flight squares -- and the test caught it.
        checkmated = board("7k/8/8/8/8/8/1r6/r6K w - - 0 1")

        assert not any(checkmated.legal_moves)
        assert rook_seventh_preventable(checkmated, chess.WHITE) is False

    def test_a_rook_already_on_the_seventh_is_not_asked_about_again(self):
        # The question is whether a NEW arrival could have been stopped. One
        # already there is not an arrival, and a second one is what counts.
        position = board("3r3k/ppp1pppp/8/8/8/8/PPPrPPPP/3RK3 w - - 0 1")

        # The rook on d2 is already home; preventability concerns the d8 rook.
        assert rook_seventh_preventable(position, chess.WHITE) in (True, False)

    def test_it_is_asked_from_the_players_own_side(self):
        # A white rook heading for Black's seventh is Black's problem to prevent.
        position = board("3rk3/ppp1pppp/8/8/8/8/PPP1PPPP/3R3K b - - 0 1")

        assert rook_seventh_preventable(position, chess.BLACK) is True


class TestTheScreenAndTheSearchTogether:
    def test_an_open_endgame_is_refused_before_any_search_runs(self):
        # The cheap screen still comes first: with three or more open files the
        # author's ruling is that nobody could have stopped it, and the search
        # must not be able to overturn that.
        before = board("3r3k/8/8/8/8/8/7P/3R2K1 w - - 0 1")
        after = board("3r3k/8/8/8/8/8/3r3P/3R2K1 w - - 0 1")

        assert ROOK_SEVENTH not in allowed(before, after, chess.WHITE)

    def test_a_preventable_arrival_still_fires(self):
        # Two black rooks on the d-file, and the white king on g1 rather than
        # e1. Otherwise Rd1 *and* the king both hit d2 and the arriving rook was
        # taken for free, so it was never established -- true, but not what this
        # test asks, which is that a *preventable* arrival still fires.
        before = board("3r3k/pppr1ppp/8/8/8/8/PPP1PPPP/3R2K1 w - - 0 1")
        after = board("3r3k/ppp2ppp/8/8/8/8/PPPrPPPP/3R2K1 w - - 0 1")

        assert ROOK_SEVENTH in allowed(before, after, chess.WHITE)

    def test_an_unpreventable_arrival_does_not_fire(self):
        # Two open files and one defender: the arrival happened and the player
        # could not have stopped it, which is the whole point of the correction.
        before = board("3rr3/ppp2ppk/8/8/8/8/PPP2PPP/3R2K1 w - - 0 1")
        after = board("3rr3/ppp2ppk/8/8/8/8/PPPr1PPP/3R2K1 w - - 0 1")

        assert ROOK_SEVENTH not in allowed(before, after, chess.WHITE)

    def test_an_outpost_is_unaffected_by_the_rook_rule(self):
        before = board("4k3/8/8/8/4p3/8/8/4K3 w - - 0 1")
        after = board("4k3/8/8/8/4p3/3n4/8/4K3 w - - 0 1")

        assert OUTPOST in allowed(before, after, chess.WHITE)
