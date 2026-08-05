"""E07 — which classifier is allowed to decide a player's gap type?

capacity.agents.prober § 4 forbids any probe result changing a finding until the
rubric has a measured agreement figure. This measures it, for every classifier
available, against the same hand-labelled answers.

Agreement is reported as **Cohen's kappa** as well as raw accuracy, because the
label distribution is uneven and a classifier that answered "yes" to everything
would score respectably on accuracy alone.

Usage:
    python run.py --answers answers.jsonl [--models a,b]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from chesscoach.classifiers import (  # noqa: E402
    ClassifierUnavailable,
    EmbeddingBaseline,
    KeywordFloor,
    OllamaClassifier,
)

LABELS = (True, False, None)


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def cohens_kappa(pairs: list[tuple]) -> float:
    """Agreement above what two raters would reach by chance alone."""
    n = len(pairs)
    if not n:
        return 0.0

    observed = sum(1 for gold, got in pairs if gold == got) / n
    gold_counts, got_counts = Counter(g for g, _ in pairs), Counter(g for _, g in pairs)
    expected = sum((gold_counts[label] / n) * (got_counts[label] / n) for label in LABELS)
    return (observed - expected) / (1 - expected) if expected != 1 else 1.0


def evaluate(classifier, answers: list[dict]) -> dict | None:
    """None when the backend is not reachable.

    Scoring an unreachable model would report every answer as "cannot tell" and
    quietly produce a kappa — a number about nothing. Better to say the model was
    not running.
    """
    started = time.perf_counter()
    try:
        pairs = [
            (item["label"], classifier.classify(item["answer"], item["expected"]))
            for item in answers
        ]
    except ClassifierUnavailable as error:
        print(f"  {classifier.name:<38} UNREACHABLE — {error}")
        return None
    elapsed = time.perf_counter() - started

    correct = sum(1 for gold, got in pairs if gold == got)
    # The costly error: the player understood, and we recorded a knowledge gap.
    understood_but_marked_wrong = sum(
        1 for gold, got in pairs if gold is True and got is False
    )
    return {
        "name": classifier.name,
        "accuracy": correct / len(pairs),
        "kappa": cohens_kappa(pairs),
        "false_ignorance": understood_but_marked_wrong,
        "seconds_each": elapsed / len(pairs),
        "pairs": pairs,
    }


def self_consistency(classifier, answers: list[dict], repeats: int) -> dict | None:
    """Does the same answer get the same verdict every time?

    `capacity.agents.prober` § 10 claims temperature 0 and a fixed seed make a
    verdict reproducible, and `ProbeRecord.classifier` is recorded on that
    basis — so a stored gap_type can supposedly be re-derived. That claim was
    asserted and never measured. This measures it (§ 9 level 4).
    """
    try:
        runs = [
            [classifier.classify(item["answer"], item["expected"]) for item in answers]
            for _ in range(repeats)
        ]
    except ClassifierUnavailable as error:
        print(f"  {classifier.name:<38} UNREACHABLE — {error}")
        return None

    unstable = [
        (answers[i]["answer"], sorted({str(run[i]) for run in runs}))
        for i in range(len(answers))
        if len({run[i] for run in runs}) > 1
    ]
    return {
        "name": classifier.name,
        "stable": len(answers) - len(unstable),
        "total": len(answers),
        "unstable": unstable,
    }


def _disagreements(answers: list[dict], pairs: list[tuple]) -> list[str]:
    return [
        f"      {item['answer'][:58]!r} -> {got} (labelled {gold})"
        for item, (gold, got) in zip(answers, pairs)
        if gold != got
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", type=Path, default=Path(__file__).parent / "answers.jsonl")
    parser.add_argument("--models", default="llama3.1:8b-instruct-q6_K,llama3.2:3b")
    parser.add_argument("--show-disagreements", action="store_true")
    parser.add_argument(
        "--repeat",
        type=int,
        default=0,
        help="measure self-consistency instead of agreement: classify everything N times",
    )
    args = parser.parse_args()

    answers = load(args.answers)
    print(f"{len(answers)} hand-labelled answers "
          f"({sum(1 for a in answers if a['label'] is True)} yes, "
          f"{sum(1 for a in answers if a['label'] is False)} no, "
          f"{sum(1 for a in answers if a['label'] is None)} unclear)\n")

    classifiers = [KeywordFloor(), EmbeddingBaseline()]
    classifiers += [OllamaClassifier(model=m) for m in args.models.split(",") if m]

    if args.repeat:
        print(f"self-consistency over {args.repeat} runs\n")
        for classifier in classifiers:
            result = self_consistency(classifier, answers, args.repeat)
            if result is None:
                continue
            share = result["stable"] / result["total"]
            print(f"  {result['name']:<38} {result['stable']}/{result['total']} stable ({share:.0%})")
            for answer, verdicts in result["unstable"][:5]:
                print(f"      {answer[:52]!r} -> {verdicts}")
        return 0

    print(f"  {'classifier':<38} {'acc':>6} {'kappa':>7} {'false-ign':>10} {'s/call':>8}")
    results = []
    for classifier in classifiers:
        result = evaluate(classifier, answers)
        if result is None:
            continue
        results.append(result)
        print(f"  {result['name']:<38} {result['accuracy']:>6.0%} {result['kappa']:>7.2f} "
              f"{result['false_ignorance']:>10} {result['seconds_each']:>8.2f}")

    if not results:
        print("\nno classifier could be evaluated")
        return 1

    if args.show_disagreements:
        for result in results:
            print(f"\n  {result['name']} disagreed on:")
            print("\n".join(_disagreements(answers, result["pairs"])) or "      (none)")

    best = max(results, key=lambda r: r["kappa"])
    print(f"\nbest agreement: {best['name']} (kappa {best['kappa']:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
