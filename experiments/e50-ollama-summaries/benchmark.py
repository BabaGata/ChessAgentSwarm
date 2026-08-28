"""Does a local model earn its place rephrasing the quoted plans?

Screen: docs/notes/experiments.e50-ollama-summaries.md

The quotes work and read like quotes: sentences from two publishers in two
registers, joined by nothing. The question is whether a local model can make them
read as one voice **without** asserting anything the sources do not.

Three arms, so the model has something to beat rather than being adopted for
sounding better — the shape `classifiers.py` uses for the same reason:

    quotes        the floor: what ships today, unchanged
    qwen2.5:3b    1.9 GB, fits alongside Docker and a desktop
    qwen3:8b      5.2 GB, better prose and needs the room

What is measured, per arm:

    accepted %    how often the rewrite survived the grounding check
    novelty       mean share of content words not in the source
    seconds       per opening, because C1 is a constraint not a preference
    the text      printed in full, because the counts cannot say whether it reads
                  well and the author's eye is the instrument that can

**A high acceptance rate is not a good result on its own.** A model that copies
its input scores 100 % and achieves nothing; one that writes freely scores low
and would be worse. The number to read alongside it is novelty, and the thing to
read instead of both is the output.

Usage:
    python benchmark.py [--models qwen2.5:3b,qwen3:8b] [--families 8]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_summary import (  # noqa: E402
    OllamaSummariser,
    QuoteSummariser,
    SummariserUnavailable,
)

QUOTES = Path(__file__).resolve().parents[1] / "e49-opening-resources" / "results" / "quotes.json"
CANDIDATES = Path(__file__).resolve().parents[1] / "e47-opening-knowledge"


def material() -> dict[str, tuple[str, ...]]:
    """The quotes E49 extracted, grouped by opening family.

    Reusing them rather than re-fetching keeps this experiment about the model:
    both arms rephrase exactly the same sentences.
    """
    sys.path.insert(0, str(CANDIDATES))
    from candidates import CANDIDATES as BY_FAMILY  # noqa: PLC0415

    cache = json.loads(QUOTES.read_text(encoding="utf-8"))
    out: dict[str, tuple[str, ...]] = {}
    for family, entries in BY_FAMILY.items():
        quotes: list[str] = []
        for _title, url, _publisher in entries:
            found = cache.get(url)
            if found:
                quotes += found.get("quotes", [])
        if quotes:
            out[family] = tuple(quotes[:4])
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="qwen2.5:3b,qwen3:8b")
    parser.add_argument("--families", type=int, default=8)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    by_family = material()
    families = sorted(by_family, key=lambda f: -len(by_family[f]))[: args.families]

    arms = [QuoteSummariser()] + [
        OllamaSummariser(model=name.strip()) for name in args.models.split(",") if name.strip()
    ]

    lines = [
        "OLLAMA REPHRASING OF THE QUOTED PLANS",
        "=" * 78,
        "",
        "Every arm rephrases the SAME extracted sentences, so the difference is",
        "the model. A rewrite that fails the grounding check falls back to the",
        "quotes, which is what ships today -- trying is never a loss.",
        "",
        "EVIDENCE CLASS: 'composed' means a local model wrote these words from",
        "the cited sentences. It is NOT the publisher's prose and is not endorsed.",
        "",
    ]
    summary_rows = []

    for arm in arms:
        accepted = 0
        novelties: list[float] = []
        durations: list[float] = []
        lines.append("=" * 78)
        lines.append(f"ARM: {arm.name}")
        lines.append("")
        unavailable = None

        for family in families:
            quotes = by_family[family]
            started = time.perf_counter()
            try:
                summary = arm.summarise(family, quotes)
            except SummariserUnavailable as error:
                unavailable = str(error)
                lines.append(f"  {family}: COULD NOT ASK -- {error}")
                break
            elapsed = time.perf_counter() - started
            durations.append(elapsed)
            accepted += int(summary.accepted and summary.evidence_class == "composed")
            if summary.grounding is not None:
                novelties.append(summary.grounding.novelty)

            lines.append("-" * 78)
            lines.append(f"{family}   [{summary.evidence_class}]  {elapsed:.1f}s")
            lines.append(f"  {summary.text}")
            if summary.rejected_for:
                lines.append(f"  REJECTED: {summary.rejected_for}")
            lines.append("")
            print(f"  {arm.name} / {family}: {elapsed:.1f}s "
                  f"{'ok' if summary.accepted else 'fell back'}", flush=True)

        if unavailable:
            summary_rows.append((arm.name, "unavailable", "", ""))
            continue
        n = len(durations) or 1
        summary_rows.append((
            arm.name,
            f"{100 * accepted / n:.0f} %",
            f"{statistics.mean(novelties):.0%}" if novelties else "n/a",
            f"{statistics.mean(durations):.1f}s",
        ))

    lines += ["", "=" * 78, "WHAT THIS MEASURES", "",
              f"  {'arm':<22}{'composed':>10}{'novelty':>10}{'per opening':>14}", ""]
    for name, rate, novelty, seconds in summary_rows:
        lines.append(f"  {name:<22}{rate:>10}{novelty:>10}{seconds:>14}")
    lines += [
        "",
        "A high acceptance rate alone is not a good result: a model that copies",
        "its input scores 100 % and achieves nothing. Read it with novelty, and",
        "read the output instead of both.",
    ]

    out = args.out / "benchmark.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
