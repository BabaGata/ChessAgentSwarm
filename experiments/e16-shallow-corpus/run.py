"""E16 — why is the swarm silent for half of players at 24 games?

[[experiments.e12-corpus-depth]] measured *that* coverage falls from 83 % to 53 %
when a player brings 24 games instead of 150. It did not measure *why*, and
[[state]] has been asserting the reason — `FOCUS_DISTINCT_GAMES` — from one
section's experience rather than from a census.

There are five gates between a claim and the player, and four of them move with
sample size in different ways:

    FOCUS_DISTINCT_GAMES = 5      the pattern must appear in 5 separate games
    FOCUS_GAMES_WITH_DATA = 20    the section needs 20 games it can speak about
    ci95[0] > baseline            a Wilson bound, which widens as n falls
    FOCUS_MARGIN = 1.25           magnitude — sample-independent
    replicated                    split-half over the player's own games

This runs the same 84 players at their real depth and truncated to 24 games,
records every tier decision both times, and counts which gate actually fires.

The distinction that matters for what to do about it: a claim blocked by
**magnitude** is one the swarm should stay quiet about however many games arrive,
while a claim blocked by **evidence** is one the depth is hiding.

Usage:
    python run.py --pgn DIR --engine PATH --cache DB --peers JSON [--games 24]
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach import confidence  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.analysis.parallel import prefetch  # noqa: E402
from chesscoach.arbiter import ASSERTABLE  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.ingest.pgn import parse_pgn_file  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

BAND = "1400-1800"
TIME_CONTROL = "rapid"

# Every gate a claim can fail. The fragments are the policy's own words, so this
# cannot drift from the code -- but they must discriminate: "distinct games"
# appears in *two* different reasons and matching on it double-counts.
NOT_A_WEAKNESS = "not actually a weakness (at or below this player's own baseline)"

GATES = (
    ("rate is no worse", NOT_A_WEAKNESS),
    ("seen in only", "seen in fewer than 3 separate games (WATCH_DISTINCT_GAMES)"),
    ("fewer than 5 distinct games", "fewer than 5 distinct games (FOCUS_DISTINCT_GAMES)"),
    ("fewer than 20 games with data", "fewer than 20 games with data (FOCUS_GAMES_WITH_DATA)"),
    ("interval does not exclude", "interval does not exclude the baseline (sample too small)"),
    ("clears the comparison by less", "too small to be worth saying (FOCUS_MARGIN)"),
    ("not replicated", "did not replicate across a split of the player's games"),
)

# The split that decides what to *do* about the silence. An evidence gate is one
# more games could open; the magnitude gate is one they never will, because the
# claim is real and too small to say.
EVIDENCE_GATES = {label for fragment, label in GATES if fragment not in
                  ("rate is no worse", "clears the comparison by less")}
MAGNITUDE_GATE = "too small to be worth saying (FOCUS_MARGIN)"


class Recorder:
    """Wraps the confidence policy and remembers every decision it made."""

    def __init__(self) -> None:
        self.calls: list[tuple[confidence.ClaimStats, confidence.TierDecision]] = []
        self._original = confidence.assign_tier

    def install(self) -> None:
        """Replace `assign_tier` everywhere a section bound it by name.

        The sections do `from chesscoach.confidence import assign_tier`, so the
        name lives in each section module and patching the source module alone
        would silently record nothing.
        """
        def recording(stats):
            decision = self._original(stats)
            self.calls.append((stats, decision))
            return decision

        confidence.assign_tier = recording
        for module in list(sys.modules.values()):
            if module and getattr(module, "__name__", "").startswith("chesscoach.sections"):
                if hasattr(module, "assign_tier"):
                    module.assign_tier = recording

    def reset(self) -> None:
        self.calls.clear()


def blockers_for(decision) -> list[str]:
    """The gates this claim failed, in the policy's own words."""
    if decision.is_assertable:
        return []
    return [
        label
        for fragment, label in GATES
        if any(fragment in reason for reason in decision.reasons)
    ]


def run_one(context: SectionContext, recorder: Recorder):
    """Diagnose, and return what was said, what was blocked, and what never ran.

    Sections that decline wholesale — too few games in which the section's
    subject even came up — return **before** consulting the confidence policy, so
    they are invisible to the recorder and have to be counted separately. That is
    a whole class of silence, and at 24 games it is the one most likely to bite:
    a player with three rook endgames has no endgame section at all.
    """
    recorder.reset()
    result = diagnose(context, default_agents())
    assertable = sum(1 for f in result.findings if f.confidence.tier in ASSERTABLE)
    blocked = [
        blockers_for(decision)
        for _stats, decision in recorder.calls
        if not decision.is_assertable
    ]
    declined = tuple(report.section for report in result.reports if report.insufficient_data)
    return assertable, blocked, declined


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True, type=Path)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--games", type=int, default=24)
    parser.add_argument(
        "--no-prior",
        action="store_true",
        help="withhold the population prior, reproducing the pre-step-4 policy. "
        "The control: comparing today's silence against a figure measured before "
        "the corpus was cleaned and the reference rebuilt would attribute all "
        "three changes to whichever one is being examined.",
    )
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    peers = PeerReference.load(args.peers)
    paths = sorted(args.pgn.glob("*.pgn"))
    recorder = Recorder()
    recorder.install()

    if args.no_prior:
        # Everything else identical -- same games, same reference, same peer
        # rates -- so the difference is the posterior and nothing else.
        SectionContext.prior_for = lambda self, claim_key: None
        print("prior withheld: pre-step-4 policy\n", flush=True)

    print(f"{len(paths)} players, truncated to the most recent {args.games} games\n", flush=True)

    gate_counts: collections.Counter = collections.Counter()
    # Of the claims that failed, how many failed on exactly one gate? Those are
    # the ones a single change could release.
    sole_gate: collections.Counter = collections.Counter()
    silent_sole_gate: collections.Counter = collections.Counter()
    declined_sections: collections.Counter = collections.Counter()
    silent_players: list[str] = []
    spoken_players: list[str] = []
    # For each silent player: real patterns held back only by thin evidence, and
    # real patterns that are simply too small to say.
    recoverable: list[int] = []
    too_small: list[int] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for index, path in enumerate(paths, start=1):
            player = path.stem
            games = parse_pgn_file(path)
            # Most recent N, by date where the PGN carries one.
            ordered = sorted(games, key=lambda g: (g.date or "", g.game_id))
            games = tuple(ordered[-args.games:])

            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue

            prefetch(games, session.cache, engine=args.engine,
                     depth=args.depth, workers=args.workers)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band=BAND, time_control=TIME_CONTROL, peers=peers,
            )

            assertable, blocked, declined = run_one(context, recorder)
            declined_sections.update(declined)

            # A claim the player genuinely has, held back only because the
            # corpus is thin -- no magnitude objection, just not enough games.
            thin = [g for g in blocked if g and NOT_A_WEAKNESS not in g
                    and MAGNITUDE_GATE not in g]
            # A claim that is real, big enough to measure, and too small to say.
            small = [g for g in blocked if MAGNITUDE_GATE in g]

            if assertable:
                spoken_players.append(player)
            else:
                silent_players.append(player)
                recoverable.append(len(thin))
                too_small.append(len(small))

            for gates in blocked:
                gate_counts.update(set(gates))
                if len(gates) == 1:
                    sole_gate.update(gates)
                    if not assertable:
                        # The question is about the silent players specifically:
                        # averaging their gates with the spoken-to ones answers a
                        # different question than the one being asked.
                        silent_sole_gate.update(gates)

            print(f"  {index:>3}/{len(paths)} {player}: {assertable} assertable, "
                  f"{len(blocked)} blocked, {len(declined)} sections declined", flush=True)

    total = total_players = len(spoken_players) + len(silent_players)
    print(f"\n{'=' * 72}")
    print(f"players spoken to   {len(spoken_players)}/{total} "
          f"({len(spoken_players) / total:.0%})")
    print(f"players told nothing {len(silent_players)}/{total} "
          f"({len(silent_players) / total:.0%})")

    print("\nGates that fired, across every blocked claim (a claim can fail several):")
    for label, count in gate_counts.most_common():
        print(f"  {count:>5}  {label}")

    print("\nClaims blocked by exactly ONE gate — what a single change could release:")
    for label, count in sole_gate.most_common():
        print(f"  {count:>5}  {label}")

    print("\nSole-gate blocks among the SILENT players only — the actual question:")
    for label, count in silent_sole_gate.most_common():
        if NOT_A_WEAKNESS not in label:
            print(f"  {count:>5}  {label}")

    print("\nSections that declined wholesale, before the policy was consulted:")
    for section, count in declined_sections.most_common():
        print(f"  {count:>5}/{total_players}  {section}")

    if silent_players:
        with_recoverable = sum(1 for n in recoverable if n > 0)
        print(f"\nThe {len(silent_players)} silent players — is the silence recoverable?")
        print(f"  had a real pattern held back ONLY by thin evidence   "
              f"{with_recoverable}/{len(silent_players)}")
        print(f"  had a real pattern that is simply too small to say   "
              f"{sum(1 for n in too_small if n > 0)}/{len(silent_players)}")
        print(f"  had neither — nothing to say even with more games    "
              f"{sum(1 for t, s in zip(recoverable, too_small) if not t and not s)}"
              f"/{len(silent_players)}")
        print(f"  median recoverable claims per silent player          "
              f"{sorted(recoverable)[len(recoverable) // 2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
