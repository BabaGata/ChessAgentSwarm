"""Planted-weakness generation: games whose flaw is known by construction.

The only route to actual ground truth that costs nothing (evaluation family C).
An agent can then be asked two questions that matter equally: does it find the
planted weakness, and does it refrain from inventing others?
"""

from __future__ import annotations

import chess

import pytest

from chesscoach.evaluation.planted import (
    PlantedGame,
    TimeModel,
    WeaknessSpec,
    generate_games,
    total_spoiled,
    write_eval_set,
)


class ScriptedChooser:
    """No engine. Varies its choice by ply so games do not repeat into a quick draw."""

    def best(self, board: chess.Board) -> chess.Move:
        moves = sorted(board.legal_moves, key=lambda m: m.uci())
        return moves[len(board.move_stack) % len(moves)]

    def inferior(self, board: chess.Board, rng) -> chess.Move:
        return sorted(board.legal_moves, key=lambda m: m.uci())[-1]


def a_spec(**overrides) -> WeaknessSpec:
    defaults = dict(kind="time_pressure", severity=1.0, threshold_seconds=120.0)
    return WeaknessSpec(**{**defaults, **overrides})


def a_time_model() -> TimeModel:
    """A clock that actually reaches time pressure inside a short test game."""
    return TimeModel(initial_seconds=300, normal_think=6, slow_think=30, slow_until_ply=200)


class TestGeneration:
    def test_generates_the_requested_number_of_games(self):
        games = generate_games(ScriptedChooser(), a_spec(), n_games=3, seed=1, max_plies=20)

        assert len(games) == 3

    def test_every_game_is_parseable_pgn_with_clocks(self):
        from chesscoach.ingest.pgn import parse_pgn_text

        games = generate_games(ScriptedChooser(), a_spec(), n_games=2, seed=1, max_plies=20)

        parsed = parse_pgn_text("\n\n".join(g.pgn for g in games))
        assert len(parsed) == 2
        assert all(clock is not None for clock in parsed[0].clocks)

    def test_records_which_plies_were_deliberately_spoiled(self):
        games = generate_games(
            ScriptedChooser(), a_spec(), n_games=1, seed=1, max_plies=40, time_model=a_time_model()
        )

        assert isinstance(games[0], PlantedGame)
        assert len(games[0].spoiled_plies) > 0

    def test_only_the_flawed_player_is_spoiled(self):
        games = generate_games(
            ScriptedChooser(), a_spec(), n_games=1, seed=1, max_plies=40, time_model=a_time_model()
        )
        game = games[0]

        # The flawed player is White, so spoiled plies are odd-numbered (1-based).
        assert game.flawed_is_white is True
        assert all(ply % 2 == 1 for ply in game.spoiled_plies)

    def test_a_zero_severity_spec_plants_nothing(self):
        games = generate_games(
            ScriptedChooser(), a_spec(severity=0.0), n_games=2, seed=1, max_plies=40
        )

        assert all(game.spoiled_plies == () for game in games)

    def test_generation_is_reproducible_from_the_seed(self):
        first = generate_games(ScriptedChooser(), a_spec(severity=0.5), n_games=2, seed=7, max_plies=30)
        second = generate_games(ScriptedChooser(), a_spec(severity=0.5), n_games=2, seed=7, max_plies=30)

        assert [g.pgn for g in first] == [g.pgn for g in second]
        assert [g.spoiled_plies for g in first] == [g.spoiled_plies for g in second]

    def test_a_different_seed_produces_different_games(self):
        first = generate_games(
            ScriptedChooser(), a_spec(severity=0.5), n_games=2, seed=1, max_plies=40,
            time_model=a_time_model(),
        )
        second = generate_games(
            ScriptedChooser(), a_spec(severity=0.5), n_games=2, seed=2, max_plies=40,
            time_model=a_time_model(),
        )

        assert [g.spoiled_plies for g in first] != [g.spoiled_plies for g in second]

    def test_reports_how_much_was_actually_planted(self):
        games = generate_games(
            ScriptedChooser(), a_spec(), n_games=2, seed=1, max_plies=40, time_model=a_time_model()
        )

        assert total_spoiled(games) == sum(len(g.spoiled_plies) for g in games)


class TestBackgroundNoise:
    def test_a_flawed_player_also_errs_outside_the_trigger(self):
        # Otherwise the player is perfect except in exactly one condition, which
        # is far easier to discriminate than any real player.
        spec = a_spec(kind="phase", phase="endgame", severity=1.0, background_severity=1.0)

        assert spec.rate_at(clock_seconds=300, phase="opening_middlegame", ply=4) == 1.0

    def test_background_noise_is_not_counted_as_the_planted_weakness(self):
        # An agent must not be credited for finding the noise.
        spec = a_spec(kind="phase", phase="endgame", severity=0.0, background_severity=1.0)

        games = generate_games(
            ScriptedChooser(), spec, n_games=1, seed=3, max_plies=30, time_model=a_time_model()
        )

        assert games[0].spoiled_plies == ()

    def test_defaults_to_no_background_noise(self):
        assert a_spec().background_severity == 0.0


class TestTriggers:
    def test_time_pressure_only_fires_when_the_clock_is_low(self):
        spec = a_spec(kind="time_pressure", threshold_seconds=60.0)

        assert spec.triggers(clock_seconds=30.0, phase="endgame", ply=40) is True
        assert spec.triggers(clock_seconds=300.0, phase="endgame", ply=40) is False

    def test_phase_weakness_only_fires_in_its_phase(self):
        spec = WeaknessSpec(kind="phase", severity=1.0, phase="endgame")

        assert spec.triggers(clock_seconds=300.0, phase="endgame", ply=60) is True
        assert spec.triggers(clock_seconds=300.0, phase="opening_middlegame", ply=10) is False

    def test_a_uniform_weakness_always_fires(self):
        spec = WeaknessSpec(kind="uniform", severity=1.0)

        assert spec.triggers(clock_seconds=300.0, phase="late_middlegame", ply=25) is True


class TestTimeModel:
    def test_the_flawed_player_burns_time_early_and_reaches_pressure(self):
        model = TimeModel(initial_seconds=300, normal_think=5, slow_think=30, slow_until_ply=16)

        remaining = model.remaining_after(ply=16, flawed=True)

        assert remaining < model.initial_seconds / 2

    def test_the_baseline_player_does_not(self):
        model = TimeModel(initial_seconds=300, normal_think=5, slow_think=30, slow_until_ply=16)

        assert model.remaining_after(ply=16, flawed=False) > model.initial_seconds / 2

    def test_the_clock_never_goes_negative(self):
        model = TimeModel(initial_seconds=60, normal_think=30, slow_think=30, slow_until_ply=2)

        assert model.remaining_after(ply=200, flawed=True) >= 0.0


class TestEvalSet:
    def test_writes_pgn_and_ground_truth(self, tmp_path):
        games = generate_games(
            ScriptedChooser(), a_spec(), n_games=2, seed=1, max_plies=40, time_model=a_time_model()
        )

        truth_path = write_eval_set(games, a_spec(), tmp_path)

        assert (tmp_path / "planted.pgn").exists()
        assert truth_path.exists()

    def test_ground_truth_records_the_spec_and_every_game(self, tmp_path):
        import json

        games = generate_games(
            ScriptedChooser(), a_spec(), n_games=2, seed=1, max_plies=40, time_model=a_time_model()
        )

        truth = json.loads(write_eval_set(games, a_spec(), tmp_path).read_text(encoding="utf-8"))

        assert truth["spec"]["kind"] == "time_pressure"
        assert len(truth["games"]) == 2

    def test_refuses_to_write_a_set_where_nothing_was_planted(self, tmp_path):
        # An empty eval set would make any agent look like it failed, when in
        # fact there was nothing to find. Fail loudly instead.
        games = generate_games(ScriptedChooser(), a_spec(), n_games=1, seed=1, max_plies=6)

        with pytest.raises(ValueError, match="nothing was planted"):
            write_eval_set(games, a_spec(), tmp_path)

    def test_allows_an_empty_set_when_the_spec_plants_nothing(self, tmp_path):
        # severity 0 is a deliberate control condition, not a mistake.
        spec = a_spec(severity=0.0)
        games = generate_games(ScriptedChooser(), spec, n_games=1, seed=1, max_plies=20)

        assert write_eval_set(games, spec, tmp_path).exists()
