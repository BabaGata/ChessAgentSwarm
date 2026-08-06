"""E18 — two candidate claims the exclusion rule was throwing away.

Step 1 excludes berserked games so a half-clock blunder is not diagnosed as a
chess mistake. Correct for *skill* diagnosis, and it silently discards two things
worth coaching, both raised by the author:

  A. **The berserk habit itself.** A player who halves their own clock in half
     their games has made a decision with a cost. The clock handicap contaminates
     what a blunder means; it does not contaminate the fact that the player chose
     the handicap. That is a process claim, not a knowledge one.

  B. **Time budget mismanagement.** Spending too long on one move early and then
     playing the rest badly for want of time. S2 measures the error *on* a long
     think (`long_think_error`) and errors *while* short of time
     (`time_pressure_error`) — it has never measured the **link**, which is the
     thing a player could actually act on.

Screened before being built, per L-023 and L-025:

  1. does it vary between players, or is it a constant of chess?
  2. does it survive dividing out what is already measured?

Usage:
    python run.py --pgn DIR --engine PATH --cache DB
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.parallel import prefetch  # noqa: E402
from chesscoach.ingest.corpus import Corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402

# The move by which a player should still have most of their thinking time. Move
# 15 is where S4 stops calling a mistake an opening mistake, so the two agree on
# where the opening ends.
BUDGET_PLY = 30

# Spending more than this share of the starting clock before move 15 is
# "overspending" -- provisional, and the screen reports the distribution so the
# threshold can be judged rather than assumed.
OVERSPEND_SHARE = 0.5

# Below this many games in a cell the rate is noise.
MIN_GAMES = 4


def initial_seconds(control: str | None) -> float | None:
    if not control or "+" not in control:
        return None
    try:
        initial, _increment = control.split("+")
        return float(initial)
    except ValueError:
        return None


def observe(player, games, session, args):
    """Analyse an arbitrary set of games, including ones the corpus now excludes."""
    if not games:
        return ()
    corpus = Corpus(
        username=player,
        corpus_id=f"e18:{player}",
        game_ids=tuple(sorted(g.game_id for g in games)),
    )
    prefetch(games, session.cache, engine=args.engine, depth=args.depth, workers=args.workers)
    return analyse_corpus(corpus, games, session.analyser)


def own_moves(observations, games, player):
    """Only the player's own moves -- an opponent's blunder is not evidence."""
    white = {g.game_id: g.player_is_white(player) for g in games}
    return tuple(o for o in observations if o.mover_is_white == white.get(o.game_id))


def rate(observations) -> float | None:
    return (sum(1 for o in observations if o.is_error) / len(observations)) if observations else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    berserk_rates, berserk_penalty = [], []
    budget_lift, budget_rate, pressure_rate = [], [], []
    proxy_lift: list[float] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(sorted(args.pgn.glob("*.pgn")), start=1):
            player = path.stem
            games = [g for g in parse_pgn_file(path) if g.involves(player)]
            if not games:
                continue

            berserked = [g for g in games if g.berserked_by(player)]
            normal = [g for g in games if not g.berserked_by(player)
                      and (g.termination or "").lower() != "abandoned"]
            berserk_rates.append(len(berserked) / len(games))

            # --- A: does berserking cost this player anything? ---------------
            if len(berserked) >= MIN_GAMES and len(normal) >= MIN_GAMES:
                inside = own_moves(observe(player, berserked, session, args), berserked, player)
                outside = own_moves(observe(player, normal, session, args), normal, player)
                a, b = rate(inside), rate(outside)
                if a is not None and b is not None and b > 0:
                    berserk_penalty.append(a / b)

            # --- B: does early overspending cause late errors? ---------------
            observations = own_moves(observe(player, normal, session, args), normal, player)
            by_game: dict[str, list] = {}
            for o in observations:
                by_game.setdefault(o.game_id, []).append(o)

            starting = {g.game_id: initial_seconds(g.time_control) for g in normal}
            overspent_late, careful_late = [], []
            # The section will only ever see observations, never the PGN's
            # TimeControl tag, so the same split is computed a second way -- from
            # the highest clock reading in the game -- and the two are compared.
            # If they disagree the implementable version is the one that matters.
            proxy_overspent, proxy_careful = [], []
            for game_id, moves in by_game.items():
                clock0 = starting.get(game_id)
                readings = [o.clock_after for o in moves if o.clock_after is not None]
                proxy0 = max(readings) if readings else None
                early_p = [o for o in moves if o.ply <= BUDGET_PLY]
                late_p = [o for o in moves if o.ply > BUDGET_PLY]
                if proxy0 and early_p and late_p:
                    left = min((o.clock_after for o in early_p if o.clock_after is not None),
                               default=None)
                    if left is not None:
                        target = (proxy_overspent if left / proxy0 < (1 - OVERSPEND_SHARE)
                                  else proxy_careful)
                        target.extend(late_p)
                if not clock0:
                    continue
                early = [o for o in moves if o.ply <= BUDGET_PLY]
                late = [o for o in moves if o.ply > BUDGET_PLY]
                if not early or not late:
                    continue
                # Clock remaining at the budget mark, as a share of the start.
                remaining = min((o.clock_after for o in early if o.clock_after is not None),
                                default=None)
                if remaining is None:
                    continue
                if remaining / clock0 < (1 - OVERSPEND_SHARE):
                    overspent_late.extend(late)
                else:
                    careful_late.extend(late)

            p_over, p_care = rate(proxy_overspent), rate(proxy_careful)
            if (p_over is not None and p_care is not None and p_care > 0
                    and len(proxy_overspent) >= 20):
                proxy_lift.append(p_over / p_care)

            after_overspend, after_care = rate(overspent_late), rate(careful_late)
            if (after_overspend is not None and after_care is not None
                    and after_care > 0 and len(overspent_late) >= 20):
                budget_lift.append(after_overspend / after_care)
                budget_rate.append(after_overspend)
                # What the swarm already measures, for the independence screen.
                pressed = [o for o in observations
                           if o.clock_after is not None and o.clock_after <= 60.0]
                pressure_rate.append(rate(pressed) or 0.0)

            print(f"  {index:>3} {player}: berserked {len(berserked)}/{len(games)}", flush=True)

    def spread(label, values, unit=""):
        values = sorted(v for v in values if v is not None)
        if len(values) < 5:
            print(f"\n{label}: too few players ({len(values)})")
            return None
        n = len(values)
        median, p90 = statistics.median(values), values[9 * n // 10]
        print(f"\n{label}  ({n} players)")
        print(f"    median {median:.3f}{unit}   p90 {p90:.3f}{unit}   "
              f"max {values[-1]:.3f}{unit}")
        if median:
            print(f"    p90/median spread {p90 / median:.2f}x")
        return values

    print(f"\n{'=' * 72}")
    print("A — the berserk habit")
    spread("  how often a player berserks", berserk_rates)
    print(f"    players who never do it: "
          f"{sum(1 for r in berserk_rates if r == 0)}/{len(berserk_rates)}")
    spread("  error rate in berserked games / their own normal games", berserk_penalty, "x")

    print(f"\n{'=' * 72}")
    print("B — early overspending, then errors late")
    spread("  late-error rate after overspending / after not", budget_lift, "x")
    spread("  the same, from observations alone (implementable version)", proxy_lift, "x")
    spread("  late-error rate after overspending", budget_rate)

    if len(budget_rate) >= 5:
        r = statistics.correlation(budget_rate, pressure_rate)
        print(f"\n  correlation with the existing time_pressure_error rate: {r:+.3f}")
        print("  (near +1 would mean this is that claim wearing a different name)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
