"""E90: does the local model's summary pass its check, and what do follow-ups get?

Design: docs/notes/design.narrated-session.md

For each player: build the profile with `coach` exactly as a user would (no
summary, no questions, no practice, so nothing interactive runs), render the
report, then time `narrate` against the real Ollama. For the first few players
ask three fixed follow-up questions -- one the report answers, one about what to
do, one about a chess idea only the books can answer -- and record where each
answer came from.

Usage:
    python run.py --players 20 --engine stockfish --cache eval-cache.db
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from chesscoach.explainer import render  # noqa: E402
from chesscoach.followup import answer_followup  # noqa: E402
from chesscoach.narrator import narrate  # noqa: E402
from chesscoach.profile.io import load_profile  # noqa: E402

CORPUS = ROOT / "data" / "raw" / "corpus-rapid"
PEERS = ROOT / "data" / "raw" / "out" / "peers-e84.json"
OUT = Path(__file__).parent / "results"

QUESTIONS = (
    "Why is my first weakness a problem for me?",
    "What should I practise first?",
    "What is a pin?",
)


def build_profile(player: str, pgn: Path, args) -> Path | None:
    out = OUT / "profiles" / f"{player}.json"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(
        [sys.executable, "-m", "chesscoach.cli", "coach", "--player", player,
         "--pgn", str(pgn), "--engine", args.engine, "--peers", str(PEERS),
         "--cache", args.cache, "--band", "1400-1800", "--time-control", "rapid",
         "--no-questions", "--no-summary", "--no-questions-after", "--no-practice",
         "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=1800, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    return out if out.exists() else None


def book_store():
    from chesscoach.graph import GraphStore, GraphUnavailable, settings_from_env
    try:
        return GraphStore.connect(settings_from_env())
    except GraphUnavailable:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", type=int, default=20)
    parser.add_argument("--asked", type=int, default=6, help="players who get the questions")
    parser.add_argument("--engine", default="stockfish")
    parser.add_argument("--cache", default=str(ROOT / "eval-cache.db"))
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    store = book_store()
    saved = OUT / "results.json"
    rows = json.loads(saved.read_text(encoding="utf-8")) if saved.exists() else []
    done = {row["player"] for row in rows}
    for pgn in sorted(CORPUS.glob("*.pgn"))[: args.players]:
        player = pgn.stem
        if player in done:
            continue
        path = build_profile(player, pgn, args)
        if path is None:
            rows.append({"player": player, "error": "no profile"})
            continue
        report = render(load_profile(path))
        started = time.perf_counter()
        narration = narrate(report)
        row = {
            "player": player,
            "accepted": narration.accepted,
            "reason": narration.reason,
            "seconds": round(time.perf_counter() - started, 2),
            "summary": narration.text,
            "report_chars": len(report),
        }
        if len([r for r in rows if "answers" in r]) < args.asked:
            row["answers"] = []
            for question in QUESTIONS:
                started = time.perf_counter()
                reply = answer_followup(question, report, store=store)
                row["answers"].append({
                    "question": question, "source": reply.source.value,
                    "reason": reply.reason, "text": reply.text,
                    "seconds": round(time.perf_counter() - started, 2),
                })
        rows.append(row)
        # Written after every player, so a run stopped part way keeps what it measured.
        (OUT / "results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
        print(f"{player:24} {'kept' if narration.accepted else 'REJECTED':9} "
              f"{row['seconds']:5.1f}s  {narration.reason}", flush=True)

    (OUT / "results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    judged = [r for r in rows if "accepted" in r]
    kept = sum(r["accepted"] for r in judged)
    print(f"\nsummaries kept {kept}/{len(judged)}; "
          f"median {sorted(r['seconds'] for r in judged)[len(judged) // 2]} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
