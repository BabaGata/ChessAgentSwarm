---
id: cas-exp-e05
title: 'E05 — Natural drift: the control condition'
desc: 'What a plan looks like when nobody follows it. 92% of targets met by doing nothing.'
updated: 1785315000000
created: 1785315000000
---

# E05 — Natural drift: the control condition

**Answers:** does the planner's target mean anything? · **Code:** `experiments/e05-natural-drift/`
**Date:** 2026-07-31 · **Status:** done — **and the answer is no**

## Question

The planner predicts a rate a player should reach. E05 asks the control question that
[[vision]] success criterion 4 always required and the planner ignored: **what happens to that
target when nobody follows the plan?**

## Method

32 players, ~60 games each. For every player: split their games by date, build a plan from the
**earlier** half, then check its predictions against the **later** half. No intervention — none of
these players was ever told anything. Any target met here was met by doing nothing.

## Result

| | |
|---|---|
| players with a plan | 12 of 32 |
| predictions made | 13 |
| **met** | **11** |
| not met | 1 |
| too early | 1 |
| **met by drift alone** | **92 % of judged predictions** |
| mean improvement, no coaching | **+11.2 points** |
| mean improvement the target asked for | **+5.5 points** |

Every single prediction's rate fell in the later period:

```
  met       19.6% ->  3.8%   (target 14.2%)   allowed_motif.fork
  met       22.5% ->  7.8%   (target 17.2%)   missed_motif.pin
  met       25.0% -> 11.0%   (target 17.2%)   allowed_motif.hangingPiece
  met       19.1% ->  6.4%   (target 14.6%)   allowed_motif.pin
  …
  not_met   15.2% -> 17.6%   (target 12.2%)   allowed_motif.hangingPiece
```

**The targets ask for less improvement than doing nothing produces.**

## Why — and it is structural, not a tuning error

**Regression to the mean, guaranteed by the selection.** A finding becomes a finding *because* its
rate was extreme in the earlier half — that is exactly what the confidence policy and the arbiter
are for. Selecting on an unusually high value and then re-measuring gives, on average, a lower
value, with no change in the player at all. The more selective the system, the larger the drop it
will observe.

The design makes this worse in two ways that were both deliberate. `allowed_motif` denominators are
the player's **errors**, which are few, so single-period rates are noisy — and noise is what
regression feeds on. And the arbiter picks the *most* extreme deviation available, which is the
value most likely to regress.

## What this means

**Any coaching system that measures a weakness, prescribes for it, and re-measures will appear to
work.** That is not a statement about this project; it is a statement about the method, and it is
almost certainly what a system reporting "your weakness improved" is reporting. None of the five
projects in [[domain.prior-art]] checks against a control, so none of them can distinguish their
coaching from this effect.

**For this project, concretely:** the progress check's verdicts are currently **not evidence that
coaching works**, and must not be presented as such. The mechanism is sound; the interpretation was
wrong.

## Corrections this forces

**L-015 was wrong**, drawn from a single player who happened to be the one exception in thirteen. It
concluded that drift is "about two points, against a target asking for four and a half" and that the
targets were therefore demanding. At scale it is **+11.2 against +5.5** — the reverse. The lesson
survives in a stronger form; the number in it did not.

**[[state]]'s D7 score is reduced** from 3 to 2. The predictions are made, checked and recorded, and
that machinery works. But a verdict that means nothing is not progress tracking, and scoring it as
though it were would be the self-flattery this project exists to avoid.

## What would fix it

1. **Shrink the estimate before setting the target.** The player's true rate is better estimated by
   pulling the observed rate toward the peer rate in proportion to how little data supports it
   (empirical-Bayes shrinkage). A target set against the shrunk estimate removes most of the
   selection bias, because the shrinkage undoes the selection.
2. **Predict the difference from a control, not the absolute rate.** E05 now provides the control:
   +11.2 points is what doing nothing achieves. A target must beat that to mean anything.
3. **Re-run E05 after any change to the target rule.** It costs engine time and nothing else, and it
   is the only thing standing between this project and a confident false claim.

## Honest limitations

- 13 predictions across 12 players is a small sample; the *direction* is unambiguous, the exact
  +11.2 is not.
- The split is retrospective, so "earlier" and "later" differ in more than intervention — form,
  opponents and time controls all vary.
- Regression is not the *only* explanation. Players may genuinely improve. But nothing here
  distinguishes the two, which is precisely the problem.
