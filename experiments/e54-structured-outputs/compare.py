"""Does a JSON Schema fix the answers that were unreadable before?

Screen: docs/notes/experiments.e54-structured-outputs.md

E51 and E52 measured three failure shapes, all of them the model answering in a
form the parser could not read:

  `NONE` where a list of integers was required -- four pages of six;
  `"3, NONE"` -- half a verdict;
  prose whose digits were then read as indices.

Ollama's `format` constrains decoding at the token level, so those become
unrepresentable rather than merely discouraged. This asks the same questions of
the same pages **with and without** the schema and counts what comes back.

**Three arms, because two would be confounded.** The prompt was rewritten at the
same time as the schema was added -- it now shows the JSON shape by example --
and a two-arm test measured both changes at once and credited the schema. The
old prompt is therefore kept here verbatim as the baseline:

    old       the prompt that shipped before, no schema
    asked     the new prompt, which shows the JSON shape, still no schema
    forced    the new prompt AND the schema constraining decoding

What is measured, per arm:

    parsed      answers the caller could read at all
    selected    answers that chose at least one sentence
    refused     answers that chose nothing (a verdict, not a failure)
    seconds     per call, because constrained decoding is not free

**A higher "selected" is not automatically better.** A model that selects
everything parses perfectly and chooses badly. The number that matters is
`parsed`, and the sentences are printed so the choosing can be judged by eye.

Usage:
    python compare.py [--model qwen2.5:3b] [--pages 8]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import ollama  # noqa: E402
from chesscoach.opening_swarm import ASSESSOR, ASSESSOR_SCHEMA, CHUNK, Assessor  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "e52-opening-swarm" / "results" / "pages.json"

# The instruction that shipped before schemas, kept verbatim so the baseline is
# the real previous behaviour rather than a reconstruction of it.
OLD_TAIL = """Pick the {limit} most informative, best first, and answer with \
ONLY their numbers separated by commas.
Answer NONE only if the page is not about chess at all.
"""

NEW_TAIL = """Pick the {limit} most informative, best first.

Answer with the numbers of the sentences you picked, in the "keep" field.
If the page is not about chess at all, keep nothing.
"""


def old_prompt(sentences: str, limit: int) -> str:
    """The new prompt with its JSON instruction swapped back for the old one."""
    body = ASSESSOR.format(opening="this opening", sentences=sentences, limit=limit)
    return body.replace(NEW_TAIL.format(limit=limit), OLD_TAIL.format(limit=limit))


def ask(model: str, prompt: str, schema: dict | None) -> tuple[str, float]:
    started = time.perf_counter()
    answer = ollama.generate(model, prompt, num_predict=60, schema=schema)
    return answer, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--pages", type=int, default=8)
    parser.add_argument("--chunk", type=int, default=CHUNK,
                        help="sentences per question; 50 recreates E52's collapse")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not CACHE.exists():
        print(f"no page cache at {CACHE}")
        return 1
    pages: dict[str, str] = json.loads(CACHE.read_text(encoding="utf-8"))
    assessor = Assessor(model=args.model)

    lines = [
        f"SCHEMA-CONSTRAINED ANSWERS  model={args.model}  chunk={args.chunk}",
        "=" * 78,
        "",
        "The same question, on the same pages, with and without a JSON Schema.",
        "",
    ]
    stats = {"old": [0, 0, 0, 0.0], "asked": [0, 0, 0, 0.0],
             "forced": [0, 0, 0, 0.0]}
    looked = 0

    for url, body in sorted(pages.items()):
        if not body or looked >= args.pages:
            continue
        chunk = assessor.candidates(body)[:args.chunk]
        if len(chunk) < 5:
            continue
        looked += 1

        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(chunk))
        new = ASSESSOR.format(opening="this opening", sentences=numbered, limit=4)
        old = old_prompt(numbered, 4)
        if old == new:
            print("  WARNING: the old prompt no longer differs -- baseline is void")

        lines.append("-" * 78)
        lines.append(url.split("//")[-1][:68])

        for arm, prompt, schema in (
            ("old", old, None),
            ("asked", new, None),
            ("forced", new, ASSESSOR_SCHEMA),
        ):
            answer, seconds = ask(args.model, prompt, schema)
            stats[arm][3] += seconds

            data = ollama.as_json(answer)
            if data is not None:
                readable = True
                chosen = ollama.ints(data, "keep", len(chunk))[:4]
            else:
                # The prose path, exactly as each agent falls back to it.
                chosen = ollama.indices(answer, len(chunk))[:4]
                readable = bool(chosen) or "none" in answer.strip().lower()[:8]

            stats[arm][0] += int(readable)
            stats[arm][1] += int(bool(chosen))
            stats[arm][2] += int(readable and not chosen)
            lines.append(f"  {arm:<8}{seconds:>5.1f}s  "
                         f"{'readable' if readable else 'UNREADABLE':<11}"
                         f"{len(chosen)} chosen   {answer.strip()[:44]!r}")
        print(f"  {url[:56]}: done", flush=True)

    lines += [
        "",
        "=" * 78,
        f"  {'arm':<10}{'parsed':>8}{'selected':>10}{'refused':>9}{'s/call':>9}",
        "",
    ]
    for arm, (parsed, selected, refused, seconds) in stats.items():
        lines.append(f"  {arm:<10}{parsed:>8}{selected:>10}{refused:>9}"
                     f"{seconds / max(looked, 1):>9.1f}")
    lines += [
        "",
        f"  pages asked about: {looked}",
        "",
        "'parsed' is the number that matters: an answer the caller cannot read is",
        "a wasted fetch and a wasted model call. 'refused' is a real verdict --",
        "the page had nothing worth keeping -- and is not a failure.",
        "",
        "old -> asked isolates the PROMPT's effect; asked -> forced isolates the",
        "SCHEMA's. A two-arm test would have credited the schema with both.",
    ]

    text = "\n".join(lines)
    print("\n" + text[-1400:])
    (args.out / f"compare-{args.model.replace(':', '-')}-{args.chunk}.txt").write_text(
        text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
