"""Freeze the strong-player expectation into a data file the swarm can load.

Design: docs/notes/design.opening-development-signals.md

The expectation is 5,917 games; recomputing it per player would be absurd, so it
is reduced once to a median per (family, colour) and shipped beside the opening
book. Same shape as `book.json`: a load format, not a query format.

The corpus itself is gitignored and refetchable via `fetch_strong.py`, so this
file is the reproducible artefact of it -- and it records the provenance, because
a threshold whose origin is not written down becomes folklore the moment nobody
remembers where it came from.

    python experiments/e58-opening-development/build_norms.py
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import defaultdict

import chess
import chess.pgn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.development import measure_development  # noqa: E402
from chesscoach.development_norms import DEFAULT_NORMS, survival_median  # noqa: E402
from chesscoach.openings import OpeningBook, _family  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
STRONG = ROOT / "data" / "raw" / "corpus-strong"


class Cell:
    def __init__(self) -> None:
        self.castled: list[int] = []
        self.ready: list[int] = []
        self.never_castled = 0
        self.incomplete = 0
        self.games = 0

    def add(self, d) -> None:
        self.games += 1
        if d.castled_at is None:
            self.never_castled += 1
        else:
            self.castled.append(d.castled_at)
        if d.ready_at is None:
            self.incomplete += 1
        else:
            self.ready.append(d.ready_at)


def main() -> int:
    if not STRONG.exists():
        print(f"no strong corpus at {STRONG}; run fetch_strong.py first")
        return 1

    book = OpeningBook.load()
    cells: dict[tuple[str, bool], Cell] = defaultdict(Cell)
    games = players = 0

    for path in sorted(STRONG.glob("*.pgn")):
        players += 1
        with path.open(encoding="utf-8", errors="replace") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if "FEN" in game.headers:
                    continue
                if game.headers.get("Variant", "Standard") != "Standard":
                    continue
                try:
                    played = list(game.mainline_moves())
                except (ValueError, AssertionError):
                    continue
                if len(played) < 8:
                    continue
                walk = book.walk([m.uci() for m in played])
                if walk.opening is None:
                    continue
                games += 1
                family = _family(walk.opening.name)
                for colour in (chess.WHITE, chess.BLACK):
                    cells[(family, colour)].add(measure_development(played, colour))

    rows = []
    for (family, colour), cell in sorted(cells.items()):
        rows.append({
            "family": family,
            "colour": "white" if colour else "black",
            "castle_ply": survival_median(cell.castled, cell.never_castled),
            "ready_ply": survival_median(cell.ready, cell.incomplete),
            "games": cell.games,
        })

    manifest = json.loads((STRONG / "manifest.json").read_text(encoding="utf-8"))
    DEFAULT_NORMS.write_text(
        json.dumps(
            {
                "source": "lichess rapid leaderboard, top 100",
                "rating_range": manifest["rating_range"],
                "players": players,
                "games": games,
                "note": "medians are survival medians: a game that never got "
                        "there sorts after every game that did",
                "norms": rows,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    usable = sum(1 for r in rows if r["games"] >= 20)
    print(f"{games} games, {players} players -> {len(rows)} cells "
          f"({usable} with 20+ games) -> {DEFAULT_NORMS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
