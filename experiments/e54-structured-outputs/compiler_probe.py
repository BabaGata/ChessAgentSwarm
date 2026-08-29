"""Does the schema make the Compiler's points worse, or did its input change?

Screen: docs/notes/experiments.e54-structured-outputs.md

Adding schemas took the offline run from five briefs to two. Two things changed
at once, though: the Assessor's schema altered which notes it keeps, so the
Compiler was also being handed different material. Blaming the schema without
separating those would be the confound this experiment already made once.

**The run store makes the separation exact.** Runs recorded before the change
hold their notes verbatim, so the same notes can be compiled twice — once with
the schema and once without — and nothing else differs.

Usage:
    python compiler_probe.py [--db data/runs.db]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import ollama  # noqa: E402
from chesscoach.opening_swarm import Compiler  # noqa: E402
from chesscoach.runstore import DEFAULT_PATH, RunStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.db.exists():
        print(f"no store at {args.db}")
        return 1

    store = RunStore(args.db)
    lines = [
        f"THE COMPILER, SAME NOTES, WITH AND WITHOUT THE SCHEMA  model={args.model}",
        "=" * 78,
        "",
        "Notes replayed verbatim from stored runs, so the ONLY difference is the",
        "`format` field. The offline run's fall from five briefs to two changed",
        "the Assessor at the same time; this does not.",
        "",
    ]
    totals = {"schema": [0, 0], "free": [0, 0]}

    for run in sorted(store.runs(limit=50), key=lambda r: r.id):
        notes = tuple(n["sentence"] for n in store.notes(run.id))
        if len(notes) < 3:
            continue

        lines.append("-" * 78)
        lines.append(f"run {run.id}  {run.opening}   {len(notes)} notes")

        for arm, compiler in (
            ("schema", Compiler(model=args.model)),
            ("free", Compiler(model=args.model, transport=_without_schema)),
        ):
            brief = compiler.compile(run.opening, notes)
            kept = len(brief.plans) + len(brief.watches)
            totals[arm][0] += kept
            totals[arm][1] += len(brief.dropped)
            lines.append(f"  {arm:<8}{kept} kept, {len(brief.dropped)} dropped")
            for point in brief.plans:
                lines.append(f"           PLAN   {point}")
            for point in brief.watches:
                lines.append(f"           WATCH  {point}")
            for point in brief.dropped:
                lines.append(f"           dropped -- {point.dropped_for[:56]}")
        print(f"  run {run.id}: done", flush=True)

    lines += [
        "",
        "=" * 78,
        f"  {'arm':<10}{'points kept':>13}{'dropped':>10}",
        "",
    ]
    for arm, (kept, dropped) in totals.items():
        lines.append(f"  {arm:<10}{kept:>13}{dropped:>10}")
    lines += [
        "",
        "Constrained decoding restricts which tokens are legal at each step. If",
        "the schema costs point quality, this is where it shows -- and if the",
        "arms match, the offline fall was the Assessor's changed notes instead.",
    ]

    store.close()
    text = "\n".join(lines)
    print("\n" + text[-900:])
    (args.out / "compiler-probe.txt").write_text(text + "\n", encoding="utf-8")
    return 0


def _without_schema(url: str, body: dict) -> dict:
    """The same call with `format` stripped, so only the constraint differs."""
    body = {k: v for k, v in body.items() if k != "format"}
    return ollama.post(url, body)


if __name__ == "__main__":
    raise SystemExit(main())
