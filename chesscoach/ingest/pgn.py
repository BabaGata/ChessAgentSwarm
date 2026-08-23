"""PGN parsing into game records.

Clock readings are extracted alongside the moves. That is not an optional extra:
S2 (decision process and clock behaviour) is the first agent to be built, and it
needs the clock more than it needs the engine.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import chess.pgn

STANDARD_VARIANT = "Standard"


def increment_seconds(time_control: str | None) -> float:
    """Seconds credited to the mover's clock after each move.

    Zero for an unreadable or absent tag rather than None: the increment is used
    to *correct* a time, and a missing correction has to be the identity, not a
    propagating unknown that disables the fix for the games that need it.
    """
    if not time_control or "+" not in time_control:
        return 0.0
    _, _, increment = time_control.partition("+")
    try:
        return max(0.0, float(increment))
    except ValueError:
        return 0.0


@dataclass(frozen=True)
class GameRecord:
    """One game, reduced to what the analysis core and the sections need."""

    game_id: str
    white: str
    black: str
    result: str
    moves: tuple[str, ...]
    clocks: tuple[float | None, ...]
    time_control: str | None = None
    white_elo: int | None = None
    black_elo: int | None = None
    eco: str | None = None
    opening: str | None = None
    date: str | None = None
    # How the game ended -- "Normal", "Time forfeit", "Abandoned". Read so the
    # corpus can leave out games nobody actually played.
    termination: str | None = None
    # Arena chess: a player may halve their own clock for an extra point. It is
    # recorded per side because only the player who did it was handicapped.
    white_berserk: bool = False
    black_berserk: bool = False

    def player_is_white(self, username: str) -> bool:
        return self.white.lower() == username.lower()

    def berserked_by(self, username: str) -> bool:
        """Did *this* player halve their own clock?

        The opponent doing it does not contaminate the player's own decisions:
        their clock was untouched, and dropping the game would discard evidence
        to correct someone else's handicap.
        """
        return self.white_berserk if self.player_is_white(username) else self.black_berserk

    def involves(self, username: str) -> bool:
        return username.lower() in (self.white.lower(), self.black.lower())


def parse_pgn_text(text: str) -> tuple[GameRecord, ...]:
    """Parse every standard game in a PGN string, skipping variants."""
    handle = io.StringIO(text)
    records: list[GameRecord] = []

    while True:
        game = chess.pgn.read_game(handle)
        if game is None:
            break
        record = _to_record(game)
        if record is not None:
            records.append(record)

    return tuple(records)


def parse_pgn_file(path: Path | str) -> tuple[GameRecord, ...]:
    return parse_pgn_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def parse_pgn_dir(directory: Path | str) -> tuple[GameRecord, ...]:
    """Parse every .pgn file in a directory, in a stable order."""
    records: list[GameRecord] = []
    for path in sorted(Path(directory).glob("*.pgn")):
        records.extend(parse_pgn_file(path))
    return tuple(records)


def _to_record(game: chess.pgn.Game) -> GameRecord | None:
    headers = game.headers
    if headers.get("Variant", STANDARD_VARIANT) != STANDARD_VARIANT:
        return None

    moves: list[str] = []
    clocks: list[float | None] = []
    for node in game.mainline():
        moves.append(node.move.uci())
        clocks.append(node.clock())

    if not moves:
        return None

    return GameRecord(
        game_id=_game_id(headers),
        white=headers.get("White", "?"),
        black=headers.get("Black", "?"),
        result=headers.get("Result", "*"),
        moves=tuple(moves),
        clocks=tuple(clocks),
        time_control=headers.get("TimeControl"),
        white_elo=_int_or_none(headers.get("WhiteElo")),
        black_elo=_int_or_none(headers.get("BlackElo")),
        eco=headers.get("ECO"),
        opening=headers.get("Opening"),
        date=headers.get("UTCDate") or headers.get("Date"),
        termination=headers.get("Termination"),
        white_berserk=_is_true(headers.get("WhiteBerserk")),
        black_berserk=_is_true(headers.get("BlackBerserk")),
    )


def _is_true(value: str | None) -> bool:
    """Lichess writes `[WhiteBerserk "true"]`, and omits the tag otherwise."""
    return (value or "").strip().lower() == "true"


def _game_id(headers: chess.pgn.Headers) -> str:
    """Prefer the explicit id; fall back to the site URL's last segment."""
    game_id = headers.get("GameId")
    if game_id:
        return game_id
    site = headers.get("Site", "")
    return site.rstrip("/").rsplit("/", 1)[-1] if site else "unknown"


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None
