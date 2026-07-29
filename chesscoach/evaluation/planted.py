"""Games whose weakness is known by construction.

Evaluation family C: the only route to actual ground truth that costs nothing.
Two players are simulated; one of them plays a deliberately inferior move
whenever a trigger condition holds. The trigger *is* the weakness, so the
correct answer is known exactly, and an agent can be asked both questions that
matter: does it find the planted flaw, and does it refrain from inventing others?

The move chooser is injected, so generation runs with a real engine or with a
scripted stub. Everything is seeded, so an evaluation set is reproducible.

The honest limitation, recorded in docs/notes/evaluation.md: an engine told to
play badly does not fail the way a human fails. This tests the detector, not the
coaching.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import chess
import chess.pgn

DEFAULT_MAX_PLIES = 120
FLAWED_PLAYER = "planted_flaw"
BASELINE_PLAYER = "baseline"


class MoveChooser(Protocol):
    """Supplies a good move and a deliberately worse one."""

    def best(self, board: chess.Board) -> chess.Move: ...

    def inferior(self, board: chess.Board, rng: random.Random) -> chess.Move: ...


@dataclass(frozen=True)
class TimeModel:
    """A simulated clock, so time-pressure weaknesses can be planted at all.

    The flawed player deliberately burns time early, which is how it arrives in
    time trouble later without that being scripted directly.
    """

    initial_seconds: float = 600.0
    increment: float = 0.0
    normal_think: float = 6.0
    slow_think: float = 25.0
    slow_until_ply: int = 20

    def remaining_after(self, ply: int, flawed: bool) -> float:
        """Clock remaining for that player after their `ply`-th half-move."""
        own_moves = (ply + 1) // 2
        spent = 0.0
        for move_number in range(1, own_moves + 1):
            in_slow_phase = flawed and move_number * 2 <= self.slow_until_ply
            spent += self.slow_think if in_slow_phase else self.normal_think
            spent -= self.increment
        return max(0.0, self.initial_seconds - spent)


@dataclass(frozen=True)
class WeaknessSpec:
    """What is wrong with the flawed player, and when it shows.

    `background_severity` is the rate of ordinary mistakes made when the trigger
    is *not* firing. Without it the flawed player is perfect except in exactly
    the planted condition, which is far easier to discriminate than any real
    player and would flatter any agent measured against it.
    """

    kind: str  # "time_pressure" | "phase" | "uniform"
    severity: float  # probability of an inferior move when triggered
    threshold_seconds: float = 60.0  # time_pressure
    phase: str = "endgame"  # phase
    background_severity: float = 0.0

    def rate_at(self, *, clock_seconds: float, phase: str, ply: int) -> float:
        """Probability of an inferior move in this position."""
        if self.triggers(clock_seconds=clock_seconds, phase=phase, ply=ply):
            return self.severity
        return self.background_severity

    def triggers(self, *, clock_seconds: float, phase: str, ply: int) -> bool:
        """Is the weakness's condition met in this position?"""
        if self.kind == "time_pressure":
            return clock_seconds <= self.threshold_seconds
        if self.kind == "phase":
            return phase == self.phase
        if self.kind == "uniform":
            return True
        raise ValueError(f"unknown weakness kind {self.kind!r}")


@dataclass(frozen=True)
class PlantedGame:
    """One generated game and the truth about it."""

    game_id: str
    pgn: str
    flawed_is_white: bool
    spoiled_plies: tuple[int, ...]
    n_plies: int


def generate_games(
    chooser: MoveChooser,
    spec: WeaknessSpec,
    n_games: int,
    seed: int = 0,
    time_model: TimeModel | None = None,
    max_plies: int = DEFAULT_MAX_PLIES,
) -> tuple[PlantedGame, ...]:
    """Generate an evaluation set carrying exactly one known weakness."""
    model = time_model or TimeModel()
    return tuple(
        _generate_one(chooser, spec, model, max_plies, index, random.Random(seed * 1000 + index))
        for index in range(n_games)
    )


def _generate_one(
    chooser: MoveChooser,
    spec: WeaknessSpec,
    model: TimeModel,
    max_plies: int,
    index: int,
    rng: random.Random,
) -> PlantedGame:
    from chesscoach.analysis.core import phase_of

    board = chess.Board()
    flawed_is_white = True  # fixed, so ground truth stays trivially checkable
    spoiled: list[int] = []
    moves: list[chess.Move] = []
    clocks: list[float] = []

    while not board.is_game_over(claim_draw=True) and len(moves) < max_plies:
        ply = len(moves) + 1
        mover_is_flawed = (board.turn == chess.WHITE) == flawed_is_white
        clock = model.remaining_after(ply, flawed=mover_is_flawed)

        position_phase = phase_of(board)
        triggered = mover_is_flawed and spec.triggers(
            clock_seconds=clock, phase=position_phase, ply=ply
        )
        rate = (
            spec.rate_at(clock_seconds=clock, phase=position_phase, ply=ply)
            if mover_is_flawed
            else 0.0
        )
        plays_badly = rng.random() < rate

        move = chooser.inferior(board, rng) if plays_badly else chooser.best(board)
        # Only trigger-driven mistakes are the planted weakness; background
        # mistakes are noise, and counting them as ground truth would make the
        # fixture score an agent for finding the noise.
        if plays_badly and triggered:
            spoiled.append(ply)

        moves.append(move)
        clocks.append(clock)
        board.push(move)

    game_id = f"planted{index:04d}"
    return PlantedGame(
        game_id=game_id,
        pgn=_to_pgn(game_id, moves, clocks, flawed_is_white, board),
        flawed_is_white=flawed_is_white,
        spoiled_plies=tuple(spoiled),
        n_plies=len(moves),
    )


def _to_pgn(
    game_id: str,
    moves: list[chess.Move],
    clocks: list[float],
    flawed_is_white: bool,
    final_board: chess.Board,
) -> str:
    game = chess.pgn.Game()
    game.headers["Event"] = "Planted evaluation set"
    game.headers["Site"] = f"planted/{game_id}"
    game.headers["GameId"] = game_id
    game.headers["White"] = FLAWED_PLAYER if flawed_is_white else BASELINE_PLAYER
    game.headers["Black"] = BASELINE_PLAYER if flawed_is_white else FLAWED_PLAYER
    game.headers["TimeControl"] = "600+0"
    game.headers["Variant"] = "Standard"
    game.headers["Result"] = final_board.result(claim_draw=True)

    node: chess.pgn.GameNode = game
    for move, clock in zip(moves, clocks):
        node = node.add_variation(move)
        node.set_clock(clock)

    return game.accept(chess.pgn.StringExporter(headers=True, variations=False, comments=True))


def total_spoiled(games: tuple[PlantedGame, ...]) -> int:
    """How many moves were actually spoiled across the set."""
    return sum(len(game.spoiled_plies) for game in games)


def write_eval_set(games: tuple[PlantedGame, ...], spec: WeaknessSpec, directory: Path | str) -> Path:
    """Write the games and the ground truth beside each other.

    Refuses to write a set in which nothing was planted despite a non-zero
    severity. Such a set would make any agent look like it had failed when in
    fact there was nothing to find -- the trigger simply never fired, most often
    because the time model never reaches pressure inside the game length. A
    severity of zero is a deliberate control condition and is allowed through.
    """
    if spec.severity > 0 and total_spoiled(games) == 0:
        raise ValueError(
            "nothing was planted: the weakness trigger never fired. "
            "Check the time model, game length and threshold against the spec."
        )

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    (directory / "planted.pgn").write_text(
        "\n\n".join(game.pgn for game in games) + "\n", encoding="utf-8"
    )

    truth_path = directory / "ground_truth.json"
    truth_path.write_text(
        json.dumps(
            {
                "spec": asdict(spec),
                "flawed_player": FLAWED_PLAYER,
                "games": [
                    {
                        "game_id": game.game_id,
                        "flawed_is_white": game.flawed_is_white,
                        "spoiled_plies": list(game.spoiled_plies),
                        "n_plies": game.n_plies,
                    }
                    for game in games
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return truth_path
