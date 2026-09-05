---
id: cas-exp-e90
title: 'E90 — The definitions reach the graph, retrieval works, and the agent fabricates when asked what it does not know'
desc: 'The knowledge base and the retrievable graph were separate stores, so no definition was ever retrievable. With a loader, ten of ten concepts return their own definition at rank one. Asked about something the shelf does not cover the agent invented a move list from real fragments and credited it to Staunton, and neither a similarity floor nor the grounding check catches it.'
updated: 1788717600000
created: 1788717600000
---

# E90 — Loading, retrieving, and one fabrication

**Answers:** the *"test retrieval and check correctness"* half of the author's request ·
**Code:** `chesscoach/graph.py` · **Date:** 2026-09-06 · **Status:** done

## Two stores, one of them invisible

`answer()` searches the graph. The graph held **1,159 book passages and 12 generated rules**, and
**no definitions at all** — there was no loader for `knowledge.json`. Asked *"what is a fork"* it
returned three unrelated passages, one of them an ASCII board diagram, while a correct sourced
definition of a fork sat in a file the retriever never reads.

`load_definitions` writes each complete entry as a `Definition` node with an embedding and a
`definition://<claim>` locator. **Loading is not endorsing**: the gate is `complete` — a definition
and a usable source, hard rule 7 as `Entry` already reads it — and `servable` is set only when the
author has reviewed it, so an unreviewed definition is retrievable for inspection and still refused
to a player.

**15 of 18 entries loaded.** The three refused are `moved_into_attack` (no quote, no sources),
`hangingPawn` and `allows_pressure` (no usable definition after re-drafting).

## Retrieval: 10 of 10

| asked about | rank of its own definition |
|---|---|
| `fork` `pin` `skewer` `hangingPiece` `backRankMate` `trappedPiece` `discoveredAttack` `capturingDefender` `allows_square` `repeat_move` | **all #1** |

Every concept's own definition comes back first. Before the loader, none of them was reachable at
all.

## Correctness: three good answers and one fabrication

Three of four questions answered correctly, and the second is genuinely good — it contrasts two
concepts rather than reciting one:

> **What is a skewer, and how is it different from a pin?**
> *"A skewer is a tactic where a high-value piece is attacked, moving out of the way to expose a
> lower-value piece behind it… It is the inverse of a pin. A pin occurs when a piece is unable to
> move without exposing a higher-value piece to an attack."*
> — cites `definition://skewer`, `definition://pin`

The fourth is the finding:

> **What is the Sicilian Najdorf move order?**
> *"1. P. to Q's 4th 2. P. to K's 4th 3. P. to Q's 4th 4. P. to K's 5th…"* — looping *"P. to K's 2d"*
> a dozen times, **attributed to Howard Staunton**.

**The shelf does not cover the Najdorf and the agent did not say so.** It assembled a plausible-
looking descriptive-notation move list out of unrelated retrieved passages and cited a real author
for it. That is R-02 and R-03 in one output: unfalsifiable content, presented with a citation.

### Neither guard catches it, and both were measured

**A similarity floor cannot separate covered from uncovered.** Measured over thirteen questions:

| | min | max |
|---|--:|--:|
| covered | **0.8272** | 0.9300 |
| not covered | 0.7300 | **0.8875** |

They overlap. *"Sicilian Najdorf"* scores **0.8875**, higher than the correctly covered *"back rank
mate"* at 0.8272. Any threshold that refuses the Najdorf also refuses real questions. The reason is
structural: the embedding measures topical similarity, every passage on the shelf is chess, and every
chess question is therefore similar to something.

**The grounding check does not catch it either.** `check()` reports `grounded=True, novelty=0.11` on
the fabricated answer, and it is right to: the model copied descriptive-notation fragments out of the
retrieved Staunton passages, so **every word it said is present in the source**. Grounding establishes
where words came from, not whether the assembly is true. A fabrication built from real fragments
passes it.

**The refusal path does work, sometimes.** *"Who won the 1972 world championship?"* returned *"The
books I have do not cover that."* The failure is narrow and characterisable: **a chess-shaped question
whose retrieved passages happen to contain move notation**, which gives the model material to
assemble.

## A second defect, in the answers that were right

Asked *"what is a fork"*, the answer came from the Lichess definition and was credited to **Howard
Staunton** — who is on the shelf and said nothing of the kind. `search` reads
`coalesce(s.author, node.provenance)`, and a `Definition` node had neither, so attribution fell
through to whatever book passages were retrieved alongside. Fixed by setting `provenance` from the
entry's publisher.

**A residual remains and is not fixed.** `Entry` records a list of sources but not *which one the
quote came from*, so `definitions_to_load` attributes to the first usable source. For the seeded
entries that is correct, because the seeder puts Lichess first. For swarm-drafted entries it is a
guess: the outpost definition is Wikipedia's text and is credited to **Philidor**, whose entry
happened to be first in the list.

## Honest limitations

- **The fabrication is not fixed**, only characterised and shown to defeat both existing guards. What
  would work is untested — a definitional-question route that requires a `Definition` hit, or a
  second model pass asked whether the answer is supported, are guesses until measured.
- **Four concepts still have no definition**: `hangingPawn`, `allows_pressure`, `moved_into_attack`,
  `pawn_error`. All four are this project's own error categories rather than terms the literature
  defines, which is what E65 already found for nine of fourteen keys.
- **Nothing is endorsed.** All fifteen loaded definitions are `servable = false`.
- **Retrieval was tested on the concepts that have good definitions.** Ten of ten is a real result and
  it is not a claim about the four that do not.
