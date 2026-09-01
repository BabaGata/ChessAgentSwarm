---
id: cas-exp-e79
title: 'E79 — Sixteen concepts of nineteen, and the model judge that never said no'
desc: 'Stage 3. A first run confirmed 19 of 19 at every threshold, including a term that appears zero times on the shelf, because the method was circular. With a vocabulary gate it is 16 of 19, and the three refused are exactly the modern tactical words E64 predicted the old books would lack. The model half of the gate kept 15 of 15 and adds nothing.'
updated: 1788278400000
created: 1788278400000
---

# E79 — What six voices actually agree about

**Answers:** [[design.graph-knowledge-base]] stage 3 ·
**Code:** `chesscoach/corroboration.py`, `chesscoach/extraction.py`,
`experiments/e79-corroboration/` · **Date:** 2026-09-01 ·
**Status:** done — **the gate matters more than the threshold, and the model judge does nothing**

## The rule being implemented

The author's, and it replaces one endorsement per entry with one rule endorsed once:

> *"count how many sources have mentioned some concept and described it in a similar way and then
> take what has been mentioned several times as a confirmed knowledge"*

## The first run was circular and reported a perfect score

**19 concepts of 19 corroborated, at every agreement threshold from 0.50 to 0.80.** Including
`skewer` — which [[experiments.e64-chess-books]] measured as appearing **zero times** across the
original shelf.

The method retrieved passages for being similar to a query, then measured that they were similar to
each other. **Every page of chess prose passes a test like that.** A result that does not move when
you sweep its threshold is not measuring anything, and the sweep is what made it visible.

## The gate, and two wrong versions of it

The design specified an extraction step and I had skipped it. Adding it took three attempts, each
measured rather than reasoned about:

| version | what happened |
|---|---|
| model judgement alone | kept **4 of 4** candidates for `skewer`, one a board diagram |
| whole `TERMS` phrases | refused **every** `pin` passage — those are search queries, and books write *"the pin"* |
| their content words | accepted **every** `skewer` passage, because **"chess"** was one of the words |

The third is the instructive one: a filter keyed on a word the entire corpus shares is not a filter.
`_GENERIC` in `knowledge_swarm` already existed for exactly this and lacked the obvious cases; it now
excludes *chess, board, game, piece, move, position, play, white, black*.

The working gate reuses the project's own `_names`: **does this passage use the term, in any wording
writers actually use, after the shared vocabulary is subtracted.**

## The model half kept everything

`qwen3:8b`, given an explicit criterion — *"a player who did not know the term could read this
sentence alone and afterwards know what it means"* — and an explicit refusal option:

| | |
|---|--:|
| passages reaching the judge | 15 |
| kept | **15** |
| **refusal rate** | **0 %** |

It kept Young rambling about *"services rendered his countrymen"* as an explanation of castling.
E63 had already spent two prompt attempts on this same judgement and recorded that *"a refusal
option needs a criterion, not a bias"* — this run supplied the criterion and the answer did not
change. **The deterministic gate does all the discrimination; the model adds nothing measurable.**

## The result

7 books, **6 independent lineages** (Edward Lasker wrote two of them and counts once), 1,159
passages.

| | |
|---|--:|
| concepts asked about | 19 |
| **reached 2 independent voices** | **16** |
| stored, not servable | **3** |
| shared-ancestor flags | 0 |

The three refused are `skewer` (**0 passages**), `trappedPiece` (1) and `hangingPiece` (3 passages,
no two from different lineages agreeing) — **exactly the modern tactical vocabulary E64 predicted a
pre-1929 shelf would lack.** The strongest are `late_castling` (28 passages, 5 voices),
`repeat_move` (24, 5) and `slow_development` (22, 5), which is the same prediction from the other
side.

## What the sweep says, and it is not flattering

| agreement | servable |
|--:|--:|
| 0.50 | 16 |
| 0.65 | 16 |
| 0.75 | 16 |
| 0.80 | 15 |

**The agreement threshold does almost nothing.** So what is being measured is *"two or more
independent lineages use this term"*, not *"describe it similarly"* — the second half of the
author's rule is implemented and is not currently discriminating. Said plainly because the summary
number would otherwise imply more than was tested.

## Consequence

- **A concept is servable when two lineages use it**, and the count is over authors, so Lasker's two
  books are one voice.
- **The base may say who describes a thing, never that it is so.** `Corroboration.attribution`
  produces *"Capablanca, Staunton and Philidor describe it this way"*, and a test pins that it does
  not say *"is"* or *"means"*.
- **0 shared-ancestor flags**, so no verbatim copying was detected between these books at passage
  level. Worth restating as a null result rather than an absence of the problem: the flag fires at
  0.95 similarity and nothing reached it.

## Honest limitations

- **The agreement half is untested in practice**, per the sweep. Corroboration here is closer to
  co-occurrence than to agreement, and calling it the latter would overstate it.
- **Six lineages is a small jury**, and four of the six are 19th-century.
- **No claim is composed and none is checked for correctness.** A corroborated concept is one the
  shelf discusses in several voices; whether what they say is *right* is not measured and could not
  be by this method.
- **`hangingPiece` failing is not evidence it is absent** — three passages use the term and none
  agreed across lineages, which at k=10 may be retrieval rather than the shelf.
