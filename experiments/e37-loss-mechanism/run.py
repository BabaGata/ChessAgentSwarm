"""E37 — what actually wins the material, inside the sequence bucket?

[[experiments.e36-forced-sequences]] established that **88.5 %** of the material
these players lose goes to a sequence over a few moves rather than to a piece
left en prise, and that the share is the same for everyone (81–93 %, spread
1.02×). It left that bucket undifferentiated. The reviewer:

    "I also want differentiation between the material lost in a sequence due the
     forks and pins, if it combined is all together now, due the exchange
     miscalculation and just pure sequence of forced attacks."

Three mechanisms, and they do want different training:

    tactic     a fork, pin, skewer or discovered attack won it -- pattern work
    exchange   captures resolved badly on one square -- counting work
    forcing    checks and threats drove it, with no named pattern -- calculation

E36's bucket cannot separate players. This asks whether its **composition** can:
two players who both lose 20 % of their material to sequences may lose it to
completely different things, and that difference is what a plan would act on.

Attribution is ordered, because a move can be several things at once:

    tactic > exchange > forcing > unattributed

A fork delivered with check is a fork -- the pattern explains it better than the
check does. "Pure sequence of forced attacks" is therefore the residual: forcing
moves that no named pattern accounts for, which is what the reviewer means by
*pure*.

Usage:
    python run.py --engine PATH [--cache CACHE]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
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

HORIZON = 3  # the player's own moves, as in E36

MECHANISMS = ("tactic", "exchange", "forcing", "unattributed")

# Patterns that count as "a tactic won it". `hangingPiece` and `hangingPawn` are
# deliberately excluded: taking something left en prise during a sequence is not
# a pattern the player failed to see coming, it is the sequence collecting.
TACTIC_MOTIFS = frozenset(
    {"fork", "pin", "skewer", "discoveredAttack", "capturingDefender",
     "trappedPiece", "backRankMate"}
)


@dataclass
class Result:
    player: str
    rating: int
    moves: int = 0
    errors: int = 0
    sequence_losses: int = 0
    by_mechanism: Counter = field(default_factory=Counter)
    by_motif: Counter = field(default_factory=Counter)

    @property
    def error_rate(self) -> float:
        return self.errors / self.moves if self.moves else 0.0

    def share(self, mechanism: str) -> float | None:
        return (self.by_mechanism[mechanism] / self.sequence_losses
                if self.sequence_losses else None)

    def per_move(self, mechanism: str) -> float | None:
        return self.by_mechanism[mechanism] / self.moves if self.moves else None


def pearson(xs, ys) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx * vy) ** 0.5 if vx and vy else float("nan")


def attribute(by_ply, game_id, start_ply, end_ply, mover_is_white):
    """What won the material between two plies. Returns (mechanism, motifs)."""
    motifs: set[str] = set()
    checks = 0
    captures_on: Counter = Counter()

    for ply in range(start_ply, end_ply + 1):
        observation = by_ply.get((game_id, ply))
        if observation is None:
            continue
        board = chess.Board(observation.fen_before)
        try:
            move = chess.Move.from_uci(observation.move_played)
        except ValueError:
            continue
        if move not in board.legal_moves:
            continue

        # Captures from BOTH sides, because an exchange is two-sided by
        # definition and counting only the opponent's would miss half of it.
        if board.is_capture(move):
            captures_on[move.to_square] += 1

        # Only the opponent can win material off the player.
        if observation.mover_is_white == mover_is_white:
            continue
        motifs |= detect_motifs(board, move) & TACTIC_MOTIFS
        after = board.copy(stack=False)
        after.push(move)
        if after.is_check():
            checks += 1

    if motifs:
        return "tactic", motifs
    if any(count >= 2 for count in captures_on.values()):
        return "exchange", set()
    if checks:
        return "forcing", set()
    return "unattributed", set()


def examine(player: str, games, observations) -> Result:
    elos = [g.white_elo if (g.white or "").lower() == player.lower() else g.black_elo
            for g in games]
    rating = round(statistics.mean([e for e in elos if e])) if any(elos) else 0
    result = Result(player=player, rating=rating)

    by_ply = {(o.game_id, o.ply): o for o in observations}
    own = [o for o in diagnosable(observations) if o.mover == player]
    result.moves = len(own)
    result.errors = sum(1 for o in own if o.label is not None)

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
            # E36's definition: the swap on this square was fine, and the
            # material is gone anyway three of the player's moves later.
            if exchange_value(board, move) <= -MATERIAL_LOSS:
                continue
            later = moves[index + HORIZON] if index + HORIZON < len(moves) else None
            if later is None:
                continue

            mover = board.turn
            before = material_balance(board, mover)
            after = material_balance(chess.Board(later.fen_before), mover)
            if before - after < MATERIAL_LOSS:
                continue

            result.sequence_losses += 1
            mechanism, motifs = attribute(
                by_ply, game_id, o.ply, later.ply, mover == chess.WHITE
            )
            result.by_mechanism[mechanism] += 1
            for motif in motifs:
                result.by_motif[motif] += 1

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

    total = sum(r.sequence_losses for r in results)
    say()
    say(f"WHAT WON THE MATERIAL - {total} sequence losses, 12 players")
    say(f"{'mechanism':<16}{'instances':>11}{'share':>9}{'median':>9}{'p90':>8}{'spread':>9}")
    say("-" * 62)
    for mechanism in MECHANISMS:
        instances = sum(r.by_mechanism[mechanism] for r in results)
        shares = sorted(r.share(mechanism) for r in results if r.share(mechanism) is not None)
        median = statistics.median(shares)
        p90 = shares[min(len(shares) - 1, int(0.9 * len(shares)))]
        say(f"{mechanism:<16}{instances:>11}{instances/max(1,total):>8.1%}"
            f"{median:>9.1%}{p90:>8.1%}{(p90/median if median else float('nan')):>8.2f}x")

    say()
    say("WHICH TACTIC, inside the tactic bucket")
    motifs = Counter()
    for r in results:
        motifs.update(r.by_motif)
    named = sum(motifs.values())
    for motif, count in motifs.most_common():
        say(f"  {motif:<22}{count:>6}{count/max(1,named):>8.1%}")

    say()
    say("SCREEN - per-move rates, the shape a claim would take")
    say(f"{'candidate':<22}{'pooled':>9}{'median':>9}{'p90':>8}{'spread':>9}"
        f"{'r with err rate':>18}")
    say("-" * 76)
    rated = [r for r in results if r.rating]
    for mechanism in MECHANISMS:
        rates = sorted(r.per_move(mechanism) for r in results
                       if r.per_move(mechanism) is not None)
        instances = sum(r.by_mechanism[mechanism] for r in results)
        moves = sum(r.moves for r in results)
        median = statistics.median(rates)
        p90 = rates[min(len(rates) - 1, int(0.9 * len(rates)))]
        pairs = [(r.per_move(mechanism), r.error_rate) for r in rated]
        r_err = pearson([p[1] for p in pairs], [p[0] for p in pairs])
        flag = "  <- restates it" if r_err >= 0.70 else ""
        say(f"{mechanism:<22}{instances/moves:>8.1%}{median:>9.1%}{p90:>8.1%}"
            f"{(p90/median if median else float('nan')):>8.2f}x{r_err:>+18.3f}{flag}")

    say()
    say("PER PLAYER - composition of the sequence losses")
    say(f"{'player':<22}{'rating':>7}{'losses':>8}" + "".join(f"{m:>14}" for m in MECHANISMS))
    say("-" * 93)
    for r in sorted(results, key=lambda r: r.rating):
        cells = "".join(
            f"{r.share(m):>13.0%}" if r.share(m) is not None else f"{'--':>14}"
            for m in MECHANISMS
        )
        say(f"{r.player:<22}{r.rating:>7}{r.sequence_losses:>8}{cells}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
