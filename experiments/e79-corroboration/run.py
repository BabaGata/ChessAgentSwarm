"""What do six voices actually agree about?

Note: docs/notes/experiments.e79-corroboration.md
Design: docs/notes/design.graph-knowledge-base.md § "The evidence rule"

Stage 3. For each concept the detectors can name, the passages nearest it are
retrieved, and a concept is **corroborated** when passages from two or more
independent lineages describe it in wording close enough to be the same idea and
far enough apart not to be a copy.

**No claim is composed.** A concept's evidence is verbatim passages with their
locators; the model is not asked to write a definition, and this stage does not
ask it to. What is measured is which concepts the free shelf can support at all.

The thresholds are swept rather than chosen -- L-054: a distribution says what a
threshold discards, only running the rule says what it buys.

    python run.py [--k 8] [--sweep]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.corroboration import (  # noqa: E402
    AGREEMENT, MIN_LINEAGES, SHARED_ANCESTOR, Attestation, corroborate,
)
from chesscoach.extraction import mentions  # noqa: E402
from chesscoach.graph import GraphStore, GraphUnavailable  # noqa: E402
from chesscoach.knowledge_swarm import TERMS  # noqa: E402


def candidates(store: GraphStore, concept: str, phrases, k: int):
    """Passages near any of the concept's real phrases, with their vectors.

    The phrases come from `TERMS`, measured in E65 against the books and the web
    -- searching for the word I would use is not the same as searching for the
    word writers use, and "outpost" scores 0 where "hole" scores 50.
    """
    seen: dict[str, Attestation] = {}
    vectors: dict[str, list[float]] = {}
    for phrase in phrases:
        for hit in store.search(f"{phrase}: what it is and why it matters", k=k):
            locator = hit["locator"]
            if locator in seen:
                continue
            rows = store._run(
                "MATCH (p:Passage {id:$id})-[:FROM]->(s:Source) "
                "RETURN p.embedding AS v, s.lineage AS lineage", id=locator)
            if not rows:
                continue
            # **The gate.** Without it every chess passage counts, because a
            # passage is retrieved for being similar to the query and then
            # measured for being similar to the others -- 19 concepts of 19
            # servable at every threshold, including `skewer`, which appears
            # zero times on the shelf. `mentions` subtracts the vocabulary every
            # chess book shares and asks whether this one uses the term at all.
            if not mentions(concept, hit["text"], phrases):
                continue
            seen[locator] = Attestation(concept, locator, rows[0]["lineage"],
                                        " ".join(hit["text"].split()))
            vectors[locator] = rows[0]["v"]
    return list(seen.values()), vectors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        store = GraphStore.connect()
    except GraphUnavailable as error:
        print(f"no graph: {error}")
        return 1

    lines = [
        "WHAT DOES THE SHELF AGREE ABOUT?",
        "=" * 94, "",
    ]
    results = []
    with store:
        sources = store._run("MATCH (s:Source) RETURN count(DISTINCT s.lineage) AS n")
        lineages = sources[0]["n"] if sources else 0
        lines += [f"{lineages} independent lineages, "
                  f"{store.counts().get('Passage', 0)} passages, k={args.k}.",
                  f"agreement >= {AGREEMENT}, shared-ancestor flag >= {SHARED_ANCESTOR}, "
                  f"minimum {MIN_LINEAGES} lineages.", ""]

        for concept in sorted(TERMS):
            found, vectors = candidates(store, concept, TERMS[concept], args.k)
            got = corroborate(concept, found, vectors)
            results.append((concept, got, found, vectors))

        lines += [f"  {'concept':<26}{'passages':>9}{'voices':>8}{'served':>8}  who",
                  "  " + "-" * 90]
        served = 0
        for concept, got, found, _ in results:
            served += got.servable()
            lines.append(
                f"  {concept[:25]:<26}{len(found):>9}{got.independent:>8}"
                f"{('YES' if got.servable() else 'no'):>8}  "
                f"{', '.join(v.split()[-1] for v in got.lineages)[:44]}")

        flags = [(c, g.shared_ancestors) for c, g, _, _ in results if g.shared_ancestors]
        lines += ["", "=" * 94, "",
                  f"  concepts asked about        {len(results)}",
                  f"  reached {MIN_LINEAGES} independent voices  {served}",
                  f"  stored but not servable     {len(results) - served}",
                  f"  shared-ancestor flags       {sum(len(f) for _, f in flags)}", ""]
        if flags:
            lines.append("  wording close enough to suggest one copied the other:")
            for concept, pairs in flags[:8]:
                for a, b in pairs[:2]:
                    lines.append(f"    {concept:<24}{a}  ~  {b}")
            lines.append("")

        if args.sweep:
            lines += ["=" * 94, "WHAT EACH THRESHOLD BUYS", "=" * 94, "",
                      f"  {'agreement':>10}{'servable':>10}{'flags':>8}", "  " + "-" * 28]
            for level in (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
                n = flagged = 0
                for concept, _, found, vectors in results:
                    got = corroborate(concept, found, vectors, agreement=level)
                    n += got.servable()
                    flagged += len(got.shared_ancestors)
                lines.append(f"  {level:>10.2f}{n:>10}{flagged:>8}")
            lines += ["",
                      "  A setting where every concept is servable is measuring nothing:",
                      "  it means any two passages count as agreeing.", ""]

    text = "\n".join(lines) + "\n"
    (args.out / "corroboration.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
