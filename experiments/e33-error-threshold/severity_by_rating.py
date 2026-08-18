"""Two questions from the reviewer.

1. goydorak "does bad sacrifices a lot, giving up a piece for a pawn for not
   much attack". Does the shipped `miscounted_exchange` claim already see it,
   and does it separate a SOUND sacrifice from an unsound one?

2. "Players in the upper range do fewer mistakes and of less severity, and they
   lose by doing multiple inaccurate moves." Is the error threshold fixed or
   per-player? It is fixed. The question is whether that systematically
   under-describes stronger players.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm")

import chess

from chesscoach.analysis.core import analyse_corpus
from chesscoach.analysis.labels import BLUNDER_WP, INACCURACY_WP, MISTAKE_WP
from chesscoach.ingest.corpus import build_corpus
from chesscoach.material import exchange_value
from chesscoach.pipeline import engine_session, load_games
from chesscoach.sections.base import diagnosable

ROOT = Path(r"C:\Users\vujic\Documents\MachineLearning\ChessAgentSwarm\expert-review")
ENGINE = r"C:\stockfish\stockfish-windows-x86-64-avx2.exe"
CACHE = sys.argv[1]


def pearson(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")


rows = []
with engine_session(ENGINE, 15, CACHE) as session:
    for path in sorted(ROOT.glob("games/*.pgn")):
        player = path.stem
        games = load_games(path)
        corpus = build_corpus(player, games)
        obs = analyse_corpus(corpus, games, session.analyser)
        own = [o for o in diagnosable(obs) if o.mover == player]

        elos = [g.white_elo if (g.white or "").lower() == player.lower() else g.black_elo
                for g in games]
        rating = round(statistics.mean([e for e in elos if e])) if any(elos) else 0

        losses = [o.loss_wp for o in own if o.label is not None]
        sacs_sound = sacs_unsound = captures = 0
        for o in own:
            board = chess.Board(o.fen_before)
            try:
                mv = chess.Move.from_uci(o.move_played)
            except ValueError:
                continue
            if mv not in board.legal_moves or not board.is_capture(mv):
                continue
            captures += 1
            if exchange_value(board, mv) <= -1:
                # The engine is the arbiter of whether the material bought
                # anything: a sound sacrifice costs little win probability.
                if o.label is None:
                    sacs_sound += 1
                else:
                    sacs_unsound += 1

        bands = {
            "5-10": sum(1 for l in losses if l < 10),
            "10-17.5": sum(1 for l in losses if 10 <= l < MISTAKE_WP),
            "17.5-30": sum(1 for l in losses if MISTAKE_WP <= l < BLUNDER_WP),
            "30+": sum(1 for l in losses if l >= BLUNDER_WP),
        }
        rows.append({
            "player": player, "rating": rating, "moves": len(own),
            "errors": len(losses),
            "error_rate": len(losses) / max(1, len(own)),
            "median_loss": statistics.median(losses) if losses else 0,
            "mean_loss": statistics.mean(losses) if losses else 0,
            "bands": bands,
            "captures": captures,
            "sacs_sound": sacs_sound, "sacs_unsound": sacs_unsound,
        })
        print(f"  {player}: done", flush=True)

rows.sort(key=lambda r: r["rating"])

print("\n=== SEVERITY BY RATING (is a fixed threshold fair to stronger players?) ===")
print(f"{'player':<22}{'rating':>7}{'err rate':>10}{'median':>9}{'mean':>8}"
      f"{'5-10':>8}{'10-17.5':>9}{'17.5-30':>9}{'30+':>7}")
print("-" * 89)
for r in rows:
    n = max(1, r["errors"])
    b = r["bands"]
    print(f"{r['player']:<22}{r['rating']:>7}{r['error_rate']:>9.1%}"
          f"{r['median_loss']:>9.1f}{r['mean_loss']:>8.1f}"
          f"{b['5-10']/n:>8.0%}{b['10-17.5']/n:>9.0%}{b['17.5-30']/n:>9.0%}{b['30+']/n:>7.0%}")

ratings = [r["rating"] for r in rows if r["rating"]]
print()
for field in ("error_rate", "median_loss", "mean_loss"):
    vals = [r[field] for r in rows if r["rating"]]
    print(f"  corr(rating, {field:<12}) = {pearson(ratings, vals):+.2f}")
share_small = [r["bands"]["5-10"] / max(1, r["errors"]) for r in rows if r["rating"]]
print(f"  corr(rating, share of errors in the 5-10 band) = {pearson(ratings, share_small):+.2f}")

print("\n=== SACRIFICES: does the shipped claim see goydorak? ===")
print(f"{'player':<22}{'rating':>7}{'captures':>10}{'sound sac':>11}{'unsound':>9}"
      f"{'unsound rate':>14}")
print("-" * 74)
for r in sorted(rows, key=lambda r: -(r["sacs_unsound"] / max(1, r["captures"]))):
    rate = r["sacs_unsound"] / max(1, r["captures"])
    mark = "  <--" if r["player"] == "goydorak" else ""
    print(f"{r['player']:<22}{r['rating']:>7}{r['captures']:>10}{r['sacs_sound']:>11}"
          f"{r['sacs_unsound']:>9}{rate:>13.1%}{mark}")

sound_total = sum(r["sacs_sound"] for r in rows)
unsound_total = sum(r["sacs_unsound"] for r in rows)
print(f"\n  material-losing captures overall: {sound_total + unsound_total}")
print(f"    the engine did NOT call an error (sound-ish): {sound_total} "
      f"({sound_total/max(1,sound_total+unsound_total):.0%})")
print(f"    the engine DID call an error (unsound):       {unsound_total} "
      f"({unsound_total/max(1,sound_total+unsound_total):.0%})")
print(f"\n  INACCURACY_WP={INACCURACY_WP}  MISTAKE_WP={MISTAKE_WP}  BLUNDER_WP={BLUNDER_WP}")
