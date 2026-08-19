---
id: cas-exp-e38
title: 'E38 — Three formulations of the exchange claim, all refused, and the pattern behind it'
desc: 'Tightening the denominator fixed discrimination and never fixed independence. Also refutes the forks-are-easier hypothesis: forks are missed MORE than pins, and pins simply arise 2.5× as often.'
updated: 1787702400000
created: 1787702400000
---

# E38 — Do exchanges a player enters go badly for them, unusually often?

**Answers:** the reviewer's *"the 31.9 % exchange should also be counted"* ·
**Code:** `experiments/e38-exchange-sequences/` · **Date:** 2026-08-18 ·
**Status:** done — **refused three times, and the third refusal explains the other two**

## What was asked, and the constraint that came with it

> "What is genuinely unreported is the 31.9 % exchange, this should also be counted."

And, in the same message, the reason it has to be counted carefully:

> "If all material loss in multiple moves is categorized all together then it will definitely end up
> in top 3 weakness for every player because the category is too broad."

That is exactly right, and it is the reason [[experiments.e37-loss-mechanism]]'s version could not
ship: dividing by every move measured how often exchanges *happen*, not how well the player handles
them, and it spread 1.17×.

## Three formulations

| | denominator | pooled | spread | r with the overall error rate |
|---|---|--:|--:|--:|
| E37, per move | every move | 5.5 % | 1.17× | −0.372 |
| **conditional** | exchanges entered | 11.0 % | **1.62×** | **+0.785** |
| **narrow** | entries that looked sound by SEE | 7.8 % | **1.49×** | **+0.760** |

**Tightening the denominator worked, and it worked on the wrong axis.** Going from "every move" to
"exchanges you actually entered" took the spread from 1.17× to 1.62× — a real improvement, and the
claim promptly failed the *other* screen at +0.785, past the +0.737 that closed S7.

The third formulation was an attempt to isolate the skill: only count exchanges where **the player's
own capture looked sound** by static exchange evaluation, so what is left is a wrinkle they did not
see rather than an exchange they were plainly losing. 3,217 such entries, 252 went wrong, spread
1.49× — and **+0.760**. Still the error rate.

## The pattern across everything screened so far

Laying the material candidates side by side, the survivors have something in common that has nothing
to do with how they were formulated:

| claim | spread | r with error rate | shape |
|---|--:|--:|---|
| `sacrificed_for_attack` | 2.71× | **+0.208** | **an action the player took** |
| `miscounted_exchange` | 1.75× | **+0.123** | **an action the player took** |
| `moved_into_attack` | 1.36× | **+0.225** | **an action the player took** |
| `left_hanging` | 1.61× | +0.917 | a state their position was in |
| `ignored_threat` | 1.44× | +0.914 | a state their position was in |
| `lost_to_a_sequence` | 1.38× | +0.838 | something that happened to them |
| exchange, conditional | 1.62× | +0.785 | something that happened to them |
| exchange, narrow | 1.49× | +0.760 | something that happened to them |

**Every claim about what the player *did* is independent of their error rate. Every claim about what
*happened to them* is the error rate.** That is not a coincidence and it is not about tuning: being
punished is downstream of erring, so any count of punishments is a count of errors with extra steps.
Recorded as L-042.

It also answers the reviewer's request in a way that is better than "no". **The action-shaped half of
the exchange question already ships**: `miscounted_exchange` counts captures the player started that
lose material, at +0.123. What cannot be separated from general error-proneness is the *outcome*
half — coming out of an exchange behind — however carefully its denominator is drawn.

## The pin/fork ordering — the hypothesis is refuted

E37 found pins winning material 1.6× as often as forks. The reviewer's explanation:

> "This statement is true maybe because forks are easier to see."

Testable, and false. Of the player's **own** chances, when the engine's best move executes each
pattern:

| motif | chances | missed | miss rate |
|---|--:|--:|--:|
| discovered attack | 425 | 138 | 32.5 % |
| **fork** | 393 | 126 | **32.1 %** |
| trapped piece | 159 | 48 | 30.2 % |
| skewer | 102 | 28 | 27.5 % |
| **pin** | 993 | 269 | **27.1 %** |
| capturing the defender | 405 | 81 | 20.0 % |
| free pawn | 685 | 122 | 17.8 % |
| free piece | 935 | 74 | 7.9 % |

**Forks are missed slightly more often than pins**, 32.1 % against 27.1 % — the opposite of the
hypothesis. What explains E37's ordering is the first column: **pins arise 2.5× as often** (993
chances against 393). Pins win more material because there are more pins, not because they are
harder to spot.

Two other things fall out of that table. **Free pieces are missed 7.9 % of the time and free pawns
17.8 %** — players take a hanging piece more than twice as reliably as a hanging pawn, which is E32's
finding arriving from a different direction. And **discovered attacks are the hardest thing on the
board** at 32.5 %, which nothing in the report currently says.

## Consequence

**No new claim.** Three formulations, three refusals, and the third one explains why a fourth is
unlikely to help.

**The unattributed 10.7 % stays out**, on the reviewer's instruction: *"this should be left aside now,
the positional weaknesses are not the priority because this is the next level of player kind of a
mistake."* That is a scope decision and a defensible one — a slow positional loss is not what a
1400–1800 player should be working on while a third of their material goes to exchanges.

## Honest limitations

- **An exchange is defined as consecutive captures on one square.** A recapture delayed by an
  in-between move breaks the run and is not counted, which is precisely the zwischenzug case the
  narrow formulation was trying to capture — so that formulation is weaker than it sounds.
- **Material balance across the run** ignores compensation. A player who gives an exchange for a
  strong initiative is counted as coming out down.
- **The miss rates above pool all twelve players** and say nothing about whether individuals differ;
  that is the per-motif claim S1 already makes.
- **Twelve players**, and correlations on twelve points have wide intervals — the +0.78 and +0.76 are
  comfortably past the line but should not be read to three decimals.
