"""Why does the swarm find nothing usable for these concepts?

Note: docs/notes/experiments.e89-why-nothing-usable.md

Re-drafting `hangingPawn`, `allows_square` and `late_castling` produced **nothing
at all** — and not from the naming gate, which never saw a sentence. Everything
was refused by `is_broad`, before any model ran:

    dropped 16  narrates a player as 'he' or 'she' rather than White or Black
    dropped  7  opens by connecting to the previous sentence
    dropped  2  points at a particular board

Two very different explanations, needing opposite fixes:

  (a) the pages have no definition, and the filter is right;
  (b) the pages define the concept and the filter throws the definition away.

This prints every sentence a page offers, with the filter that refused it, so
the two can be told apart by reading rather than by guessing.

    python run.py --keys hangingPawn,allows_square
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments" / "e63-knowledge-swarm"))

from chesscoach.knowledge_swarm import (  # noqa: E402
    KnowledgeSwarm,
    _names,
    is_broad,
    reads_as_commentary,
    topic_for,
)
from chesscoach.opening_agent import FallbackSearcher, SearxSearcher  # noqa: E402
from chesscoach.skiplist import SkipList  # noqa: E402
from run import CACHE, Fetcher  # noqa: E402


def verdict(sentence: str) -> str:
    """Why this sentence did not survive, in the order the code asks."""
    from chesscoach.knowledge_swarm import _SPECIFIC
    from chesscoach.opening_plans import (
        MAX_WORDS,
        MIN_WORDS,
        NAVIGATION,
        SELL,
        STATISTIC,
        is_analysis_line,
    )

    words = len(sentence.split())
    if words < MIN_WORDS:
        return f"too short ({words}w)"
    if words > MAX_WORDS:
        return f"too long ({words}w)"
    if sentence.endswith("?"):
        return "a question"
    if SELL.search(sentence):
        return "advertising"
    if STATISTIC.search(sentence):
        return "a statistic"
    if NAVIGATION.search(sentence):
        return "navigation"
    if is_analysis_line(sentence):
        return "an analysis line"
    commentary = reads_as_commentary(sentence)
    if commentary:
        return commentary.split(":")[0]
    if _SPECIFIC.search(sentence):
        return "names a square or move"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", default="hangingPawn,allows_square,late_castling")
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    swarm = KnowledgeSwarm(
        searcher=FallbackSearcher(SearxSearcher()),
        fetch=Fetcher(CACHE),
        skiplist=SkipList.load(),
    )

    lines: list[str] = []
    for key in [k.strip() for k in args.keys.split(",") if k.strip()]:
        topic = topic_for(key)
        lines += ["", "=" * 96, f"{key}   (searched as: {topic!r})", "=" * 96]
        try:
            candidates = swarm.scout.find(key)[: args.pages]
        except Exception as exc:  # noqa: BLE001 - a failed search is a result here
            lines.append(f"  search failed: {type(exc).__name__}: {exc}")
            continue
        if not candidates:
            lines.append("  no pages found at all")
            continue

        for candidate in candidates:
            body = swarm.fetch(candidate.url)
            if not body:
                lines += [f"\n  -- {candidate.url}", "     could not fetch"]
                continue
            offered = swarm.assessor.candidates(body)
            lines += [f"\n  -- {candidate.url}", f"     {len(offered)} sentences offered"]
            kept = 0
            for sentence in offered:
                why = verdict(sentence)
                names = _names(sentence, key)
                if not why:
                    kept += 1
                mark = "KEPT " if not why else "     "
                flag = "names-it" if names else "        "
                lines.append(f"     {mark}{flag}  {('' if not why else why)[:38]:<38} "
                             f"{sentence[:110]}")
            lines.append(f"     -> {kept} survived `is_broad`")

    text = "\n".join(lines) + "\n"
    (args.out / "sentences.txt").write_text(text, encoding="utf-8")
    print(text[-14000:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
