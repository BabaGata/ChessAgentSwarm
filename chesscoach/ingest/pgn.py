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

    def player_is_white(self, username: str) -> bool:
        return self.white.lower() == username.lower()

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
    )


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
