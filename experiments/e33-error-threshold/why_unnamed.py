"""Why does naming fail? Two failure modes need opposite fixes.

  A. NO MOTIF AT ALL     the eight patterns do not cover the position
  B. A DIFFERENT MOTIF   the swarm named the mechanism, the reviewer the outcome

And a third possibility the current design cannot even express:

  C. the property is of the PLAYED move, not of the best move or the reply.
     `_count_available` detects motifs on the ENGINE's move; `_count_allowed`
     on the opponent's best reply. Nothing looks at what the player actually
     played -- so "placing a piece on the attacked square" has nowhere to land.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm")
sys.path.insert(0, r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm\experiments\e31-move-level-agreement")

import chess

from compare import expected_signals, parse_notes

from chesscoach.analysis.core import analyse_corpus
from chesscoach.ingest.corpus import build_corpus
from chesscoach.phrasing import move_number  # noqa: E402
from chesscoach.pipeline import engine_session, load_games
from chesscoach.tactics import detect_motifs

ROOT = Path(r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm\expert-review")
ENGINE = r"C:\stockfish\stockfish-windows-x86-64-avx2.exe"
CACHE = sys.argv[1]
PLAYERS = ("bjagus", "cademan", "Crossfire1983")
WINDOW = 1


def motifs_of(fen: str, uci: str | None) -> set[str]:
    if not uci:
        return set()
    board = chess.Board(fen)
    move = chess.Move.from_uci(uci)
    return set(detect_motifs(board, move)) if move in board.legal_moves else set()


modes: Counter = Counter()
errors_with_motif = errors_total = 0
played_move_would_help = 0

with engine_session(ENGINE, 15, CACHE) as session:
    for player in PLAYERS:
        games = load_games(ROOT / "games" / f"{player}.pgn")[:20]
        corpus = build_corpus(player, games)
        observations = analyse_corpus(corpus, games, session.analyser)

        by_ply = {(o.game_id, o.ply): o for o in observations}
        own: dict[str, dict[int, list]] = {}
        for o in observations:
            if o.mover == player:
                # `move_number`, not `ply // 2 + 1`. This joins the reviewer's own
                # notes by move number, and the second form puts every Black move
                # one too high -- so a note about Black's move 31 was read against
                # move 32 (L-044, D17).
                own.setdefault(o.game_id, {}).setdefault(move_number(o.ply), []).append(o)

        # Coverage: of all this player's labelled errors, how many carry ANY
        # motif under the current scheme (best move, or opponent's reply)?
        for o in observations:
            if o.mover != player or o.label is None:
                continue
            errors_total += 1
            found = motifs_of(o.fen_before, o.best_move)
            reply = by_ply.get((o.game_id, o.ply + 1))
            if reply is not None:
                found |= motifs_of(reply.fen_before, reply.best_move)
            if found:
                errors_with_motif += 1

        notes = [n for n in parse_notes(ROOT / "a-your-reading" / f"{player}.txt") if n.move]
        index = {i: g for i, g in enumerate(games, start=1)}

        for note in notes:
            game = index.get(note.game)
            expected = expected_signals(note.text)
            if game is None or not expected:
                continue

            found: set[str] = set()
            played: set[str] = set()
            erred = False
            for offset in range(-WINDOW, WINDOW + 1):
                for o in own.get(game.game_id, {}).get(note.move + offset, []):
                    if o.label is None:
                        continue
                    erred = True
                    found |= motifs_of(o.fen_before, o.best_move)
                    reply = by_ply.get((o.game_id, o.ply + 1))
                    if reply is not None:
                        found |= motifs_of(reply.fen_before, reply.best_move)
                    # What the PLAYER's own move did, which nothing currently reads.
                    played |= motifs_of(o.fen_before, o.move_played)

            if any(s in found for s in expected):
                modes["named correctly"] += 1
            elif not erred:
                modes["below threshold - no label, no detector runs"] += 1
            elif not found:
                modes["A. error, but NO motif covers the position"] += 1
            else:
                modes["B. a motif fired, but a different one"] += 1
                if any(s in played for s in expected):
                    played_move_would_help += 1

print(f"\nMOTIF COVERAGE OF ERRORS ({', '.join(PLAYERS)}, 20 games each)")
print(f"  labelled errors                     {errors_total}")
print(f"  carrying any motif at all           {errors_with_motif} "
      f"({errors_with_motif / max(1, errors_total):.0%})")
print(f"  carrying none                       {errors_total - errors_with_motif} "
      f"({1 - errors_with_motif / max(1, errors_total):.0%})")

print("\nWHY EACH REVIEWER NOTE WENT UNNAMED")
total = sum(modes.values())
for mode, count in modes.most_common():
    print(f"  {mode:<52}{count:>4}  ({count / max(1, total):.0%})")

print(f"\n  of the 'different motif' cases, the PLAYED move carries what the")
print(f"  reviewer described: {played_move_would_help}")
