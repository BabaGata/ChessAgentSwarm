---
id: cas-exp-e05
title: 'E05 — Natural drift: the control condition'
desc: 'What a plan looks like when nobody follows it. 92% of targets met by doing nothing — on thin histories; most of that turned out to be an artefact of the sample depth.'
updated: 1785315000000
created: 1785315000000
---

# E05 — Natural drift: the control condition

**Answers:** does the planner's target mean anything? · **Code:** `experiments/e05-natural-drift/`
**Date:** 2026-07-31, rerun 2026-08-03 · **Status:** done — **the answer was no, and is now
"partly, with a stated false-positive rate and unknown power"**

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

The rate fell in 12 of 13 predictions; the one that rose is the one not met. (Corrected 2026-09-14: this line used to say every rate fell, contradicting the table below.)

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

## The fix, and what it took

Three target rules, each measured against the same 32 untreated players:

| Rule | Met by doing nothing | Target asked for |
|---|---|---|
| halve the gap from the **measured** rate | **92 %** | +5.5 pts |
| halve the gap from a **shrunk** estimate | 83 % | +7.8 pts |
| **calibrated against the no-change distribution** | **8 %** | +15.8 pts |

**Shrinkage alone was not enough**, and the reason is informative. Empirical-Bayes shrinkage corrects
for *sampling noise*, and the observed regression is far larger than sampling noise explains: across
the 13 predictions the later rate is a **median 0.44** of the earlier one, mean 0.51. A rate that
halves on its own is not being moved by chance in a handful of observations.

Two candidates for the extra, and **E05 cannot separate them**: selection on statistical significance
(a finding must clear a confidence test to exist at all, which inflates it beyond simple noise), and
genuine improvement over a split that spans months of real play. Both would produce exactly this.

So the correction had to be **calibrated rather than derived**: the target is set at the 20th
percentile of the measured no-change distribution. That turns it into a hypothesis test with a
stated false-positive rate, and the progress sign now says so out loud — *"about 20 % of players
reach this without doing anything"*.

### Cross-validated — and the 8 % does not survive

The constant was fitted on the same 13 predictions it was tested against, so it was refitted properly:
two folds split by player, fit on one, evaluate on the other, then swap
(`experiments/e05-natural-drift/calibrate.py`).

| | |
|---|---|
| in-sample | 8 % met by doing nothing |
| **out-of-sample** | **38 %** (5 of 13) |
| fitted ratios | **0.518** and **0.385** |
| out-of-sample per fold | **5/7** and **0/6** |

**The in-sample figure was optimistic by about five times**, and the folds disagree so violently —
nearly all met against none met — that the constant plainly cannot be estimated from this data at
all. Thirteen predictions will not support a percentile.

Three things follow, all applied:

1. **The 8 % is withdrawn.** It appears nowhere as a property of the system.
2. **The stated false-positive rate is removed from the output.** The progress sign used to say
   "about 20 % of players reach this without doing anything", which was itself an unsupported claim.
   It now says what *is* measured — that rates typically halve on their own, and the target sits
   below that.
3. **The constant stays at 0.34**, deliberately more demanding than either fitted value, because
   being too strict costs a missed success while being too loose manufactures one.

**The real blocker is sample size, not method.** Only 12 of 32 players produced a plan, most with a
single step, because the confidence gate needs 20+ games with data in the *earlier* half alone. More
predictions require more players with deeper histories — a data problem, and the honest name for
what stands between this project and a defensible claim.

## Rerun on deep histories — and most of the drift was an artefact

**Date:** 2026-08-03 · 84 players, ~150 games each (11,890 games), against 32 players at ~60 before.
Same pipeline, same depth 15, same peer reference.

The data problem above was the whole blocker, so it was fixed first: `fetch_histories.py` gained
arena-based discovery, so the sample is no longer limited to the players already held for the peer
reference.

| | 32 players, 60 games | 84 players, 150 games |
|---|---|---|
| produced a plan | 12 of 32 (38 %) | **40 of 84 (48 %)** |
| predictions | 13 | **57** |
| mean improvement, no coaching | **+11.2 pts** | **+4.8 pts** |
| median `after`/`expected` | **0.52** | **0.87** |

**The regression to the mean was mostly an artefact of thin samples.** This is the substantive
finding, and it corrects the framing above rather than the mechanism. A finding is selected for being
extreme, and a rate measured over ~30 games is far likelier to be extreme by luck than one measured
over ~78. Deepen the earlier half and the winner's curse largely dissolves: drift falls from +11.2
points to +4.8, and the typical rate no longer halves — it lands at 87 % of its no-change estimate.

So **the +11.2 was never a fact about chess players. It was a fact about measuring them briefly.**
The section above should be read with that qualification throughout: its numbers are correct *for
60-game histories*, and 60-game histories are the worst case.

### What that did to the constant

`NO_CHANGE_RATIO = 0.34` was fitted where drift was large. Applied where drift is small it asks a
player's rate to fall to a third of where it would naturally sit — and **1 of 52 untreated
predictions met it (2 %)**. That is not a conservative setting, it is an unmeetable one: a target
nothing reaches cannot detect coaching either, because a coached player would fail it too. A test
with no power is not caution.

Refitted on the 57 predictions, cross-validated by player at **both 2 and 5 folds**
(`calibrate.py --sweep --folds N`):

| quantile | constant | fold spread | out-of-sample met by doing nothing |
|---|---|---|---|
| 10 % | 0.55–0.57 | 0.029–0.067 | 9–12 % |
| **15 %** | **0.58–0.59** | **0.011–0.036** | **14–16 %** |
| 20 % | 0.63–0.68 | 0.027–0.094 | 21–30 % |
| 50 % | 0.87–0.88 | 0.062–0.073 | 53–58 % |

**The constant is now actually being estimated.** On 13 predictions the two folds fitted 0.385 and
0.518 — a spread of 0.133 — and disagreed 0/6 against 5/7. On 57 the spread narrows to **0.011** at
the 15 % quantile, and 2-fold and 5-fold agree across the whole curve. The spread is smallest in the
10–20 % band, which is also where a false-positive rate is worth having.

**Applied:** `NO_CHANGE_RATIO = 0.58`, and a false-positive rate is stated again — but the
**held-out** one. In-sample 0.58 meets 7 of 57 (12 %); cross-validated it is 14–16 %. The output
quotes **15 %**, the honest figure rather than the flattering one. This is [[learning.lessons]]
L-018 applied rather than merely recorded.

**Still unmeasured: the power of the test.** 15 % is a false-*positive* rate. Whether a genuinely
coached player can meet the target is unknown, because no coached cohort exists. A target could be
well-calibrated against drift and still be unreachable by real coaching, and nothing here would show
it. That is open question **D8** and it now blocks V7 more than calibration does.

## D9 — how much of this is depth? (2026-08-03)

The rerun above compared two different corpora at two different depths, so it could not separate
"thinner measurement" from "different players". This isolates it: **the outcome period is held whole
and only the measurement period is capped** — the last K games before the split — so the same 84
players are re-run at K = 30 / 45 / 60 / 78. Every position is already cached, so it cost no engine
time.

| early games | players with a plan | predictions | fitted constant @ 15 % | median `after`/`expected` | met with 0.58 |
|---|---|---|---|---|---|
| 30 | 24 | 27 | **0.488** | 0.77 | 23 % |
| 45 | 32 | 39 | **0.503** | 0.77 | 22 % |
| 60 | 41 | 55 | **0.571** | 0.88 | 18 % |
| ~78 | 40 | 57 | **0.594** | 0.87 | 15 % |

**The dependence is real, monotone, and modest** — and it corrects the previous section's framing.

### The correction

L-019 originally read *"0.34 fitted 60-game histories, 0.58 fits 150-game ones"*. That is wrong.
**0.34 was never a fitted value at any depth.** It came from 13 predictions whose folds disagreed
0.385 against 0.518, and was then tightened by hand. Fitted properly at the same measurement depth,
the constant is **0.488**.

So the 0.34 → 0.58 move was *mostly replacing a guess with a fit*; only **0.488 → 0.594** is the
genuine depth effect, and that is a 22 % relative change rather than 70 %.

The same correction applies to the drift figure. At K = 30 on **this** corpus drift is **+7.4 %**, not
+11.2 %. Depth explains +7.4 → +4.8; the remainder was a different player set. The claim "regression
scales with the thinness of the measurement" survives — the direction is confirmed four times over —
but its magnitude was overstated by attributing a cross-corpus difference entirely to depth.

### What was done about it

**Not a per-depth constant.** Four points do not determine a curve, and fitting one through them is
precisely the overfitting L-018 warns about. The spread (0.488–0.594) is narrow enough that modelling
it would add more risk than it removes.

**Instead the output states the range.** `NO_CHANGE_RATIO` stays 0.58, and the progress sign now says
**15 %–23 % of players reach this target without changing anything** rather than a single figure. A
point estimate would have been true only at the deep end and would have flattered the system for most
players.

A single constant *is* slightly too generous for thin histories — a finding resting on 30 games faces
23 % rather than 15 %. That is stated rather than corrected, because the honest fix is a number the
player can see, not a hidden adjustment.

> **A note on the numeral.** The withdrawn claim was *"about 20 % reach this anyway"* — an in-sample
> percentile from 13 predictions whose true out-of-sample value was 38 %. The range above overlaps
> that region for entirely different reasons: it is the measured out-of-sample rate at each of four
> depths. A regression test (`test_the_withdrawn_twenty_percent_claim_has_not_crept_back`) keeps the
> two apart, so reintroducing the old phrasing has to be deliberate.

**D9 is resolved.** The remaining question about the constant is not its depth dependence but its
power — **D8**.

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

- **The false-positive rate is calibrated; the power is not.** 15 % of untreated predictions meet
  their target. Whether a coached player can meet one is untested, and no data in this project can
  test it. See **D8**.
- The split is retrospective, so "earlier" and "later" differ in more than intervention — form,
  opponents and time controls all vary.
- Regression is not the *only* explanation. Players may genuinely improve. But nothing here
  distinguishes the two, which is precisely the problem.
- **The constant is depth-dependent, and that is not yet modelled.** 0.34 fitted 60-game histories,
  0.58 fits 150-game ones. The planner applies a single constant regardless of how many games a
  finding was measured over, so a player with a thin history gets a target calibrated for someone
  with a thick one. Two points do not determine the relationship, and inventing a curve through them
  would be exactly the overfitting L-018 warns about — but the assumption of a single constant is
  now known to be wrong rather than merely unexamined. Registered as **D9**.
- 84 players is still one rating band, one time control, one site.
