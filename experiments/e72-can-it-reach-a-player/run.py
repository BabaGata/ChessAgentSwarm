"""How much of the vocabulary can ever reach a player at all?

Note: docs/notes/experiments.e72-can-it-reach-a-player.md

[[experiments.e71-why-the-pool-was-empty]] found, incidentally, that
`concedes_weakness` is measured, printed on the detection sheet, and **can never
fill a priority slot**: the section structurally cannot price it, because
conceding a structure is a choice rather than a mistake, and the cost pool needs
a price. That is defensible for one claim. It is a question about the system if
it is true of many.

It matters because of what the author is being asked to do. The detection sheet
is **145 boxes across 29 claims**, and marking one is a careful judgement against
a real position. If some of those claims cannot reach a player by any route, the
marks are still worth having -- a wrong detector is worth knowing about -- but
they are worth **less** than marks on claims that do reach someone, and nothing
currently says which is which.

There are exactly two routes to a player:

    asserted    the claim cleared the confidence gate: unusual for this band,
                enough games, replicated. `select_priorities` ranks these first.

    cost pool   it did not, but it is priced, costs at least
                NEGLIGIBLE_COST_PER_GAME, and is not simply rarer than peers.

A claim that takes neither route across every player in the corpus is **mute**:
measured, sheet-listed, and unable to say anything to anyone.

    python run.py --engine stockfish [--cache PATH]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "expert-review"


# Claims that are silent **on purpose**, each with the line that says so. A first
# pass counted these as defects and reported 23 mute claims; two thirds of that
# was the system working. Reporting it would have sent the author to fix code
# that is right.
#
#   executed_motif   s1_tactical_gaps.NOT_ASSERTED -- "knowing what a player does
#                    well matters for not prescribing it, but it is not a
#                    weakness and must not be reported as one"
#   plays_queenless  style.py -- "A tendency is not a weakness, and routing it
#                    through the findings machinery" is refused; it is a profile
#                    field, not a Finding (D3)
#   concedes_weakness.any
#                    s5_pawn_structure -- the pooled claim "reaches this bar for
#                    nobody, and [is] measured, kept in the peer reference, and
#                    never asserted"
BY_DESIGN_KINDS = ("executed_motif", "plays_queenless")
BY_DESIGN_KEYS = ("concedes_weakness.any.own",)


def silent_on_purpose(claim_key: str) -> bool:
    return (claim_key.split(".")[0] in BY_DESIGN_KINDS
            or claim_key in BY_DESIGN_KEYS)


class Tally:
    """What one claim kind managed, across every player."""

    def __init__(self, key: str = "") -> None:
        self.key = key
        self.measured_for = 0        # players whose sections looked at it
        self.fired_for = 0           # players where it had instances
        self.priced_for = 0          # players where it carried a cost
        self.asserted_for = 0        # players where it cleared the gate
        self.pooled_for = 0          # players where it entered the cost pool
        self.chosen_for = 0          # players actually told about it
        self.instances = 0

    @property
    def route(self) -> str:
        if self.chosen_for:
            return "reaches players"
        if self.asserted_for or self.pooled_for:
            return "eligible, never chosen"
        if silent_on_purpose(self.key):
            return "silent by design"
        if not self.fired_for:
            return "never fires"
        if not self.priced_for:
            return "MUTE — fires, never priced, never asserted"
        return "MUTE — fires, priced, never a finding"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="stockfish")
    parser.add_argument("--peers", default=str(
        Path(__file__).resolve().parents[2] / "data" / "raw" / "out" / "peers-3af3206.json"))
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--band", default="1400-1800")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    tallies: dict[str, Tally] = {}

    def tally_for(key: str) -> Tally:
        if key not in tallies:
            tallies[key] = Tally(key)
        return tallies[key]
    players = 0

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("games/*.pgn")):
            player = path.stem
            games = load_games(path)[: args.window]
            corpus = build_corpus(player, games)
            if corpus.n_games == 0:
                continue
            players += 1

            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band=args.band, time_control="rapid", peers=peers,
            )
            agents = default_agents()

            # Every condition a section looked at, before any judgement -- the
            # only view that shows a claim which never reached `watch`.
            for agent in agents:
                try:
                    for condition in agent.measure(context):
                        tally = tally_for(condition.claim_key)
                        tally.measured_for += 1
                        if condition.instances:
                            tally.fired_for += 1
                            tally.instances += condition.instances
                        if condition.cost_wp is not None:
                            tally.priced_for += 1
                except Exception as error:
                    print(f"    {agent.section}: measure unavailable ({error})", flush=True)

            result = diagnose(context, agents)
            picked = select_priorities(result.findings, also=result.sub_threshold)

            for finding in result.findings:
                tally_for(finding.claim.key()).asserted_for += 1
            for finding in result.sub_threshold:
                tally_for(finding.claim.key()).pooled_for += 1
            for priority in picked.priorities:
                tally_for(priority.finding.claim.key()).chosen_for += 1

            print(f"  {player}: {len(picked.priorities)} priorities", flush=True)

    ordered = sorted(tallies.items(), key=lambda kv: (-kv[1].chosen_for, -kv[1].instances, kv[0]))
    lines = [
        "CAN THIS CLAIM EVER REACH A PLAYER?",
        "=" * 92, "",
        f"{players} players, {args.window} games each, band {args.band}, depth {args.depth}.",
        "",
        "Two routes exist: clear the confidence gate (asserted), or be priced",
        "into the cost pool. A claim that took neither for anyone is MUTE --",
        "measured, printed on the detection sheet, and unable to say anything.",
        "",
        f"  {'claim':<38}{'fires':>7}{'priced':>8}{'assert':>8}{'pool':>6}{'told':>6}  route",
        "  " + "-" * 88,
    ]
    for key, t in ordered:
        lines.append(
            f"  {key[:37]:<38}{t.fired_for:>7}{t.priced_for:>8}"
            f"{t.asserted_for:>8}{t.pooled_for:>6}{t.chosen_for:>6}  {t.route}"
        )

    groups: dict[str, list[str]] = defaultdict(list)
    for key, t in ordered:
        groups[t.route].append(key)

    lines += ["", "=" * 92, "SUMMARY", "=" * 92, ""]
    for route in ("reaches players", "eligible, never chosen", "silent by design",
                  "MUTE — fires, priced, never a finding",
                  "MUTE — fires, never priced, never asserted", "never fires"):
        got = groups.get(route, [])
        lines.append(f"  {route:<45} {len(got):>3}")
    mute = sum(len(v) for k, v in groups.items() if k.startswith("MUTE"))
    lines += [
        "", f"  in the vocabulary                             {len(ordered):>3}",
        f"  MUTE (fire, and can never be told to anyone)  {mute:>3}",
        "",
        "  `silent by design` is not a defect: a strength, a style tendency and a",
        "  pooled claim that discriminates nobody are all deliberately kept out of",
        "  the priorities, each with a line in the code saying so.",
        "",
    ]
    for route in ("MUTE — fires, priced, never a finding",
                  "MUTE — fires, never priced, never asserted", "silent by design"):
        if groups.get(route):
            lines.append(f"  {route}:")
            for key in groups[route]:
                lines.append(f"      {key}")
            lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "reachability.txt").write_text(text, encoding="utf-8")
    print()
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
