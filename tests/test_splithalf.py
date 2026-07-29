"""Split-half replication: does a measurement reproduce on the player's other games?

This is evaluation metric B1 and, at the same time, a runtime promotion rule in
architecture.confidence -- built once, used twice.

It exists because of a specific failure: E03 found an effect with lift 2.40 and a
tidy mechanism that reversed to 0.76 on held-out players (L-008). A plausible
mechanism is not evidence; it is what makes an artefact convincing.
"""

from __future__ import annotations

from chesscoach.evaluation.splithalf import split_games, split_half_check


def measure_from(counts: dict[str, tuple[int, int]]):
    """Build a measure function from a game_id -> (successes, trials) mapping."""

    def measure(game_ids):
        successes = sum(counts[game_id][0] for game_id in game_ids)
        trials = sum(counts[game_id][1] for game_id in game_ids)
        return successes, trials

    return measure


class TestSplitGames:
    def test_splits_into_two_halves(self):
        first, second = split_games(["g1", "g2", "g3", "g4"])

        assert len(first) == 2
        assert len(second) == 2

    def test_is_deterministic_and_order_independent(self):
        forwards = split_games(["g1", "g2", "g3", "g4"])
        backwards = split_games(["g4", "g3", "g2", "g1"])

        assert forwards == backwards

    def test_puts_every_game_in_exactly_one_half(self):
        games = [f"g{n}" for n in range(9)]

        first, second = split_games(games)

        assert sorted(first + second) == sorted(games)
        assert not set(first) & set(second)

    def test_handles_an_odd_number_of_games(self):
        first, second = split_games(["g1", "g2", "g3"])

        assert len(first) + len(second) == 3


class TestSplitHalfCheck:
    def test_a_consistent_effect_replicates(self):
        counts = {f"g{n}": (2, 10) for n in range(10)}

        result = split_half_check(list(counts), measure_from(counts))

        assert result.replicated is True
        assert result.intervals_overlap is True

    def test_an_effect_present_in_only_one_half_does_not_replicate(self):
        # Every odd game shows the pattern strongly, every even game not at all.
        counts = {f"g{n}": ((9, 10) if n % 2 else (0, 10)) for n in range(20)}

        result = split_half_check(list(counts), measure_from(counts))

        assert result.replicated is False
        assert result.intervals_overlap is False

    def test_requires_both_halves_on_the_same_side_of_a_reference(self):
        # Both halves have wide overlapping intervals, but straddle the peer rate.
        counts = {f"g{n}": ((4, 10) if n % 2 else (1, 10)) for n in range(8)}

        result = split_half_check(list(counts), measure_from(counts), reference_rate=0.25)

        assert result.same_side_of_reference is False
        assert result.replicated is False

    def test_reports_both_halves_rates(self):
        counts = {f"g{n}": (3, 10) for n in range(6)}

        result = split_half_check(list(counts), measure_from(counts))

        assert result.first.rate == 0.3
        assert result.second.rate == 0.3

    def test_refuses_to_conclude_from_too_few_games(self):
        counts = {"g1": (1, 5), "g2": (1, 5)}

        result = split_half_check(list(counts), measure_from(counts), min_games_per_half=3)

        assert result.replicated is False
        assert result.insufficient_data is True

    def test_is_deterministic(self):
        counts = {f"g{n}": (n % 3, 10) for n in range(12)}

        first = split_half_check(list(counts), measure_from(counts))
        second = split_half_check(list(counts)[::-1], measure_from(counts))

        assert first == second
