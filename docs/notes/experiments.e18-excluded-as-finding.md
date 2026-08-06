---
id: cas-exp-e18
title: 'E18 — What the exclusion rule was throwing away'
desc: 'The berserk habit fails the cost screen (1.04x). The time-budget chain passes at 1.91x and is now built: the long think costs you twenty moves later, not on the move itself.'
updated: 1786492800000
created: 1786492800000
---

# E18 — What the exclusion rule was throwing away

**Answers:** the author, on step 1 discarding evidence · **Date:** 2026-08-06 ·
**Status:** done — **one candidate built, one refused**

## Question

Step 1 excludes berserked games so a half-clock blunder is not diagnosed as a chess mistake. Correct
for *skill* diagnosis, and it silently discards something coachable. As put by the author: the
pattern behind the discarded games *"also tells something about how the players are playing"* — and
the worked example, a player who *"focuses on one move for too long and then plays badly afterwards
because they don't have much time left"*.

Two candidates, screened before building per L-023 and L-025:

| | claim |
|---|---|
| **A** | the **berserk habit** itself — the clock handicap contaminates what a blunder means, not the fact that the player chose the handicap |
| **B** | **time budget mismanagement** — spending the clock early and paying for it late |

## Result A — the habit varies, the harm does not

| | |
|---|--:|
| players who never berserk | **56 / 84** |
| berserk rate, median / p90 / max | 0.000 / 0.189 / **0.488** |
| **error rate in berserked games ÷ their own normal games** | median **1.04×**, p90 1.33×, max 1.43× |
| spread (p90/median) | **1.27×** |

The *rate* varies enormously. The **cost does not**: halving your own clock raises your error rate by
four per cent at the median. At 1.27× spread this is below every claim the project has shipped —
`allows_king_pressure` went in at 1.59 and was called marginal at the time.

**Not built as a diagnosis.** Telling a player "you berserk too much" would be asserting a cost the
measurement does not support, and berserking buys a tournament point, so it may be a rational choice
rather than a weakness at all.

**It is disclosed instead, which step 1 already does.** A real report now reads:

> *63 of your games were left out because you berserked them — with half your clock, the mistakes
> are about the handicap rather than about you.*

That is the honest form of the author's request: state the pattern, refuse the verdict.

## Result B — built, at the best spread in the project

| | |
|---|--:|
| late-error rate after overspending ÷ after not | median **1.28×**, p90 2.24×, max 3.36× |
| spread (p90/median) | **1.75×** |
| **same, computed from observations alone (the implementable form)** | median 1.18×, **spread 1.91×** |
| correlation with the existing `time_pressure_error` rate | **+0.204** |

**It clears every bar the project uses.** 1.91× is above `long_think_error` (1.60) and
`allows_king_pressure` (1.59). At +0.204 it is not the time-pressure claim renamed — the same
independence figure S8 was accepted on.

**And it is the claim S2 was missing.** S2 measured the error *on* a long think and the error *while*
short of time; it never measured the **link**, which is the only part a player can act on. Time spent
early is a budget, and spending it does not hurt on the move it is spent.

### As built

`time_budget_error.after_overspending` in S2. A game counts as overspent when the player's clock is
below half its starting value by ply 30, and the claim covers their moves *after* that point.

Two implementation choices worth recording:

- **The starting clock is the highest reading seen in the game**, because a section only ever sees
  observations, never the PGN's `TimeControl`. This measures relative spend, so a 300-second game
  burned to 100 counts exactly as a 600-second one burned to 200. The screen was re-run in this form
  before building, and it scored *better* than the tag-based version (1.91× against 1.75×) — the
  implementable measure is the one that was screened.
- **The baseline is late moves in the player's unhurried games**, not "every other move", which
  needed a new `Condition.baseline_applies`. Comparing late-and-rushed against everything would fold
  the opening into the baseline and measure the phase as much as the clock.

**Deliberately not marked `selection_confounded`**, unlike `long_think_error`. A hard position causes
both a long think and an error on that move, which is why *that* one is withheld. Here the magnitude
varies strongly between players — 1.18 median against 3.36 max — and that is the signature of a
player property rather than a base rate, which is exactly the test that caught L-011 in M5.

### What it changed

| | before | after |
|---|--:|--:|
| players advised | 69 | 69 |
| distinct claim kinds | 26 | **27** |
| mean pairwise overlap | 0.05 | 0.05 |
| `time_budget_error` detected / advised | — | **2 / 2** |
| peer rate for the new claim | — | 17.1 % (1,265 moves, 27 players) |

**Two players, and nobody new reached.** Both were already being advised, so this changed *what* they
hear rather than *whether* they hear anything — the same outcome S8 had, and stated the same way.

The gap between 27 players showing the pattern in the screen and 2 clearing the gates is E16's story
again: the binding constraint is the confidence policy, not the supply of claims. **This claim should
be re-measured after step 4** (shrinkage), which is where it is likely to earn its place properly.

## Honest limitations

- **A single threshold decides the split.** Half the clock by move 15 was chosen before the spread
  was measured, not tuned until it looked good, but it is one number and it is not calibrated.
- **The residual confound is real.** A game where the player burned the clock early may simply have
  been a harder game throughout. The between-player variation argues against that being the whole
  story; it does not eliminate it, and the peer rate is recorded alongside so it can be revisited.
- **Two clock claims can now reach the same player.** `Master26` is advised on both mistakes when
  short of time (19 % against 14 %) and mistakes after overspending (22 % against 17 %). They are
  independent by measurement (+0.204) and may still *feel* like one thing to a reader. The arbiter's
  diversity rule looks at subjects, not at families of claim, and this is the first case where that
  distinction bites.
- **2 of 84 is thin evidence that this was worth building.** Recorded as such rather than dressed up.
