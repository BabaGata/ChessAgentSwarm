"""Draft knowledge-base entries for the claims that actually reach players.

Design: docs/notes/design.knowledge-base.md (Option C)

    "I want C -- the existing swarm drafts, you approve. LLM agents should be
    used as much as possible."

Not all 33 claims: an entry for a claim no player is ever told about is wasted
work, and across the review twelve only about fourteen ever reached a headline
or a plan. Those come first.

Nothing this writes is ever shown to a player. Every entry lands with
`reviewed=false`, and `KnowledgeBase.for_player` refuses anything else --
endorsement is the author's act, the same rule as `reviewed` on a guide link.

    python run.py [--keys fork,pin] [--model qwen2.5:3b] [--searcher searx]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import ollama  # noqa: E402
from chesscoach.knowledge import KnowledgeBase  # noqa: E402
from chesscoach.knowledge_swarm import KnowledgeSwarm, topic_for  # noqa: E402
from chesscoach.opening_agent import (  # noqa: E402
    AGENT,
    FallbackSearcher,
    SearchUnavailable,
    SearxSearcher,
    WikimediaSearcher,
)
from chesscoach.skiplist import SkipList  # noqa: E402

CACHE = Path(__file__).parent / "results" / "pages.json"
OUT = Path(__file__).resolve().parents[2] / "data" / "knowledge.json"

# The claims that reached a headline or a plan across the review twelve. Ordered
# by how often a player is actually told about them, so a run that is cut short
# has still done the most useful part.
WANTED = (
    "hangingPawn",
    "hangingPiece",
    "capturingDefender",
    "trappedPiece",
    "allows_pressure",
    "allows_square",
    "endgame_error",
    "long_think_error",
    "moved_into_attack",
    "slow_development",
    "late_castling",
    "pawn_error",
    "repeat_move",
    "fork",
)


class Fetcher:
    """Fetches a page once and remembers it, so a re-run costs nothing.

    Lifted from the opening swarm's runner rather than rewritten: 33 claims is a
    small fixed set and one good crawl should never have to be repeated, which
    is also what turns a rate limit into a one-off cost.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._cache: dict[str, str] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    def __call__(self, url: str) -> str:
        if url in self._cache:
            return self._cache[url]
        try:
            request = urllib.request.Request(url, headers={"User-Agent": AGENT})
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(400_000).decode("utf-8", "replace")
        except Exception:
            body = ""
        self._cache[url] = body
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache), encoding="utf-8")
        time.sleep(1.5)
        return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--searcher", choices=("searx", "wikimedia"), default="searx")
    parser.add_argument("--keys", default="", help="comma-separated; default is WANTED")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--redraft", action="store_true",
                        help="re-draft keys that already have a complete entry")
    args = parser.parse_args()

    keys = tuple(k.strip() for k in args.keys.split(",") if k.strip()) or WANTED

    # Wikimedia is the fallback the author asked for, and it is LABELLED: the
    # searcher records whether it fell back, so a Wikimedia-sourced entry can be
    # told from a web-sourced one afterwards.
    primary = SearxSearcher() if args.searcher == "searx" else WikimediaSearcher()
    searcher = FallbackSearcher(primary) if args.searcher == "searx" else primary

    base = KnowledgeBase.load(args.out)
    print(f"{len(base)} entries already; drafting {len(keys)}")
    print(f"missing: {', '.join(base.missing(keys)) or 'nothing'}")
    print()

    swarm = KnowledgeSwarm(
        searcher=searcher,
        fetch=Fetcher(CACHE),
        skiplist=SkipList.load(),
        model=args.model,
    )

    drafted = failed = 0
    for key in keys:
        existing = base.get(key)
        if existing is not None and existing.reviewed:
            print(f"  {key:20} already reviewed, left alone")
            continue
        # Resumable. Long runs here have been killed twice partway through, and
        # each entry costs three searches, four fetches and two model calls --
        # so a re-run continues rather than starting again. `--redraft` is the
        # way to deliberately redo one.
        if existing is not None and existing.complete and not args.redraft:
            print(f"  {key:20} already drafted, skipped (--redraft to redo)")
            continue
        try:
            entry = swarm.draft(key)
        except (SearchUnavailable, ollama.OllamaUnavailable) as exc:
            # "Could not ask" is not "nothing to say", and the difference has to
            # survive into the report of the run (L-046).
            #
            # **And it must not end the run.** A first batch died on claim 7
            # when Ollama returned HTTP 500, losing six claims of completed
            # work -- a recoverable failure treated as fatal, which is the same
            # family of mistake as an empty case answering like a real one.
            print(f"  {key:20} COULD NOT ASK: {type(exc).__name__}: {exc}")
            failed += 1
            continue

        base.draft(entry)
        # Saved per claim, not at the end. Each entry costs three searches, four
        # fetches and two model calls; losing a batch's work to its last claim
        # is not a trade worth making for one less file write.
        base.save(args.out)
        fell_back = getattr(searcher, "fell_back", False)
        if entry.complete:
            drafted += 1
            print(f"  {key:20} drafted from {len(entry.sources)} source(s)"
                  f"{'  [wikimedia fallback]' if fell_back else ''}")
            print(f"  {'':20}   {entry.definition[:88]}")
        else:
            print(f"  {key:20} nothing usable found"
                  f" ({len(entry.sources)} source(s) read)")
        # What the filters refused, so a run that produces nothing still says
        # what it saw. Ordered by count: the commonest reason is the one worth
        # arguing with.
        for reason, count in sorted(swarm.discarded.items(),
                                    key=lambda kv: -kv[1])[:4]:
            print(f"  {'':20}   dropped {count:>4}  {reason}")

    base.save(args.out)
    swarm.skiplist.save()

    print()
    print(f"drafted   {drafted}")
    print(f"could not ask  {failed}")
    print(f"still missing  {len(base.missing(keys))}")
    print()
    print(f"{len(base.pending())} entries are waiting for review.")
    print("Nothing here reaches a player until it is endorsed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
