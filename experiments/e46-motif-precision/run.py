"""E46 — what the exchange-based motifs fire on, and whether it is true.

D17. The author read three reports against the games and reported the motifs
wrong often enough to call the design faulty. The cause was one helper:
`_lands_safely` asked *"attacked → is it defended?"* with no piece values, while
`material.py` already held a static exchange evaluator the motifs never called.

**Precision cannot be measured without a human.** A detector's own opinion that
it fired correctly is worth nothing, and [[experiments.e04-motif-precision]] —
which caught two over-firing detectors — worked by hand-verifying samples. So
this produces two things:

  a **rate comparison**, free and automatic, against the same players' rates
  stored by [[experiments.e43-focus-gates]] before the change; and

  a **verification sheet** per motif — a uniform, seeded sample of firings with
  the position, the move in SAN, and a link that opens at that move, with a box
  to mark each one right or wrong.

The sheet is the deliverable. The rate comparison only says how much moved, not
whether what is left is true.

Usage:
    python run.py --engine PATH [--cache CACHE] [--window 20] [--per-motif 12]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.phrasing import move_number  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
OLD_RATES = (Path(__file__).resolve().parents[1]
             / "e43-focus-gates" / "results" / "candidates.json")


def firings(observations, games_by_id):
    """Every motif each played move executes, with enough context to check it."""
    out = []
    for o in observations:
        game = games_by_id.get(o.game_id)
        if game is None:
            continue
        try:
            board = chess.Board(o.fen_before)
            move = chess.Move.from_uci(o.move_played)
            if move not in board.legal_moves:
                continue
            motifs = detect_motifs(board, move)
            san = board.san(move)
        except (ValueError, IndexError):
            continue
        for motif in motifs:
            out.append({
                "motif": str(motif),
                "player": o.mover,
                "game_id": o.game_id,
                "ply": o.ply,
                "move_no": move_number(o.ply),
                "as_white": o.mover_is_white,
                "san": san,
                "fen": o.fen_before,
                "phase": o.phase,
                "loss_wp": round(o.loss_wp, 1),
            })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--per-motif", type=int, default=12)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    all_firings = []
    moves_seen = 0

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            observations = analyse_corpus(corpus, games, session.analyser)
            mine = [o for o in observations if o.mover.lower() == player.lower()]
            moves_seen += len(mine)
            all_firings += firings(mine, {g.game_id: g for g in games})
            print(f"  {player}: {len(mine)} moves", flush=True)

    counts = Counter(f["motif"] for f in all_firings)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say()
    say(f"FIRINGS ON {moves_seen} PLAYED MOVES, {args.window}-game windows")
    say(f"{'motif':<22}{'firings':>9}{'per 1000 moves':>16}")
    say("-" * 47)
    for motif, n in counts.most_common():
        say(f"{motif:<22}{n:>9}{1000 * n / moves_seen:>16.1f}")
    say(f"{'TOTAL':<22}{sum(counts.values()):>9}")

    # --- the verification sheet, which is the point ------------------------
    sheet = [
        "MOTIF VERIFICATION SHEET",
        "=" * 78,
        "",
        "One line per firing. For each, open the link, look at the position, and",
        "mark the box:  [y] the motif really is there   [n] it is not   [?] unsure",
        "",
        "You are judging the DETECTOR, not the move. A move can be bad for other",
        "reasons and still not be the motif named, and that counts as [n].",
        "",
    ]
    for motif in sorted(counts):
        pool = sorted(
            (f for f in all_firings if f["motif"] == motif),
            key=lambda f: (f["player"], f["game_id"], f["ply"]),
        )
        digest = hashlib.sha256(motif.encode()).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        sample = rng.sample(pool, min(args.per_motif, len(pool)))
        sheet += [
            "", f"{motif.upper()}  —  {len(pool)} firings, {len(sample)} sampled",
            "-" * 78,
        ]
        for f in sorted(sample, key=lambda f: (f["player"], f["ply"])):
            colour = "White" if f["as_white"] else "Black"
            sheet.append(
                f"  [ ]  {f['player']:<20} move {f['move_no']:>3} as {colour:<5} "
                f"{f['san']:<8} {f['phase']:<10} lost {f['loss_wp']:>5.1f}wp"
            )
            sheet.append(f"       lichess.org/{f['game_id']}#{f['ply']}")
    (args.out / "verification-sheet.txt").write_text(
        "\n".join(sheet) + "\n", encoding="utf-8-sig")

    # --- how much moved, against the pre-change rates ----------------------
    if OLD_RATES.exists():
        old = json.loads(OLD_RATES.read_text(encoding="utf-8"))["short"]
        say()
        say("AGAINST THE SAME PLAYERS BEFORE THE CHANGE (E43's stored candidates)")
        say(f"{'claim':<34}{'rate before':>12}{'rate now':>10}")
        say("-" * 56)
        by_claim = {}
        for player, claims in old.items():
            for c in claims:
                if c["kind"] in ("missed_motif", "allowed_motif"):
                    by_claim.setdefault(f"{c['kind']}.{c['subject']}", []).append(c["rate"])
        for claim, rates in sorted(by_claim.items()):
            before = sum(rates) / len(rates)
            say(f"{claim:<34}{before:>11.1%}{'  (see sheet)':>10}")
        say()
        say("  Rates here are the swarm's own claim rates, which are conditional on")
        say("  opportunity and so not directly comparable to the firing counts above.")
        say("  What settles precision is the sheet, and only the author can fill it.")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'verification-sheet.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
