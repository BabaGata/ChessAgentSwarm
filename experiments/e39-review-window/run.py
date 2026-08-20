"""E39 — is a 20-game read enough to judge a player?

The reviewer, six players into the expert review: *"I reviewed 20 games per
player up to maikel5, is this going to be enough."*

Two different power questions hide in that, and they have different answers.

**The move-level comparison** ([[experiments.e31-move-level-agreement]]) is fed by
individual annotated moves, and six players have already produced 270 checkable
ones. That is not the fragile part.

**The pre-registered agreement test** is. It asks whether the system's top
finding appears in the reviewer's ranked slots, for at least 7 of 12 players —
and the reviewer ranks from **20 games** while the report is built from **~50**.
If a 20-game window does not agree with the full corpus about what a player's
main weakness is, then some disagreement is sampling rather than judgement, and
the review would be measuring the window instead of the swarm.

So: run the swarm on each player's first 20 games and on their whole corpus, both
against the same reference, and ask how often the leading finding survives.

[[experiments.e17-ranking-stability]] asked a version of this and found severity
rankings agreeing 65 % at 20 games. That was before the error threshold moved to
5.0, before S7, and against a five-player-per-stratum reference — so it is worth
asking again rather than citing.

Usage:
    python run.py --engine PATH --peers PEERS [--cache CACHE] [--window 20]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.arbiter import select_priorities  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"


@dataclass
class Verdict:
    player: str
    window_top: str | None
    window_all: tuple[str, ...]
    full_top: str | None
    full_all: tuple[str, ...]

    @property
    def top_survives(self) -> bool:
        return self.window_top is not None and self.window_top == self.full_top

    @property
    def full_top_seen_in_window(self) -> bool:
        """Weaker test: the full-corpus answer appears anywhere in the window's list."""
        return self.full_top is not None and self.full_top in self.window_all

    @property
    def overlap(self) -> int:
        return len(set(self.window_all) & set(self.full_all))


def priorities(player: str, games, session, peers) -> tuple[str, ...]:
    corpus = build_corpus(player, games)
    if corpus.n_games == 0:
        return ()
    observations = analyse_corpus(corpus, games, session.analyser)
    context = SectionContext(
        observations, corpus, session.provenance(corpus.corpus_id),
        band="1400-1800", time_control="rapid", peers=peers,
    )
    result = diagnose(context, default_agents())
    selection = select_priorities(
        result.findings, limit=3, also=result.sub_threshold
    )
    return tuple(p.finding.claim.key() for p in selection.priorities)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--peers", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    peers = PeerReference.load(args.peers)
    verdicts: list[Verdict] = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(GAMES.glob("*.pgn")):
            player = path.stem
            games = load_games(path)
            window = priorities(player, games[: args.window], session, peers)
            full = priorities(player, games, session, peers)
            verdicts.append(
                Verdict(player, window[0] if window else None, window,
                        full[0] if full else None, full)
            )
            print(f"  {player}: done", flush=True)

    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say()
    say(f"DOES A {args.window}-GAME READ AGREE WITH THE WHOLE CORPUS?")
    say(f"{'player':<22}{'window top':<34}{'full-corpus top':<34}{'same':>6}")
    say("-" * 96)
    for v in verdicts:
        say(f"{v.player:<22}{(v.window_top or '(silent)'):<34}"
            f"{(v.full_top or '(silent)'):<34}{'yes' if v.top_survives else 'NO':>6}")

    n = len(verdicts)
    same = sum(1 for v in verdicts if v.top_survives)
    seen = sum(1 for v in verdicts if v.full_top_seen_in_window)
    silent = sum(1 for v in verdicts if v.window_top is None)
    overlaps = [v.overlap for v in verdicts]

    say()
    say(f"  top finding identical                 {same}/{n}  ({same/n:.0%})")
    say(f"  full-corpus top appears in the window {seen}/{n}  ({seen/n:.0%})")
    say(f"  window says nothing at all            {silent}/{n}")
    say(f"  median claims shared out of 3         {statistics.median(overlaps):.1f}")

    (args.out / "screen.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {args.out / 'screen.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
