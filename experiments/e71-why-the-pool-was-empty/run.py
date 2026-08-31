"""Why maikel5's cost pool was empty, measured rather than inferred.

Note: docs/notes/experiments.e71-why-the-pool-was-empty.md

[[experiments.e70-band-mismatch]] established that maikel5 is 1929 and was
diagnosed against the 1400-1800 band, and *named* his two measured claims from
the detection sheet -- `concedes_weakness.backward` and `time_pressure_error` --
without being able to read their numbers, because no engine would run. It said so
in its limitations. This reads them.

Two questions, and they are different:

    which gate    for every claim in both pools, which of `_worth_a_slot`'s
                  conditions does it fail, and by how much? A claim with no cost
                  and a claim priced below its peers are different problems.

    band or rule  E56 measured maikel5 at 2 priorities and he now has 0. The band
                  was always wrong, so the band cannot explain a *change*. The
                  endgame run rule did change in between -- twice -- and the two
                  changes must be told apart: E67 introduced the run, E68 tightened
                  it from 3-in-4 to 3-in-3. Three arms, one engine pass, because
                  blaming the wrong one of those is the easy mistake.

The band's own contribution cannot be measured by toggling, because there is no
second stratum to toggle to. That asymmetry is the finding, not a gap in this
experiment.

    python run.py --engine stockfish [--cache PATH] [--players maikel5,...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import NEGLIGIBLE_COST_PER_GAME, select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference, declared_band_is_wrong  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections import s3_endgame_technique as s3  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"

# The shipped rule, the one before it, and none at all. E67 introduced the run
# on the author's words -- *"imprecise one move after the other"* -- and E68
# tightened the window from four to three after measuring clustering against a
# permutation baseline. They are separate changes and cost separate things.
SHIPPED = (3, 3)
E67_SETTING = (3, 4)
NO_RUN_RULE = (1, 1)


def why_not_a_slot(finding) -> str:
    """Which of `_worth_a_slot`'s conditions this claim fails, in words.

    Mirrors the function rather than calling it, because "it returned False" is
    the answer that started this and the question is *which* False.
    """
    m = finding.measurement
    cost = m.cost_per_game
    if cost is None:
        return "UNPRICEABLE — the section cannot say what it cost"
    if cost < NEGLIGIBLE_COST_PER_GAME:
        return f"TOO CHEAP — {cost:.2f} < {NEGLIGIBLE_COST_PER_GAME} wp/game"
    if m.peer_rate is None or m.rate >= m.peer_rate:
        return "eligible"
    if m.driven_by_exposure:
        return "eligible (below peer rate, but driven by exposure)"
    return (f"BELOW PEERS — rate {m.rate:.1%} < peer {m.peer_rate:.1%}, "
            f"and not exposure-driven")


def describe(finding) -> list[str]:
    m = finding.measurement
    cost = m.cost_per_game
    peer_cost = m.peer_cost_per_game
    lines = [
        f"    {finding.claim.key()}",
        f"      tier          {finding.confidence.tier.name}",
        f"      instances     {m.instances} in {m.distinct_games} games "
        f"(of {m.games_with_data} with data)",
        f"      rate          {m.rate:.1%}" + (
            f"   peers {m.peer_rate:.1%}" if m.peer_rate is not None else "   peers —"),
        f"      cost/game     " + (f"{cost:.2f} wp" if cost is not None else "—")
        + ("   peers " + (f"{peer_cost:.2f} wp" if peer_cost is not None else "—")),
    ]
    if m.opportunities is not None:
        per_game = m.opportunities / m.games_with_data if m.games_with_data else 0.0
        peers_per = m.peer_opportunities_per_game
        lines.append(f"      exposure      {per_game:.2f}/game" + (
            f"   peers {peers_per:.2f}/game" if peers_per is not None else "   peers —"))
    lines.append(f"      cost pool     {why_not_a_slot(finding)}")
    return lines


def run_arm(context, run_length: int, run_window: int):
    """Diagnose with a given endgame run rule, restoring it afterwards."""
    was = (s3.RUN_LENGTH, s3.RUN_WINDOW)
    try:
        s3.RUN_LENGTH, s3.RUN_WINDOW = run_length, run_window
        result = diagnose(context, default_agents())
    finally:
        s3.RUN_LENGTH, s3.RUN_WINDOW = was
    return result, select_priorities(result.findings, also=result.sub_threshold)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="stockfish")
    parser.add_argument("--peers", default=str(
        Path(__file__).resolve().parents[2] / "data" / "raw" / "out" / "peers-3af3206.json"))
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--band", default="1400-1800")
    parser.add_argument("--players", default=None,
                        help="comma-separated; default every review player")
    parser.add_argument("--detail", default="maikel5",
                        help="comma-separated players to print claim by claim")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    wanted = {p.strip().lower() for p in args.players.split(",")} if args.players else None
    detail = {p.strip().lower() for p in args.detail.split(",")} if args.detail else set()
    peers = PeerReference.load(args.peers)

    paths = [p for p in sorted(ROOT.glob("games/*.pgn"))
             if wanted is None or p.stem.lower() in wanted]

    lines: list[str] = []
    table: list[tuple] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in paths:
            player = path.stem
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue

            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band=args.band, time_control="rapid", peers=peers,
            )

            # One engine pass, three section runs: only the run rule differs.
            now, now_picked = run_arm(context, *SHIPPED)
            _, e67_picked = run_arm(context, *E67_SETTING)
            _, none_picked = run_arm(context, *NO_RUN_RULE)

            mismatch = declared_band_is_wrong(load_games(path), player, args.band)
            table.append((player, mismatch is not None,
                          len(now.findings), len(now.sub_threshold),
                          len(now_picked.priorities), len(e67_picked.priorities),
                          len(none_picked.priorities)))
            print(f"  {player}: {len(now_picked.priorities)} priorities shipped, "
                  f"{len(e67_picked.priorities)} at E67's setting, "
                  f"{len(none_picked.priorities)} with no run rule", flush=True)

            if player.lower() in detail:
                lines += ["", "=" * 78,
                          f"EVERY CLAIM MEASURED FOR {player}", "=" * 78, ""]
                if mismatch:
                    lines += ["  BAND: " + mismatch, ""]
                lines.append("  ASSERTED (reached the confidence gate)")
                asserted = now.findings
                if not asserted:
                    lines.append("    none — nothing was unusual against this band")
                for finding in asserted:
                    lines += describe(finding)
                lines += ["", "  SUB-THRESHOLD (measured, not unusual; the cost pool)"]
                if not now.sub_threshold:
                    lines.append("    none")
                for finding in now.sub_threshold:
                    lines += describe(finding)

    header = [
        "WHY THE COST POOL WAS EMPTY",
        "=" * 78, "",
        f"engine depth {args.depth}, {args.window} games per player, band {args.band}",
        "",
        f"  {'player':<24}{'band':>7}{'assert':>8}{'sub':>6}"
        f"{'3-in-3':>9}{'3-in-4':>9}{'no rule':>9}",
        "  " + "-" * 76,
    ]
    for player, off_band, asserted, sub, shipped_n, e67_n, none_n in table:
        header.append(f"  {player[:23]:<24}{'OUT' if off_band else 'in':>7}"
                      f"{asserted:>8}{sub:>6}{shipped_n:>9}{e67_n:>9}{none_n:>9}")

    tightening = sum(r[5] - r[4] for r in table)
    introducing = sum(r[6] - r[5] for r in table)
    header += [
        "",
        "  3-in-3   the shipped rule: three consecutive imprecise endgame moves",
        "           (E68 calibrated the window against a permutation baseline)",
        "  3-in-4   E67's setting, three drops inside a window of four",
        "  no rule  every imprecise endgame move counted on its own",
        "",
        f"  priority slots E68's tightening cost:      {tightening}",
        f"  priority slots introducing the run cost:   {introducing}",
        "",
        "  Those two numbers are the point. Blaming the calibration for what",
        "  the rule itself did would have been the easy mistake.",
    ]

    text = "\n".join(header + lines) + "\n"
    (args.out / "why-empty.txt").write_text(text, encoding="utf-8")
    print()
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
