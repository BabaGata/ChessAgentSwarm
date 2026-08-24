"""How much the exchange-based helpers changed what fires.

Reinstates the three pre-D17 helpers by monkeypatch and counts both ways over the
same moves, so the difference is the change and nothing else.
"""
from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach import tactics  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.tactics import PIECE_VALUE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"


def old_lands_safely(after, square, mover):
    if not after.is_attacked_by(not mover, square):
        return True
    return after.is_attacked_by(mover, square)


def old_is_worth_winning(after, square, attacker, mover):
    target = after.piece_at(square)
    if target is None or target.color == mover:
        return False
    if target.piece_type == chess.KING:
        return True
    if PIECE_VALUE[target.piece_type] > PIECE_VALUE[attacker.piece_type]:
        return True
    return not after.is_attacked_by(not mover, square)


def old_is_winnable(after, square, piece, mover):
    if not after.is_attacked_by(not mover, square):
        return True
    return any(
        PIECE_VALUE[a.piece_type] < PIECE_VALUE[piece.piece_type]
        for sq in after.attackers(mover, square)
        if (a := after.piece_at(sq)) is not None
    )


def count(positions, old: bool) -> Counter:
    saved = (tactics._lands_safely, tactics._is_worth_winning, tactics._is_winnable)
    if old:
        tactics._lands_safely = old_lands_safely
        tactics._is_worth_winning = old_is_worth_winning
        tactics._is_winnable = old_is_winnable
    try:
        tally = Counter()
        for fen, uci in positions:
            board = chess.Board(fen)
            move = chess.Move.from_uci(uci)
            for motif in tactics.detect_motifs(board, move):
                tally[str(motif)] += 1
        return tally
    finally:
        tactics._lands_safely, tactics._is_worth_winning, tactics._is_winnable = saved


def main() -> int:
    engine, cache = sys.argv[1], sys.argv[2]
    positions = []
    with engine_session(engine, 15, cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            games = load_games(path)[:20]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            for o in analyse_corpus(corpus, games, session.analyser):
                if o.mover.lower() != player.lower():
                    continue
                board = chess.Board(o.fen_before)
                move = chess.Move.from_uci(o.move_played)
                if move in board.legal_moves:
                    positions.append((o.fen_before, o.move_played))
            print(f"  {player}: {len(positions)} moves so far", flush=True)

    before, after = count(positions, old=True), count(positions, old=False)
    print(f"\nOVER {len(positions)} PLAYED MOVES")
    print(f"{'motif':<22}{'before':>8}{'after':>8}{'change':>10}")
    print("-" * 48)
    for motif in sorted(set(before) | set(after)):
        b, a = before[motif], after[motif]
        pct = f"{(a - b) / b:+.0%}" if b else "new"
        print(f"{motif:<22}{b:>8}{a:>8}{pct:>10}")
    print(f"{'TOTAL':<22}{sum(before.values()):>8}{sum(after.values()):>8}"
          f"{(sum(after.values()) - sum(before.values())) / sum(before.values()):>+9.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
