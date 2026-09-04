"""What the clock says about the moves the reviewer wrote down.

The reviewer, after annotating seven players:

    "I didnt check it at all because that took me a lot of time. So no mistake
     is recorded as a instant move while for some this could definitely be the
     case."

Which is true and checkable: the clock is in the PGN, and the notes carry move
numbers. This joins the two.

**It writes a companion file and never touches Form A.** The notes are the ground
truth that [[experiments.e31-move-level-agreement]] and
[[experiments.e40-derived-ranking]] score the swarm against. Writing
"instant move" into them would put the swarm's own vocabulary into the answer key
and let it take credit for naming something a machine inserted — the reviewer can
fold any of this into their reading themselves, and that is their judgement to
make rather than this script's.

**Two figures per move, because the system's own is wrong on increment games.**
`Observation.seconds_spent` is `clock_before - clock_after`, and with an increment
of `i` the clock reads `before - spent + i`, so the stored figure **understates
thinking time by exactly the increment**. On a 180+2 game a 3.5 s move is recorded
as 1.5 s and reads as instant. 91 % of the review games are increment-free so most
rows are unaffected, but the ones that are not are flagged rather than silently
reported.

Usage:
    python clock_annotate.py --engine PATH [--cache CACHE] [--window 20]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e31-move-level-agreement"))

from compare import parse_notes  # noqa: E402

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.phrasing import move_number  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import diagnosable  # noqa: E402
from chesscoach.sections.s2_decision_process import INSTANT_MOVE_SECONDS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"
MIN_NOTES = 5


def increment_of(time_control: str | None) -> float:
    """Seconds added after each move, or 0 when the tag is unreadable."""
    if not time_control or "+" not in time_control:
        return 0.0
    _, _, inc = time_control.partition("+")
    try:
        return float(inc)
    except ValueError:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    args = parser.parse_args()

    totals = {"notes": 0, "timed": 0, "instant": 0, "instant_corrected": 0}
    summary: list[str] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            notes = [n for n in parse_notes(ROOT / "a-your-reading" / f"{player}.txt")
                     if n.move is not None]
            if len(notes) < MIN_NOTES:
                continue

            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            mine = [o for o in observations if o.mover.lower() == player.lower()]
            by_game = {}
            for o in mine:
                # `move_number`, not `ply // 2 + 1`: the second gets White
                # right and puts **every Black move one too high**, so a
                # reviewer's note about Black's move 31 was read against
                # move 32's clock (L-044).
                by_game.setdefault(o.game_id, {})[move_number(o.ply)] = o

            # The reviewer numbers games by their order in the PGN they opened.
            games_by_index = {i: g for i, g in enumerate(games, start=1)}
            timed_moves = [o.seconds_spent for o in mine if o.seconds_spent is not None]
            typical = statistics.median(timed_moves or [0])
            # The control, without which 34 % is an uninterpretable number: how
            # often is ANY move instant? Only the ratio of the two says whether
            # the reviewer's noticed mistakes are unusually rushed.
            def instant_rate(seconds: list[float]) -> float:
                return (sum(1 for t in seconds if t <= INSTANT_MOVE_SECONDS) / len(seconds)
                        if seconds else 0.0)

            base_instant = instant_rate(timed_moves)
            # The fairer denominator. Every-move includes opening book and
            # forced recaptures, which are instant by nature and nothing a
            # reviewer would write down, so it flatters the comparison.
            # `diagnosable` is post-opening and still competitive -- the moves a
            # reviewer is actually reading, and the population the swarm uses.
            considered = [o.seconds_spent for o in diagnosable(tuple(mine))
                          if o.seconds_spent is not None]
            base_diagnosable = instant_rate(considered)
            # And the tightest control of all: of the moves the ENGINE calls
            # errors, how many were instant? That asks whether rushing explains
            # mistakes at all, independently of which ones a human noticed.
            engine_errors = [o.seconds_spent for o in diagnosable(tuple(mine))
                             if o.is_error and o.seconds_spent is not None]
            base_errors = instant_rate(engine_errors)

            lines = [
                f"CLOCK TIMES FOR THE MOVES YOU WROTE DOWN — {player}",
                "=" * 78,
                "",
                "Machine-generated from the PGN clock. NOT part of your Form A, and",
                "nothing here has been written into your notes: if you want any of it in",
                "your reading, that is your call to make, not the script's.",
                "",
                f"'Instant' is the system's own threshold: {INSTANT_MOVE_SECONDS:.0f} seconds or less.",
                f"Your typical move in these {len(games)} games took {typical:.1f}s, and",
                f"{base_instant:.0%} of ALL your moves were instant — but that count includes",
                f"opening book and forced recaptures. The fair comparison is the",
                f"{base_diagnosable:.0%} of your post-opening, still-competitive moves that were",
                f"instant, and the {base_errors:.0%} of the moves the engine calls mistakes.",
                "",
                f"{'game':>5} {'move':>5}  {'spent':>7} {'corrected':>10}  note",
                "-" * 78,
            ]

            instant = corrected_instant = timed = 0
            for note in sorted(notes, key=lambda n: (n.game, n.move or 0)):
                game = games_by_index.get(note.game)
                if game is None:
                    lines.append(f"{note.game:>5} {note.move:>5}  {'—':>7} {'—':>10}  "
                                 f"(game not in the first {args.window})")
                    continue
                observation = by_game.get(game.game_id, {}).get(note.move)
                if observation is None or observation.seconds_spent is None:
                    lines.append(f"{note.game:>5} {note.move:>5}  {'—':>7} {'—':>10}  "
                                 f"(no clock, or not your move)")
                    continue

                timed += 1
                spent = observation.seconds_spent
                inc = increment_of(game.time_control)
                real = spent + inc
                is_instant = spent <= INSTANT_MOVE_SECONDS
                really_instant = real <= INSTANT_MOVE_SECONDS
                instant += is_instant
                corrected_instant += really_instant

                mark = ""
                if is_instant and not really_instant:
                    mark = "  <-- NOT instant once the increment is added back"
                elif really_instant:
                    mark = "  <-- INSTANT"
                shown = f"{real:.1f}s" if inc else "same"
                lines.append(
                    f"{note.game:>5} {note.move:>5}  {spent:>6.1f}s {shown:>10}  "
                    f"{note.text[:44]}{mark}"
                )

            lines += [
                "-" * 78,
                f"  notes with a move number      {len(notes)}",
                f"  of those, with a clock reading{timed:>4}",
                f"  played in {INSTANT_MOVE_SECONDS:.0f}s or less        {instant:>4}"
                f"   ({instant / timed:.0%} of the timed ones)" if timed else "",
                f"  still instant after increment {corrected_instant:>4}",
                f"  your instant rate, all moves  {base_instant:>4.0%}",
                f"  ...post-opening & competitive {base_diagnosable:>4.0%}"
                f"   <-- the fair comparison",
                f"  ...moves the engine calls bad {base_errors:>4.0%}",
                f"  so a mistake YOU noticed was "
                f"{(instant / timed) / base_diagnosable:.2f}x as likely to be instant "
                f"as a typical position you were reading"
                if timed and base_diagnosable else "",
                "",
                "None of your notes mentions the clock, so these are mistakes you found",
                "on the board alone. Where the time is very short, the move may be worth",
                "a second look as a decision-process failure rather than a knowledge gap.",
            ]
            out = ROOT / "a-your-reading" / f"{player}-clock.txt"
            out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

            totals["notes"] += len(notes)
            totals["timed"] += timed
            totals["instant"] += instant
            totals["instant_corrected"] += corrected_instant
            summary.append(
                f"  {player:<22} {timed:>3} timed  {instant:>3} instant "
                f"({instant / timed:>3.0%})  base {base_instant:>3.0%}  "
                f"vs diagnosable {base_diagnosable:>3.0%} = {(instant / timed) / base_diagnosable:.2f}x"
                f"   (engine-flagged errors: {base_errors:>3.0%})"
                if timed and base_instant else f"  {player:<22} none timed"
            )
            print(summary[-1], flush=True)

    print()
    print(f"  TOTAL  {totals['timed']} timed notes, {totals['instant']} instant "
          f"({totals['instant'] / totals['timed']:.0%})" if totals["timed"] else "nothing")
    print(f"         {totals['instant_corrected']} still instant with the increment added back")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
