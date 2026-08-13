---
id: cas-exp-e27
title: 'E27 — On strangers the diagnosis holds and the blitz rating does not'
desc: 'Coverage generalises once corpus size is matched (86% vs 84%). V1-rapid is excellent on new players (MAE 50). V1-blitz barely beats guessing.'
updated: 1786752000000
created: 1786752000000
---

# E27 — The first players the swarm was not built on

**Answers:** in-sample optimism, the risk this project has been caught by twice ·
**Date:** 2026-08-10 · **Status:** done — **one half validated, one half found wanting**

## Question

Every threshold, screened claim and constant in the swarm was chosen while looking at the same 84
players it is then run on: `FOCUS_MARGIN`, the five band-note claims, the section screens (E09, E11,
E14, E25), both strength fits, the peer reference itself. Leave-one-out removes a player from their
*own* peer rate; it does nothing about the fact that **what to measure** was selected on this sample.

This project has been caught by exactly that twice — E03's effect reversed on held-out players
(L-008), and E05's constant looked five times better than it was until cross-validated (L-018). The
whole pipeline had never been run on strangers.

## Method

**30 new players**, discovered the same way the original corpus was (arena standings in the
1400–1800 band), **excluding every username already used**, fetched exactly as production fetches —
`DIAGNOSTIC_PERF_TYPES`, 60 pooled games — and diagnosed against the **existing** peer reference with
nothing refitted.

## Result — the diagnosis generalises

| | held out | in sample |
|---|--:|--:|
| players | 30 | 84 |
| median games each | 54 | 70 |
| **advised** | **67 %** | 79 % |
| distinct claim kinds | 14 | 25 |
| mean pairwise overlap | **0.09** | 0.09 |
| groundedness | **31/31** | 113/113 |
| priorities per player | never > 2 | never > 2 |

Resampling the in-sample set to 30 players, 2,000 draws, puts held-out coverage at the **5th
percentile** and claim kinds at the 9th — borderline. But the held-out corpora are smaller, and
coverage rises with games, so the two explanations are tangled. Matched on corpus size:

| games | held out | in sample |
|---|--:|--:|
| 40–60 | 55 % | 43 % |
| **60–80** | **86 %** | **84 %** |

**Fisher exact, two-tailed: p = 0.457.** The coverage gap is corpus size, not novelty. Within the
band where both sets have players, the strangers do marginally *better*. Overlap sits at the 70th
percentile of resampled draws — dead normal.

**The diagnostic machinery is not an artefact of the players it was built on.**

## Result — and the blitz rating estimate is not

These 30 players carry their own Elo in their game headers, so V1 gets a genuine external check for
free — the only capability where that is possible.

| | held out | claimed |
|---|--:|--:|
| mean absolute error | **127** | 118 |
| median absolute error | 105 | — |
| within 100 | 43 % | — |
| within 200 | 80 % | — |
| **mean signed error** | **−88** | — |

Split by speed, the picture separates completely:

| speed | n | MAE | guessing the median | |
|---|--:|--:|--:|---|
| **rapid** | 7 | **50** | 133 | excellent |
| **blitz** | 23 | **150** | 157 | **barely beats guessing** |

### The blitz line is compressed, not broken

| | r with actual | spread of estimates | spread of actual | slope(actual ~ estimate) |
|---|--:|--:|--:|--:|
| blitz | **+0.83** | 115 | **210** | **1.50** |
| rapid | +0.96 | 234 | 201 | 0.83 |

Blitz **ranks** players well and gets the **scale** wrong by half. Estimates spread 115 points where
the players themselves spread 210, so everyone is pulled toward the middle: a 2008-rated player is
read as 1718, a 1402 as 1608. That is textbook slope attenuation — blunder rate is a noisier
measurement of skill in blitz, and OLS shrinks a slope toward zero in proportion to the noise in its
predictor.

**Cross-validation could not have caught this**, and that is the lesson. Folds within the fitting
corpus test prediction on players from the *same* narrow range, where compression costs little. The
held-out sample spans 1184–2008; across that range it costs 150 points. **A cross-validated error is
not an out-of-sample error when the whole sample was selected the same way** (L-036).

## What was changed, and what deliberately was not

**Changed:** `BLITZ_FIT.typical_error` 123 → **150**, the figure measured on strangers, because that
number is a promise the report makes to a player. The report now says the blitz reading is rough, out
by about 150, biased low, and worst for strong players.

**Not changed: the line itself.** A rescale fitted on these 30 players would fit the model to the set
that measures it — exactly L-018. The real fix is a refit on a blitz sample with a genuinely wide
rating range, validated on a *further* held-out set, and it is recorded as work rather than done
cheaply here.

## Honest limitations

- **7 rapid players is a thin basis for MAE 50.** It is encouraging and it is not established.
- **The 30 players are still arena players from one band**, discovered the same way as the original
  84. Genuinely independent sampling would be a different discovery route entirely.
- **Coverage matching used buckets on 30 players**; the 60–80 comparison rests on 7 held-out players
  against 75 in-sample.
- **Claim kinds at the 9th percentile** is inside the resampled band but at its edge, and smaller
  corpora explain part but perhaps not all of it. Not chased down.
- **Nothing here is about correctness.** The claims generalise in *rate*; whether they are the right
  claims still needs a person.
