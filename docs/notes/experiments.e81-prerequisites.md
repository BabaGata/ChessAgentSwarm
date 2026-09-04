---
id: cas-exp-e81
title: 'E81 — The prerequisite order the arbiter refused to invent, now readable'
desc: 'Stage 4. The partial order existed as prose in the domain note and nothing could read it; it is now ten Domain nodes and nine PREREQUISITE_OF edges. 89 % of claim pairs answer unknown, which is the definition of done rather than a shortfall.'
updated: 1788307200000
created: 1788307200000
---

# E81 — What gates what

**Answers:** [[design.graph-knowledge-base]] stage 4, and the hole in
`chesscoach/arbiter.py` · **Code:** `chesscoach/domains.py`, `GraphStore.load_domains` ·
**Date:** 2026-09-02 · **Status:** done — **and *unknown* is the common answer, on purpose**

## The hole this fills

`arbiter.py` has carried this since it was written:

> *"On prerequisite ordering. The spec lists it as a ranking criterion, and **it is deliberately not
> implemented yet** … among the claim kinds that currently exist, tactical and process weaknesses
> have no defensible ordering between them. **Inventing one would be fabricated pedagogy.**"*

The blocker was never the data structure. `domain.chess-concepts` § C draws the partial order and
cites it at `expert-consensus`; it had simply never been written where code could read it.

## What was loaded

**10 `Domain` nodes, 9 `PREREQUISITE_OF` edges, 21 `Claim` nodes** — 40 in total, each edge carrying
its source.

```
what gates the endgames (K7)?        K1
what gates planning (K5)?            K1, K2, K3, K4
what gates practical process (K9)?   nothing — cross-cutting
```

That last line is the note being obeyed rather than a gap: § C calls K9 and K10 *"cross-cutting,
teachable at any level"*, so they gate nothing and nothing gates them.

## Three answers, not two

`gates(a, b)` returns **True, False, or None**. A function answering only yes or no would let the
arbiter order tactics before process while looking careful — which is the exact failure it refused
to commit.

Across all 420 ordered pairs of claim kinds:

| answer | pairs | |
|---|--:|--:|
| **unknown** | **372** | **89 %** |
| yes | 24 | 6 % |
| no | 24 | 6 % |

**The design note's definition of done was that unknown should be the common answer.** It is, and a
test asserts it stays that way — if most pairs ever came back ordered, the structure would be
claiming far more than § C supports.

## Two kinds of statement, and only one is chess knowledge

- **The domains and their order** are a claim about chess pedagogy, sourced to the note and through
  it to the literature.
- **The claim-to-domain map** is a statement about *what our own detectors measure*:
  `allowed_motif.fork` counts a tactical motif, so it is K2 by K2's own definition. That is the same
  kind of statement as a `Claim` node, which needs no endorsement.

**16 claim kinds are mapped. 5 are deliberately not**, each with the reason stored on the node:

| claim | why it is unmapped |
|---|---|
| `late_castling` | an opening principle (K6) or a practical habit (K9), depending on why the player delayed |
| `slow_development`, `repeat_move` | the same ambiguity |
| `pawn_error` | K4 if it is structure, K3 if it is calculation, and the detector cannot tell |
| `early_error` | any error inside the opening window, so it spans every domain an error can belong to |

Storing the reason is what keeps *"nobody decided"* from later reading as *"there is nothing to
decide"*.

## Honest limitations

- **The arbiter does not use this yet.** Stage 4's stated done-condition was that it *can ask* and
  gets three answers; making prerequisite order actually rank a plan is a further step and a
  judgement about coaching, not a wiring job.
- **§ C is one note's partial order**, at `expert-consensus`, and one of its two structural claims —
  that calculation depends on the pattern vocabulary — is the load-bearing one. If that is wrong,
  most of the graph is.
- **A mapped claim is not a validated claim.** `allowed_motif` being K2 says what it measures, not
  that it measures it correctly; that is still the detection sheet's question.
- **Only 24 of 420 pairs answer yes**, so as a ranking signal this is currently very thin. Whether
  that thinness is honest or merely incomplete depends on how much of § C's order the shipped claims
  actually reach, and they reach little of it: no shipped claim is K3, K5 or K10 at all.
