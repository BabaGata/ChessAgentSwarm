"""Does retrieval make a small model better at chess questions?

Note: docs/notes/experiments.e77-retrieval-ablation.md
Design: docs/notes/design.graph-knowledge-base.md

Stage 2's stated done-condition, and the thesis result the author described:

    "a good showcase for a thesis of how to use llm with knowledgebase to get
    more informed and correct answers with a smaller llm like ollama's llms"

Three arms, same questions, same model, same seed:

    alone       the model answers from what it remembers
    rules       plus the generated rules layer, where one applies
    passages    plus the nearest book passages, quoted

**What can be scored without a person, and what cannot.** Whether an answer is
*correct* about chess needs a chess player, and this experiment does not pretend
otherwise -- it writes the answers side by side for the author to read. What it
does measure automatically is the thing V8 already demands everywhere else:
**does the answer cite something, and is what it cites real.** A fabricated
citation is worse than none, and it is machine-checkable.

    python run.py [--model phi4-mini:3.8b] [--k 3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chesscoach.graph import GraphStore, GraphUnavailable  # noqa: E402
from chesscoach.ollama import generate  # noqa: E402

# Questions a 1400-1800 player actually asks, split between the two layers the
# base now holds. The rules questions have exact answers; the concept questions
# do not, which is why the author reads those rather than a script.
QUESTIONS = (
    ("rules", "How does a knight move?"),
    ("rules", "What is stalemate, and how is it different from checkmate?"),
    ("rules", "What counts as a rapid game rather than blitz?"),
    ("rules", "When can I capture en passant?"),
    ("concept", "What is a backward pawn and why is it a weakness?"),
    ("concept", "Why is it usually good to castle early?"),
    ("concept", "What does it mean to control the centre?"),
    ("concept", "Why are doubled pawns often considered weak?"),
)

ALONE = (
    "You are a chess coach talking to a club player rated about 1500.\n"
    "Answer the question in at most four sentences.\n\n"
    "Question: {question}\n"
)

GROUNDED = (
    "You are a chess coach talking to a club player rated about 1500.\n"
    "Answer the question in at most four sentences, using ONLY the reference\n"
    "material below. If the material does not answer it, say so plainly rather\n"
    "than filling the gap from memory.\n"
    "End with a line: SOURCE: <the locator you used>\n\n"
    "Reference material:\n{context}\n\n"
    "Question: {question}\n"
)


def rules_context(store: GraphStore, question: str) -> list[tuple[str, str]]:
    """The generated rules that bear on this question, as (locator, text)."""
    found = []
    # A question can name a rule without naming its piece: "en passant" and
    # "promotion" live in the pawn rule's `special`, and "castling" in the
    # king's. Matching piece names alone left the en-passant question with no
    # reference material at all, which measured the gate rather than retrieval.
    aliases = {
        "en passant": "pawn", "promotion": "pawn", "promote": "pawn",
        "castl": "king", "50-move": "fifty-move rule", "repetition":
        "threefold repetition", "draw": "insufficient material",
    }
    subjects = ["knight", "bishop", "rook", "queen", "king", "pawn",
                "stalemate", "checkmate", "check", "fifty-move rule",
                "threefold repetition", "insufficient material"]
    subjects += [target for phrase, target in aliases.items()
                 if phrase in question.lower()]
    for subject in dict.fromkeys(subjects):
        if subject in question.lower() or subject in [
                aliases.get(p) for p in aliases if p in question.lower()]:
            rule = store.rule_about(subject)
            if rule:
                body = rule["statement"]
                if rule.get("special"):
                    body += " " + rule["special"]
                if rule.get("attacks_from_centre"):
                    body += (" From d4 it attacks: "
                             + ", ".join(rule["attacks_from_centre"]) + ".")
                found.append((f"rule://{rule['name']}", body))
    for word, speed in (("rapid", "rapid"), ("blitz", "blitz"),
                        ("bullet", "bullet"), ("classical", "classical")):
        if word in question.lower():
            rows = store._run(
                "MATCH (t:TimeControl {name: $name}) RETURN t", name=speed)
            if rows:
                node = dict(rows[0]["t"])
                found.append((f"rule://{node['name']}", node["statement"]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="phi4-mini:3.8b")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        store = GraphStore.connect()
    except GraphUnavailable as error:
        print(f"no graph: {error}")
        return 1

    lines = [
        "DOES RETRIEVAL MAKE A SMALL MODEL BETTER AT CHESS QUESTIONS?",
        "=" * 92, "",
        f"model {args.model}, k={args.k}, temperature 0.3, seed 7.",
        "",
        "Correctness needs a chess player and is left to one. What is scored",
        "here is whether a cited locator is real, which is machine-checkable and",
        "is what V8 demands of everything else in this project.",
        "",
    ]
    fabricated = cited = grounded_answers = 0

    with store:
        known = {row["id"] for row in store._run("MATCH (p:Passage) RETURN p.id AS id")}
        known |= {f"rule://{row['r']['name']}" for row in
                  store._run("MATCH (r:Rule) RETURN r")}
        known |= {f"rule://{row['t']['name']}" for row in
                  store._run("MATCH (t:TimeControl) RETURN t")}

        for kind, question in QUESTIONS:
            lines += ["=" * 92, f"[{kind}] {question}", "=" * 92, ""]

            alone = generate(args.model, ALONE.format(question=question),
                             num_predict=220).strip()
            lines += ["  ALONE", "  " + "-" * 88]
            lines += ["    " + line for line in alone.splitlines() if line.strip()]
            lines.append("")

            if kind == "rules":
                context = rules_context(store, question)
            else:
                context = [(h["locator"], " ".join(h["text"].split()))
                           for h in store.search(question, k=args.k)]

            if not context:
                lines += ["  RETRIEVED  nothing applied", ""]
                continue

            block = "\n".join(f"[{loc}] {text}" for loc, text in context)
            answer = generate(args.model,
                              GROUNDED.format(context=block, question=question),
                              num_predict=260).strip()
            lines += [f"  WITH RETRIEVAL ({len(context)} passages)", "  " + "-" * 88]
            lines += ["    " + line for line in answer.splitlines() if line.strip()]

            grounded_answers += 1
            # Searched anywhere in the answer, not at a line start. A first
            # version required the line to begin with SOURCE: and scored a real
            # citation as "none offered" because the model wrote it at the end
            # of its last sentence -- the harness understating its own result.
            marker = answer.upper().rfind("SOURCE:")
            if marker >= 0:
                cited += 1
                # To the end of the line, not to the first space: locators like
                # "rule://how the pawn moves" contain spaces, and truncating at
                # one left "rule://how" -- which then matched by prefix and
                # scored REAL on a string that identifies nothing.
                claimed = answer[marker + len("SOURCE:"):].splitlines()[0]
                claimed = claimed.strip().strip("<>[]. ")
                # Exact, or the locator with a trailing sentence attached.
                # A prefix match in the other direction says "REAL" for any
                # fragment, which is the opposite of what this measures.
                real = claimed in known or any(
                    claimed.startswith(k) for k in known)
                lines.append(f"    citation: {'REAL' if real else 'FABRICATED'} — {claimed}")
                fabricated += 0 if real else 1
            else:
                lines.append("    citation: none offered")
            lines += ["", "  retrieved:"]
            lines += [f"    {loc}" for loc, _ in context]
            lines.append("")

    lines += [
        "=" * 92, "SUMMARY", "=" * 92, "",
        f"  grounded answers        {grounded_answers}",
        f"  offered a citation      {cited}",
        f"  citation was real       {cited - fabricated}",
        f"  citation was invented   {fabricated}",
        "",
        "  A fabricated citation is the one failure worse than no citation, and",
        "  it is the half of this a script can judge. The rest is the author's.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    (args.out / "ablation.txt").write_text(text, encoding="utf-8")
    print(text[-900:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
