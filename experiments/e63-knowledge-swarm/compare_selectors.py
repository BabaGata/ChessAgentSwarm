"""Three ways of choosing the sentences a definition is picked from.

Design: docs/notes/design.knowledge-base.md

The author, after seeing what the opening Assessor discards:

    "There should be 2 versions tested, one without the assessor and one with
    assessor changed in a way to remove specifics and keep the broad
    definitions"

So three arms, and the current behaviour is kept as the control rather than
assumed to be the worst:

| arm | how sentences reach the judge |
|---|---|
| `assessor` | the opening Assessor, unchanged -- **the control** |
| `definition` | a model pick, with the veto INVERTED to keep broad sentences |
| `none` | no model selection at all; the mechanical filter only |

**The same cached pages for every arm**, so the only variable is selection. The
retrieval, the relevance gate and the judge are identical across the three.

    python compare_selectors.py [--keys fork,hangingPiece]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chesscoach import ollama  # noqa: E402
from chesscoach.knowledge_swarm import KnowledgeSwarm  # noqa: E402
from chesscoach.opening_agent import (  # noqa: E402
    FallbackSearcher,
    SearchUnavailable,
    SearxSearcher,
)
from chesscoach.skiplist import SkipList  # noqa: E402
from run import CACHE, Fetcher  # noqa: E402

ARMS = ("assessor", "definition", "none")
DEFAULT_KEYS = ("fork", "hangingPiece", "trappedPiece", "late_castling")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keys", default=",".join(DEFAULT_KEYS))
    args = parser.parse_args()
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]

    fetch = Fetcher(CACHE)
    print("THREE WAYS OF CHOOSING THE NOTES")
    print("=" * 88)
    print()
    print("Same pages, same relevance gate, same judge. Only the selection differs.")
    print()

    found: dict[str, dict[str, str]] = {}
    for key in keys:
        found[key] = {}
        for arm in ARMS:
            swarm = KnowledgeSwarm(
                searcher=FallbackSearcher(SearxSearcher()),
                fetch=fetch,
                skiplist=SkipList.load(),
                select=arm,
            )
            try:
                entry = swarm.draft(key)
                found[key][arm] = entry.definition
            except (SearchUnavailable, ollama.OllamaUnavailable) as exc:
                found[key][arm] = f"<{type(exc).__name__}>"
            state = found[key][arm]
            print(f"  {key:16} {arm:11} "
                  f"{(state[:70] if state else '(refused -- nothing defines it)')}")
        print()

    print("=" * 88)
    print("SUMMARY")
    print("=" * 88)
    print()
    print(f"{'claim':<16}" + "".join(f"{a:<12}" for a in ARMS))
    print("-" * 52)
    for key in keys:
        row = "".join(
            f"{('yes' if found[key][a] and not found[key][a].startswith('<') else 'no'):<12}"
            for a in ARMS
        )
        print(f"{key:<16}{row}")
    print()
    print("'yes' only means something was produced. Whether it is a DEFINITION")
    print("rather than an example is a judgement, and it is the author's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
