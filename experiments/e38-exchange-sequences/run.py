"""E38 — do exchanges a player ENTERS go badly for them, unusually often?

[[experiments.e37-loss-mechanism]] found that **31.9 %** of sequence material
losses come from captures resolving badly on one square, and that as a per-move
rate it separates nobody (1.17×). The reviewer: *"what is genuinely unreported is
the 31.9 % exchange, this should also be counted."*

They also supplied the reason it must be counted **carefully**, in the same
message: *"if all material loss in multiple moves is categorized all together
then it will definitely end up in top 3 weakness for every player because the
category is too broad."* Exactly right, and it is why E37's version cannot ship.

So the denominator changes. E37 divided by **every move**, which is why the rate
was flat: nearly all of it measures how often exchanges happen at all. This asks
the conditional question instead:

    when you go into an exchange, how often do you come out of it down material?

An exchange is a run of consecutive captures on one square that the player took
part in. The opportunity is entering one; the instance is coming out behind. That
is a counting skill with a clean denominator, and it is the shape that worked for
`missed_motif` (opportunities, never moves).

Also measured, because the reviewer's hypothesis about the pin/fork ordering is
testable: are forks simply **easier to see** than pins? If so, players should
miss fewer of their own fork chances than pin chances, and concede more pins than
forks — which is the asymmetry the E37 ordering would predict.

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
from chesscoach.tactics import detect_motifs  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# A run of at least this many captures on one square is an exchange rather than
# a single capture. Two: I take, you take back.
EXCHANGE_LENGTH = 2


@dataclass
class Result:
    player: str
    rating: int
    moves: int = 0
    errors: int = 0
    entered: int = 0          # exchanges the player took part in
    lost: int = 0             # ...and came out of down material
    faulted: int = 0          # ...that the engine also called an error
    # Narrower: the player's own capture looked sound by static exchange
    # evaluation, and the sequence went wrong anyway -- a wrinkle they did
    # not see rather than an exchange they were simply losing.
    sound_entry: int = 0
    sound_entry_lost: int = 0
    # For the pin/fork asymmetry.
    motif_seen: dict = field(default_factory=lambda: {"missed": {}, "chances": {}})

    @property
    def error_rate(self) -> float:
        return self.errors / self.moves if self.moves else 0.0

    @property
    def rate(self) -> float | None:
        return self.lost / self.entered if self.entered else None

    @property
    def wrinkle_rate(self) -> float | None:
        return (self.sound_entry_lost / self.sound_entry
                if self.sound_entry else None)


def pearson(xs, ys) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")


def exchange_runs(plies: list) -> list[tuple[int, int, int]]:
    """Maximal runs of consecutive captures on one square: (start, end, square)."""
    runs = []
    index = 0
    while index < len(plies):
        observation = plies[index]
        board = chess.Board(observation.fen_before)
        try:
            move = chess.Move.from_uci(observation.move_played)
        except ValueError:
            index += 1
            continue
        if move not in board.legal_moves or not board.is_capture(move):
            index += 1
            continue

        square = move.to_square
        end = index
        while end + 1 < len(plies):
            nxt = plies[end + 1]
            nboard = chess.Board(nxt.fen_before)
            try:
                nmove = chess.Move.from_uci(nxt.move_played)
            except ValueError:
                break
            if (nmove not in nboard.legal_moves or not nboard.is_capture(nmove)
                    or nmove.to_square != square):
                break
            end += 1

        if end - index + 1 >= EXCHANGE_LENGTH:
            runs.append((index, end, square))
        index = end + 1
    return runs


def examine(player: str, games, observations) -> Result:
    elos = [g.white_elo if (g.white or "").lower() == player.lower() else g.black_elo
            for g in games]
    rating = round(statistics.mean([e for e in elos if e])) if any(elos) else 0
    result = Result(player=player, rating=rating)

    own = [o for o in diagnosable(observations) if o.mover == player]
    result.moves = len(own)
    result.errors = sum(1 for o in own if o.label is not None)

    by_game: dict[str, list] = {}
    for o in observations:
        by_game.setdefault(o.game_id, []).append(o)
    for plies in by_game.values():
        plies.sort(key=lambda o: o.ply)

    for plies in by_game.values():
        for start, end, _square in exchange_runs(plies):
            took_part = any(plies[i].mover == player for i in range(start, end + 1))
            if not took_part:
                continue

            board = chess.Board(plies[start].fen_before)
            mover = chess.WHITE if plies[start].mover_is_white else chess.BLACK
            # Whose material we are tracking is the PLAYER's, not the starter's.
            colour = mover if plies[start].mover == player else not mover

            after_index = end + 1
            if after_index >= len(plies):
                continue
            after_board = chess.Board(plies[after_index].fen_before)

            result.entered += 1
            before = material_balance(board, colour)
            after = material_balance(after_board, colour)
            went_wrong = before - after >= MATERIAL_LOSS
            if went_wrong:
                result.lost += 1
                if any(plies[i].mover == player and plies[i].label is not None
                       for i in range(start, end + 1)):
                    result.faulted += 1

            # Did the player's OWN capture look sound when they played it?
            own_capture = next(
                (plies[i] for i in range(start, end + 1) if plies[i].mover == player),
                None,
            )
            if own_capture is None:
                continue
            cboard = chess.Board(own_capture.fen_before)
            try:
                cmove = chess.Move.from_uci(own_capture.move_played)
            except ValueError:
                continue
            if cmove not in cboard.legal_moves:
                continue
            if exchange_value(cboard, cmove) >= 0:
                result.sound_entry += 1
                if went_wrong:
                    result.sound_entry_lost += 1

    # The pin/fork asymmetry: of the player's own chances, how many are missed?
    for o in own:
        if not o.best_move:
            continue
        board = chess.Board(o.fen_before)
        try:
            best = chess.Move.from_uci(o.best_move)
        except ValueError:
            continue
        if best not in board.legal_moves:
            continue
        erred = o.label is not None and not o.played_best
        for motif in detect_motifs(board, best):
            result.motif_seen["chances"][motif] = result.motif_seen["chances"].get(motif, 0) + 1
            if erred:
                result.motif_seen["missed"][motif] = result.motif_seen["missed"].get(motif, 0) + 1

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

    entered = sum(r.entered for r in results)
    lost = sum(r.lost for r in results)
    faulted = sum(r.faulted for r in results)
    rates = sorted(r.rate for r in results if r.rate is not None)
    median = statistics.median(rates)
    p90 = rates[min(len(rates) - 1, int(0.9 * len(rates)))]
    rated = [r for r in results if r.rating and r.rate is not None]
    r_err = pearson([r.error_rate for r in rated], [r.rate for r in rated])
    r_rat = pearson([r.rating for r in rated], [r.rate for r in rated])

    say()
    say("THE CLAIM - when you enter an exchange, how often do you come out down?")
    say(f"  exchanges entered                {entered}")
    say(f"  came out down material           {lost}  ({lost/max(1,entered):.1%})")
    say(f"  of those, engine faulted a move  {faulted}  ({faulted/max(1,lost):.0%})")
    say()
    say(f"  median {median:.1%}   p90 {p90:.1%}   SPREAD {p90/median:.2f}x")
    say(f"  r with the overall error rate    {r_err:+.3f}"
        f"{'   <- restates it' if r_err >= 0.70 else ''}")
    say(f"  r with rating                    {r_rat:+.3f}")
    say()
    say("  Compare E37's per-move version: 5.5% pooled, spread 1.17x. The denominator")
    say("  is the whole difference - dividing by every move mostly measured how often")
    say("  exchanges happen at all.")

    sound = sum(r.sound_entry for r in results)
    sound_lost = sum(r.sound_entry_lost for r in results)
    wrinkles = sorted(r.wrinkle_rate for r in results if r.wrinkle_rate is not None)
    wmedian = statistics.median(wrinkles)
    wp90 = wrinkles[min(len(wrinkles) - 1, int(0.9 * len(wrinkles)))]
    wrated = [r for r in results if r.rating and r.wrinkle_rate is not None]
    wr_err = pearson([r.error_rate for r in wrated], [r.wrinkle_rate for r in wrated])
    say()
    say("NARROWER - your own capture looked sound, and it went wrong anyway")
    say(f"  sound-looking entries            {sound}")
    say(f"  went wrong anyway                {sound_lost}  ({sound_lost/max(1,sound):.1%})")
    say(f"  median {wmedian:.1%}   p90 {wp90:.1%}   SPREAD {wp90/wmedian:.2f}x")
    say(f"  r with the overall error rate    {wr_err:+.3f}"
        f"{'   <- restates it' if wr_err >= 0.70 else ''}")

    say()
    say(f"{'player':<22}{'rating':>7}{'entered':>9}{'lost':>7}{'rate':>8}")
    say("-" * 53)
    for r in sorted(results, key=lambda r: -(r.rate or 0)):
        say(f"{r.player:<22}{r.rating:>7}{r.entered:>9}{r.lost:>7}"
            f"{'--' if r.rate is None else format(r.rate, '.1%'):>8}")

    say()
    say("ARE FORKS EASIER TO SEE THAN PINS? - the reviewer's hypothesis for E37's order")
    say(f"{'motif':<20}{'chances':>10}{'missed':>9}{'miss rate':>12}")
    say("-" * 51)
    chances: dict = {}
    missed: dict = {}
    for r in results:
        for motif, n in r.motif_seen["chances"].items():
            chances[motif] = chances.get(motif, 0) + n
        for motif, n in r.motif_seen["missed"].items():
            missed[motif] = missed.get(motif, 0) + n
    for motif in sorted(chances, key=lambda m: -(missed.get(m, 0) / max(1, chances[m]))):
        if chances[motif] < 50:
            continue
        say(f"{motif:<20}{chances[motif]:>10}{missed.get(motif,0):>9}"
            f"{missed.get(motif,0)/chances[motif]:>11.1%}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
