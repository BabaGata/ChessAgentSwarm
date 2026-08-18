"""E36 — material lost on the square against material lost to a sequence.

The reviewer, twice:

    "piece losses in forced couple of moves are counted the same as direct
     losses. Those should be separated because players on this level miss those
     in couple of moves much often and the advice for those should be separated
     as well."

They are right that the advice differs. Losing a piece on the square you put it
on is a **counting** failure — attackers against defenders, visible without
moving anything. Losing it to a three-move sequence is a **calculation** failure,
and telling someone to count better is no use if the loss was never on one
square to count.

**This corrects a measurement, not just a gap.** [[experiments.e35-attacking-style]]
screened `delayed_material_loss`, got a spread of 1.20x, and refused it. That
measurement was wrong: it took the **minimum** material balance over the next
three of the player's turns, which dips whenever the *opponent* initiates any
ordinary exchange and the player recaptures next move. It was firing on normal
trades — 31.7 % of all moves — so of course it separated nobody. The candidate
was never actually tested.

Corrected here by requiring the loss to be **sustained**: down at the player's
turn three moves later, not merely down at some point in between.

Two candidates, plus the composition the reviewer is really pointing at:

    lost_on_the_square    the swap on that square loses material outright
    lost_to_a_sequence    the swap was fine and the material is gone anyway
    sequence_share        of your material losses, the share needing calculation

Usage:
    python run.py --engine PATH [--cache CACHE]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import chess  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.material import (  # noqa: E402
    MATERIAL_LOSS,
    exchange_value,
    material_balance,
)
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# How far ahead to settle up, in the player's own moves. The reviewer's "couple
# of moves"; three gives a forcing sequence room to finish.
HORIZON = 3

CANDIDATES = ("lost_on_the_square", "lost_to_a_sequence")


@dataclass
class Tally:
    instances: int = 0
    opportunities: int = 0
    faulted: int = 0

    @property
    def rate(self) -> float | None:
        return self.instances / self.opportunities if self.opportunities else None


@dataclass
class Result:
    player: str
    rating: int
    moves: int = 0
    errors: int = 0
    tallies: dict[str, Tally] = field(default_factory=dict)
    # The composition: of all material lost, how much needed calculation.
    direct: int = 0
    sequence: int = 0

    @property
    def error_rate(self) -> float:
        return self.errors / self.moves if self.moves else 0.0

    @property
    def sequence_share(self) -> float | None:
        total = self.direct + self.sequence
        return self.sequence / total if total else None


def pearson(xs, ys) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")


def examine(player: str, games, observations) -> Result:
    elos = [g.white_elo if (g.white or "").lower() == player.lower() else g.black_elo
            for g in games]
    rating = round(statistics.mean([e for e in elos if e])) if any(elos) else 0
    result = Result(player=player, rating=rating)
    for name in CANDIDATES:
        result.tallies[name] = Tally()

    own = [o for o in diagnosable(observations) if o.mover == player]
    result.moves = len(own)
    result.errors = sum(1 for o in own if o.label is not None)

    by_game: dict[str, list] = {}
    for o in own:
        by_game.setdefault(o.game_id, []).append(o)
    for moves in by_game.values():
        moves.sort(key=lambda o: o.ply)

    for moves in by_game.values():
        for index, o in enumerate(moves):
            board = chess.Board(o.fen_before)
            try:
                move = chess.Move.from_uci(o.move_played)
            except ValueError:
                continue
            if move not in board.legal_moves:
                continue

            mover = board.turn
            faulted = o.label is not None
            swap = exchange_value(board, move)

            # Every move is a chance to drop material on the square it lands on.
            result.tallies["lost_on_the_square"].opportunities += 1
            if swap <= -MATERIAL_LOSS:
                result.tallies["lost_on_the_square"].instances += 1
                result.direct += 1
                if faulted:
                    result.tallies["lost_on_the_square"].faulted += 1
                continue

            # Only a move that did NOT drop material on its square can lose it to
            # a sequence instead; otherwise the two would double-count one loss.
            later = moves[index + HORIZON] if index + HORIZON < len(moves) else None
            if later is None:
                continue

            result.tallies["lost_to_a_sequence"].opportunities += 1
            # SUSTAINED, not the minimum along the way. The minimum dips on any
            # exchange the opponent starts, which is what broke E35's version.
            before = material_balance(board, mover)
            after = material_balance(chess.Board(later.fen_before), mover)
            if before - after >= MATERIAL_LOSS:
                result.tallies["lost_to_a_sequence"].instances += 1
                result.sequence += 1
                if faulted:
                    result.tallies["lost_to_a_sequence"].faulted += 1

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    results = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(GAMES.glob("*.pgn")):
            player = path.stem
            games = load_games(path)
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            results.append(examine(player, games, observations))
            print(f"  {player}: done", flush=True)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say()
    say("SCREEN 1 - does it separate players?")
    say(f"{'candidate':<24}{'instances':>10}{'chances':>9}{'pooled':>9}"
        f"{'median':>9}{'p90':>8}{'spread':>9}{'engine faults':>15}")
    say("-" * 93)
    for name in CANDIDATES:
        rates = sorted(r.tallies[name].rate for r in results
                       if r.tallies[name].rate is not None)
        instances = sum(r.tallies[name].instances for r in results)
        chances = sum(r.tallies[name].opportunities for r in results)
        faulted = sum(r.tallies[name].faulted for r in results)
        median = statistics.median(rates)
        p90 = rates[min(len(rates) - 1, int(0.9 * len(rates)))]
        say(f"{name:<24}{instances:>10}{chances:>9}{instances/chances:>8.1%}"
            f"{median:>9.1%}{p90:>8.1%}{(p90/median):>8.2f}x"
            f"{faulted/max(1,instances):>14.0%}")

    shares = sorted(r.sequence_share for r in results if r.sequence_share is not None)
    say(f"{'sequence_share':<24}{'':>10}{'':>9}"
        f"{sum(r.sequence for r in results)/max(1,sum(r.direct+r.sequence for r in results)):>8.1%}"
        f"{statistics.median(shares):>9.1%}{shares[min(len(shares)-1,int(0.9*len(shares)))]:>8.1%}"
        f"{(shares[min(len(shares)-1,int(0.9*len(shares)))]/statistics.median(shares)):>8.2f}x")

    say()
    say("SCREEN 2 - or is it the error rate under another name? (E10 refused at +0.737)")
    say(f"{'candidate':<24}{'r with error rate':>20}{'r with rating':>16}")
    say("-" * 62)
    rated = [r for r in results if r.rating]
    for name in CANDIDATES:
        pairs = [(r.tallies[name].rate, r.error_rate, r.rating)
                 for r in rated if r.tallies[name].rate is not None]
        r_err = pearson([p[1] for p in pairs], [p[0] for p in pairs])
        r_rat = pearson([p[2] for p in pairs], [p[0] for p in pairs])
        flag = "  <- restates it" if r_err >= 0.70 else ""
        say(f"{name:<24}{r_err:>+20.3f}{r_rat:>+16.3f}{flag}")
    pairs = [(r.sequence_share, r.error_rate, r.rating) for r in rated
             if r.sequence_share is not None]
    say(f"{'sequence_share':<24}"
        f"{pearson([p[1] for p in pairs], [p[0] for p in pairs]):>+20.3f}"
        f"{pearson([p[2] for p in pairs], [p[0] for p in pairs]):>+16.3f}")

    say()
    say("PER PLAYER - of your material losses, how many needed calculation?")
    say(f"{'player':<22}{'rating':>7}{'on the square':>15}{'to a sequence':>15}"
        f"{'sequence share':>16}")
    say("-" * 75)
    for r in sorted(results, key=lambda r: r.rating):
        share = r.sequence_share
        say(f"{r.player:<22}{r.rating:>7}{r.direct:>15}{r.sequence:>15}"
            f"{'--' if share is None else format(share, '.0%'):>16}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
