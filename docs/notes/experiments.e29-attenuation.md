---
id: cas-exp-e29
title: 'E29 — Correcting the blitz rating line, with the control that makes it believable'
desc: 'Reliability 0.641 gives a 1.56x correction; the held-out players independently demand 1.48x. MAE 149 to 129. Rapid says do not, and that is the point.'
updated: 1786838400000
created: 1786838400000
---

# E29 — Correcting the blitz line for regression dilution

**Repairs the defect found by** [[experiments.e27-held-out]] · **Date:** 2026-08-14 ·
**Status:** done — **corrected for blitz, refused for rapid**

## The defect

E27 tested V1's blitz line on 30 players fetched after every constant was frozen and it failed:
**MAE 150 against 157 for guessing the band's median**, with a systematic −88 bias. It *ranked*
players well (r = +0.83) and compressed the scale — estimates spread 115 points where the players
spread 210 — so a 2008 read as 1718 and a 1402 as 1608.

That is **slope attenuation**, and it has a standard cause. When the predictor carries measurement
error, OLS shrinks the slope toward zero in proportion to that error:

    slope_observed = slope_true × λ,    λ = reliability of the predictor

Blunder rate at blitz is a noisy measure of skill — which is exactly *why* blitz is hard to read — so
the fitted slope was too flat. The remedy is to divide by λ.

## The discipline that makes it legitimate

E27 could have produced a correction directly, by regressing actual on estimated across the 30
held-out players. That is fitting the model to the set that measures it, which is L-018 exactly. So
the two numbers come from **different data**:

| | source |
|---|---|
| **λ, the correction** | split-half by **game** on the **84-player fitting corpus**, Spearman–Brown corrected. No held-out rating touched |
| **validation** | the **30 held-out players**, whose ratings have never fitted anything |

Split by game rather than by move, deliberately: moves within a game are not independent, and
splitting by move would report a reliability the corpus does not have.

## Result — the two estimates agree

| blitz | |
|---|--:|
| split-half correlation | +0.472 |
| **reliability (Spearman–Brown)** | **0.641** |
| **correction it implies** | **1.56×** |
| **stretch the held-out players independently demand** | **1.48×** |

**1.56 against 1.48, computed from different data.** That agreement is the evidence that attenuation
was the right diagnosis rather than a plausible story — a wrong diagnosis has no reason to produce
matching numbers from the fitting corpus's internal consistency and from 30 strangers' ratings.

    before   rating = 1841.3 − 12045.1 × blunder_rate
    after    rating = 2000.6 − 18791.9 × blunder_rate

Validated on the held-out 30 (24 of whom are read at blitz):

| line | MAE | bias | ≤100 | ≤200 |
|---|--:|--:|--:|--:|
| shipped | 149 | −111 | 33 % | 75 % |
| **corrected** | **129** | **−97** | **46 %** | **88 %** |
| guessing the median | 148 | | | |

Every measure improves, and the largest gain is at the tail: estimates landing within 200 points go
from three in four to seven in eight.

## Result — rapid refuses the same treatment, and that is the point

| rapid (control) | |
|---|--:|
| reliability | **0.853** |
| correction it implies | 1.17× |
| stretch the held-out players demand | **0.63×** |
| MAE if corrected | **79 → 111** |

Rapid's predictor is much less noisy, so theory asks for only a small stretch — and the held-out
players point the *other way*. Applying the correction there makes it worse.

**This is what makes the blitz result credible.** Had only blitz been run, *"stretching the slope
improved it"* would be indistinguishable from tinkering until something looked better. The remedy
helps precisely where the predictor is noisy and hurts where it is not, which is what attenuation
predicts and what a blanket rescale would not (L-037).

## What shipped

- `BLITZ_FIT` — corrected slope and intercept, `typical_error` **150 → 129**, the figure measured on
  strangers.
- `BLITZ_BIAS` **−88 → −97**, *reported* rather than subtracted. An offset read off the validation
  set is the error the whole design avoided.
- `RAPID_FIT` — **unchanged**, with the control's reasoning recorded beside it.
- The report now says the blitz reading is out by about **130** rather than 150, and still reads
  people low.
- A test pins the correction factor, because a future refit that silently dropped it would look like
  a small change and cost 20 points of held-out accuracy.

## Honest limitations

- **Still the weaker reading.** 129 against 148 for guessing the band's median is an improvement, not
  a good rating estimate. Blitz remains the speed where the swarm should be least believed, and the
  report says so.
- **The held-out set has now been spent on this question.** Using it to *decide whether to ship* is
  legitimate validation, but it can no longer serve as a clean test of the blitz line. A further
  refit needs fresh players.
- **24 blitz players and 9 rapid.** The rapid control rests on nine, so its 0.63× demand is very
  noisy; the argument for leaving rapid alone rests mainly on its high reliability and its already
  good MAE, with the held-out figure as corroboration rather than proof.
- **Reliability was estimated on half-corpora.** Spearman–Brown extrapolates from a half-length
  instrument to the whole, which assumes the halves are parallel measurements — reasonable for games
  drawn from the same period, weaker for a player who changed mid-corpus.
- **The bias is not fixed, only reduced.** −97 points of systematic understatement remains, and the
  most likely cause is that the fitting corpus's blitz ratings sit lower than the held-out players'.
  A wider-range fitting sample is the real fix and is not done.
