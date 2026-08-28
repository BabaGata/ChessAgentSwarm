"""Why does a page with 40 usable sentences yield none?

`supply.py` counted 1,061 sentences passing the veto across 38 cached pages, and
the Assessor turned them into 3 notes. The filters are therefore not the
constraint, and the loss is between offering sentences and reading an answer.

Two candidates, and they need different fixes:

  the model answers NONE or garbage when handed 50 numbered sentences at once;
  the veto after selection removes what it chose.

So this prints, per page: how many were offered, the model's raw answer, how many
indices parsed, and how many survived the veto. Nothing is inferred.

Usage:
    python probe_assessor.py [--offered 50] [--pages 6]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach import ollama  # noqa: E402
from chesscoach.opening_plans import is_admissible  # noqa: E402
from chesscoach.opening_swarm import ASSESSOR, Assessor  # noqa: E402

CACHE = Path(__file__).parent / "results" / "pages.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--offered", type=int, default=50)
    parser.add_argument("--pages", type=int, default=6)
    parser.add_argument("--keep", type=int, default=4)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    pages: dict[str, str] = json.loads(CACHE.read_text(encoding="utf-8"))
    assessor = Assessor(model=args.model, keep=args.keep)

    lines = [f"WHY A PAGE YIELDS NOTHING  offered={args.offered} keep={args.keep}",
             "=" * 78, ""]
    yielded = 0
    looked = 0

    for url, body in sorted(pages.items()):
        if not body or looked >= args.pages:
            continue
        sentences = assessor.candidates(body)[: args.offered]
        if len(sentences) < 5:
            continue
        looked += 1

        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences))
        answer = ollama.generate(
            args.model,
            ASSESSOR.format(opening="this opening", sentences=numbered,
                            limit=args.keep),
            num_predict=60,
        )
        chosen = ollama.indices(answer, len(sentences))[: args.keep]
        kept = [sentences[i] for i in chosen if is_admissible(sentences[i])]
        yielded += int(bool(kept))

        lines.append("-" * 78)
        lines.append(url.split("//")[-1][:70])
        lines.append(f"  offered {len(sentences)}   parsed {len(chosen)}   "
                     f"kept after veto {len(kept)}")
        lines.append(f"  raw answer: {answer.strip()[:100]!r}")
        for sentence in kept:
            lines.append(f"    \"{sentence[:86]}\"")
        print(f"  {url[:52]}: {len(kept)}", flush=True)

    lines += ["", "=" * 78,
              f"  pages yielding at least one note: {yielded} of {looked}"]
    text = "\n".join(lines)
    print("\n" + text[-1200:])
    (args.out / f"assessor-probe-{args.offered}.txt").write_text(
        text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
