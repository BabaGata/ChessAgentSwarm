"""Ask the detectors, position by position, about the rows the author rejected.

Screen: docs/notes/experiments.e55-detector-precision.md

`carry_marks.py` says which marked rows are no longer on the sheet. That is
**not** the same as fixed: the sheet samples five instances of each claim, so a
row leaves it either because the detector stopped firing there or because the
sample reshuffled when the pool changed. Both look identical in a diff, and
reading one as the other is how a fix gets claimed that never happened.

This settles it the only way that settles it -- by reconstructing each rejected
position from the game and asking `detect_motifs` again.

Every motif row on the sheet names the move that executes it in SAN, which is
what makes this cheap:

    [n] Crossfire1983  move 36 Black Nd7  lost 25.1 wp
        lichess.org/SuvK6tPc#72
        was available Rd1+ -- forker rd1, target Bb1, target Kg1

For a **missed** motif the named move is the player's alternative in the same
position. For an **allowed** one it is the opponent's reply, so the played move
goes on the board first. Either way the question is one call and no engine.

Only motif claims are checked. `out_of_book`, `late_castling` and the rest are
whole-game judgements with no single move to re-ask about, and pretending
otherwise would answer a question this cannot see.

Usage:
    python recheck.py --sheet MARKED.txt [--only n]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import chess
import chess.pgn

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.tactics import detect_motifs  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

ROW = re.compile(
    r"^  \[([yn?]?)\s*\]\s+(\S+)\s+move\s+(\d+)\s+(White|Black)\s+(\S+)\s+lost"
)
LINK = re.compile(r"^\s+lichess\.org/(\S+)#(\d+)\s*$")
EXECUTES = re.compile(r"^\s+(?:punished by|was available) (\S+)")


def positions(path: Path):
    """(mark, claim, player, game_id, ply, played_san, motif_san) per motif row."""
    claim = player = None
    row = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith(" ") and not line.startswith("-") \
                and "." in line.split()[0]:
            claim = line.strip()
            continue
        match = ROW.match(line)
        if match and claim:
            row = {"mark": (match.group(1) or "").strip(), "claim": claim,
                   "player": match.group(2), "played": match.group(5),
                   "game": None, "ply": None, "motif_move": None}
            continue
        if row is None:
            continue
        link = LINK.match(line)
        if link:
            row["game"], row["ply"] = link.group(1), int(link.group(2))
            continue
        executes = EXECUTES.match(line)
        if executes and row["game"]:
            row["motif_move"] = executes.group(1)
            yield row
            row = None


def board_at(game_id: str, ply: int) -> tuple[chess.Board, chess.pgn.Game] | tuple[None, None]:
    """The position with `ply` plies played, with its move stack intact.

    The stack matters: `_is_recapture` needs one ply of history, and a board
    built from a bare FEN cannot answer it -- which would make every recapture
    look like a fresh hanging piece and quietly undo the thing being checked.
    """
    for path in sorted(GAMES.glob("*.pgn")):
        with open(path, encoding="utf-8", errors="ignore") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                site = game.headers.get("Site", "")
                if not site.endswith("/" + game_id):
                    continue
                board = game.board()
                for index, move in enumerate(game.mainline_moves()):
                    if index >= ply:
                        break
                    board.push(move)
                return board, game
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--only", default="n", help="marks to re-check (default: n)")
    args = parser.parse_args()

    wanted = set(args.only)
    checked = still = moved = unreachable = 0

    print(f"{'verdict':10s} {'claim':38s} link")
    print("-" * 96)
    for row in positions(args.sheet):
        if row["mark"] not in wanted:
            continue
        claim = row["claim"]
        kind = claim.split(".")[0]
        motif = claim.split(".")[1]
        # The sheet's ply is the player's move: `#72` is the position *after*
        # 71 plies, with the player to move.
        board, _ = board_at(row["game"], row["ply"] - 1)
        if board is None:
            print(f"{'no game':10s} {claim:38s} lichess.org/{row['game']}#{row['ply']}")
            unreachable += 1
            continue

        if kind == "allowed_motif":
            # The motif is the opponent's reply, so the player's move goes on
            # the board first.
            try:
                board.push(board.parse_san(row["played"]))
            except ValueError:
                print(f"{'no move':10s} {claim:38s} lichess.org/{row['game']}#{row['ply']}")
                unreachable += 1
                continue
        try:
            move = board.parse_san(row["motif_move"])
        except ValueError:
            print(f"{'no move':10s} {claim:38s} lichess.org/{row['game']}#{row['ply']}")
            unreachable += 1
            continue

        found = {str(m) for m in detect_motifs(board, move)}
        checked += 1
        if motif in found:
            still += 1
            verdict = "STILL"
        else:
            moved += 1
            verdict = "gone"
        others = ", ".join(sorted(found - {motif})) or "nothing"
        print(f"{verdict:10s} {claim:38s} lichess.org/{row['game']}#{row['ply']}"
              f"  now: {others if verdict == 'gone' else 'unchanged'}")

    print()
    print(f"re-checked {checked} rejected rows: "
          f"**{moved} no longer fire**, {still} still do"
          + (f", {unreachable} unreachable" if unreachable else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
