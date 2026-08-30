"""Counting the three development claims, and keeping the two bases apart.

Design: docs/notes/design.opening-development-signals.md
"""

from __future__ import annotations

import chess
import pytest

from chesscoach.analysis.observations import Observation
from chesscoach.development import measure_development
from chesscoach.development_norms import DevelopmentNorms, Norm
from chesscoach.opening_development import (
    BY_BOOK,
    BY_SELF,
    count,
    developments,
    games_from,
    habit_costs,
)
from chesscoach.openings import OpeningBook

PLAYER = "subject"

# A real Italian, White castling on ply 7 and finishing development on ply 13.
ITALIAN = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6", "d3", "d6",
           "Bg5", "Bg4", "Nbd2", "Nd4")
# The same opening played slowly: White castles on ply 19.
SLOW_ITALIAN = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "a3", "a6", "h3", "h6",
                "a4", "b6", "h4", "d6", "Nc3", "Nf6", "d3", "Bg4", "O-O", "O-O",
                "Bg5", "Qd7")


def observations_for(sans, game_id: str, player_is_white: bool = True):
    """A game as the analyser would have recorded it: one observation per ply."""
    board = chess.Board()
    rows = []
    for index, san in enumerate(sans):
        move = board.parse_san(san)
        mover_is_white = board.turn == chess.WHITE
        is_player = mover_is_white == player_is_white
        rows.append(
            Observation(
                game_id=game_id,
                ply=index + 1,
                mover=PLAYER if is_player else "opponent",
                mover_is_white=mover_is_white,
                fen_before=board.fen(),
                move_played=move.uci(),
                best_move=None,
                score_cp_before=0,
                score_cp_after=0,
                loss_wp=0.0,
                label=None,
                phase="opening",
                played_best=False,
                clock_before=None,
                clock_after=None,
                engine="test",
                depth=1,
            )
        )
        board.push(move)
    return tuple(rows)


@pytest.fixture(scope="module")
def book():
    return OpeningBook.load()


def norms(cells: dict | None = None) -> DevelopmentNorms:
    """A hand-built expectation, so no test depends on the fetched corpus."""
    return DevelopmentNorms(
        {key: Norm(*values) for key, values in (cells or {}).items()}
    )


class TestRebuildingGamesFromObservations:
    def test_it_recovers_the_move_list_and_the_players_colour(self):
        rows = observations_for(ITALIAN, "g1", player_is_white=True)
        (game_id, moves, colour), = games_from(rows, PLAYER)
        assert game_id == "g1"
        assert len(moves) == len(ITALIAN)
        assert colour == chess.WHITE

    def test_it_finds_black_when_the_player_had_black(self):
        rows = observations_for(ITALIAN, "g1", player_is_white=False)
        (_, _, colour), = games_from(rows, PLAYER)
        assert colour == chess.BLACK

    def test_observations_arriving_out_of_order_still_rebuild_the_game(self):
        # Nothing promises the analyser's output is sorted, and a shuffled game
        # would silently produce a different -- and legal-looking -- move list.
        rows = observations_for(ITALIAN, "g1")
        shuffled = tuple(sorted(rows, key=lambda o: -o.ply))
        (_, moves, _), = games_from(shuffled, PLAYER)
        board = chess.Board()
        for move in moves:
            assert move in board.legal_moves
            board.push(move)

    def test_a_game_the_player_never_moved_in_is_skipped(self):
        rows = observations_for(ITALIAN, "g1")
        foreign = tuple(
            Observation(**{**o.__dict__, "mover": "somebody_else"}) for o in rows
        )
        assert list(games_from(foreign, PLAYER)) == []


class TestNamingTheOpening:
    def test_it_files_the_game_under_its_opening_family(self, book):
        found = developments(observations_for(ITALIAN, "g1"), PLAYER, book)
        assert len(found) == 1
        assert found[0].family == "Italian Game"
        assert found[0].development.castled_at == 7


class TestJudging:
    def test_a_game_slower_than_the_norm_is_counted(self, book):
        # Norm: castle by ply 7, ready by ply 13. Tolerance is 4 plies, so the
        # slow game (castles ply 19) is past both.
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].instances == 1
        assert tallies[f"slow_development.{BY_BOOK}"].instances == 1

    def test_a_game_inside_the_tolerance_is_not_counted(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        tallies = count(observations_for(ITALIAN, "g1"), PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].instances == 0
        assert tallies[f"late_castling.{BY_BOOK}"].opportunities == 1

    def test_the_tolerance_actually_forgives_two_moves(self, book):
        # Castling on ply 7 against a norm of 4 is 3 plies late -- inside the
        # +2-move tolerance, and must NOT fire. Without the tolerance a bare
        # median would flag half of everybody by construction.
        expectation = norms({("Italian Game", True): (4, 13, 50)})
        tallies = count(observations_for(ITALIAN, "g1"), PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].instances == 0

    def test_an_opening_with_too_few_strong_games_gets_no_expectation(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 3)})
        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, expectation)
        assert f"late_castling.{BY_BOOK}" not in tallies


class TestTheTwoBasesStayApart:
    def test_an_uncovered_opening_is_judged_against_the_players_own_habit(self, book):
        # Four fast Italians establish the habit; the Sicilian has no norm and is
        # judged against them. The two must land in DIFFERENT claim keys --
        # "late by this opening's standard" and "later than you usually are" are
        # different evidence.
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        rows = ()
        for i in range(4):
            rows += observations_for(ITALIAN, f"fast{i}")
        rows += observations_for(
            ("e4", "c5", "Nf3", "d6", "a3", "Nf6", "h3", "g6", "a4", "Bg7",
             "h4", "O-O", "Nc3", "Nc6", "d3", "Bd7", "Be3", "Rc8", "Be2", "b6",
             "O-O", "Qc7"),
            "slow_sicilian",
        )
        tallies = count(rows, PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].opportunities == 4
        assert tallies[f"late_castling.{BY_SELF}"].opportunities == 1
        assert tallies[f"late_castling.{BY_SELF}"].instances == 1

    def test_the_own_median_needs_enough_games_to_be_a_median(self, book):
        # Two games is a difference, not a norm.
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        rows = observations_for(ITALIAN, "a") + observations_for(ITALIAN, "b")
        rows += observations_for(
            ("d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bg5", "Be7", "e3", "O-O"),
            "uncovered",
        )
        tallies = count(rows, PLAYER, book, expectation)
        assert f"late_castling.{BY_SELF}" not in tallies


class TestRepeatMoves:
    def test_it_counts_moves_not_games_and_needs_no_expectation(self, book):
        # No norm at all: repeat share is compared straight against peers.
        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, norms())
        repeats = tallies["repeat_move.any"]
        development = measure_development(
            [chess.Move.from_uci(o.move_played)
             for o in observations_for(SLOW_ITALIAN, "g1")],
            chess.WHITE,
        )
        assert repeats.opportunities == development.moves_in_window
        assert repeats.instances == development.repeat_moves
        assert repeats.opportunities > 1


class TestEvidence:
    """V8: every claim cites the player's own games.

    These tests exist because the claims were wired up once with correct numbers
    and no examples, and the confidence policy refused them **silently** -- a
    report that said nothing, with nothing wrong in any count.
    """

    def test_every_instance_carries_a_move_to_cite(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, expectation)
        for key in (f"late_castling.{BY_BOOK}", f"slow_development.{BY_BOOK}",
                    "repeat_move.any"):
            tally = tallies[key]
            assert tally.instances > 0, key
            assert tally.examples, f"{key} has instances but nothing to cite"
            assert all(o.mover == PLAYER for o in tally.examples)

    def test_the_cited_move_is_the_one_that_decided_it(self, book):
        # SLOW_ITALIAN castles on ply 19, so that is the move the claim points at.
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].examples[0].ply == 19

    def test_a_player_who_never_castled_is_cited_by_their_last_move(self, book):
        # There is no castling move to point at, so the honest evidence is the
        # last move of the opening -- "and here the king was still at home".
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        never = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "d3", "d6", "a3", "a6",
                 "h3", "h6", "a4", "b6", "h4", "Nf6", "Nc3", "Bg4", "Be3", "Qd7")
        tallies = count(observations_for(never, "g1"), PLAYER, book, expectation)
        tally = tallies[f"late_castling.{BY_BOOK}"]
        assert tally.instances == 1
        assert tally.examples[0].mover == PLAYER
        assert tally.examples[0].ply == 19


def observations_with_loss(sans, game_id, losses, player_is_white=True):
    """A game where named plies lost win probability."""
    rows = observations_for(sans, game_id, player_is_white)
    return tuple(
        Observation(**{**o.__dict__, "loss_wp": losses.get(o.ply, 0.0)})
        for o in rows
    )


class TestHabitCost:
    """The author's costing method.

    > *"Combining cost of the moves when the same piece was moved repeatedly
    > instead of developing the other piece, combining the cost of every pawn
    > move when the piece should be developed instead and combining the cost for
    > every move when the player should castle the king but he did something
    > else."*

    Their reason for it, which is what rules out an end-of-opening measure:
    *"in the games of weaker players they don't have to eventually end opening
    worse because their opponent also plays badly."*
    """

    def test_it_sums_what_the_habits_own_moves_lost(self, book):
        # Ply 7 is a3, a pawn move with minors still at home and castling legal.
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0})
        game, = developments(rows, PLAYER, book)
        costs = habit_costs(game)
        assert costs["late_castling"] == 5.0    # castling was available, declined
        assert costs["slow_development"] == 5.0  # the union counts it once

    def test_the_headline_takes_the_union_and_never_double_counts(self, book):
        # One move that is BOTH a declined castle and a pawn-instead-of-develop
        # must contribute its loss once, not twice.
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 4.0, 9: 6.0})
        game, = developments(rows, PLAYER, book)
        costs = habit_costs(game)
        assert costs["slow_development"] == 10.0
        assert costs["slow_development"] <= sum(
            o.loss_wp for o in game.mine
        )

    def test_a_move_that_lost_nothing_costs_nothing(self, book):
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {})
        game, = developments(rows, PLAYER, book)
        assert habit_costs(game) == {
            "late_castling": 0.0, "repeat_move": 0.0, "slow_development": 0.0,
        }

    def test_the_cost_reaches_the_tally(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0})
        tallies = count(rows, PLAYER, book, expectation)
        assert tallies[f"slow_development.{BY_BOOK}"].cost_wp == 5.0
