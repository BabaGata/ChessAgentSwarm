"""Do the four signals tell a 2600 from a 1600? The test that decides everything.

Design: docs/notes/design.opening-development-signals.md

The tolerance sweep in `expectations.py` asked what share of STRONG players'
games a threshold calls late, and treated a high share as a false-positive rate.
**That framing was wrong**, and this script replaces it.

The claim is not a verdict on one game. It is a per-player RATE compared with
peers, so a high base rate is harmless as long as it discriminates: strong
players late 30 % of the time and a weak player late 70 % of the time is a
perfectly good signal. What kills a signal is not firing often -- it is firing
equally on both populations, which is what E10 closed a section slot for.

So the question is separation, per player, not per game.
"""

from __future__ import annotations

import pathlib
import statistics
import sys
from collections import defaultdict

import chess
import chess.pgn

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from chesscoach.development import measure_development  # noqa: E402
from chesscoach.openings import OpeningBook, _family  # noqa: E402
from expectations import MIN_GAMES, STRONG, SUBJECTS, norms_for  # noqa: E402

TOLERANCE_PLIES = 4  # +2 moves, the author's upper setting
MIN_PLAYER_GAMES = 10


def per_player(directory, book, expectation):
    """Each player's own rates, using the strong-player expectation."""
    players = defaultdict(
        lambda: {"late": 0, "slow": 0, "seen": 0, "pawn": [], "repeat": []}
    )
    # File by file rather than through `read_corpus`, because a rate belongs to
    # the player the file is named for and the pooled reader loses that.
    for path in sorted(directory.glob("*.pgn")):
        name = path.stem
        with path.open(encoding="utf-8", errors="replace") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                if "FEN" in game.headers or game.headers.get("Variant", "Standard") != "Standard":
                    continue
                try:
                    played = list(game.mainline_moves())
                except (ValueError, AssertionError):
                    continue
                if len(played) < 8:
                    continue
                white = game.headers.get("White", "").lower()
                colour = chess.WHITE if white == name.lower() else chess.BLACK
                walk = book.walk([m.uci() for m in played])
                if walk.opening is None:
                    continue
                family = _family(walk.opening.name)
                cell = expectation.get((family, colour))
                if cell is None or cell.games < MIN_GAMES:
                    continue
                base, ready = cell.median_castle(), cell.median_ready()
                if base is None or ready is None:
                    continue
                d = measure_development(played, colour)
                players[name]["seen"] += 1
                if d.castled_at is None or d.castled_at > base + TOLERANCE_PLIES:
                    players[name]["late"] += 1
                if d.ready_at is None or d.ready_at > ready + TOLERANCE_PLIES:
                    players[name]["slow"] += 1
                pawn, repeat = d.rate(d.pawn_moves), d.rate(d.repeat_moves)
                if pawn is not None:
                    players[name]["pawn"].append(pawn)
                if repeat is not None:
                    players[name]["repeat"].append(repeat)
    return {
        n: {
            "late": v["late"] / v["seen"],
            "slow": v["slow"] / v["seen"],
            "pawn": statistics.mean(v["pawn"]),
            "repeat": statistics.mean(v["repeat"]),
        }
        for n, v in players.items()
        if v["seen"] >= MIN_PLAYER_GAMES and v["pawn"]
    }


def report(label, strong_vals, subject_vals):
    s_med = statistics.median(strong_vals)
    u_med = statistics.median(subject_vals)
    # Share of subjects worse than three quarters of the strong players.
    cut = statistics.quantiles(strong_vals, n=4)[2]
    above = sum(1 for v in subject_vals if v > cut) / len(subject_vals)
    # Rank-sum separation: probability a random subject exceeds a random strong.
    wins = sum(1 for u in subject_vals for s in strong_vals if u > s)
    ties = sum(1 for u in subject_vals for s in strong_vals if u == s)
    auc = (wins + 0.5 * ties) / (len(subject_vals) * len(strong_vals))
    print(f"{label:<22}{s_med:>10.0%}{u_med:>10.0%}{above:>12.0%}{auc:>9.2f}")


def main() -> None:
    book = OpeningBook.load()
    expectation, _ = norms_for(STRONG, book)
    strong = per_player(STRONG, book, expectation)
    subjects = per_player(SUBJECTS, book, expectation)

    print("DO THE SIGNALS SEPARATE A 2600 FROM A 1600?")
    print("=" * 70)
    print()
    print(f"strong players scored   {len(strong)}")
    print(f"subject players scored  {len(subjects)}")
    print()
    print("Each player's own rate, both judged against the SAME strong-player")
    print("expectation. AUC is the chance a random subject scores worse than a")
    print("random strong player: 0.50 is a coin, 1.00 is perfect separation.")
    print()
    print(f"{'signal':<22}{'strong':>10}{'subject':>10}{'above p75':>12}{'AUC':>9}")
    print("-" * 63)
    for key, label in (("slow", "slow development"),
                       ("late", "late castling"),
                       ("pawn", "pawn share"),
                       ("repeat", "repeat share")):
        report(label, [p[key] for p in strong.values()],
               [p[key] for p in subjects.values()])

    print()
    print("=" * 70)
    print("DOES slow_development CARRY ANYTHING late_castling DOES NOT?")
    print("=" * 70)
    print()
    print("`ready_at` is the later of castling and development, so the two")
    print("overlap by construction. If they correlate above 0.85 they are one")
    print("signal with two names and only the stronger ships -- the ceiling the")
    print("design states, and the screen E10 established.")
    print()
    for label, group in (("strong", strong), ("subject", subjects)):
        late = [p["late"] for p in group.values()]
        slow = [p["slow"] for p in group.values()]
        r = statistics.correlation(late, slow)
        agree = sum(1 for a, b in zip(late, slow) if abs(a - b) < 0.05) / len(late)
        print(f"  {label:<10} r = {r:>5.2f}   "
              f"rates within 5 pp of each other for {agree:.0%} of players")

    both = {**strong, **subjects}
    late_all = [p["late"] for p in both.values()]
    slow_all = [p["slow"] for p in both.values()]
    print(f"  {'pooled':<10} r = {statistics.correlation(late_all, slow_all):>5.2f}")
    print()
    only_slow = sum(1 for p in subjects.values() if p["slow"] - p["late"] > 0.15)
    print(f"  subjects whose slow rate exceeds their late rate by 15+ pp: "
          f"{only_slow}/{len(subjects)}")
    print("  (these are players who castle on time and still leave a piece at home)")
    print()
    print("A signal near AUC 0.50 fires equally on both populations and cannot")
    print("carry a claim, however sensible it sounds. That is what closed a")
    print("section slot in E10.")


if __name__ == "__main__":
    main()
