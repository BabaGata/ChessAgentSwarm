"""What a game says about how one player developed.

Design: docs/notes/design.opening-development-signals.md

The module reports facts and judges nothing. There is no threshold in it,
because a threshold is the part that has to come from the player's peers in the
same opening -- "castle by move 10" is a teaching heuristic, not a fact, and
hard-coding it would be the folklore laundering R-03 forbids.
"""

from __future__ import annotations

import chess

from chesscoach.book_depth import own_plies_in_window
from chesscoach.development import Development, measure_development
from chesscoach.opening_development import CITABLE_OPENING_PLIES, GameDevelopment


def moves(*sans: str, start: str | None = None) -> list[chess.Move]:
    """SAN into moves, so the fixtures read like games."""
    board = chess.Board() if start is None else chess.Board(start)
    played = []
    for san in sans:
        move = board.parse_san(san)
        played.append(move)
        board.push(move)
    return played


ITALIAN = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6", "d3", "d6",
           "Bg5", "Bg4", "Nbd2", "Nd4")


class TestCastling:
    def test_it_finds_the_ply_the_player_castled(self):
        # White castles on their 4th move, which is ply 7 counting from 1.
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.castled_at == 7

    def test_a_player_who_never_castles_has_no_castling_ply(self):
        black = measure_development(moves(*ITALIAN), chess.BLACK)
        assert black.castled_at is None

    def test_walking_the_king_by_hand_is_not_castling(self):
        # Ke2 is not castling however much it resembles getting the king out of
        # the centre, and counting it would flatter exactly the players this
        # claim exists to find.
        game = measure_development(moves("e4", "e5", "Ke2", "Nc6"), chess.WHITE)
        assert game.castled_at is None


class TestDevelopment:
    def test_finished_developing_means_all_four_minors(self):
        """What `slow_development` measures, and what the norms are built from.

        White's minors leave on plies 3 (Nf3), 5 (Bc4), 11 (Bg5), 13 (Nbd2).
        """
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.developed_at == 13

    def test_most_of_them_is_the_end_of_the_PHASE_and_a_different_number(self):
        """The author's rule -- and it is about the phase, not about finishing.

        Applying "most of the pieces" to `developed_at` itself changed what
        `slow_development` measures and silenced three firings the author had
        accepted. The phase boundary closes the counting window; `developed_at`
        answers *"when did you finish developing"*, and they are different plies.
        """
        white = measure_development(moves(*ITALIAN), chess.WHITE)

        assert white.developed_enough_at == 11
        assert white.developed_at == 13

    def test_development_is_incomplete_while_a_minor_sits_at_home(self):
        white = measure_development(moves("e4", "e5", "Nf3", "Nc6"), chess.WHITE)
        assert white.developed_at is None

    def test_a_minor_captured_at_home_no_longer_blocks_development(self):
        # Nothing is left to develop on that square, so waiting for it would
        # mean development never completes in any game where a piece is traded
        # on its home square.
        # Black's bishop reaches c1 down the empty h6-c1 diagonal and takes
        # White's dark bishop where it started.
        played = moves("d4", "g6", "Nf3", "Bh6", "c3", "Bxc1")
        white = measure_development(played, chess.WHITE)
        assert "c1" not in white.still_at_home

    def test_ready_is_the_later_of_the_king_moving_and_development(self):
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.ready_at == 13
        assert white.phase_over_at == 11
        assert white.completed

    def test_a_king_that_moved_without_castling_still_ends_the_opening(self):
        """The case that showed castling is the wrong signal.

        The author: *"sometimes the king had to move because of check or
        something else and is not possible to do the casteling again."* In
        `goydorak/EHDkU9YW` the king was forced to `Kxf2` on ply 7 and walked to
        g1 by ply 19 -- so the opening plainly ended, and `ready_at` returned
        None because no castle ever happened. The window then ran to the end of
        the game: 21 % of player-games never closed one, reaching 89 moves.
        """
        # 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.Ke2 -- the king moves, castling is gone.
        played = moves("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "Ke2", "d6",
                       "Nc3", "Nf6", "d3", "Bg4")
        white = measure_development(played, chess.WHITE)

        assert white.castled_at is None
        assert white.king_moved_at == 7
        assert white.phase_over_at is not None
        assert white.completed


class TestRepeatMoves:
    def test_moving_a_piece_that_has_already_moved_is_a_repeat(self):
        # Nf3 then Ng5: the second is a repeat, the first is not.
        played = moves("e4", "e5", "Nf3", "Nc6", "Ng5", "d5")
        white = measure_development(played, chess.WHITE)
        assert white.repeat_moves == 1

    def test_a_piece_returning_home_has_still_moved(self):
        # Nf3, Ng1 -- both count as moves of an already-developed piece from the
        # second onward. A knight that goes home has not become undeveloped.
        played = moves("e4", "e5", "Nf3", "Nc6", "Ng1", "d5")
        white = measure_development(played, chess.WHITE)
        assert white.repeat_moves == 1

    def test_castling_does_not_count_as_moving_the_rook_again(self):
        # Every white move in this line is a different piece's first move, so
        # the honest answer is zero -- and it is only zero if castling did not
        # leave a phantom record on the rook's new square.
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.repeat_moves == 0
        assert white.castled_at == 7

    def test_a_piece_recaptured_on_its_square_does_not_make_the_next_move_a_repeat(self):
        # White's bishop is traded on f2 and Black's king recaptures there. The
        # king has now moved, but the entry that has to be cleared is the
        # BISHOP's -- if a capture left the mover's record in place, the
        # recapturing piece would inherit it.
        played = moves("e4", "e5", "Nf3", "Bc5", "Nc3", "Bxf2+", "Kxf2", "Nc6", "Kg1")
        white = measure_development(played, chess.WHITE)
        # Kxf2 is the king's first move; Kg1 is its second and the only repeat.
        assert white.repeat_moves == 1


class TestPawnMoves:
    def test_it_counts_only_the_players_own_pawn_moves(self):
        white = measure_development(moves(*ITALIAN), chess.WHITE)
        assert white.pawn_moves == 2  # e4 and d3
        black = measure_development(moves(*ITALIAN), chess.BLACK)
        assert black.pawn_moves == 2  # e5 and d6


class TestTheWindow:
    def test_counting_stops_once_development_is_complete(self):
        # Three further pawn moves after White is ready must not be counted:
        # the claim is about the opening, and the window ends when the opening
        # is over for this player.
        played = moves(*ITALIAN, "a3", "a6", "b4", "b5", "c3")
        white = measure_development(played, chess.WHITE)
        # Counting stops at the **phase** boundary, not when the last minor
        # finally comes out.
        assert white.phase_over_at == 11
        assert white.moves_in_window == 6

    def test_an_unfinished_game_reports_what_it_saw_and_says_so(self):
        # Right-censored: development had not finished and could not have. The
        # measurement must not pretend otherwise -- a rate built over this game
        # as though it were complete would report short games as slow
        # development.
        white = measure_development(moves("e4", "e5", "Nf3", "Nc6"), chess.WHITE)
        assert not white.completed
        assert white.ready_at is None
        assert white.moves_in_window == 2


class TestWhatIsCitedWhenTheDecidingMoveNeverCame:
    """A claim about move 15 must not be evidenced by move 5.

    `at_ply` falls back to *"the player's last move inside the opening window"*
    when the deciding move does not exist -- they never castled, or never
    finished developing. The window it used was `EARLY_PLIES = 10`, which E76
    calibrated for `out_of_book` and which ends at **move 5 for both colours**.
    So every fallback citation was move 5, whatever the claim.

    All five rejected `late_castling` and `slow_development` rows on the
    2026-09-07 sheet were exactly this, and the author rejected each for the
    same reason:

    > *"this exact move did not had any significant wp loss and should not be
    > counted"*

    > *"There were some unnecessary movements of the pawns instead of developing
    > pieces and allowing the king to castle but d5 was not one of them"*

    They are right about the move and it was never the move the claim rested
    on. The claim is about a game; the citation is meant to say *"and here the
    king was still in the centre"*, which move 5 cannot say -- nobody has
    castled by move 5.
    """

    def game(self, plies: int, colour, **development):
        observations = tuple(
            _observation(ply=ply)
            for ply in range(1, plies + 1)
            if (ply % 2 == 1) == (colour == chess.WHITE)
        )
        fields = {
            "castled_at": None, "king_moved_at": None, "developed_at": None,
            "developed_enough_at": None, "still_at_home": 0, "moves_in_window": 0,
            "repeat_moves": 0, "pawn_moves": 0, "completed": False,
        }
        fields.update(development)
        return GameDevelopment(
            game_id="g", family="Test", colour=colour,
            development=Development(**fields), mine=observations,
        )

    def test_the_fallback_reaches_past_the_out_of_book_window(self):
        # White never castled. The old fallback stopped at ply 9 (move 5); the
        # opening does not end there and neither does the evidence.
        game = self.game(40, chess.WHITE, castled_at=None)

        cited = game.at_ply(None)

        assert cited is not None
        assert cited.ply > own_plies_in_window(True)[-1]

    def test_it_still_refuses_the_late_middlegame(self):
        """The defect this fallback was written to fix: it once cited `Rf7#` on
        move 36 as evidence of slow development. Reaching further must not
        reach that far."""
        game = self.game(80, chess.WHITE, castled_at=None)

        cited = game.at_ply(None)

        assert cited.ply <= CITABLE_OPENING_PLIES

    def test_the_deciding_move_still_wins_when_there_is_one(self):
        game = self.game(40, chess.WHITE, castled_at=21)

        assert game.at_ply(21).ply == 21


def _observation(ply: int):
    """One ply, with only the fields a citation actually reads filled in."""
    from chesscoach.analysis.observations import Observation

    return Observation(
        game_id="g", ply=ply, mover="player", mover_is_white=ply % 2 == 1,
        fen_before="8/8/8/8/8/8/8/K6k w - - 0 1", move_played="a1a2",
        best_move=None, score_cp_before=0, score_cp_after=0, loss_wp=0.0,
        label=None, phase="opening", played_best=False,
        clock_before=None, clock_after=None, engine="test", depth=1,
    )
