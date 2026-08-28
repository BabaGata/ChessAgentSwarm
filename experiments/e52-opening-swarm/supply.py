"""Where does the note supply actually go?

Screen: docs/notes/experiments.e52-opening-swarm.md

Three notes survived seventeen cached pages, and the Compiler then invented the
rest and was rejected. Every failure measured so far traces here, so before
changing anything the loss is located stage by stage.

No model runs. Each stage is deterministic and countable:

    blocks        readable block-level chunks of the page
    fragments     sentences split out of them
    windowed      inside the length and punctuation window offered to a model
    admissible    passing the current veto (which includes a jargon test)
    usable        passing a veto WITHOUT the jargon and readability tests

The last column is the proposal. The author's correction is that a term a 1500
would have to look up is **not** a reason for the Assessor to throw a sentence
away — the Compiler is what turns notes into something readable, and it cannot
do that with material it never receives.

Usage:
    python supply.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_plans import (  # noqa: E402
    BOARD,
    MAX_WORDS,
    META,
    MIN_WORDS,
    SELL,
    is_admissible,
    is_analysis_line,
    text_blocks,
)

CACHE = Path(__file__).parent / "results" / "pages.json"
_SPLIT = re.compile(r"(?<=[.!?])\s+")


def windowed(fragment: str, whole_block: bool) -> bool:
    """The current window, plus list items that carry no full stop.

    Chess guides put plans in bullet lists -- "King safety: often castle
    queenside in sharp lines" -- and a terminal-punctuation rule drops every one
    of them.
    """
    words = len(fragment.split())
    if not (MIN_WORDS <= words <= MAX_WORDS):
        return False
    return fragment.endswith((".", "!")) or whole_block


def usable(fragment: str) -> bool:
    """Relevance and information, without judging readability."""
    if SELL.search(fragment) or META.search(fragment):
        return False
    if is_analysis_line(fragment):
        return False
    return bool(BOARD.search(fragment))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    pages: dict[str, str] = json.loads(CACHE.read_text(encoding="utf-8"))
    rows = []
    totals = [0, 0, 0, 0, 0]

    for url, body in sorted(pages.items()):
        if not body:
            continue
        blocks = text_blocks(body)
        counts = [len(blocks), 0, 0, 0, 0]
        for block in blocks:
            fragments = _SPLIT.split(block)
            for fragment in fragments:
                fragment = fragment.strip()
                if not fragment:
                    continue
                counts[1] += 1
                if not windowed(fragment, len(fragments) == 1):
                    continue
                counts[2] += 1
                counts[3] += int(is_admissible(fragment))
                counts[4] += int(usable(fragment))
        rows.append((url, counts))
        totals = [t + c for t, c in zip(totals, counts)]

    lines = [
        "WHERE THE NOTE SUPPLY GOES",
        "=" * 88,
        "",
        "blocks -> fragments -> windowed -> admissible (current) / usable (proposed)",
        "",
        f"  {'page':<44}{'blocks':>8}{'frags':>8}{'window':>8}{'admis':>8}{'usable':>8}",
        "",
    ]
    for url, counts in rows:
        short = url.split("//")[-1][:42]
        lines.append(f"  {short:<44}" + "".join(f"{c:>8}" for c in counts))
    lines += [
        "",
        "=" * 88,
        f"  {'TOTAL':<44}" + "".join(f"{t:>8}" for t in totals),
        "",
        f"  pages yielding at least one admissible sentence: "
        f"{sum(1 for _u, c in rows if c[3]):>3} of {len(rows)}",
        f"  pages yielding at least one usable sentence:     "
        f"{sum(1 for _u, c in rows if c[4]):>3} of {len(rows)}",
        "",
        "The gap between the last two columns is what the readability test was",
        "costing, and it is material the Compiler could have worked from.",
    ]
    text = "\n".join(lines)
    print(text)
    (args.out / "supply.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
