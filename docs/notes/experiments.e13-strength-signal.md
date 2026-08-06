---
id: cas-exp-e13
title: 'E13 — Strength, from blunder rate alone'
desc: 'V1 built and cross-validated: rating estimated to ±103 points from one feature, with the rating hidden.'
updated: 1786579200000
created: 1786579200000
---

# E13 — Strength, from blunder rate alone

**Answers:** V1, via [[evaluation]]'s A2 · **Code:** `experiments/e13-strength-signal/`
**Date:** 2026-08-06 · **Status:** done — **built and shipped**

## Question

V1 was the last vision capability at flat zero that a game record could support: *estimate playing
strength from games, not from a self-reported rating*. [[evaluation]]'s A2 makes it unusually
tractable, because the data carries its own ground truth — estimate with the rating hidden, then
compare against the rating the player actually has.

## The worry that turned out not to apply

The screen was written expecting **range restriction** to sink it. Every player was discovered by
filtering arena standings to 1400–1800, which should leave too little rating variance to predict and
attenuate every correlation toward zero — making a weak result uninterpretable.

It does not apply. The band filter was applied to *standings at discovery*, not to the games, and the
ratings on the games run **789 to 2129**, sd **233**. The caveat was written into the experiment
before the data was seen and had to be removed after; it is recorded here because a null result would
otherwise have been read as "no signal" when it might have meant "no room to show one".

## Result

84 players, ~150 games each, depth 15.

| feature | correlation with rating | held-out MAE | within 100 | within 200 |
|---|---|---|---|---|
| **`blunder_rate`** | **−0.832** | **103** | **60 %** | **89 %** |
| `mean_loss_wp` | −0.802 | 115 | 50 % | 88 % |
| `error_rate` | −0.754 | 127 | 45 % | 82 % |
| `best_move_rate` | +0.648 | 134 | 49 % | 77 % |
| *guess the median* | — | *162* | — | — |

Five-fold cross-validation, **split by player**, because an in-sample fit is not an estimator — L-018
is the standing reminder of what that costs.

**Blunder rate wins and nothing else is needed.** The fitted line:

    rating ≈ 2053 − 19859 × blunder_rate

Every candidate beats guessing the median, so all four carry strength; the differences between them
are smaller than the error on any of them.

## What shipped

`chesscoach/strength.py`, and a `strength` field on the profile (schema v6) — **not** a Finding, since
a rating is not a weakness. Three properties matter more than the arithmetic:

- **The error travels with the number.** The report says *"About 1650, and most likely between 1547
  and 1753"*, never a bare figure. D1 is explicit that this project must not promise rating it cannot
  evidence, and ±103 is what the measurement supports.
- **It refuses to speak below 200 diagnosable moves.** One blunder in 80 moves and one in 90 are the
  same player, and the line would put 250 points between them.
- **It admits extrapolation.** Outside the blunder rates the fit was made over (0.008–0.072) the
  estimate is flagged as a direction rather than a figure, because a linear fit outside its range is
  a guess with a decimal point on it.

A live session on `Gaurishb` estimated **1391** against an actual **1406**. That is 15 points and it
is *not* evidence — he is inside the fitting corpus. The held-out 103 is the number that means
something.

## Honest limitations

- **One feature, one fit, one band-ish population.** 84 players discovered the same way, at one time
  control, on one site.
- **No per-player uncertainty.** The vision asks for strength *and its variance*; what exists is a
  population-level error bar applied to everyone. A player with 1,100 measured moves and one with 210
  get the same ±103, which is wrong and known to be wrong.
- **Blunder rate is depth-bound**, like every signal here (E01). The coefficients belong to depth 15
  and would need refitting at any other.
- **Correlation is not causation and this is not a target.** Blundering less would raise the estimate
  by construction; whether it raises the *rating* is a different claim and this experiment does not
  make it.
- **Ratings come from the PGN headers**, so they are the rating at the time of each game, averaged —
  not a current, settled figure.
