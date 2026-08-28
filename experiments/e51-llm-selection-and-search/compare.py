"""Does a model select better plan sentences than eight regexes, and search better?

Screen: docs/notes/experiments.e51-llm-selection-and-search.md

Two questions the author raised, measured on the same twelve families.

**Selection.** The regexes are brittle: six of the eight filters exist because a
specific bad sentence shipped. What has never been measured is what they *reject*
wrongly. So both selectors run on the same pages and the disagreement is printed
in full — the sentences only one of them found are the whole answer, and no count
can substitute for reading them.

**Search.** The plain query is one hand-written string that has never been varied,
and it returned a Duolingo blog post for the Grob. `GuidedSearcher` lets the model
throw results away and reword. Measured: results kept, wordings tried, and the
kept URLs printed for the author.

Both need a model running and, for the search half, SearxNG:
    cd ../e50-ollama-summaries/searxng && docker compose up -d

Usage:
    python compare.py [--families 8] [--search]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e47-opening-knowledge"))

from candidates import CANDIDATES  # noqa: E402

from chesscoach.opening_agent import Gap, SearchUnavailable, SearxSearcher  # noqa: E402
from chesscoach.opening_search import GuidedSearcher  # noqa: E402
from chesscoach.plan_selector import LlmSelector, RegexSelector, is_plan_sentence  # noqa: E402

PAGES = Path(__file__).resolve().parents[1] / "e48-opening-agent" / "results" / "page-text.json"

# Openings with no curated guide -- the case the searcher exists for.
UNCOVERED = ("Bird Opening", "Grob Opening", "Nimzo-Larsen Attack", "Owen Defense")


def pages() -> dict[str, list[tuple[str, str]]]:
    """Per family, the (publisher, page text) of each candidate that is readable."""
    cache = json.loads(PAGES.read_text(encoding="utf-8"))
    out: dict[str, list[tuple[str, str]]] = {}
    for key, entries in CANDIDATES.items():
        family = key.split(":")[0].strip()
        for _title, url, publisher in entries:
            text = cache.get(url, "")
            if text and not text.startswith("__UNREADABLE__"):
                out.setdefault(family, []).append((publisher, text))
    return out


def compare_selection(by_family, families, lines) -> None:
    regex, llm = RegexSelector(), LlmSelector()
    both = regex_only = llm_only = 0
    durations: list[float] = []

    lines += ["=" * 78, "SELECTION -- eight regexes against a local model", ""]
    for family in families:
        for publisher, text in by_family[family][:2]:
            # The cached text is already flattened, so it is fed as-is; both
            # selectors see exactly the same input, which is the point.
            picked_regex = set(regex.select(family, text, limit=3))
            started = time.perf_counter()
            picked_llm = set(llm.select(family, text, limit=3))
            durations.append(time.perf_counter() - started)

            both += len(picked_regex & picked_llm)
            regex_only += len(picked_regex - picked_llm)
            llm_only += len(picked_llm - picked_regex)

            lines.append("-" * 78)
            lines.append(f"{family}  [{publisher}]")
            for sentence in sorted(picked_regex & picked_llm):
                lines.append(f"  BOTH       {sentence}")
            for sentence in sorted(picked_regex - picked_llm):
                lines.append(f"  REGEX ONLY {sentence}")
            for sentence in sorted(picked_llm - picked_regex):
                # Would the filters have kept it? If not, this is a sentence the
                # regexes were losing -- which is the question being asked.
                verdict = "kept" if is_plan_sentence(sentence) else "REJECTED by filters"
                lines.append(f"  LLM ONLY   {sentence}")
                lines.append(f"             ^ filters would have {verdict}")
            print(f"  {family} / {publisher}: done", flush=True)

    total = both + regex_only + llm_only or 1
    lines += [
        "", "=" * 78, "SELECTION SUMMARY", "",
        f"  chosen by both              {both:>4}  ({both / total:.0%})",
        f"  regex only                  {regex_only:>4}",
        f"  model only                  {llm_only:>4}",
        f"  seconds per page (model)    {statistics.mean(durations):>6.1f}"
        if durations else "",
        "",
        "The disagreement is the result. A count cannot say which selector was",
        "right, and the sentences above can.",
        "",
    ]


def compare_search(lines) -> None:
    plain = SearxSearcher()
    guided = GuidedSearcher(inner=SearxSearcher())

    lines += ["=" * 78, "SEARCH -- one fixed query against a model that rewords", ""]
    for opening in UNCOVERED:
        gap = Gap(opening=opening, games=5, share=0.3)
        lines.append("-" * 78)
        lines.append(f"{opening}")
        try:
            before = plain.search(gap)
            after = guided.search(gap)
        except SearchUnavailable as error:
            lines.append(f"  COULD NOT ASK -- {error}")
            continue
        lines.append("  plain:")
        for _title, url, publisher in before:
            lines.append(f"    {publisher:<24}{url[:64]}")
        lines.append("  guided:")
        for _title, url, publisher in after:
            lines.append(f"    {publisher:<24}{url[:64]}")
        print(f"  {opening}: {len(before)} -> {len(after)}", flush=True)

    lines += ["", "queries tried and verdicts:", ""]
    for row in guided.log:
        lines.append(f"  {row['opening']:<22}#{row['attempt']}  "
                     f"{row['returned']} returned, {row['kept']} kept   "
                     f"{row['query'][:52]}")
    lines += [
        "",
        "Acquisition is now non-deterministic, so it is recorded instead: the log",
        "above is what makes a run readable when it cannot be replayed exactly.",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", type=int, default=8)
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    by_family = pages()
    families = sorted(by_family, key=lambda f: -len(by_family[f]))[: args.families]

    lines = ["LLM SELECTION AND LLM-GUIDED SEARCH", "=" * 78, ""]
    compare_selection(by_family, families, lines)
    if args.search:
        compare_search(lines)

    out = args.out / "compare.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
