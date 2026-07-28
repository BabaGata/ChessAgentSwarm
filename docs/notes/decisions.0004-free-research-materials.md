---
id: cas-adr-0004
title: 'ADR-0004 — Free research materials (constraint C7)'
desc: 'The knowledge base is built from freely obtainable sources; paid material only when a free path cannot resolve a blocker.'
updated: 1785255000000
created: 1785255000000
---

# ADR-0004 — Free research materials (constraint C7)

**Date:** 2026-07-28 · **Status:** accepted (thesis author's decision)

## Context

Constraint C1 said the *system* must be free or near-free to operate. It said nothing about the cost
of *building* it. F2 in [[open-questions]] then proposed acquiring published curricula — Steps Method,
Yusupov, Silman, Dvoretsky — several of which are paid books.

The thesis author has ruled: everything stays free for now; paid options are considered only when the
free path cannot resolve a blocker.

## Decision

Extend the constraint set with **C7 — free research materials**. Sources, datasets, papers and books
used to build the knowledge base must be freely obtainable. Paid material is a last resort, allowed
only when it unblocks something a free source demonstrably cannot, and must be justified in an ADR.

## Consequences

**This is less limiting than it first appears.** The free corpus available is genuinely strong:

| Need | Free source |
|---|---|
| Positional concept taxonomy | **Nimzowitsch, *My System*** (1925–27) — the canonical decomposition: prophylaxis, overprotection, blockade, outposts, open files, pawn chains. On archive.org and Wikisource |
| Graded beginner→intermediate pedagogy by a world champion | **Capablanca, *Chess Fundamentals*** (1921) — [Project Gutenberg #33870](https://www.gutenberg.org/ebooks/33870), unambiguously public domain in the USA |
| Cognitive science of expertise | Gobet, *Expert memory: a comparison of four theories* (held locally, `docs/pdf/`); Hambrick et al. (2014) free full text on PubMed Central |
| Tactical vocabulary + labelled training material | Lichess puzzle database (CC0) — [[domain.puzzle-themes]] |
| Opening/trap vocabulary | `lichess-org/chess-openings` (CC0) |
| Engine documentation | Stockfish wiki (held locally) |
| Prior art | five projects, held locally — [[domain.prior-art]] |

**What we lose:** the modern graded curricula (Steps Method, Yusupov) whose *structure* was the most
attractive part of F2. Mitigation: their syllabus structure is often described publicly even when the
books are not free, and the public-domain classics cover the same conceptual ground with more
authority, if less pedagogical grading.

**What it forces, usefully:** citing primary sources by recognised masters instead of chess blogs —
which is what F2 was actually about. C7 pushes the sourcing *up* in quality, not down.

## Consequence for open question D4

Reading the free corpus reframes the biggest technical risk. D4 asked whether positional concepts can
be classified without labelled data, on the assumption that no positional taxonomy exists. That was
wrong: **the taxonomy exists in the literature** — *My System* is a positional concept catalogue, and
Silman's imbalances are another. What is missing is not the vocabulary but the *machine labels*.

D4 therefore becomes a much better-posed question: **can we build board-feature detectors for a
taxonomy that already exists in text?** That is the same shape of problem as the tactical motif
detectors, which prior art shows is tractable (L-004).

## Vision link

Adds C7. Serves C1's spirit and improves the evidence quality behind V2/V4/V5.

## Revisit when

A free path genuinely cannot resolve a blocker — most likely candidate: if band-graded curriculum
structure turns out to be essential to M2 and no free description is adequate.
