"""What does the two-ply search buy, on top of the screen that came first?

Note: docs/notes/experiments.e74-rook-seventh-precise.md
Design: docs/notes/design.detectors-name-consequences.md § 4

[[experiments.e66-rook-seventh-and-doubled]] built the cheap half of the author's
correction -- three or more open files and nobody could have stopped it -- and
measured it removing **52 %** of firings. The design note had said the precise
search would be unnecessary only if the cheap one removed *most*. Half is not
most, so the search was still owed. This measures what it adds.

Three arms over the same transitions:

    raw        a rook arrived on the player's seventh
    screened   ... and fewer than three files were open (E66's rule, shipped)
    precise    ... and some legal move of the player's would have stopped it

**No engine.** Preventability is a question about legal moves, so the games are
replayed directly and the corpus can be large.

The transition is the one `squares.allowed` uses: the position before the
player's move, and the position after the opponent's reply. A rook arrives on the
opponent's turn, so comparing across the player's move alone finds almost
nothing -- the mistake E09 made.

    python run.py [--corpus data/raw/corpus-rapid] [--players 40]
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.pipeline import load_games  # noqa: E402
from chesscoach.squares import (  # noqa: E402
    OPEN_FILES_UNPREVENTABLE,
    _rooks_on_seventh,
    open_files,
    rook_seventh_preventable,
)

REPO = Path(__file__).resolve().parents[2]


def transitions(game, player: str):
    """(before, after) around each of the player's moves, and their colour.

    `before` is the position with the player to move; `after` is the position
    once the opponent has answered. A game that ends on the player's move has no
    answer and contributes nothing, which is correct -- nothing was allowed.
    """
    white = (game.white or "").lower() == player.lower()
    colour = chess.WHITE if white else chess.BLACK
    board = chess.Board()
    positions = [board.copy(stack=False)]
    # `GameRecord.moves` is UCI (`ingest/pgn.py` stores `node.move.uci()`). A
    # first version pushed them as SAN and happened to be correct, because
    # python-chess's SAN parser also accepts long algebraic -- right answer,
    # wrong reason. Saying UCI is what the data is makes the next reader safe.
    for uci in game.moves:
        try:
            board.push_uci(uci)
        except ValueError:
            break
        positions.append(board.copy(stack=False))

    start = 0 if white else 1
    for index in range(start, len(positions) - 2, 2):
        yield positions[index], positions[index + 2], colour


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/raw/corpus-rapid")
    parser.add_argument("--players", type=int, default=40)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    paths = sorted((REPO / args.corpus).glob("*.pgn"))[: args.players]
    raw = screened = precise = 0
    seen_transitions = 0
    open_when_arrived: Counter = Counter()
    search_seconds = 0.0
    searches = 0
    # A sample of what the search newly REMOVES, so the rule can be read
    # against positions rather than trusted. E66's stated gap.
    removed_sample: list[tuple[str, str, int]] = []

    for index, path in enumerate(paths, 1):
        player = path.stem
        for game in load_games(path):
            for before, after, colour in transitions(game, player):
                seen_transitions += 1
                had = _rooks_on_seventh(before, colour)
                now = _rooks_on_seventh(after, colour)
                if now <= had:
                    continue
                raw += 1
                opened = open_files(before)
                open_when_arrived[opened] += 1
                if opened >= OPEN_FILES_UNPREVENTABLE:
                    continue
                screened += 1
                started = time.perf_counter()
                could_have = rook_seventh_preventable(before, colour)
                search_seconds += time.perf_counter() - started
                searches += 1
                if could_have:
                    precise += 1
                elif len(removed_sample) < 12:
                    removed_sample.append((player, before.fen(), opened))
        if index % 10 == 0:
            print(f"  {index}/{len(paths)} players, {raw} arrivals", flush=True)

    def pct(part: int, whole: int) -> str:
        return f"{part / whole:.0%}" if whole else "—"

    lines = [
        "WHAT THE TWO-PLY SEARCH BUYS ON TOP OF THE SCREEN",
        "=" * 82, "",
        f"corpus {args.corpus}, {len(paths)} players, "
        f"{seen_transitions:,} player moves with an answer.",
        "",
        "  A rook ARRIVING on the player's seventh, not merely standing there:",
        "",
        f"  {'arrivals':<44}{raw:>8}",
        f"  {'screened out (>= 3 open files)':<44}{raw - screened:>8}   {pct(raw - screened, raw)}",
        f"  {'survive the screen':<44}{screened:>8}   {pct(screened, raw)}",
        f"  {'... and were preventable (still fire)':<44}{precise:>8}   {pct(precise, raw)}",
        f"  {'... and were NOT (newly removed)':<44}{screened - precise:>8}   "
        f"{pct(screened - precise, raw)}",
        "",
        "=" * 82, "",
        f"  the screen removed        {pct(raw - screened, raw)} of arrivals",
        f"  the search removes a further {pct(screened - precise, raw)} of arrivals,",
        f"                              {pct(screened - precise, screened)} of what "
        f"reached it",
        f"  the claim now fires on    {pct(precise, raw)} of arrivals",
        "",
        "  open files when a rook arrived:",
        f"    {dict(sorted(open_when_arrived.items()))}",
        "",
        "  cost (C1): the search is deterministic and runs only on arrivals that",
        "  survive the screen.",
        f"    searches run        {searches:,}",
        f"    total time          {search_seconds:.1f} s",
        f"    per search          {search_seconds / searches * 1000:.1f} ms"
        if searches else "    per search          —",
        "",
    ]

    sample = [
        "POSITIONS THE SEARCH NEWLY REMOVES",
        "=" * 82, "",
        "Each is a position where a rook DID arrive on the player's seventh, with",
        "fewer than three files open, and where no legal move of the player's",
        "would have stopped it. The claim used to fire on every one of these.",
        "",
        "Paste a FEN into any board. The question is the author's own: was there",
        "a real opportunity to block the rook from coming to the seventh?",
        "",
    ]
    for player, fen, opened in removed_sample:
        sample += [f"  {player}   {opened} open file(s)", f"    {fen}", ""]
    (args.out / "removed-sample.txt").write_text("\n".join(sample) + "\n", encoding="utf-8")

    text = "\n".join(lines) + "\n"
    (args.out / "precise.txt").write_text(text, encoding="utf-8")
    print()
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
