"""Why did an arm return nothing? Print the raw Ollama response.

qwen3:8b scored 0 % composed with 0 % novelty and no rejection reason, which is
the signature of an EMPTY response rather than a rejected one. Before that goes
in a note as a fact about the model, it has to be separated from a fact about
this harness (L-046).

Usage:
    python probe_model.py --model qwen3:8b
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.opening_summary import PROMPT, OLLAMA_URL  # noqa: E402

NOTES = (
    "Black allows White to occupy the center with pawns on e4 and d4, aiming to "
    "undermine it later with well timed pawn breaks and piece pressure. "
    "Black aims to stay flexible, first completing development and only later "
    "choosing a pawn break."
)


def ask(model: str, num_predict: int, think: bool | None) -> dict:
    body = {
        "model": model,
        "prompt": PROMPT.format(opening="Pirc Defense", notes=NOTES, sentences=3),
        "stream": False,
        "options": {"temperature": 0.3, "seed": 7, "num_predict": num_predict},
    }
    if think is not None:
        body["think"] = think
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()

    for num_predict, think in ((220, None), (900, None), (900, False)):
        label = f"num_predict={num_predict} think={think}"
        try:
            payload = ask(args.model, num_predict, think)
        except Exception as error:
            print(f"{label}: FAILED {type(error).__name__} {error}")
            continue
        response = payload.get("response", "")
        thinking = payload.get("thinking", "")
        print(f"\n=== {label} ===")
        print(f"  done_reason : {payload.get('done_reason')}")
        print(f"  eval_count  : {payload.get('eval_count')}")
        print(f"  thinking len: {len(thinking)}")
        print(f"  response len: {len(response)}")
        print(f"  response    : {response[:400]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
