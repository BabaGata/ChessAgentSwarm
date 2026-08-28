"""Turn a stored run back into the text report, and ask the store questions.

Screen: docs/notes/experiments.e53-storage.md

The store exists because performance mattered more than readability, so this is
the readability half: one command turns any run back into the same report the
experiments used to write, and the same command answers the questions a text file
never could.

    python dump_run.py                          the most recent runs
    python dump_run.py --run 7                  one run in full
    python dump_run.py --opening "Pirc Defense" the latest run for an opening
    python dump_run.py --dropped                why points are lost, everywhere
    python dump_run.py --domains                which sites actually yield notes
    python dump_run.py --unfinished             runs that died partway
    python dump_run.py --pending                briefs waiting to be read
    python dump_run.py --approve 4              show every point of run 4
    python dump_run.py --approve 4 --points 1,3 show only those two
    python dump_run.py --withdraw 4 --points 2  stop showing that one
    python dump_run.py --reject 4               read it, approve nothing

Approving is the same act as setting `reviewed: true` on a guide link, and it is
the author's alone: `RunStore.approved_brief` is the only door the report reads
through, and it returns only points a person has approved.

**--points takes 1-based numbers over the KEPT points**, exactly as `--run N`
prints them. Dropped points are not numbered, because numbering something that
failed its own checks would invite approving it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.runstore import DEFAULT_PATH, RunStore  # noqa: E402


def one_run(store: RunStore, run_id: int) -> list[str]:
    rows = [r for r in store.runs(limit=10_000) if r.id == run_id]
    if not rows:
        return [f"no run {run_id}"]
    run = rows[0]

    lines = [
        "=" * 78,
        f"RUN {run.id}   {run.opening}   model={run.model}",
        f"  started  {run.started_at}",
        f"  finished {run.finished_at or 'NOT FINISHED -- what follows is what it had'}",
        "",
    ]

    pages = store.pages(run.id)
    skipped = [p for p in pages if p["outcome"] == "skipped"]
    if skipped:
        lines.append("  SCOUT      skipped before fetching: "
                     + ", ".join(sorted({p["publisher"] for p in skipped})))
    lines.append(f"  SCOUT      {len(pages) - len(skipped)} pages handed on")

    notes_by_page: dict[int, list[str]] = {}
    for note in store.notes(run.id):
        notes_by_page.setdefault(note["page_id"], []).append(note["sentence"])

    for page in pages:
        if page["outcome"] == "skipped":
            continue
        kept = notes_by_page.get(page["id"], [])
        verdict = (f"{len(kept)} kept" if kept
                   else f"not an article -> {page['skip_reason']}"
                   if page["skip_reason"] else "nothing usable")
        lines.append(f"  ASSESSOR   {page['publisher']:<26}{verdict}")
        # Full sentences, not truncated: the store keeps them whole and the
        # report used to crop them for column alignment, which was confusing.
        for sentence in kept:
            lines.append(f"               \"{sentence}\"")
    lines.append("")

    # Numbered so --points can refer to them, and marked so a second reading
    # shows what was already decided.
    for number, point in enumerate(store.kept_points(run.id), start=1):
        mark = "  [approved]" if point["approved"] else ""
        lines.append(f"  {number}. {point['kind'].upper():<6} {point['text']}{mark}")
    for point in store.points(run.id):
        if not point["kept"]:
            lines.append(f"     dropped ({point['kind']}) -- {point['dropped_for']}")
    lines += ["", f"  approve all: --approve {run.id}"
                  f"   |   some: --approve {run.id} --points 1,3"
                  f"   |   none: --reject {run.id}", ""]
    return lines


def _numbers(text: str | None) -> list[int] | None:
    """Read "1,3" into [1, 3]. None means every point, which is the default."""
    if not text:
        return None
    return [int(part) for part in text.replace(" ", ",").split(",")
            if part.strip().isdigit()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--run", type=int, default=None)
    parser.add_argument("--opening", default=None)
    parser.add_argument("--dropped", action="store_true")
    parser.add_argument("--domains", action="store_true")
    parser.add_argument("--unfinished", action="store_true")
    parser.add_argument("--pending", action="store_true")
    parser.add_argument("--approve", type=int, default=None)
    parser.add_argument("--withdraw", type=int, default=None)
    parser.add_argument("--reject", type=int, default=None,
                        help="mark a run read with nothing approved")
    parser.add_argument("--points", default=None,
                        help="1-based point numbers, as --run N prints them: 1,3")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    if not args.db.exists():
        print(f"no store at {args.db} -- run the swarm with --store first")
        return 1

    store = RunStore(args.db)
    lines: list[str] = []

    chosen = _numbers(args.points)

    if args.approve is not None:
        count = store.approve(args.approve, chosen)
        lines = [f"run {args.approve}: {count} point(s) approved -- they may now "
                 f"reach a player"]
    elif args.withdraw is not None:
        count = store.withdraw(args.withdraw, chosen)
        lines = [f"run {args.withdraw}: {count} point(s) withdrawn -- nothing "
                 f"deleted, they stop showing"]
    elif args.reject is not None:
        store.mark_reviewed(args.reject)
        lines = [f"run {args.reject} marked read with nothing approved -- it will "
                 f"not appear as pending again"]
    elif args.pending:
        lines += ["BRIEFS WAITING TO BE READ", "=" * 78, "",
                  "Read one with --run N, then --approve N.", ""]
        for run in store.pending(limit=args.limit):
            lines.append(f"  run {run.id:<5} {run.opening:<26}"
                         f"{run.points_kept} points   {run.started_at}")
        if not store.pending():
            lines.append("  none")
    elif args.dropped:
        lines += ["WHY POINTS ARE DROPPED, ACROSS EVERY RUN", "=" * 78, ""]
        for row in store.drop_reasons(limit=args.limit):
            lines.append(f"  {row['n']:>5}  {row['dropped_for']}")
    elif args.domains:
        lines += ["WHICH SITES YIELD NOTES, ACROSS EVERY RUN", "=" * 78, "",
                  f"  {'publisher':<32}{'pages':>7}{'notes':>7}", ""]
        for row in store.productive_domains(limit=args.limit):
            lines.append(f"  {row['publisher'][:31]:<32}{row['pages']:>7}"
                         f"{row['notes']:>7}")
    elif args.unfinished:
        lines += ["RUNS THAT DID NOT FINISH", "=" * 78, ""]
        for run in store.unfinished():
            lines.append(f"  run {run.id:<5} {run.opening:<26}{run.started_at}"
                         f"   {run.pages} pages, {run.notes} notes")
        if not store.unfinished():
            lines.append("  none")
    elif args.run is not None:
        lines += one_run(store, args.run)
    elif args.opening:
        run = store.latest(args.opening)
        lines += one_run(store, run.id) if run else [f"no run for {args.opening}"]
    else:
        lines += ["RUNS, MOST RECENT FIRST", "=" * 78, "",
                  f"  {'id':>4}  {'opening':<26}{'pages':>6}{'notes':>6}"
                  f"{'kept':>6}  started", ""]
        for run in store.runs(limit=args.limit):
            mark = "" if run.finished else "  (unfinished)"
            if run.points_approved:
                mark += f"  {run.points_approved} SHOWN"
            elif run.reviewed:
                mark += "  reviewed, none shown"
            lines.append(f"  {run.id:>4}  {run.opening[:25]:<26}{run.pages:>6}"
                         f"{run.notes:>6}{run.points_kept:>6}  "
                         f"{run.started_at}{mark}")

    store.close()
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
