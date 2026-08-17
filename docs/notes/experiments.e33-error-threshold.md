---
id: cas-exp-e33
title: 'E33 — Lowering the error threshold buys detection, not naming, and discrimination survives'
desc: 'From 10 wp to 3 wp, agreement with the reviewer rises 58% to 89% while naming stays flat at 8-9%. Claims still separate players. The blast radius, not the screen, is what should decide it.'
updated: 1787270400000
created: 1787270400000
---

# E33 — What does lowering the error threshold buy, and what does it cost?

**Answers:** the open question left by [[experiments.e32-hanging-pawn-screen]] ·
**Date:** 2026-08-16 · **Status:** done — **favourable on the screen; not applied**

## The question

`INACCURACY_WP = 10.0` decides what counts as a mistake at all, and everything inherits it: no label
means **no motif detector ever runs**, `allowed_motif` denominators are the player's error count, and
S2 sorts errors by the clock.

E32 found 24 of 45 reviewer pawn notes sitting below that line — for `Crossfire1983` the median
noticed mistake cost **8.9 wp**, so most of what a strong club player writes down is invisible by
construction. Lowering the floor is the obvious move, and obvious moves are what this project
screens.

Analysis ran **once** per player; thresholds were applied by relabelling the stored `loss_wp`, which
is exact and free. The `mistake` band was scaled with the floor rather than left at 20, so the tiers
do not overlap strangely at 3.0. `blunder` stays at 30, so V1's strength estimate — which reads
blunder rate — is untouched at every threshold.

## Result

**Volume and cost**, 12 players:

| threshold | moves called an error | mean cost of one |
|--:|--:|--:|
| **10.0** (ships) | 9.0 % | 22.3 wp |
| 7.0 | 13.7 % | 17.6 wp |
| **5.0** | 19.2 % | 14.2 wp |
| 3.0 | 27.8 % | 11.0 wp |

**Agreement** with the reviewer, 106 move-level notes across three annotated players:

| threshold | detected | named |
|--:|--:|--:|
| **10.0** | 61 (**58 %**) | 8 (8 %) |
| 7.0 | 74 (70 %) | 8 (8 %) |
| **5.0** | 83 (**78 %**) | 9 (8 %) |
| 3.0 | 94 (**89 %**) | 10 (9 %) |

**Discrimination**, p90 ÷ median — the L-024 screen. The expected failure mode was spreads collapsing
toward 1.00× as cheap errors flooded the evidence:

| threshold | missed hangingPawn | allowed hangingPawn | missed fork | allowed hangingPiece | instant move |
|--:|--:|--:|--:|--:|--:|
| 10.0 | 1.53× | 1.38× | 1.40× | 1.56× | **1.91×** |
| 7.0 | 1.25× | 1.53× | 1.55× | 1.39× | 1.74× |
| **5.0** | **1.75×** | **1.59×** | **1.59×** | **1.64×** | 1.59× |
| 3.0 | 1.65× | 1.56× | 1.40× | 1.55× | 1.40× |

## Two findings, and the second is the important one

**1. The veto did not happen.** Discrimination does not collapse. It wobbles without trend, and at
5.0 four of the five watched claims reach their *best* spread of any threshold tested. The one clear
casualty is `instant_move_error`, falling 1.91× → 1.40× as the floor drops — which makes sense, since
a habit defined by speed rather than by severity gains the most noise from admitting small errors.

**2. Naming is completely flat: 8 % → 9 %.** This refutes E32's own hypothesis. E32 concluded that
the pawn-naming gap was gated by the threshold — 24 of 45 notes below the line, so no motif could
run. At 3.0 those detectors all run, detection climbs 31 points, and **one extra note gets named**.

So the motif vocabulary does not describe what the reviewer describes, and it is not the threshold
holding it back. The swarm can be made to *see* almost everything a strong club player sees — 89 % —
and still has nothing to *call* it. Detection and naming are independent problems, which is what
E31's original split said and this now confirms by intervention rather than by observation.

## Consequence — screened, not applied

The screen is favourable and it is **not** what should decide this. Lowering the floor has a blast
radius the screen does not measure:

- **[[experiments.e05-natural-drift]]'s `NO_CHANGE_RATIO = 0.58` was fitted at threshold 10**, from 57
  predictions cross-validated at 2 and 5 folds. Change what counts as an error and that constant is
  describing a different quantity. The progress check is the one part of this system that can be
  proven wrong, and its calibration is not something to invalidate as a side effect.
- **Every peer reference must be rebuilt.** Rates are not comparable across thresholds any more than
  across depths (E01).
- **Every figure in the vault shifts** — coverage, overlap, groundedness, the anti-pattern family, the
  cost-per-game numbers the arbiter ranks on.
- **"You went wrong on one move in four"** is a different kind of statement to a player than "one in
  eleven", and nothing here says which is more useful to receive.

**If it is changed, 5.0 is the value the evidence points at**: detection 78 %, the best discrimination
of the four thresholds, and a mean error still costing 14.2 wp rather than 11.0. 3.0 buys 11 more
points of detection for a quarter of all moves being errors and the sharpest dilution of cost.

Recorded as a decision for the author rather than taken here, with the refit work stated so it is
priced honestly rather than discovered afterwards.

## Honest limitations

- **Agreement is measured on three players' notes** and rests on the phrase table written after
  reading them (E31's stated weakest link).
- **The `mistake` band was rescaled** rather than held fixed; a different choice there would move the
  middle tier's counts, though not the error/non-error split these figures turn on.
- **Discrimination is measured on 12 players**, so a 1.25× against a 1.59× is not a reliable ordering
  — only the absence of a collapse is.
- **Nothing here measures whether a lower floor makes the advice better**, only whether the swarm
  sees more and can still tell players apart.
