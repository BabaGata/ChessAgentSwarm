---
id: cas-exp-e20
title: 'E20 — Shrinkage halves coverage, and step 4 is withdrawn'
desc: 'The plan said a posterior would soften the cliff that silences players. Measured against its own control it halves coverage at 24 games: 50% spoken to becomes 26%.'
updated: 1786492800000
created: 1786492800000
---

# E20 — Shrinkage halves coverage

**Answers:** step 4 of [[design.short-history-prioritisation]] · **Date:** 2026-08-06 ·
**Status:** done — **built, measured, and reverted**

## What was predicted

Layer 2 of the plan, written before any of it was measured:

> Replace the interval test and the distinct-game floors with **empirical-Bayes shrinkage**. Sample
> size then enters **continuously** rather than as a cliff, which is exactly the flexibility the
> proposal asked for.

[[experiments.e16-shallow-corpus]] had found the interval test blocking **69** claims on its own at
24 games, the second-largest gate. Softening it should let players be spoken to.

## What was built

`chesscoach/shrinkage.py` — the exact regularised incomplete beta by continued fraction, a
`Posterior` with mean, credible interval and `probability_above`, and the beta-binomial update using
`peers.prior_strength` as the prior weight. 29 tests, checked against the identities
I_x(1,1) = x, I_x(a,1) = xᵃ, I_x(1,b) = 1−(1−x)ᵇ and the symmetry relation, so it needs no external
table to be trusted. The interval test in `_focus_blockers` was then replaced by
`P(θ > baseline) ≥ 0.95`.

## What was measured

Against its own control — the same games, the same reference, the same peer rates, the prior
withheld — so the difference is the posterior and nothing else:

| at 24 games | players spoken to |
|---|--:|
| **control, no prior** | **42 / 84 — 50 %** |
| **with shrinkage** | **22 / 84 — 26 %** |

And on the deep corpus: 69 players advised → **57**, overlap 0.05 → **0.09**, claim kinds 23 → 20.

**Shrinkage halves coverage.** Every measurement moved the wrong way.

## Why the prediction was wrong

A Wilson bound is computed from **the player's own games alone**. A shrunk posterior pulls that
estimate toward the population, so the probability that the player's true rate exceeds the baseline
is *lower* than their raw data suggests. Shrinkage is a **conservatism device** — it corrects for
regression to the mean — and it cannot manufacture confidence that the evidence does not contain.

E16's 69 interval-blocked claims were not blocked by an artefact of the test's sharpness. They were
blocked because the evidence does not support them, and the posterior agrees more strongly. The plan
read a cliff as a *calibration* problem when it was a *quantity of evidence* problem, which is what
E16 had said all along: *"shrinkage does not manufacture events."* That sentence was written into the
design note's own limitations and then not believed.

## A second, self-inflicted error worth recording

The first implementation also moved the `FOCUS_MARGIN = 1.25` magnitude test onto the **shrunk mean**.
That took silence at 24 games to **74 %**, with `FOCUS_MARGIN` becoming the dominant blocker at 279
sole blocks — because 1.25 was calibrated by D12 against *observed* rates, chosen so it cut nothing
then in existence, and the shrunk mean lives on a scale where it sits far closer to the baseline.

This is **L-032 committed one step after L-032 was written**: a constant carries the scale it was
calibrated on. Fixing it recovered 74 % → the 26 % result above, which is still half the control.

## What is kept

- **`chesscoach/shrinkage.py` and its 29 tests.** The maths is correct and now has a production
  user: `PeerReference.expected_rate` was doing this update by hand, and now calls it, so there is
  **one** shrinkage formula in the system instead of two that could drift apart.
- **`PeerReference.prior_for`**, which `expected_rate` uses.
- Nothing in the confidence policy. `ClaimStats` carries no prior, and says why.

## Consequences

1. **Step 4 is withdrawn**, not deferred. The sequence in
   [[design.short-history-prioritisation]] is rewritten rather than left claiming a step that was
   measured not to work.
2. **A 20-game minimum has lost the mechanism that was supposed to justify it.** It was called
   *"defensible at step 4"*; step 4 does not deliver, so it is back to being an aspiration and the
   note says so.
3. **The remaining levers are all supply-side** — steps 5 and 6, admitting blitz and accumulating the
   corpus. E16 said the binding constraint is events per corpus; three separate attempts to fix it at
   the policy end have now failed, and that is a pattern worth trusting.

## Honest limitations

- **Coverage is not correctness.** Shrinkage may be the *better estimator* and the current policy may
  be over-claiming; nothing here tests which findings are right. What is established is that shipping
  it would halve what the coach can say, and there is no evidence that the half it removes is the
  wrong half.
- **One threshold, one prior.** `FOCUS_CERTAINTY = 0.95` was chosen to mirror what the Wilson test
  implied, and `prior_strength` is the reference's own estimator. A different pairing might behave
  differently; tuning either until coverage looked acceptable would have been fitting the threshold
  to the desired answer, which is the move this project exists to avoid.
- **The deep-corpus drop is less surprising than it looks** and was not investigated separately:
  with 150 games the prior should barely bind, so a fall from 69 to 57 suggests the certainty
  threshold rather than the shrinkage is doing that work there.
