"""What the report prints before and after a brief is approved.

Screen: docs/notes/experiments.e53-storage.md

The gate is the point of the whole store: a brief the swarm produced is a
candidate, exactly as a guide link is, and only the author turns a candidate into
something a player sees.

**This works on a COPY of the store.** Approving is the author's act and nothing
here should pre-empt it, so the real `data/runs.db` is left with every run
pending and the copy is thrown away.

Usage:
    python show_gate.py [--db data/runs.db] [--run N]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.explainer import _opening_section  # noqa: E402
from chesscoach.runstore import DEFAULT_PATH, RunStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--run", type=int, default=None)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.db.exists():
        print(f"no store at {args.db}")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "copy.db"
        shutil.copy(args.db, copy)
        store = RunStore(copy)

        pending = store.pending()
        if not pending:
            print("nothing pending to demonstrate with")
            return 1
        run = next((r for r in pending if r.id == args.run), pending[0])

        lines = [
            "THE APPROVAL GATE, ON A COPY OF THE STORE",
            "=" * 74,
            "",
            f"run {run.id}: {run.opening}, {run.points_kept} points kept",
            "",
            "-" * 74,
            "BEFORE -- the run exists, is finished, and nobody has approved it",
            "",
        ]
        before = store.approved_brief(run.opening)
        lines.append(f"  approved_brief() -> {before}")
        lines.append("  report section   -> "
                     + (repr(_opening_section(before)) if before is None
                        else "shown"))

        # Point by point, as the author would: keep the ones that say
        # something, leave the rest. Approving all of them would demonstrate
        # less than approving some.
        kept = store.kept_points(run.id)
        chosen = [i for i, _p in enumerate(kept, start=1) if i != 3]
        store.approve(run.id, chosen)
        after = store.approved_brief(run.opening)
        lines += [
            "",
            "-" * 74,
            f"AFTER -- a person approved points {chosen} and left point 3 out",
            "",
        ]
        lines += _opening_section(after)
        lines += [
            "-" * 74,
            "",
            f"The real store at {args.db} is untouched: every run is still",
            "pending, because approving is the author's act and not this script's.",
        ]
        store.close()

    text = "\n".join(lines)
    print(text)
    (args.out / "gate.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
