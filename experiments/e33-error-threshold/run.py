"""E33 — what does lowering the error threshold buy, and what does it cost?

`INACCURACY_WP = 10.0` decides what counts as a mistake at all, and everything
downstream inherits it: no label means no motif detector runs, `allowed_motif`
denominators are the player's error count, and S2 sorts errors by the clock.

[[experiments.e32-hanging-pawn-screen]] left this as the open question. Adding a
free-pawn motif named 1 of 45 reviewer notes because **24 of those 45 sat below
the threshold** — for one player the median noticed mistake cost 8.9 wp, so most
of what a strong club player writes down is invisible by construction.

Lowering it is therefore the obvious move and is exactly the kind of change this
project does not make on an obvious argument. Four things are measured at each
threshold, and the last two are the ones that can veto it:

    volume          how much more of the game becomes "an error"
    agreement       does the reviewer's reading and the swarm's converge (E31)
    discrimination  do claims still separate players (p90/median, L-024)
    cost dilution   does the average error get cheap enough to blunt the
                    ranking D5 depends on

Analysis runs ONCE per player; thresholds are applied by relabelling the stored
`loss_wp`, which is exact and costs nothing.

Usage:
    python run.py --engine PATH [--cache CACHE]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e31-move-level-agreement"))

from compare import expected_signals, parse_notes  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.labels import BLUNDER_WP, ErrorLabel  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402
from chesscoach.tactics import detect_motifs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

THRESHOLDS = (10.0, 7.0, 5.0, 3.0)

# The claims whose behaviour decides this. Two that the reviewer's notes bear on
# directly, two that must not degrade.
WATCHED = (
    "missed_motif.hangingPawn.own",
    "allowed_motif.hangingPawn.own",
    "missed_motif.fork.own",
    "allowed_motif.hangingPiece.own",
    "instant_move_error.instant_moves.own",
)

ANNOTATED = ("bjagus", "cademan", "Crossfire1983")
MOVE_WINDOW = 1


def relabel(observations, threshold: float):
    """The same analysis, judged against a different floor."""

    def label_for(loss: float) -> ErrorLabel | None:
        if loss >= BLUNDER_WP:
            return ErrorLabel.BLUNDER
        # The middle tier scales with the floor rather than staying at 20: a
        # fixed mistake threshold with a moving inaccuracy one would make the
        # bands overlap strangely at 3.0.
        if loss >= (threshold + BLUNDER_WP) / 2:
            return ErrorLabel.MISTAKE
        if loss >= threshold:
            return ErrorLabel.INACCURACY
        return None

    return tuple(replace(o, label=label_for(o.loss_wp)) for o in observations)


def agreement(player: str, games, observations, threshold: float) -> tuple[int, int, int]:
    """(checkable, detected, named) for one player's move-level notes."""
    import chess

    notes = [n for n in parse_notes(ROOT / "a-your-reading" / f"{player}.txt") if n.move]
    by_index = {index: game for index, game in enumerate(games, start=1)}
    own = {}
    for o in observations:
        if o.mover != player:
            continue
        own.setdefault(o.game_id, {}).setdefault(o.ply // 2 + 1, []).append(o)

    checkable = detected = named = 0
    for note in notes:
        game = by_index.get(note.game)
        expected = expected_signals(note.text)
        if game is None or not expected:
            continue
        checkable += 1

        signals: set[str] = set()
        erred = False
        for offset in range(-MOVE_WINDOW, MOVE_WINDOW + 1):
            for o in own.get(game.game_id, {}).get(note.move + offset, []):
                if o.label is None:
                    continue
                erred = True
                if not o.best_move:
                    continue
                board = chess.Board(o.fen_before)
                move = chess.Move.from_uci(o.best_move)
                if move in board.legal_moves:
                    signals |= set(detect_motifs(board, move))
        detected += int(erred)
        named += int(any(signal in signals for signal in expected))
    return checkable, detected, named


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    analysed: dict[str, tuple] = {}
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted((ROOT / "games").glob("*.pgn")):
            player = path.stem
            games = load_games(path)
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            provenance = session.provenance(corpus.corpus_id)
            analysed[player] = (games, corpus, observations, provenance)
            print(f"  analysed {player}", flush=True)

    agents = default_agents()
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    rows = []
    for threshold in THRESHOLDS:
        moves = errors = 0
        costs: list[float] = []
        rates: dict[str, list[float]] = {}
        checkable = detected = named = 0

        for player, (games, corpus, observations, provenance) in analysed.items():
            relabelled = relabel(observations, threshold)
            own = [o for o in relabelled if o.mover == player]
            moves += len(own)
            errors += sum(1 for o in own if o.is_error)
            costs += [o.loss_wp for o in own if o.is_error]

            context = SectionContext(
                relabelled, corpus, provenance, band="1400-1800", time_control="rapid"
            )
            for agent in agents:
                for m in agent.measure(context):
                    if m.claim_key in WATCHED and m.opportunities:
                        rates.setdefault(m.claim_key, []).append(m.instances / m.opportunities)

            if player in ANNOTATED:
                c, d, n = agreement(player, games, relabelled, threshold)
                checkable, detected, named = checkable + c, detected + d, named + n

        spreads = {}
        for key, values in rates.items():
            values = sorted(values)
            median = statistics.median(values)
            p90 = values[min(len(values) - 1, int(0.9 * len(values)))]
            spreads[key] = (p90 / median) if median else float("nan")

        rows.append({
            "threshold": threshold,
            "error_share": errors / moves if moves else 0.0,
            "mean_cost": statistics.mean(costs) if costs else 0.0,
            "checkable": checkable, "detected": detected, "named": named,
            "spreads": spreads,
        })
        print(f"  threshold {threshold} done", flush=True)

    say()
    say("VOLUME AND COST — 12 players")
    say(f"{'threshold':>10}{'moves called an error':>24}{'mean cost of one':>20}")
    say("-" * 56)
    for row in rows:
        say(f"{row['threshold']:>10.1f}{row['error_share']:>23.1%}"
            f"{row['mean_cost']:>19.1f}wp")

    say()
    say("AGREEMENT WITH THE REVIEWER — 3 annotated players, move-level notes")
    say(f"{'threshold':>10}{'checkable':>11}{'detected':>17}{'named':>16}")
    say("-" * 56)
    for row in rows:
        c = row["checkable"] or 1
        say(f"{row['threshold']:>10.1f}{row['checkable']:>11}"
            f"{row['detected']:>10} ({row['detected']/c:>4.0%}){row['named']:>9} "
            f"({row['named']/c:>4.0%})")

    say()
    say("DISCRIMINATION — p90/median, the L-024 screen. Higher separates players better.")
    header = f"{'threshold':>10}" + "".join(f"{k.split('.')[0][:14]:>16}" for k in WATCHED)
    say(header)
    say("-" * len(header))
    for row in rows:
        cells = "".join(
            f"{row['spreads'].get(k, float('nan')):>15.2f}x" for k in WATCHED
        )
        say(f"{row['threshold']:>10.1f}{cells}")

    say()
    say("Read the last table against the first: a threshold that buys agreement by")
    say("flooding the evidence with cheap errors shows up as spreads collapsing")
    say("toward 1.00x, which is a claim that can no longer tell players apart.")

    (args.out / "threshold-screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'threshold-screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
