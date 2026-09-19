"""E90, second arm: the summary written one finding at a time, on the same profiles.

The first arm (`run.py`) summarised the whole report in one call; reading its
output by hand found findings mixed up. This re-runs only the summary, on the
profiles `run.py` already built, so the two arms differ in nothing but the method.

Usage:
    python summaries.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from chesscoach.narrator import facts, narrate  # noqa: E402
from chesscoach.profile.io import load_profile  # noqa: E402

OUT = Path(__file__).parent / "results"


def main() -> int:
    rows = []
    for path in sorted((OUT / "profiles").glob("*.json")):
        profile = load_profile(path)
        started = time.perf_counter()
        narration = narrate(profile)
        rows.append({
            "player": path.stem,
            "findings": len(facts(profile)),
            "accepted": narration.accepted,
            "reason": narration.reason,
            "seconds": round(time.perf_counter() - started, 2),
            "summary": narration.text,
        })
        print(f"{path.stem:24} {'kept' if narration.accepted else 'REJECTED':9} "
              f"{rows[-1]['seconds']:5.1f}s  {narration.reason[:90]}", flush=True)
        (OUT / "summaries-fact-sheets.json").write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    findings = sum(r["findings"] for r in rows)
    left_out = sum(int(r["reason"].split(" of ")[0]) for r in rows
                   if r["reason"] and " of " in r["reason"] and r["accepted"])
    rejected = sum(r["findings"] for r in rows if not r["accepted"])
    print(f"\nreports with a summary {sum(r['accepted'] for r in rows)}/{len(rows)}; "
          f"findings kept {findings - left_out - rejected}/{findings}; "
          f"median {sorted(r['seconds'] for r in rows)[len(rows) // 2]} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
