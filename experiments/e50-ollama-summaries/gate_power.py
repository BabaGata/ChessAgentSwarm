"""Does the grounding check still work if the model is given the whole page?

The author asks whether the regex plan-selection (step 9) could be dropped and the
model handed the article instead. The regexes are brittle -- six defects were
found by reading one run's output -- so the question is a fair one.

**The concern is that the check and the selection are coupled.** `grounding.py`
asks whether every square and most content words in the output appear in the
source. Against four sentences that is a real constraint. Against a 9,796-word
essay the page already contains most chess vocabulary and dozens of squares, so a
false claim can find its parts scattered across it and pass.

This measures that directly, with no model involved. **A sentence quoted from a
different opening's page is a true sentence that is false here** -- exactly the
shape of a plausible hallucination, and it needs no invention to obtain. Each is
checked against:

    SMALL   the extracted quotes for this opening  (what ships today)
    FULL    the entire page text                   (what dropping step 9 gives)

If the gate rejects them against SMALL and accepts them against FULL, the
selection step is load-bearing for the check and cannot be removed on its own.

Usage:
    python gate_power.py
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "e47-opening-knowledge"))

from candidates import CANDIDATES  # noqa: E402

from chesscoach import grounding  # noqa: E402
from chesscoach.grounding import check  # noqa: E402

QUOTES = Path(__file__).resolve().parents[1] / "e49-opening-resources" / "results" / "quotes.json"
PAGES = Path(__file__).resolve().parents[1] / "e48-opening-agent" / "results" / "page-text.json"


def material() -> dict[str, tuple[str, str]]:
    """Per family: (the extracted quotes, the full page text)."""
    quotes = json.loads(QUOTES.read_text(encoding="utf-8"))
    pages = json.loads(PAGES.read_text(encoding="utf-8"))

    out: dict[str, tuple[str, str]] = {}
    for key, entries in CANDIDATES.items():
        family = key.split(":")[0].strip()
        small: list[str] = []
        full: list[str] = []
        for _title, url, _publisher in entries:
            found = quotes.get(url)
            if found:
                small += found.get("quotes", [])
            text = pages.get(url, "")
            if text and not text.startswith("__UNREADABLE__"):
                full.append(text)
        if small and full:
            out[family] = (" ".join(small), " ".join(full))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    by_family = material()
    families = sorted(by_family)

    lines = [
        "DOES THE GATE STILL BITE IF THE SOURCE IS THE WHOLE PAGE?",
        "=" * 78,
        "",
        "Probe sentences are real quotes from OTHER openings' pages: true there,",
        "false here, and shaped exactly like a plausible hallucination.",
        "",
        "  SMALL = the extracted quotes (ships today)",
        "  FULL  = the entire page text (what dropping the selection step gives)",
        "",
        "A probe that PASSES is a false claim the check would have let through.",
        "",
        f"  {'family':<24}{'words S':>9}{'words F':>9}{'pass S':>9}{'pass F':>9}",
        "",
    ]

    small_pass_rates: list[float] = []
    full_pass_rates: list[float] = []

    for family in families:
        small, full = by_family[family]
        probes = [
            by_family[other][0] for other in families if other != family
        ]
        # One sentence at a time, as a summary sentence would be judged.
        sentences = []
        for probe in probes:
            sentences += [s.strip() for s in probe.split(". ") if len(s.split()) >= 8]
        if not sentences:
            continue

        passed_small = sum(1 for s in sentences if check(s, small).grounded)
        passed_full = sum(1 for s in sentences if check(s, full).grounded)
        rate_small = passed_small / len(sentences)
        rate_full = passed_full / len(sentences)
        small_pass_rates.append(rate_small)
        full_pass_rates.append(rate_full)

        lines.append(
            f"  {family[:23]:<24}{len(small.split()):>9}{len(full.split()):>9}"
            f"{rate_small:>8.0%}{rate_full:>9.0%}"
        )

    lines += [
        "",
        "=" * 78,
        f"  mean false-claim pass rate, SMALL source : {statistics.mean(small_pass_rates):.0%}",
        f"  mean false-claim pass rate, FULL source  : {statistics.mean(full_pass_rates):.0%}",
        "",
        "The selection step is not only a filter on what the model reads. It is",
        "what makes the check on what the model writes mean anything.",
    ]

    # The Compiler now paraphrases more, because the Assessor passes on hard
    # vocabulary for it to translate. So the novelty ceiling has to be chosen
    # against evidence rather than left where it happened to be.
    lines += ["", "=" * 78, "NOVELTY CEILING SWEEP", "",
              "  A higher ceiling lets the Compiler explain a term in words the",
              "  source never used -- and lets a false claim through.", "",
              f"  {'ceiling':>9}{'false claims passing':>24}", ""]
    original = grounding.MAX_NOVELTY
    try:
        for ceiling in (0.35, 0.45, 0.55, 0.65, 0.75):
            grounding.MAX_NOVELTY = ceiling
            rates = []
            for family in families:
                small, _full = by_family[family]
                probes = []
                for other in families:
                    if other == family:
                        continue
                    probes += [s.strip() for s in by_family[other][0].split(". ")
                               if len(s.split()) >= 8]
                if probes:
                    rates.append(
                        sum(1 for p in probes if check(p, small).grounded) / len(probes)
                    )
            lines.append(f"  {ceiling:>9.2f}{statistics.mean(rates):>23.0%}")
    finally:
        grounding.MAX_NOVELTY = original

    text = "\n".join(lines)
    print(text)
    (args.out / "gate-power.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
