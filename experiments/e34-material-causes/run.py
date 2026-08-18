"""E34 — do the causes of material loss earn a place in the report?

Answers D13. The reviewer's objection was that naming *what punished you* is
worth less than naming *what you did that made it possible*:

    "leaving many undefended regularly, does the player move them to the
     attacked spot, does he calculate the exchange badly, doesn't see defending
     moves"

`chesscoach/material.py` implements four of those as detectors over the move the
player **actually played** — the first in the project to read it, since every
other detector reads the engine's best move or the opponent's reply.

Accuracy is settled in `tests/test_material.py`. This asks the two questions that
decide whether any of it reaches a player, and they are the ones that killed most
of E09's and E11's candidates:

    1. does it fire often enough to measure?
    2. does it DISTINGUISH players, or does everyone do it alike? (L-024)

Plus the payoff question D13 was raised about:

    3. how much of what the swarm already calls a mistake can it now EXPLAIN?
       Currently 54 % of errors carry any motif at all, so 46 % are anonymous.

Denominators are opportunities, not moves, wherever the condition needs one:
only a capture can miscount an exchange, and only a position with something
already attacked can have a threat ignored. A per-move rate would mostly measure
how sharp the opponents were (S1's rule).

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
    ignored_threat,
    left_hanging,
    miscounted_exchange,
    moved_into_attack,
    _winnable_squares,
)
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

CAUSES = ("moved_into_attack", "miscounted_exchange", "left_hanging", "ignored_threat")

# The two that survived E10's test: their rate is not the player's overall error
# rate wearing a better name. `left_hanging` (+0.917) and `ignored_threat`
# (+0.914) are, comfortably past the +0.737 that closed S7 — which stands to
# reason, since a player who errs more often has more loose pieces and more
# unanswered threats as a simple consequence.
SURVIVORS = ("moved_into_attack", "miscounted_exchange")


@dataclass
class Tally:
    """One cause, for one player: how often, out of how many chances."""

    instances: int = 0
    opportunities: int = 0
    # Errors this cause fired on, so coverage can be attributed.
    on_errors: int = 0

    @property
    def rate(self) -> float | None:
        return self.instances / self.opportunities if self.opportunities else None


@dataclass
class PlayerResult:
    player: str
    rating: int | None
    tallies: dict[str, Tally] = field(default_factory=dict)
    errors: int = 0
    errors_with_motif: int = 0
    errors_with_cause: int = 0
    errors_with_both: int = 0
    errors_with_neither: int = 0
    errors_with_survivor: int = 0
    errors_survivor_only: int = 0
    errors_losing_material: int = 0
    material_errors_explained: int = 0
    moves: int = 0

    @property
    def error_rate(self) -> float | None:
        return self.errors / self.moves if self.moves else None


def rating_of(games, player: str) -> int | None:
    """The player's own mean Elo across the corpus, from the PGN headers."""
    seen = []
    for game in games:
        white = (game.white or "").lower() == player.lower()
        elo = game.white_elo if white else game.black_elo
        if elo:
            seen.append(elo)
    return round(statistics.mean(seen)) if seen else None


def examine(player: str, games, observations) -> PlayerResult:
    result = PlayerResult(player=player, rating=rating_of(games, player))
    for cause in CAUSES:
        result.tallies[cause] = Tally()

    by_ply = {(o.game_id, o.ply): o for o in observations}
    own = [o for o in diagnosable(observations) if o.mover == player]
    result.moves = len(own)

    for o in own:
        board = chess.Board(o.fen_before)
        try:
            move = chess.Move.from_uci(o.move_played)
        except ValueError:
            continue
        if move not in board.legal_moves:
            continue

        # Opportunity denominators, one per cause.
        threatened = bool(_winnable_squares(board, board.turn))
        fired: dict[str, bool] = {}

        result.tallies["moved_into_attack"].opportunities += 1
        fired["moved_into_attack"] = moved_into_attack(board, move)

        result.tallies["left_hanging"].opportunities += 1
        fired["left_hanging"] = left_hanging(board, move) >= 1

        if board.is_capture(move):
            result.tallies["miscounted_exchange"].opportunities += 1
            fired["miscounted_exchange"] = miscounted_exchange(board, move)
        else:
            fired["miscounted_exchange"] = False

        if threatened:
            result.tallies["ignored_threat"].opportunities += 1
            fired["ignored_threat"] = ignored_threat(board, move)
        else:
            fired["ignored_threat"] = False

        for cause, hit in fired.items():
            if hit:
                result.tallies[cause].instances += 1

        if o.label is None:
            continue

        result.errors += 1
        has_cause = any(fired.values())
        if has_cause:
            result.errors_with_cause += 1
            for cause, hit in fired.items():
                if hit:
                    result.tallies[cause].on_errors += 1

        # Does the current motif vocabulary say anything here?
        has_motif = bool(_motifs(o, by_ply))
        if has_motif:
            result.errors_with_motif += 1

        # The question that decides whether this adds anything: do causes reach
        # errors the motifs cannot, or only re-describe the same ones?
        if has_motif and has_cause:
            result.errors_with_both += 1
        elif not has_motif and not has_cause:
            result.errors_with_neither += 1

        # The same accounting for the survivors alone, which is what would
        # actually ship.
        survived = any(fired[c] for c in SURVIVORS)
        if survived:
            result.errors_with_survivor += 1
            if not has_motif:
                result.errors_survivor_only += 1

        # Errors that actually cost material, which is what D13 is about.
        if exchange_value(board, move) <= -MATERIAL_LOSS or _lost_material_next(o, by_ply):
            result.errors_losing_material += 1
            if any(fired.values()):
                result.material_errors_explained += 1

    return result


def _motifs(observation, by_ply) -> set[str]:
    found: set[str] = set()
    for source in (observation, by_ply.get((observation.game_id, observation.ply + 1))):
        if source is None or not source.best_move:
            continue
        board = chess.Board(source.fen_before)
        move = chess.Move.from_uci(source.best_move)
        if move in board.legal_moves:
            found |= set(detect_motifs(board, move))
    return found


def _lost_material_next(observation, by_ply) -> bool:
    """Did the opponent's best reply win material on the next move?"""
    reply = by_ply.get((observation.game_id, observation.ply + 1))
    if reply is None or not reply.best_move:
        return False
    board = chess.Board(reply.fen_before)
    move = chess.Move.from_uci(reply.best_move)
    if move not in board.legal_moves:
        return False
    return exchange_value(board, move) >= MATERIAL_LOSS


def _pearson(xs, ys) -> float:
    """Correlation, written out rather than pulled in, as elsewhere in this project."""
    n = len(xs)
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    return cov / (var_x * var_y) ** 0.5 if var_x and var_y else float("nan")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    results: list[PlayerResult] = []
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
    say("DOES IT FIRE, AND DOES IT SEPARATE PLAYERS?")
    say(f"{'cause':<24}{'players':>8}{'instances':>11}{'chances':>9}"
        f"{'pooled':>9}{'median':>9}{'p90':>8}{'spread':>9}")
    say("-" * 87)
    for cause in CAUSES:
        rates = sorted(r.tallies[cause].rate for r in results
                       if r.tallies[cause].rate is not None)
        instances = sum(r.tallies[cause].instances for r in results)
        chances = sum(r.tallies[cause].opportunities for r in results)
        if not rates or not chances:
            say(f"{cause:<24}{'never fired':>8}")
            continue
        median = statistics.median(rates)
        p90 = rates[min(len(rates) - 1, int(0.9 * len(rates)))]
        spread = (p90 / median) if median else float("nan")
        say(f"{cause:<24}{len(rates):>8}{instances:>11}{chances:>9}"
            f"{instances / chances:>8.1%}{median:>9.1%}{p90:>8.1%}{spread:>8.2f}x")

    say()
    say("HOW MUCH OF WHAT IT ALREADY CALLS A MISTAKE CAN IT NOW EXPLAIN?")
    errors = sum(r.errors for r in results)
    with_motif = sum(r.errors_with_motif for r in results)
    with_cause = sum(r.errors_with_cause for r in results)
    material = sum(r.errors_losing_material for r in results)
    explained = sum(r.material_errors_explained for r in results)
    both = sum(r.errors_with_both for r in results)
    neither = sum(r.errors_with_neither for r in results)
    motif_only = with_motif - both
    cause_only = with_cause - both

    say(f"  labelled errors                        {errors}")
    say(f"  carrying a tactical MOTIF (today)      {with_motif:>6} ({with_motif/max(1,errors):.0%})")
    say(f"  carrying a material CAUSE (new)        {with_cause:>6} ({with_cause/max(1,errors):.0%})")
    say()
    say("  the overlap, which is what decides whether causes ADD anything:")
    say(f"    motif only                           {motif_only:>6} ({motif_only/max(1,errors):.0%})")
    say(f"    cause only  <- newly explained       {cause_only:>6} ({cause_only/max(1,errors):.0%})")
    say(f"    both                                 {both:>6} ({both/max(1,errors):.0%})")
    say(f"    still anonymous                      {neither:>6} ({neither/max(1,errors):.0%})")
    survivor = sum(r.errors_with_survivor for r in results)
    survivor_only = sum(r.errors_survivor_only for r in results)
    say()
    say("  SURVIVORS ONLY (moved_into_attack + miscounted_exchange), which is")
    say("  what would actually ship:")
    say(f"    errors they explain                  {survivor:>6} ({survivor/max(1,errors):.0%})")
    say(f"    of those, no motif said anything     {survivor_only:>6} ({survivor_only/max(1,errors):.0%})")
    say(f"    anonymous after shipping only these  "
        f"{(errors-with_motif-survivor_only)/max(1,errors):.0%}")
    say()
    say(f"  anonymous before / after               "
        f"{(errors-with_motif)/max(1,errors):.0%} -> {neither/max(1,errors):.0%}")
    say()
    say(f"  errors that actually cost material     {material}")
    say(f"  of those, a cause explains             {explained:>6} "
        f"({explained/max(1,material):.0%})")
    say("    NOTE: this figure is near-tautological. 'Cost material' is defined")
    say("    as a losing exchange or material won on the reply, which is close to")
    say("    the union of the cause definitions. It cannot fail and is not evidence.")

    # L-025's screen: does the rate still fall with rating once general skill is
    # divided out? Everything correlates with rating by construction, because
    # better players make fewer mistakes of every kind.
    say()
    say("DOES IT FALL WITH RATING, AFTER DIVIDING OUT GENERAL SKILL? (L-025)")
    say(f"{'cause':<24}{'raw r':>10}{'divided r':>12}")
    say("-" * 46)
    rated = [r for r in results if r.rating and r.error_rate]
    for cause in CAUSES:
        pairs = [(r.rating, r.tallies[cause].rate, r.error_rate)
                 for r in rated if r.tallies[cause].rate is not None]
        if len(pairs) < 3:
            say(f"{cause:<24}{'too few':>10}")
            continue
        ratings = [p[0] for p in pairs]
        raw = _pearson(ratings, [p[1] for p in pairs])
        divided = _pearson(ratings, [p[1] / p[2] for p in pairs])
        say(f"{cause:<24}{raw:>+10.2f}{divided:>+12.2f}")
    say(f"  ({len(rated)} players with a rating; E25 used 84 and called 12 thin)")

    # E10's test, and the one that closed S7. `missed_quiet` had a respectable
    # 1.56 spread and was refused anyway, because it correlated +0.737 with
    # another error rate: the players who went wrong on quiet moves were the
    # players who went wrong on forcing moves, so the claim restated the overall
    # error rate under a more flattering name (L-014).
    say()
    say("OR IS IT THE ERROR RATE UNDER ANOTHER NAME? (E10's test, which closed S7)")
    say(f"{'cause':<24}{'r with overall error rate':>28}")
    say("-" * 54)
    withrate = [r for r in results if r.error_rate]
    for cause in CAUSES:
        pairs = [(r.tallies[cause].rate, r.error_rate)
                 for r in withrate if r.tallies[cause].rate is not None]
        if len(pairs) < 3:
            say(f"{cause:<24}{'too few':>28}")
            continue
        r_value = _pearson([p[0] for p in pairs], [p[1] for p in pairs])
        flag = "  <- restates the error rate" if r_value >= 0.70 else ""
        say(f"{cause:<24}{r_value:>+28.3f}{flag}")
    say("  E10 refused a candidate at +0.737. Above ~0.70 a claim is not a new")
    say("  diagnosis, it is how often the player goes wrong at all.")

    say()
    say("PER PLAYER - the spread above, made concrete")
    say(f"{'player':<22}{'rating':>7}" + "".join(f"{c[:14]:>16}" for c in CAUSES))
    say("-" * 86)
    for r in sorted(results, key=lambda r: r.player.lower()):
        cells = "".join(
            f"{r.tallies[c].rate:>15.1%}" if r.tallies[c].rate is not None else f"{'--':>16}"
            for c in CAUSES
        )
        say(f"{r.player:<22}{r.rating or 0:>7}{cells}")

    say()
    say("Spread is p90/median. A cause every player commits at the same rate cannot")
    say("select anyone's priority however common it is, which is what removed most")
    say("of E09's and E11's candidates.")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
