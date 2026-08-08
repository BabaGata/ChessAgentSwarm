"""The strength estimate is per speed, and says which.

Refit: docs/notes/experiments.e13-strength-signal.md § blitz

E13 fitted the rating estimate on rapid and classical games. Step 5 pooled blitz
into the corpus, and a live session then reported "About 1645" for a player whose
59 games were **all blitz** — a rapid line applied to a blitz corpus, unadmitted
(I-04).

Refit on the same 84 players' blitz games:

    rapid   rating = 2053.1 - 19858.6 * blunder_rate,  held out +/- 103
    blitz   rating = 1841.3 - 12045.1 * blunder_rate,  held out +/- 123

Blitz is genuinely harder to read — a flatter line and a wider error — because
blunder rate separates players less when everyone is rushing. Still well clear of
the 141 that guessing the median scores.

**One speed, never a blend.** A player with games at both has two ratings about
80 points apart (E19), so averaging them estimates a quantity that does not
exist. The dominant speed is used and named.
"""

from __future__ import annotations

import pytest

from chesscoach.analysis.labels import ErrorLabel
from chesscoach.analysis.observations import Observation
from chesscoach.strength import BLITZ_FIT, MIN_MOVES, RAPID_FIT, estimate

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def moves(total: int, blunders: int, game_id: str = "g1") -> tuple[Observation, ...]:
    """`total` diagnosable moves by alice, `blunders` of them blunders."""
    return tuple(
        Observation(
            game_id=game_id,
            ply=10 + i,
            mover="alice",
            mover_is_white=True,
            fen_before=FEN,
            move_played="e2e4",
            best_move="e2e4",
            score_cp_before=0,
            score_cp_after=0,
            loss_wp=0.0,
            label=ErrorLabel.BLUNDER if i < blunders else None,
            phase="opening_middlegame",
            played_best=i >= blunders,
            clock_before=None,
            clock_after=None,
            engine="stub",
            depth=15,
        )
        for i in range(total)
    )


class TestChoosingTheLine:
    def test_a_blitz_corpus_is_read_against_the_blitz_fit(self):
        observations = moves(400, 8)

        result = estimate(observations, "alice", {"g1": "blitz"})

        assert result.speed == "blitz"
        assert result.rating == BLITZ_FIT.rating(8 / 400)
        assert result.typical_error == BLITZ_FIT.typical_error

    def test_a_rapid_corpus_is_read_against_the_rapid_fit(self):
        result = estimate(moves(400, 8), "alice", {"g1": "rapid"})

        assert (result.speed, result.rating) == ("rapid", RAPID_FIT.rating(8 / 400))

    def test_classical_shares_the_rapid_line_because_the_fit_included_it(self):
        result = estimate(moves(400, 8), "alice", {"g1": "classical"})

        assert result.rating == RAPID_FIT.rating(8 / 400)

    def test_the_same_blunder_rate_reads_differently_at_different_speeds(self):
        # The whole reason for the refit: an identical rate is not an identical
        # player, and the rapid line would have over-read this blitz corpus.
        rapid = estimate(moves(400, 8), "alice", {"g1": "rapid"})
        blitz = estimate(moves(400, 8), "alice", {"g1": "blitz"})

        assert rapid.rating != blitz.rating

    def test_without_speeds_it_reads_as_rapid(self):
        # What every corpus was before step 5 pooled the speeds.
        assert estimate(moves(400, 8), "alice").speed == "rapid"


class TestTheDominantSpeedWins:
    def test_the_speed_with_the_most_moves_is_the_one_reported(self):
        mixed = moves(300, 6, "blitzy") + moves(220, 4, "slow")

        result = estimate(mixed, "alice", {"blitzy": "blitz", "slow": "rapid"})

        assert result.speed == "blitz"

    def test_only_that_speeds_moves_count_toward_the_rate(self):
        # Not a blend: the rate is measured within the speed it is read against.
        mixed = moves(300, 30, "blitzy") + moves(220, 0, "slow")

        result = estimate(mixed, "alice", {"blitzy": "blitz", "slow": "rapid"})

        assert result.moves == 300
        assert result.blunder_rate == pytest.approx(0.1)

    def test_a_genuinely_split_player_with_a_thin_corpus_gets_nothing(self):
        # Stricter than before, and deliberately: MIN_MOVES now applies within
        # one speed. Averaging two rating scales would be worse than silence.
        split = moves(150, 3, "blitzy") + moves(150, 3, "slow")

        assert estimate(split, "alice", {"blitzy": "blitz", "slow": "rapid"}) is None


class TestRefusing:
    def test_too_few_moves_in_any_speed_says_nothing(self):
        assert estimate(moves(MIN_MOVES - 1, 4), "alice", {"g1": "blitz"}) is None

    def test_a_speed_with_no_fit_is_not_read_against_the_nearest_one(self):
        # Bullet has no fit and is not fetched. If one arrives, no estimate is
        # the honest answer.
        assert estimate(moves(400, 8), "alice", {"g1": "bullet"}) is None

    def test_no_moves_at_all_says_nothing(self):
        assert estimate((), "alice", {}) is None


class TestTheFitsThemselves:
    def test_blitz_is_reported_as_the_less_certain_reading(self):
        assert BLITZ_FIT.typical_error > RAPID_FIT.typical_error

    def test_blitz_separates_players_less(self):
        # A flatter line: the same change in blunder rate moves the rating less.
        assert abs(BLITZ_FIT.slope) < abs(RAPID_FIT.slope)

    def test_each_fit_knows_where_it_stops_extrapolating(self):
        for fit in (RAPID_FIT, BLITZ_FIT):
            low, high = fit.fitted_range
            assert 0 < low < high < 1
            assert not fit.extrapolating((low + high) / 2)
            assert fit.extrapolating(high + 0.05)


def test_the_speed_survives_a_round_trip():
    from chesscoach.profile.io import from_dict, to_dict
    from chesscoach.profile.models import CorpusRef, PlayerProfile, PlayerRef, Strength

    profile = PlayerProfile(
        player=PlayerRef(source="lichess", username="alice"),
        corpus=CorpusRef(corpus_id="c1", n_games=59),
        strength=Strength(
            rating=1645, typical_error=123, moves=1411, method="blunder_rate", speed="blitz"
        ),
    )

    assert from_dict(to_dict(profile)).strength.speed == "blitz"
