"""One session end to end with the real model, scripted input, for the record.

Usage:
    python demo.py PLAYER "question 1" "question 2" ... -- MOVE MOVE ...
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from chesscoach.after_report import ask_questions, practise, summary_lines  # noqa: E402
from chesscoach.explainer import render  # noqa: E402
from chesscoach.graph import GraphStore, GraphUnavailable, settings_from_env  # noqa: E402
from chesscoach.profile.io import load_profile  # noqa: E402


def scripted(lines):
    queue = list(lines)

    def read(prompt):
        answer = queue.pop(0) if queue else ""
        print(f"{prompt}{answer}")
        return answer
    return read


def main() -> int:
    player, *rest = sys.argv[1:]
    split = rest.index("--") if "--" in rest else len(rest)
    questions, moves = rest[:split], rest[split + 1:]
    profile = load_profile(Path(__file__).parent / "results" / "profiles" / f"{player}.json")
    report = render(profile)
    print("\n".join(summary_lines(profile)))
    print(report)
    try:
        store = GraphStore.connect(settings_from_env())
    except GraphUnavailable:
        store = None
    ask_questions(report, scripted([*questions, ""]), print, store=store, profile=profile)
    practise(profile, scripted(["y", *moves]), print)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
