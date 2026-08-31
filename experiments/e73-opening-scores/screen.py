"""Does the replacement name different people than the thing it replaces?

Design: docs/notes/design.detectors-name-consequences.md § 1

The note sets its own acceptance test, and sets it as a *falsifier*:

    "Testable: on the review twelve, [the replacement] must name a different set
    of players than the current early_error does. If it names the same people it
    has only been renamed."

`early_error` was marked 0/4 by the author -- *"fires on real errors, explains
them wrongly"* -- and it is a claim about a **circumstance** ("you go wrong
early"). The replacement is a claim about a **choice** ("this opening is costing
you"). If both land on the same players, nothing has been fixed and the second is
the first with better wording.

    python screen.py --engine stockfish [--cache PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.analysis.core import analyse_corpus  # noqa: E402
from chesscoach.ingest.corpus import build_corpus  # noqa: E402
from chesscoach.opening_scores import MIN_GAMES, weak_openings  # noqa: E402
from chesscoach.openings import OpeningBook  # noqa: E402
from chesscoach.orchestrator import default_agents, diagnose  # noqa: E402
from chesscoach.peers import PeerReference  # noqa: E402
from chesscoach.pipeline import engine_session, load_games  # noqa: E402
from chesscoach.sections.base import SectionContext  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "expert-review" / "games"
BOOK = REPO / "data" / "openings" / "book.json"
EARLY = "early_error"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="stockfish")
    parser.add_argument("--peers", default=str(REPO / "data/raw/out/peers-3af3206.json"))
    parser.add_argument("--cache", default=None)
    parser.add_argument("--depth", type=int, default=15)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--repertoire", type=int, default=60,
                        help="games read for the opening scores; the repertoire "
                             "question needs more games than the engine window")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    book = OpeningBook.load(BOOK)
    peers = PeerReference.load(args.peers)
    rows = []

    with engine_session(args.engine, args.depth, args.cache) as session:
        for path in sorted(ROOT.glob("*.pgn")):
            player = path.stem
            all_games = load_games(path)
            corpus = build_corpus(player, all_games[: args.window])
            if corpus.n_games == 0:
                continue

            observations = analyse_corpus(corpus, all_games[: args.window], session.analyser)
            context = SectionContext(
                observations, corpus, session.provenance(corpus.corpus_id),
                band="1400-1800", time_control="rapid", peers=peers,
            )
            result = diagnose(context, default_agents())
            early = sorted({
                f.claim.key() for f in tuple(result.findings) + tuple(result.sub_threshold)
                if f.claim.kind == EARLY
            })
            weak = weak_openings(all_games[: args.repertoire], player, book)
            rows.append((player, early, weak))
            print(f"  {player}: early_error {len(early)}, weak openings {len(weak)}", flush=True)

    named_by_early = {p for p, early, _ in rows if early}
    named_by_weak = {p for p, _, weak in rows if weak}

    lines = [
        "DOES THE REPLACEMENT NAME DIFFERENT PEOPLE?",
        "=" * 84, "",
        f"{len(rows)} players. early_error over {args.window} analysed games; opening",
        f"scores over {args.repertoire} games, floor {MIN_GAMES}.",
        "",
        f"  {'player':<24}{'early_error':>28}   weak opening",
        "  " + "-" * 78,
    ]
    for player, early, weak in rows:
        early_text = ", ".join(k.split(".")[1] for k in early) or "—"
        weak_text = ", ".join(f"{w.family} {w.score:.0%}/{w.games}" for w in weak) or "—"
        lines.append(f"  {player[:23]:<24}{early_text[:27]:>28}   {weak_text}")

    both = named_by_early & named_by_weak
    lines += [
        "", "=" * 84, "",
        f"  named by early_error        {len(named_by_early):>2}  "
        f"{', '.join(sorted(named_by_early)) or '—'}",
        f"  named by the replacement    {len(named_by_weak):>2}  "
        f"{', '.join(sorted(named_by_weak)) or '—'}",
        f"  named by both               {len(both):>2}  {', '.join(sorted(both)) or '—'}",
        "",
    ]
    # A first version failed only on set equality, and called a strict subset a
    # pass at "overlapping 100 %". That is the screen answering a question it was
    # not asked: the note wants a DIFFERENT set, and every player the
    # replacement names already being named is not different, it is narrower.
    fresh = named_by_weak - named_by_early
    if not named_by_weak:
        lines.append("  FAILS: names nobody, so it replaces nothing.")
    elif named_by_weak == named_by_early:
        lines.append("  FAILS: the same set. This is early_error renamed.")
    elif not fresh:
        lines += [
            "  PARTIAL: every player the replacement names is ALREADY named by",
            "  early_error -- a strict subset, not a different set. What it says",
            "  about them is genuinely different and actionable (a named opening",
            "  and a score, against a circumstance), so it is not a rename. But",
            "  it reaches nobody new, and it therefore CANNOT be swapped in for",
            f"  early_error: {len(named_by_early - named_by_weak)} of the "
            f"{len(named_by_early)} players early_error",
            "  names would be left with no opening claim at all.",
        ]
    else:
        lines += [
            f"  PASSES: reaches {len(fresh)} player(s) early_error does not "
            f"({', '.join(sorted(fresh))}).",
        ]
    lines.append("")

    text = "\n".join(lines) + "\n"
    (args.out / "screen.txt").write_text(text, encoding="utf-8")
    print()
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
