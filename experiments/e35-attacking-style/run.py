"""E35 — is "plays for the attack and pays for it" a measurable claim?

The reviewer, correcting E34's `miscounted_exchange`:

    "a sacrifice is when a player deliberately gives a stronger piece for a
     weaker piece to make opening for attack which is usually on the king...
     Those are usually direct material losses while miscalculated exchange can
     be usually seen after 2 or 3 moves. ... goydorak is a player who likes to
     attack and is willing to sacrifice material just to get an opportunity to
     attack. And because of forcing attacks that are not good he looses games
     often. Besides sacrificing, sometimes he does not take free pawn on the
     opposite side just to go with his pieces towards the king."

E34 shipped one claim covering all material-losing captures and called it
`miscounted_exchange`. That name is wrong for an attacking player: it prescribes
"count the exchange" to someone who counted it and accepted the cost on purpose.

Four candidates here, from the reviewer's own distinctions:

    sacrificed_for_attack     material given up on or beside the enemy king
    miscounted_away_from_king the same loss with no attacking idea behind it
    declined_material         free material on offer, went for the king instead
    delayed_material_loss     the swap looked fine and the material went in 3 moves

The screens are the project's usual two, and the second has killed more
candidates than anything else:

    1. does it separate players?  (p90/median, L-024)
    2. or is it the overall error rate under another name?  (r, E10's test)

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
    best_free_capture,
    declined_material_to_attack,
    material_balance,
    miscounted_exchange_away_from_king,
    exchange_value,
    sacrificed_for_attack,
)
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# How far ahead a "delayed" loss is allowed to show up, in the player's own
# moves. The reviewer's "2 or 3 moves".
DELAY_HORIZON = 3

CANDIDATES = (
    "sacrificed_for_attack",
    "miscounted_away_from_king",
    "declined_material",
    "delayed_material_loss",
)


@dataclass
class Tally:
    instances: int = 0
    opportunities: int = 0
    faulted: int = 0  # of the instances, how many the engine called an error

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

    @property
    def error_rate(self) -> float:
        return self.errors / self.moves if self.moves else 0.0


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

    # Indexed so a move's own future can be read for the delayed candidate.
    by_game: dict[str, list] = {}
    for o in own:
        by_game.setdefault(o.game_id, []).append(o)
    for moves in by_game.values():
        moves.sort(key=lambda o: o.ply)

    for game_id, moves in by_game.items():
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

            if board.is_capture(move):
                result.tallies["sacrificed_for_attack"].opportunities += 1
                result.tallies["miscounted_away_from_king"].opportunities += 1
                if sacrificed_for_attack(board, move):
                    _hit(result.tallies["sacrificed_for_attack"], faulted)
                if miscounted_exchange_away_from_king(board, move):
                    _hit(result.tallies["miscounted_away_from_king"], faulted)
            else:
                # Only a position with free material on offer is a chance to
                # decline it, so that is the denominator.
                _capture, gain = best_free_capture(board)
                if gain >= MATERIAL_LOSS:
                    result.tallies["declined_material"].opportunities += 1
                    if declined_material_to_attack(board, move):
                        _hit(result.tallies["declined_material"], faulted)

            # Delayed: the swap on this square looked fine, and material went
            # anyway within the next few of the player's own moves.
            if exchange_value(board, move) >= 0:
                result.tallies["delayed_material_loss"].opportunities += 1
                before = material_balance(board, mover)
                horizon = moves[index + 1: index + 1 + DELAY_HORIZON]
                if horizon:
                    after = min(
                        material_balance(chess.Board(later.fen_before), mover)
                        for later in horizon
                    )
                    if before - after >= MATERIAL_LOSS:
                        _hit(result.tallies["delayed_material_loss"], faulted)

    return result


def _hit(tally: Tally, faulted: bool) -> None:
    tally.instances += 1
    if faulted:
        tally.faulted += 1


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
    say(f"{'candidate':<28}{'instances':>10}{'chances':>9}{'pooled':>9}"
        f"{'median':>9}{'p90':>8}{'spread':>9}{'engine faults':>15}")
    say("-" * 97)
    for name in CANDIDATES:
        rates = sorted(r.tallies[name].rate for r in results
                       if r.tallies[name].rate is not None)
        instances = sum(r.tallies[name].instances for r in results)
        chances = sum(r.tallies[name].opportunities for r in results)
        faulted = sum(r.tallies[name].faulted for r in results)
        if not rates or not chances:
            say(f"{name:<28}{'never fired':>10}")
            continue
        median = statistics.median(rates)
        p90 = rates[min(len(rates) - 1, int(0.9 * len(rates)))]
        spread = (p90 / median) if median else float("nan")
        say(f"{name:<28}{instances:>10}{chances:>9}{instances/chances:>8.1%}"
            f"{median:>9.1%}{p90:>8.1%}{spread:>8.2f}x"
            f"{faulted/max(1,instances):>14.0%}")

    say()
    say("SCREEN 2 - or is it the error rate under another name? (E10 refused at +0.737)")
    say(f"{'candidate':<28}{'r with error rate':>20}{'r with rating':>16}")
    say("-" * 66)
    rated = [r for r in results if r.rating]
    for name in CANDIDATES:
        pairs = [(r.tallies[name].rate, r.error_rate, r.rating)
                 for r in rated if r.tallies[name].rate is not None]
        if len(pairs) < 3:
            say(f"{name:<28}{'too few':>20}")
            continue
        r_err = pearson([p[1] for p in pairs], [p[0] for p in pairs])
        r_rat = pearson([p[2] for p in pairs], [p[0] for p in pairs])
        flag = "  <- restates it" if r_err >= 0.70 else ""
        say(f"{name:<28}{r_err:>+20.3f}{r_rat:>+16.3f}{flag}")

    say()
    say("PER PLAYER")
    say(f"{'player':<22}{'rating':>7}" + "".join(f"{n[:13]:>15}" for n in CANDIDATES))
    say("-" * 89)
    for r in sorted(results, key=lambda r: -r.tallies["sacrificed_for_attack"].rate
                    if r.tallies["sacrificed_for_attack"].rate is not None else 0):
        cells = "".join(
            f"{r.tallies[n].rate:>14.1%}" if r.tallies[n].rate is not None else f"{'--':>15}"
            for n in CANDIDATES
        )
        mark = "  <--" if r.player == "goydorak" else ""
        say(f"{r.player:<22}{r.rating:>7}{cells}{mark}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
