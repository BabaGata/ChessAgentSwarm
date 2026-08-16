"""Build the pack a strong player is asked to fill in.

Protocol: docs/notes/evaluation.expert-review.md, pre-registered before any
reviewer was approached.

The one structural rule the pack enforces: **the reviewer writes down their own
diagnosis before seeing the system's.** Form A and the report live in separate
files, and the report is not in the folder Form A is read from. The difference
between "would you have said this?" and "do you agree with this?" is the whole
measurement, and it is lost the moment the two are on the same page.

Sampling is stratified, seeded and recorded, so the review cannot later be run on
whichever players happened to look best.

Usage:
    python prepare.py --profiles DIR --pgn DIR --out DIR
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.explainer import render  # noqa: E402
from chesscoach.profile.io import load_profile  # noqa: E402

SEED = 20260810

# The strata, and how many of each. Deliberately includes the cases that flatter
# the system least: the marginal findings and the players it had nothing to say
# about.
STRATA = (
    ("two_priorities", 5),
    ("one_priority", 3),
    ("silent", 2),
    ("strongest_finding", 1),
    ("weakest_finding", 1),
)

FORM_A = """FORM A — your own reading, before you see the system's
=========================================================

Player: {player}
Games:  {games} games, in {pgn}

Please answer from the games alone. Do not open the report yet — it is in a
separate folder for that reason, and the value of this whole exercise depends
on these answers being yours rather than a reaction to the system's.

THREE mistakes, ranked, because the report now names three and the comparison
is only fair if both sides get the same number of slots. If only one or two
stand out, leave the rest blank — a padded third is worse than an empty one.


0. How many of the {games} games did you actually look at?

   [    ]  games

   Answered first, and honestly. A reading of the first twenty is a perfectly
   good reading of the first twenty, and it is a different measurement from a
   reading of all of them. Recording which one this is costs you a number and
   saves the result from being over-read.


1. What is this player's MAIN weakness?



2. Second?



3. Third?



4. What one thing would you tell them to work on first?



5. Roughly how strong do you think they are?



6. Anything you counted here that a computer might define differently?

   Optional, and unusually useful. "Hanging pieces" might mean undefended
   pieces only, or pieces and pawns together; "misses tactics" might or might
   not include the ones they had no time for. Where your definition is wider
   or narrower than the obvious one, saying so turns a disagreement into a
   measurable question instead of a difference of opinion.


"""

FORM_B = """FORM B/C — judging the system's report
======================================

Player: {player}

Now read report.txt in this folder, then rate each item 1-5.

  correctness   is the named weakness real?
                1 contradicted by the games / 3 present but minor
                5 clearly a main weakness
                                                            [   ]

  priority      is it what you would work on first?
                1 would not mention it / 3 reasonable, not my first choice
                5 exactly my first choice
                                                            [   ]

  specificity   could the player act on this?
                1 generic advice / 3 actionable with effort
                5 concrete and immediately actionable
                                                            [   ]

  evidence      do the cited positions support the claim?
                1 they do not show it / 3 mixed / 5 they show it plainly
                                                            [   ]

  harm          could following this make them worse?
                1 yes, plainly / 3 neutral / 5 actively helpful
                                                            [   ]

The most useful box on this form:

  What did the system MISS?



  Anything it said that is simply wrong?



  If the report was empty: was there something worth telling this player?


"""

README = """Expert review pack
==================

{n} players. For each, work in this order:

  1. open  games/<player>.pgn            (or the study link, if provided)
  2. fill  a-your-reading/<player>.txt    <-- before anything else
  3. open  b-the-system/<player>/report.txt
  4. fill  b-the-system/<player>/form.txt

The order matters more than anything else here. Once you have seen the
system's answer you cannot un-see it, and "would you have said this?" is a
different and much more informative question than "do you agree with this?".

There is no need to be kind. A finding you would not have mentioned is the
most useful thing you can report, and the protocol was written down before
you were asked, thresholds included, so a bad result is a result rather than
a disappointment: docs/notes/evaluation.expert-review.md

Roughly 15-20 minutes per player.
"""


def classify(profile) -> tuple[str, float]:
    """Which stratum a player belongs to, and how strong their best finding is."""
    steps = profile.plan.steps if profile.plan else ()
    advised = {s.finding_id for s in steps}
    strength = max(
        (f.measurement.lift_vs_peer or 0.0 for f in profile.findings if f.id in advised),
        default=0.0,
    )
    if not steps:
        return "silent", 0.0
    return ("two_priorities" if len(steps) >= 2 else "one_priority"), strength


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", required=True, type=Path)
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    rng = random.Random(SEED)
    profiles = {}
    for path in sorted(args.profiles.glob("*.json")):
        profiles[path.stem] = load_profile(path)

    grouped: dict[str, list[tuple[str, float]]] = {}
    for player, profile in profiles.items():
        stratum, strength = classify(profile)
        grouped.setdefault(stratum, []).append((player, strength))

    chosen: list[tuple[str, str]] = []
    taken: set[str] = set()

    # The two extreme strata are picked by strength, not at random: the point of
    # including them is that they are the best and worst cases.
    ranked = sorted(
        (p for p, _ in grouped.get("two_priorities", []) + grouped.get("one_priority", [])),
        key=lambda p: -max(
            (f.measurement.lift_vs_peer or 0.0 for f in profiles[p].findings), default=0.0
        ),
    )
    for stratum, pool in (("strongest_finding", ranked), ("weakest_finding", ranked[::-1])):
        for player in pool:
            if player not in taken:
                chosen.append((stratum, player))
                taken.add(player)
                break

    for stratum, wanted in STRATA:
        if stratum in ("strongest_finding", "weakest_finding"):
            continue
        pool = [p for p, _ in grouped.get(stratum, []) if p not in taken]
        rng.shuffle(pool)
        for player in pool[:wanted]:
            chosen.append((stratum, player))
            taken.add(player)

    if not chosen:
        print("no players to review")
        return 1

    out = args.out
    (out / "games").mkdir(parents=True, exist_ok=True)
    (out / "a-your-reading").mkdir(parents=True, exist_ok=True)
    (out / "b-the-system").mkdir(parents=True, exist_ok=True)

    manifest = []
    for stratum, player in chosen:
        profile = profiles[player]
        source = args.pgn / f"{player}.pgn"
        if source.exists():
            shutil.copy(source, out / "games" / f"{player}.pgn")

        # utf-8-sig throughout the pack: these files are opened by a stranger on
        # their own machine, and without a BOM Windows tools read UTF-8 as ANSI
        # and turn every dash into mojibake. Found by looking at the pack the way
        # a reviewer would rather than the way the writer does.
        (out / "a-your-reading" / f"{player}.txt").write_text(
            FORM_A.format(player=player, games=profile.corpus.n_games,
                          pgn=f"games/{player}.pgn"),
            encoding="utf-8-sig",
        )

        folder = out / "b-the-system" / player
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "report.txt").write_text(render(profile), encoding="utf-8-sig")
        (folder / "form.txt").write_text(
            FORM_B.format(player=player), encoding="utf-8-sig"
        )

        steps = len(profile.plan.steps) if profile.plan else 0
        manifest.append({
            "player": player,
            "stratum": stratum,
            "games": profile.corpus.n_games,
            "findings": len(profile.findings),
            "priorities": steps,
        })
        print(f"  {stratum:<18} {player:<24} {profile.corpus.n_games:>3} games, "
              f"{steps} priorities")

    (out / "README.txt").write_text(README.format(n=len(chosen)), encoding="utf-8-sig")
    # Written so the sample cannot be quietly changed after the answers arrive.
    (out / "selection.json").write_text(
        json.dumps({"seed": SEED, "players": manifest}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"\n{len(chosen)} players written to {out}")
    print("selection.json records the sample; the protocol and its thresholds are in")
    print("docs/notes/evaluation.expert-review.md, both fixed before any reviewer sees this")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
