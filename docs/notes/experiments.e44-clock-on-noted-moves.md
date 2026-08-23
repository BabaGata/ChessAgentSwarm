---
id: cas-exp-e44
title: 'E44 — A third of the reviewer''s noted mistakes were played in under two seconds, and it means less than it looks'
desc: 'The reviewer never checked the clock. Joining their 263 move-numbered notes to the PGN finds 89 played in ≤2s — but against a fair denominator the enrichment is 0.77x, so noticed mistakes are not unusually rushed. Also finds seconds_spent understating thinking time by the increment.'
updated: 1787961600000
created: 1787961600000
---

# E44 — What the clock says about the moves the reviewer wrote down

**Answers:** the reviewer's *"no mistake is recorded as an instant move while for some this could
definitely be the case"* · **Code:** `experiments/e28-expert-review/clock_annotate.py` ·
**Date:** 2026-08-20 · **Status:** done — **the question is answered, the hypothesis is not supported**

## The ask, and the trap in it

The reviewer annotated seven players without ever opening the clock, because checking it per move was
too slow. So no note says "instant move", and they suspected some should.

The join is trivial — the clock is in the PGN and the notes carry move numbers. The trap is what to
do with the answer. **The notes are the answer key** that [[experiments.e31-move-level-agreement]]
and [[experiments.e40-derived-ranking]] score the swarm against. Writing "instant move" into them
would put the swarm's own vocabulary (`instant_move_error`) into the ground truth and let it take
credit for naming something a script inserted.

So this writes `a-your-reading/<player>-clock.txt`, a companion file, and **touches no note**. What
the reviewer folds into their reading is their judgement to make.

## Result — the raw number, which is what was asked for

| | |
|---|--:|
| move-numbered notes across six players | 263 |
| with a clock reading | **263** |
| **played in ≤ 2 s** | **89 (34 %)** |

Every note resolved to a timed move, which is the best case for this instrument.

## And the control, which reverses the reading

34 % means nothing without knowing how often *any* move is instant. These are mostly 3+0 games and
the base rates are very high. Three denominators, from loosest to tightest:

| player | noted & instant | all moves | post-opening & competitive | engine-flagged errors | enrichment |
|---|--:|--:|--:|--:|--:|
| bjagus | 30 % | 62 % | 58 % | 48 % | **0.52×** |
| cademan | 35 % | 39 % | 28 % | 19 % | **1.25×** |
| Crossfire1983 | 34 % | 56 % | 49 % | 41 % | **0.70×** |
| goydorak | 20 % | 29 % | 30 % | 15 % | **0.68×** |
| Hirsican | 43 % | 57 % | 51 % | 41 % | **0.84×** |
| maikel5 | 35 % | 39 % | 30 % | 13 % | **1.18×** |

Enrichment is against the **post-opening, still-competitive** denominator — the moves a reviewer is
actually reading, and the population the swarm uses. Every-move flatters the comparison because it
counts opening book and forced recaptures, which are instant by nature and nothing anyone writes down.

**Median enrichment 0.77×, and only two of six players exceed 1.0.** The mistakes a strong player
notices on the board are, if anything, *less* rushed than the positions around them. The reviewer's
hypothesis is **not supported** — though the per-move facts they asked for are real and delivered,
and 89 individual moves are worth a second look regardless of what the aggregate says.

## The finding nobody was looking for

Read the last two columns together: for every one of the six players, **the moves the engine calls
mistakes are instant *less* often than post-opening moves in general** — 19 % against 28 %, 15 %
against 30 %, 13 % against 30 %, and closer but still below for the other three.

That sits awkwardly beside [[experiments.e25-shared-weaknesses]], where `instant_move_error` is the
most expensive claim measured in this project — 16.1 wp/game as this was written, **22.8 once the
increment was corrected and the reference rebuilt** ([[experiments.e45-increment-correction]]) — and is advised to nobody. It is not a
contradiction — a rate can be low while a total is large if instant moves are numerous, and E25 is a
population measurement where this is six players — but *"these players err on the moves they thought
about"* is not what the band note implies, and the two should be reconciled rather than left side by
side.

## A code defect this surfaced

`Observation.seconds_spent` is `clock_before - clock_after`. With an increment of `i` the clock reads
`before - spent + i`, so the stored figure **understates thinking time by exactly the increment**. On
a 180+2 game a 3.5 s move records as 1.5 s and reads as instant. Only
`chesscoach/evaluation/planted.py` subtracts an increment; the analysis path never does.

**It does not affect this experiment** — all 89 flagged moves stay instant with the increment added
back, because 91 % of the review games are increment-free (180+0, 600+0, 300+0). It is recorded as
**D16** because it does affect S2's claims and E25's band note wherever increment games are in the
corpus, and the peer reference is not 91 % increment-free by design.

## Honest limitations

- **Six players**, the ones annotated, which is not a random half.
- **Enrichment spans 0.52× to 1.25×** on note counts of 17 to 71. With that spread and those counts,
  what is established is the absence of a *strong consistent* effect, not the absence of an effect.
- **A reviewer's move number is a move pair**, resolved here to the player's own move at
  `ply // 2 + 1`, reusing E31's mapping. A note about the opponent's move at the same number would be
  silently attributed to the player.
- **`INSTANT_MOVE_SECONDS = 2.0` is the system's threshold**, inherited rather than examined. A
  2.0 s cut is arbitrary at the boundary and several rows sit exactly on it.
