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
    GameDevelopment,
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


def drifting(sans, game_id, player_is_white=True, plies=(7, 9, 11), best=None):
    """A game whose player made unexplained errors before castling.

    `late_castling` now fires only when the player was **drifting** while they
    were late ([[design.castling-under-drift]]), so a fixture with a clean
    opening no longer counts however late the king is -- which is the point of
    the change and not a fault in these tests.

    `label` and `loss_wp` make the move an error; `best_move` stays None so no
    motif explains it, which is what makes it drift rather than a missed tactic.

    **The plies are inside the opening window** (`EARLY_PLIES = 10`, so White
    moves on 1, 3, 5, 7, 9). `slow_development` reads `window_moves`, so an error
    outside the window is invisible to it however large -- an earlier version of
    this helper used plies 15 and 17 and could not make the claim fire at all.

    `best` supplies the engine's move, which `declined_development` needs: a
    developing move there means development was on offer and not played.

    Ply 11 is outside the window on purpose. `drift_before` is bounded by the
    book and by the castling ply, not by the window, and these fixtures have
    six or seven plies of real theory in them -- so without a move past the
    window there is only one non-theory error and `late_castling` cannot reach
    its two.
    """
    from chesscoach.analysis.observations import ErrorLabel

    rows = observations_for(sans, game_id, player_is_white)
    return tuple(
        Observation(**{
            **o.__dict__,
            "label": ErrorLabel.INACCURACY if o.ply in plies else o.label,
            "loss_wp": 6.0 if o.ply in plies else o.loss_wp,
            "best_move": best if (best and o.ply in plies) else o.best_move,
        })
        for o in rows
    )


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
        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, expectation)
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
        # The Sicilian is the one being judged, so it is the one that has to be
        # drifting for the claim to fire at all.
        rows += drifting(
            ("e4", "c5", "Nf3", "d6", "a3", "Nf6", "h3", "g6", "a4", "Bg7",
             "h4", "O-O", "Nc3", "Nc6", "d3", "Bd7", "Be3", "Rc8", "Be2", "b6",
             "O-O", "Qc7"),
            "slow_sicilian", plies=(15, 17),
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
        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, expectation)
        for key in (f"late_castling.{BY_BOOK}", f"slow_development.{BY_BOOK}",
                    "repeat_move.any"):
            tally = tallies[key]
            assert tally.instances > 0, key
            assert tally.examples, f"{key} has instances but nothing to cite"
            assert all(o.mover == PLAYER for o in tally.examples)

    def test_the_cited_move_is_the_one_that_decided_it(self, book):
        # SLOW_ITALIAN castles on ply 19, so that is the move the claim points at.
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, expectation)
        assert tallies[f"late_castling.{BY_BOOK}"].examples[0].ply == 19

    def test_a_player_who_never_castled_is_cited_by_their_last_move(self, book):
        # There is no castling move to point at, so the honest evidence is the
        # last move of the opening -- "and here the king was still at home".
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        never = ("e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "d3", "d6", "a3", "a6",
                 "h3", "h6", "a4", "b6", "h4", "Nf6", "Nc3", "Bg4", "Be3", "Qd7")
        # Drifting, because a king left at home while the player was playing
        # well is not the fault the claim names.
        tallies = count(drifting(never, "g1", best=DEVELOPS), PLAYER, book, expectation)
        tally = tallies[f"late_castling.{BY_BOOK}"]
        assert tally.instances == 1
        assert tally.examples[0].mover == PLAYER
        # The last move **of the opening**, not of the game. `mine` holds every
        # move the player made, and citing the last of those put `Rf7#` --
        # checkmate on move 36 -- under a slow-development claim.
        assert tally.examples[0].ply == 9


# Nc3 -- a developing move, legal throughout the SLOW_ITALIAN window. A habit is
# only charged where the engine wanted development instead, so a fixture that
# leaves `best_move` empty measures nothing.
DEVELOPS = "b1c3"
ANOTHER_PAWN = "d2d4"


def observations_with_loss(sans, game_id, losses, player_is_white=True,
                           best=DEVELOPS):
    """A game where named plies lost win probability, and what was better."""
    rows = observations_for(sans, game_id, player_is_white)
    return tuple(
        Observation(**{
            **o.__dict__,
            "loss_wp": losses.get(o.ply, 0.0),
            "best_move": best if o.ply in losses else o.best_move,
        })
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
        assert set(habit_costs(game).values()) == {0.0}

    def test_the_cost_reaches_the_tally(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0})
        tallies = count(rows, PLAYER, book, expectation)
        assert tallies[f"slow_development.{BY_BOOK}"].cost_wp == 5.0


class TestTheoryIsNotThePlayersMistake:
    """The author, on gambits:

    > *"For gambits, signature gambit move that looses cost should not be
    > counted with the rest since giving a pawn or 2 for a quick development is
    > a nature of the gambits."*

    The general form is broader than gambits: a move the book still names is not
    the player's own choice. Charging the King's Gambit's f4 or the Englund's e5
    to the player would penalise them hardest for *knowing* a line, which is the
    opposite of what these claims are for.
    """

    def test_a_move_inside_the_book_is_not_charged(self, book):
        # Ply 7 is a3 and loses 5.0. With the game in book to ply 8, it is
        # theory and costs the player nothing.
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0})
        game, = developments(rows, PLAYER, book)
        in_theory = GameDevelopment(
            game_id=game.game_id, family=game.family, colour=game.colour,
            development=game.development, mine=game.mine, plies_in_book=8,
        )
        assert set(habit_costs(in_theory).values()) == {0.0}

    def test_the_same_move_outside_the_book_is_charged(self, book):
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0})
        game, = developments(rows, PLAYER, book)
        out_of_theory = GameDevelopment(
            game_id=game.game_id, family=game.family, colour=game.colour,
            development=game.development, mine=game.mine, plies_in_book=6,
        )
        assert habit_costs(out_of_theory)["slow_development"] == 5.0

    def test_a_real_gambit_sacrifice_is_recognised_as_theory(self, book):
        # The King's Gambit. 2.f4 is a pawn move made instead of developing, and
        # it gives away a pawn on purpose -- the exact case the author named.
        kings_gambit = ("e4", "e5", "f4", "exf4", "Nf3", "g5", "Bc4", "Bg7",
                        "d4", "d6", "O-O", "Nc6")
        rows = observations_with_loss(kings_gambit, "kg", {3: 9.0})
        game, = developments(rows, PLAYER, book)
        assert game.plies_in_book >= 3, "the book should name the King's Gambit"
        assert habit_costs(game)["slow_development"] == 0.0


class TestOnlyChargedWhenDevelopingWasBetter:
    """The condition that makes each claim's NAME true.

    Found by reading positions, not counts: across the review corpus the engine
    wanted another *pawn* move on 40 % of the moves `opening_pawn_error` charged. Those
    are real errors and not errors of this habit -- "you pushed the wrong pawn"
    is not "you pushed a pawn instead of developing", and a plan built on the
    second sends the player to fix the wrong thing.
    """

    def test_a_move_the_engine_would_have_answered_with_a_pawn_is_not_charged(self, book):
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0},
                                      best=ANOTHER_PAWN)
        game, = developments(rows, PLAYER, book)
        assert set(habit_costs(game).values()) == {0.0}

    def test_the_same_move_is_charged_when_developing_was_better(self, book):
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0}, best=DEVELOPS)
        game, = developments(rows, PLAYER, book)
        assert habit_costs(game)["slow_development"] == 5.0

    def test_an_unanalysed_move_is_never_charged(self, book):
        # No engine opinion means no evidence that developing was better, and a
        # missing answer must not read as a positive one (L-046).
        rows = observations_with_loss(SLOW_ITALIAN, "g1", {7: 5.0}, best=None)
        game, = developments(rows, PLAYER, book)
        assert set(habit_costs(game).values()) == {0.0}


class TestPawnErrorClaim:
    def test_it_counts_bad_pawn_moves_not_pawn_moves(self, book):
        # E59 measured that 1600s push as many pawns as 2600s in the same
        # opening, so the RATE of pawn moves says nothing. This asks a different
        # question: of the pawn moves you played instead of developing, how many
        # went wrong?
        from chesscoach.analysis.observations import ErrorLabel
        rows = observations_for(SLOW_ITALIAN, "g1")
        marked = tuple(
            Observation(**{
                **o.__dict__,
                "label": ErrorLabel.MISTAKE if o.ply == 7 else None,
                "best_move": DEVELOPS if o.ply == 7 else o.best_move,
            })
            for o in rows
        )
        tallies = count(marked, PLAYER, book, norms())
        pawns = tallies["opening_pawn_error.any"]
        assert pawns.opportunities > pawns.instances
        assert pawns.instances == 1
        assert pawns.examples[0].ply == 7


class TestClaimKeysMatchTheRestOfTheSystem:
    """Every claim in the system is `kind.subject.own`. These were not.

    The detection sheet builds its vocabulary from `measure()` and its fired set
    from `Claim.key()`, then subtracts one from the other. With the development
    tallies emitting `slow_development.book` and the findings emitting
    `slow_development.book.own`, the subtraction listed four claims as NEVER
    FIRED while they were reaching three of twelve plans.
    """

    def test_the_section_emits_the_same_shape_as_every_other_claim(self, book):
        from chesscoach.profile.models import Claim
        from chesscoach.sections.s4_opening_outcomes import _key

        # What the section reports must round-trip through Claim.key().
        for kind, subject in (("slow_development", "book"), ("late_castling", "own"),
                              ("repeat_move", "any"), ("opening_pawn_error", "any")):
            key = _key(kind, subject)
            assert key.endswith(".own")
            assert Claim.of(kind=kind, subject=subject).key() == key


class TestCastlingUnderDrift:
    """`late_castling` fires only when the player was drifting while they were late.

    Design: [[design.castling-under-drift]]. The author, rejecting a firing:

    > *"In this example white took opportunities in the opening and now is
    > better of even though he castled late. This should be taken in the account
    > only when there are repeated bad moves before having the opportunity to
    > castle."*

    Measured on that game (`0tP1Rbmj`): drift **0**, against 2, 3 and 7 for the
    three the author accepted. The bar is not load-bearing at that separation --
    it is named in `DRIFT_MOVES` so moving it stays visible.
    """

    def test_a_clean_opening_is_not_a_late_castling_fault(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        tallies = count(observations_for(SLOW_ITALIAN, "g1"), PLAYER, book, expectation)

        assert tallies[f"late_castling.{BY_BOOK}"].instances == 0
        # ...and it is still counted as an opportunity, so the rate has a
        # denominator and the player is not silently dropped from the claim.
        assert tallies[f"late_castling.{BY_BOOK}"].opportunities == 1

    def test_drifting_before_castling_is(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, expectation)

        assert tallies[f"late_castling.{BY_BOOK}"].instances == 1

    def test_one_bad_move_is_not_repeated(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        tallies = count(drifting(SLOW_ITALIAN, "g1", plies=(15,)), PLAYER, book, expectation)

        assert tallies[f"late_castling.{BY_BOOK}"].instances == 0

    def test_an_error_a_motif_explains_is_not_drift(self, book):
        """It belongs to `missed_motif`; charging it here counts it twice."""
        from chesscoach.opening_development import _explained_by_a_motif

        # Nxf6+ is a verified capturingDefender (tests/test_capturing_defender_
        # precision.py): the engine's move executes a motif, so an error here is
        # a missed tactic and not aimless play.
        tactical = Observation(**{
            **observations_for(SLOW_ITALIAN, "g1")[14].__dict__,
            "fen_before": "1r1q1rk1/pp1n1ppp/5b2/2pNn3/2P5/PP2P3/1B2BPPP/R2Q1RK1 w - - 5 16",
            "best_move": "d5f6",
        })
        assert _explained_by_a_motif(tactical)

    def test_a_quiet_error_is_drift(self, book):
        """The other side of the same test: no motif, so it counts."""
        from chesscoach.opening_development import _explained_by_a_motif

        quiet = Observation(**{
            **observations_for(SLOW_ITALIAN, "g1")[14].__dict__,
            "best_move": "b1c3",
        })
        assert not _explained_by_a_motif(quiet)

    def test_errors_inside_the_book_are_not_the_players_own(self, book):
        """Theory is not a choice, so it cannot be drift."""
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        tallies = count(drifting(SLOW_ITALIAN, "g1", plies=(1, 3)), PLAYER, book, expectation)

        assert tallies[f"late_castling.{BY_BOOK}"].instances == 0


class TestSlowDevelopmentNeedsDevelopmentToHaveBeenOnOffer:
    """Pieces out late is only a fault if the position wanted them out.

    The author:

    > *"There are detected some slow development moves that are product of the
    > other moves like out of the book incorrect move, forced exchanges and
    > defenses and other moves that were better in those positions than the
    > development moves."*

    **The drift test was tried first and does not separate their marks** -- one
    accepted game measured zero drift and both rejected ones measured one. What
    does separate them is whether the engine ever wanted a piece developed:
    **0 and 0** for the rejected, **3, 5 and 7** for the accepted.
    """

    def test_a_game_where_the_engine_never_wanted_development_is_not_slow(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        # Errors in the window, but the engine wanted something else each time.
        rows = drifting(SLOW_ITALIAN, "g1", best="e4e5")
        tallies = count(rows, PLAYER, book, expectation)

        assert tallies[f"slow_development.{BY_BOOK}"].instances == 0

    def test_declining_development_is(self, book):
        expectation = norms({("Italian Game", True): (7, 13, 50)})

        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, expectation)

        assert tallies[f"slow_development.{BY_BOOK}"].instances == 1

    def test_it_is_still_counted_as_an_opportunity(self):
        """A game that no longer fires keeps the rate's denominator."""
        from chesscoach.development_norms import DevelopmentNorms  # noqa: F401

        expectation = norms({("Italian Game", True): (7, 13, 50)})
        rows = drifting(SLOW_ITALIAN, "g1", best="e4e5")

        tallies = count(rows, PLAYER, OpeningBook.load(), expectation)

        assert tallies[f"slow_development.{BY_BOOK}"].opportunities == 1


class TestOutOfBookChargesOnlyYourOwnDeparture:
    """You cannot be out of theory before there is any theory left to be in.

    The author: *"There are plenty of the opening detections that are just a
    product of not having the proper variants in the downloaded books."*

    Measured across the reviewed games: the book ran out in 658, and in **377
    (57 %) the opponent left first**, carrying **53 % of every instance the claim
    charged**. A book walk stops at the first move outside the tree, so after an
    opponent's deviation no later position is in the book and the player is out
    of theory by construction.
    """

    def test_the_player_who_deviates_is_charged(self, book):
        # 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 is theory; White's a3 leaves it.
        rows = observations_for(SLOW_ITALIAN, "g1", player_is_white=True)

        tallies = count(rows, PLAYER, book, norms())

        assert tallies["out_of_book.any"].instances > 0

    def test_the_player_whose_OPPONENT_deviates_is_not(self):
        """Same game, read from Black: White left theory, so Black is not charged."""
        rows = observations_for(SLOW_ITALIAN, "g1", player_is_white=False)

        tallies = count(rows, PLAYER, OpeningBook.load(), norms())

        assert tallies["out_of_book.any"].instances == 0
        # ...and it is not counted as an opportunity either: scoring zero on a
        # game where staying in book was impossible would dilute the rate rather
        # than measure it.
        assert tallies["out_of_book.any"].opportunities == 0

    def test_who_left_is_read_from_the_ply(self):
        from chesscoach.opening_development import left_book_themselves

        white = GameDevelopment(game_id="g", family="X", colour=chess.WHITE,
                                development=measure_development([], chess.WHITE),
                                left_at_ply=5)
        black = GameDevelopment(game_id="g", family="X", colour=chess.BLACK,
                                development=measure_development([], chess.BLACK),
                                left_at_ply=5)

        assert left_book_themselves(white)      # ply 5 is White's third move
        assert not left_book_themselves(black)


class TestOpeningPawnErrorHasItsOwnBaseline:
    """The claim compares the player against themselves, not against peers.

    The separation register withdrew its peer comparison (dispersion 1.26 against
    a 1.29 threshold), and the author kept the claim:

    > *"opening_pawn_error should stay and it gives good information for players
    > that push pawns unnecessarily instead of developing, if it doesn't reach
    > players it doesn't mean that some other players this wouldn't reach."*

    Right about the sample -- but S4 returns None without a baseline, so the
    claim was **unreachable** rather than unreached. The within-player baseline
    is *how often the player's other opening moves went wrong*, on the same terms
    (out of book, not explained by a motif), which needs no population at all.

    Across the twelve reviewed players every one errs **less** on pawn pushes
    than on their other opening moves -- 1.5-13.7 % against 12.9-22.7 % -- so
    0 of 12 is an honest answer about them and not a broken claim.
    """

    def test_the_other_moves_are_tallied_as_a_comparison_arm(self, book):
        from chesscoach.opening_development import (
            OPENING_PAWN_ERROR,
            OTHER_OPENING_MOVES,
        )

        tallies = count(drifting(SLOW_ITALIAN, "g1", best=DEVELOPS), PLAYER, book, norms())
        arm = tallies[f"{OPENING_PAWN_ERROR}.{OTHER_OPENING_MOVES}"]

        assert arm.opportunities > 0

    def test_the_comparison_arm_is_never_asserted(self):
        """It is a denominator, not a claim about the player."""
        from chesscoach.opening_development import (
            OPENING_PAWN_ERROR,
            OTHER_OPENING_MOVES,
        )
        from chesscoach.sections.s4_opening_outcomes import _is_comparison_arm

        assert _is_comparison_arm(f"{OPENING_PAWN_ERROR}.{OTHER_OPENING_MOVES}")
        assert not _is_comparison_arm(f"{OPENING_PAWN_ERROR}.any")

    def test_the_baseline_is_the_rate_on_those_other_moves(self):
        from chesscoach.opening_development import (
            OPENING_PAWN_ERROR,
            OTHER_OPENING_MOVES,
        )
        from chesscoach.sections.s4_opening_outcomes import (
            _Counts, _Tally, _other_opening_moves_rate,
        )

        arm = _Tally(instances=3, opportunities=12)
        counts = _Counts(
            tallies={f"{OPENING_PAWN_ERROR}.{OTHER_OPENING_MOVES}": arm},
            games_with_data=20,
        )

        assert _other_opening_moves_rate(counts) == pytest.approx(0.25)

    def test_without_the_arm_there_is_no_baseline_rather_than_a_wrong_one(self):
        from chesscoach.sections.s4_opening_outcomes import _Counts, _other_opening_moves_rate

        assert _other_opening_moves_rate(_Counts(tallies={}, games_with_data=20)) is None

    def test_the_arm_is_not_reported_as_a_condition(self):
        """It reached the detection sheet's vocabulary as a claim named
        `opening_pawn_error.__other_opening_moves` -- the raw-key defect (D8)
        arriving by a different door than the phrasing one."""
        from chesscoach.opening_development import OTHER_OPENING_MOVES
        from chesscoach.sections.s4_opening_outcomes import S4OpeningOutcomes

        from chesscoach.ingest.corpus import Corpus
        from chesscoach.profile.models import Provenance
        from chesscoach.sections.base import SectionContext

        rows = drifting(SLOW_ITALIAN, "g1", best=DEVELOPS)
        context = SectionContext(
            rows,
            Corpus(username=PLAYER, corpus_id="c1",
                   game_ids=tuple(sorted({o.game_id for o in rows}))),
            Provenance(engine="stub", depth=15, corpus_id="c1",
                       analysed_at="2026-09-07"),
            band="1400-1800",
            time_control="rapid",
        )

        measured = {m.claim_key for m in S4OpeningOutcomes().measure(context)}

        assert not any(k.endswith(OTHER_OPENING_MOVES) for k in measured)
