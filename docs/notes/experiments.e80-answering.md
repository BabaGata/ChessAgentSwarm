---
id: cas-exp-e80
title: 'E80 — The coach answers a chess question, cites the book, or says it does not know'
desc: 'The conversational path the graph was built for. One retrieval over rules and passages together, an answer that names who says a thing and never that it is so, and a refusal that cites nothing. Two defects on the way, both from hand-written gates in front of retrieval.'
updated: 1788289200000
created: 1788289200000
---

# E80 — Answering from the shelf, or refusing to

**Answers:** the goal [[design.graph-knowledge-base]] was written for ·
**Code:** `chesscoach/answering.py`, `chesscoach.cli ask` · **Date:** 2026-09-01 ·
**Status:** done — **it answers, cites, and refuses**

## What it is for

> *"I want the ollama agent to be able to have normal conversation with the player… so that it is
> not only able to give to the player the generated review but also to discuss it with the player."*

Stages 1–3 built a base. Nothing used it. This is the path from a question to an answer.

## The line it holds

**The answer says who says a thing, never that it is so.**

- *"Edward Lasker, Philidor and Staunton describe it this way"* — a claim about the literature,
  checkable against the locators printed beneath it;
- *"A backward pawn is one that…"* — a chess claim this project cannot support, and a model's own
  words wearing the authority of a knowledge base, which is what R-03 forbids.

A test pins that the attribution contains no *"is"* and no *"means"*.

## It works

```
$ chesscoach ask "What is a backward pawn?"
A backward pawn is a pawn that is located on its own half of the chessboard and
cannot be defended by any friendly pawns. It is considered a weakness.

— Edward Lasker, François-André Danican Philidor and Howard Staunton describe it this way.
  book://edward-lasker-chess-strategy#101
  book://philidor-studies-of-chess#78
  book://staunton-blue-book-of-chess#9

$ chesscoach ask "How does a knight move?"
The knight moves in an L-shape: two squares in one direction and then one square
perpendicular to that. It can jump over other pieces.
  rule://how the knight moves  ...

$ chesscoach ask "Why is the Sveshnikov Sicilian good?"
The books I have do not cover that.
```

**A refusal cites nothing**, and that is deliberate: naming books beside *"I cannot answer"* implies
they were consulted and found wanting on this point, which is more than was established.

## Two defects, both from putting a hand-written gate in front of retrieval

**1. The rules layer answered by keyword.** A first version consulted the generated rules when the
question's **last word** named one. Asked *"What is a backward pawn?"* it returned the rule for how a
pawn **moves** — confidently, and about something else entirely — and it missed *"How does a knight
move?"*, because the last word is "move".

Removed rather than patched. Rules and passages now carry a shared `:Knowledge` label and one vector
index, so **similarity decides what a question is about** instead of the last noun in it.

**2. Twelve rules then drowned out 1,159 passages.** With one index, *"What is a backward pawn?"*
retrieved three rules and **refused** — from a shelf that discusses backward pawns in four voices.
The rules are short, focused statements and they embed strongly for any definitional question.

Fixed by over-fetching and capping the generated share at half the material, which is a floor on
book coverage rather than a preference between them.

## A third thing, smaller and worth naming

`python-chess: Board.attacks(d4)` was being treated as an **author**, so the knight answer read
*"python-chess describes it this way"* followed by a warning that only one author discusses it — a
hedge about scholarly consensus attached to arithmetic. Generated material is now labelled *"computed
from the rules of chess rather than quoted from a book"*, and the lone-author hedge is reserved for
actual lone authors.

## Honest limitations

- **Which source the model actually used is not knowable from here.** The citations are what was put
  in front of it, which is honest but weaker than "this sentence came from that passage".
- **Correctness is unmeasured.** These three answers read correctly to me; that is not a measurement,
  and E77's ablation measured provenance rather than truth for the same reason.
- **Refusal is only as good as retrieval.** *"Sveshnikov"* is refused because nothing on a pre-1929
  shelf mentions it, which is the right answer for the right reason — but a question the shelf
  covers badly may still get a confident answer from three weak passages.
- **No corroboration gate on the answer path yet.** E79 counts independent lineages per concept;
  this path counts distinct authors among the retrieved passages, which is close but not the same
  thing, and it does not use the agreement check at all.
