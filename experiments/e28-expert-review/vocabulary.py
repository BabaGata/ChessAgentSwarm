"""Write out everything the swarm can and cannot say, for the reviewer.

Generated from the code rather than written by hand, so it cannot drift away
from what the sections actually measure — the failure D11 was docked for twice.

Asked for directly, and the request was the right one:

    "I would like to see what the system evaluates because maybe I am not
     writing something down that is actually evaluated but I didn't noticed
     those concepts."

A reviewer annotating games without this is being tested on their ability to
guess the system's vocabulary, which is not the thing under test.

Usage:
    python vocabulary.py --out ../../expert-review/what-the-system-looks-for.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.labels import (  # noqa: E402
    BLUNDER_WP,
    CLAMP_CP,
    INACCURACY_WP,
    MISTAKE_WP,
)
from chesscoach.phrasing import (  # noqa: E402
    MOTIF_NAMES,
    POOLED_STATEMENTS,
    STATEMENTS,
    STRUCTURE_NAMES,
    SQUARE_NAMES,
)
from chesscoach.sections.s2_decision_process import (  # noqa: E402
    INSTANT_MOVE_SECONDS,
    LONG_THINK_MULTIPLE,
    OVERSPEND_BUDGET_PLY,
    TIME_PRESSURE_SECONDS,
)
from chesscoach.tactics import HANGING_MIN_VALUE, Motif  # noqa: E402

# What each section counts, in the reviewer's terms rather than the code's.
SECTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "S1  tactics",
        "missed_motif / allowed_motif",
        "For every move, the engine's best move is checked for a tactical pattern.\n"
        "    MISSED  = the pattern was there, you played something that lost ground.\n"
        "    ALLOWED = your move was an error, and the opponent's best reply plays\n"
        "              the pattern against you.",
    ),
    (
        "S2  decision process",
        "time_pressure / instant_move / long_think / time_budget",
        "The same errors, sorted by the CLOCK rather than by the board: what were\n"
        "    you doing with your time when you went wrong.",
    ),
    (
        "S3  endgames",
        "endgame_error / advantage_error",
        "Errors once the position is an endgame, split by material left, and errors\n"
        "    made while already clearly better.",
    ),
    (
        "S4  openings",
        "early_error / opening_disadvantage",
        "Errors before move 15, split by colour; and how often you leave the opening\n"
        "    already worse.",
    ),
    (
        "S5  pawn structure",
        "concedes_weakness",
        "Moves after which YOUR OWN pawn structure has a new weakness in it.",
    ),
    (
        "S6  squares and files",
        "allows_square",
        "Moves after which the opponent has a square or file they did not have.",
    ),
    (
        "S8  attack and defence",
        "allows_pressure",
        "Moves after which more enemy pieces bear on your king.",
    ),
)

# Things a reviewer would reasonably write down that the swarm has NO
# representation of. Listed because an honest tool says where it is blind, and
# because every one of these came out of real review notes.
BLIND: tuple[tuple[str, str], ...] = (
    ("why you lost the material",
     "The swarm records WHAT punished you, never WHY you allowed it. Undefended\n"
     "    pieces left standing, a piece moved to an attacked square, an exchange\n"
     "    counted wrongly, a defensive resource missed — none of these are\n"
     "    measured. Only a probe (V9) asks, and only about a shortlisted finding."),
    ("piece quality",
     "\"Gave up a good bishop for a bad knight\" has no detector. Nothing in the\n"
     "    swarm represents a piece being good or bad."),
    ("free pawns",
     f"The hanging-piece detector ignores anything worth less than a knight\n"
     f"    (HANGING_MIN_VALUE = {HANGING_MIN_VALUE}), so a dropped pawn is never NAMED — though the\n"
     "    error underneath it is usually still counted. See E30 and E31."),
    ("plans and ideas",
     "No detector represents a plan, a wrong plan, or playing without one."),
    ("openings by name",
     "Games carry their ECO code, and nothing diagnoses a specific line."),
    ("whether the opponent was any good",
     "Opponent rating is not used anywhere in the diagnosis."),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    out: list[str] = []

    def say(text: str = "") -> None:
        out.append(text)

    say("WHAT THE SYSTEM LOOKS FOR")
    say("=" * 74)
    say()
    say("Generated from the code, so it is what the swarm actually measures rather")
    say("than what anyone remembers it measuring.")
    say()
    say("Read this BEFORE annotating, not after. You are not being tested on your")
    say("ability to guess the vocabulary — if you notice something real that is not")
    say("in here, that is a finding about the system and the most useful thing you")
    say("can write down.")
    say()

    say()
    say("HOW A MISTAKE IS DECIDED AT ALL")
    say("-" * 74)
    say()
    say("Every one of your moves is compared with the engine's best move at depth 15,")
    say("and the difference is converted to WIN PROBABILITY, not centipawns.")
    say()
    say(f"    inaccuracy   {INACCURACY_WP:>4.0f} points of win probability given away")
    say(f"    mistake      {MISTAKE_WP:>4.0f}")
    say(f"    blunder      {BLUNDER_WP:>4.0f}")
    say()
    say("Three consequences worth knowing while you annotate:")
    say()
    say("  * FORCED SEQUENCES ARE INCLUDED. The engine's evaluation already accounts")
    say("    for anything forced inside its search, so a move that loses a rook six")
    say("    moves later, or allows a mate in three, registers on the move that")
    say("    ALLOWED it. You do not need to count material yourself, and the swarm")
    say("    never counts material — it reads the evaluation.")
    say()
    say(f"  * Evaluations are clamped at +-{CLAMP_CP}cp first, so mate is treated as")
    say("    'completely winning' rather than as infinity. Allowing mate in 1 and")
    say("    allowing mate in 10 therefore score the SAME, and going from already")
    say("    winning to mate scores nothing at all.")
    say()
    say(f"  * Anything below {INACCURACY_WP:.0f} points carries no label. A move giving away 9")
    say("    points of win probability is real and is not counted as an error. If you")
    say("    are noticing small errors, you are working finer than the swarm does")
    say("    (measured in E31).")
    say()

    say()
    say("THE SEVEN SECTIONS")
    say("-" * 74)
    for name, keys, description in SECTIONS:
        say()
        say(f"  {name}")
        say(f"    claims: {keys}")
        say(f"    {description}")
    say()

    say()
    say("EVERY SENTENCE IT CAN SAY ABOUT YOU")
    say("-" * 74)
    say()
    say("Verbatim from the report templates. If your note matches one of these,")
    say("the swarm has a name for it; if it does not, it may still have SEEN the")
    say("mistake without being able to name it.")
    say()
    for kind, template in sorted(STATEMENTS.items()):
        say(f"  {kind}")
        say(f"      {template}")
    say()
    say("  ...and where a claim covers everything of its type at once:")
    say()
    for kind, template in sorted(POOLED_STATEMENTS.items()):
        say(f"  {kind} (pooled)")
        say(f"      {template}")
    say()

    say()
    say("THE TACTICAL PATTERNS IT KNOWS")
    say("-" * 74)
    say()
    say("These eight and no others. Both directions: missing one, and allowing one.")
    say()
    for motif in Motif:
        say(f"  {MOTIF_NAMES.get(motif.value, motif.value):<24} ({motif.value})")
    say()
    say("  pawn structure it can concede : "
        + ", ".join(sorted(STRUCTURE_NAMES.values())))
    say("  squares it can give away      : "
        + ", ".join(sorted(SQUARE_NAMES.values())))
    say()

    say()
    say("THE CLOCK CONDITIONS IT SORTS ERRORS INTO")
    say("-" * 74)
    say()
    say(f"  instant move     played in {INSTANT_MOVE_SECONDS:.0f} seconds or less")
    say(f"  time pressure    {TIME_PRESSURE_SECONDS:.0f} seconds or less left on the clock")
    say(f"  long think       {LONG_THINK_MULTIPLE:.0f}x your own typical time for that game")
    say(f"  time budget      the rest of a game after overspending by move "
        f"{OVERSPEND_BUDGET_PLY // 2}")
    say()

    say()
    say("WHAT IT IS BLIND TO")
    say("-" * 74)
    say()
    say("Written down so you can tell a gap from an oversight. If you notice one of")
    say("these, the swarm will not have it, and saying so is still worth the line.")
    say()
    for name, description in BLIND:
        say(f"  {name}")
        say(f"    {description}")
        say()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
    print(f"written {args.out}  ({len(out)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
