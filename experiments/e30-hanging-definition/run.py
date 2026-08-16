"""E30 — does "hanging piece" mean pieces, or pieces and pawns?

Answers the one open disagreement from the first expert review
(docs/notes/evaluation.expert-review.md). The reviewer named *undefended pieces*
as bernes' main weakness and *missing hanging pieces* as the second; the system
measured the second at 3.9 % against 6.9 % for peers -- bernes converts free
material slightly BETTER than their level -- and reported neither.

The reviewer then said what they had counted: **pawns and pieces together**.
`chesscoach/tactics.py` sets `HANGING_MIN_VALUE = 3`, so free pawns are excluded
by construction, with a recorded reason:

    "You hang pieces" is not a claim about pawns. Measured on real games, free
    pawn grabs were the bulk of this motif's firings.

That reason is about **precision of the phrase**, not about whether the pawns
matter. So the two sides were never measuring the same thing, and the question
becomes answerable rather than a difference of opinion:

    does including pawns change what the swarm would have said about this player?

Both directions are measured, because the reviewer named both:

    missed_motif.hangingPiece    free material the player did not take
    allowed_motif.hangingPiece   free material the player handed over

All twelve expert-review players are run, not just bernes, so the comparison has
a population rather than an anecdote. They are the same band and the same depth,
which is what makes the rates comparable at all (E01).

Usage:
    python run.py --cache CACHE --engine PATH [--out results/]
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import tactics  # noqa: E402
from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402
from chesscoach.sections.s1_tactical_gaps import _count  # noqa: E402

GAMES = Path(__file__).resolve().parents[2] / "expert-review" / "games"

# The two readings of the phrase. 3 is what ships (knight or better); 1 admits
# pawns, which is what the reviewer was counting.
PIECES_ONLY = 3
PIECES_AND_PAWNS = 1

CLAIMS = ("missed_motif.hangingPiece.own", "allowed_motif.hangingPiece.own")


@dataclass(frozen=True)
class Row:
    player: str
    claim: str
    threshold: int
    instances: int
    opportunities: int

    @property
    def rate(self) -> float | None:
        return self.instances / self.opportunities if self.opportunities else None


def measure(context: SectionContext, threshold: int) -> dict[str, tuple[int, int]]:
    """S1's own counting, with the motif definition swapped underneath it."""
    original = tactics.HANGING_MIN_VALUE
    tactics.HANGING_MIN_VALUE = threshold
    try:
        counts = _count(context)
    finally:
        tactics.HANGING_MIN_VALUE = original

    out = {}
    for claim in CLAIMS:
        tally = counts.tallies.get(claim)
        out[claim] = (tally.instances, tally.opportunities) if tally else (0, 0)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows: list[Row] = []
    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(GAMES.glob("*.pgn")):
            player = path.stem
            games = load_games(path)
            corpus = build_corpus(player, games)
            observations = analyse_corpus(corpus, games, session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid",
            )

            for threshold in (PIECES_ONLY, PIECES_AND_PAWNS):
                for claim, (instances, opportunities) in measure(context, threshold).items():
                    rows.append(Row(player, claim, threshold, instances, opportunities))
            print(f"  {player}: done", flush=True)

    _report(rows, args.out)
    return 0


def _report(rows: list[Row], out: Path) -> None:
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    for claim in CLAIMS:
        say()
        say("=" * 78)
        say(claim)
        say("=" * 78)
        say(f"{'player':<24}{'pieces only':>26}{'pieces + pawns':>26}")
        say(f"{'':<24}{'inst/opps':>14}{'rate':>12}{'inst/opps':>14}{'rate':>12}")
        say("-" * 78)

        strict_rates, loose_rates = [], []
        for player in sorted({r.player for r in rows}):
            strict = next(r for r in rows
                          if r.player == player and r.claim == claim
                          and r.threshold == PIECES_ONLY)
            loose = next(r for r in rows
                         if r.player == player and r.claim == claim
                         and r.threshold == PIECES_AND_PAWNS)
            if strict.rate is not None:
                strict_rates.append(strict.rate)
            if loose.rate is not None:
                loose_rates.append(loose.rate)

            mark = " <-- reviewer's player" if player == "bernes" else ""
            say(
                f"{player:<24}"
                f"{f'{strict.instances}/{strict.opportunities}':>14}"
                f"{_pct(strict.rate):>12}"
                f"{f'{loose.instances}/{loose.opportunities}':>14}"
                f"{_pct(loose.rate):>12}{mark}"
            )

        say("-" * 78)
        if strict_rates and loose_rates:
            say(f"{'population median':<24}{'':>14}{_pct(statistics.median(strict_rates)):>12}"
                f"{'':>14}{_pct(statistics.median(loose_rates)):>12}")

            bernes_strict = next(r for r in rows if r.player == "bernes"
                                 and r.claim == claim and r.threshold == PIECES_ONLY)
            bernes_loose = next(r for r in rows if r.player == "bernes"
                                and r.claim == claim and r.threshold == PIECES_AND_PAWNS)
            say()
            say(f"  bernes against the population, pieces only    : "
                f"{_ratio(bernes_strict.rate, statistics.median(strict_rates))}")
            say(f"  bernes against the population, pieces + pawns : "
                f"{_ratio(bernes_loose.rate, statistics.median(loose_rates))}")

    (out / "hanging-definition.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out / 'hanging-definition.txt'}")


def _pct(rate: float | None) -> str:
    return "--" if rate is None else f"{rate:.1%}"


def _ratio(rate: float | None, reference: float) -> str:
    if rate is None or not reference:
        return "--"
    return f"{rate:.1%} vs {reference:.1%}  ({rate / reference:.2f}x)"


if __name__ == "__main__":
    raise SystemExit(main())
