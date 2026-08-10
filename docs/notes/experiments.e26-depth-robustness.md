---
id: cas-exp-e26
title: 'E26 — 90% of the swarm''s errors survive a much deeper engine'
desc: 'Blunders 97%, all errors 90%, implied rate ratio 1.05. The weak spot is the suggested better move at 78%, not the diagnosis.'
updated: 1786665600000
created: 1786665600000
---

# E26 — Do the findings survive a deeper engine?

**Answers:** the first evidence bearing on [[vision]]'s success criterion 2 · **Date:** 2026-08-08 ·
**Status:** done — **the foundation holds**

## Question

Every claim in this project rests on **depth 15** calling a move an error. E01 established at the
very beginning that labels shift with depth, and that fact was used to key the evaluation cache and
then never followed up. Nothing had ever asked whether a deeper engine agrees with the diagnoses the
swarm ships — which is the assumption underneath all seven sections, V1's rating estimate, and every
cited position in every report.

This is the closest thing to *"the weaknesses the swarm names match those an independent analysis
identifies"* that can be run without a human. The independent analysis is the same engine given far
more time: a weaker check than a strong player, and a real one.

## Method

**1,200 moves sampled from 30 players**, re-labelled at **depth 22** by exactly the production path —
evaluate the position before, evaluate it after the move played, run the same `move_loss_wp` and
`classify`. Only the depth changes.

**Sampled rather than exhaustive, deliberately.** The first design re-analysed one player's whole
corpus and was measured at **53 minutes per player**. The quantity being estimated is a proportion,
so its precision comes from the number of moves and its generality from the spread of players; the
same compute buys far more of both by sampling 30 players than by exhausting one (L-035). Cost as
run: 2,400 distinct positions, **32.5 minutes** at 16 workers.

## Result — the diagnosis is robust

| | |
|---|--:|
| moves called an error at depth 15 | 169 |
| **still an error at depth 22** | **152 — 90 %** |
| exactly the same label | **95 % of all moves** |
| clean at 15, an error at 22 | 26 — 2.5 % of clean moves |
| **implied error-rate ratio at 22** | **1.05** |

By severity:

| label at 15 | n | still that label | still an error at all |
|---|--:|--:|--:|
| **blunder** | 34 | **97 %** | **100 %** |
| mistake | 33 | 79 % | **100 %** |
| inaccuracy | 102 | 75 % | 83 % |

**Blunders are the most robust tier and they are the one V1's rating estimate rides on.** Not one
blunder at depth 15 became a clean move at depth 22.

Mistakes never became clean either — they move between tiers, not out of the set. **All the genuine
disagreement is at the inaccuracy boundary**, which is what a threshold at 10 win-probability points
should be expected to do: 17 inaccuracies went clean, 26 clean moves became inaccuracies, and those
two nearly cancel. That cancellation is why the implied rate ratio is **1.05** — a claim's rate, and
therefore the peer comparison that turns it into a finding, barely moves.

## Result — the suggested move looked like a weak spot and is not

> **the better move the player was shown is still the engine's top choice: 78 %**

In roughly one case in five, depth 22 prefers a different move. That figure is easy to overread, and
the follow-up shows it should not be read as a defect at all — because **the report never claims the
shown move is optimal**. It claims it was better than what happened:

> For example game 3YS085d3, move 40, you played `f6e6` (`h3e6` was better)

So the bar that matters is the weaker one. Measured directly, on the 169 sampled moves where the
report would offer an alternative (`better_move.py`, 338 positions, 2.7 minutes):

| at depth 22 | |
|---|--:|
| **the shown move still beats the move played** | **169 / 169 — 100 %** |
| the two are within 1 win-probability point | 0 |
| **the shown move is worse** | **0** |

| win probability the shown move gains | |
|---|--:|
| median | **17.8** |
| p10 / p90 | 9.6 / 37.8 |

**Not one regression.** With n = 169 and zero failures, the rule of three puts the true rate of
"we showed you something worse than you played" **under about 2 %**, which is the honest way to
state a clean sweep.

So the 78 % measures the alternative slipping from first to second best — sound advice either way —
and the claim the report actually makes holds in every case sampled, by a wide margin: the typical
suggestion is worth nearly 18 points of win probability over what the player did.

## Consequences

1. **The foundation under every section holds.** The single largest untested assumption in the
   project has now been tested and survived.
2. **Rates are depth-stable at 1.05**, so findings are not an artefact of the depth setting, and
   depth 15 remains the right operating point under C1 — depth 22 costs ~40× more for a 5 % shift in
   a rate that is then compared against a population measured the same way.
3. **The evidence lines hold too.** The concern the 78 % raised was measured and dismissed: every
   suggestion sampled still beats what the player played, by a median of 17.8 win-probability points.
   Nothing to fix.

## Honest limitations

- **Depth 22 is not truth**, it is more evidence. Where the two disagree this says a label is
  *fragile*, not that it is wrong.
- **The blunder figure rests on 34 moves.** 97 % with n = 34 is roughly ±6 points; the headline 90 %
  on 169 errors is roughly ±4.5. Both are consistent with the claim and neither is precise.
- **Sampling was uniform over the player's diagnosable moves**, so severe and trivial positions are
  represented in proportion. A sample weighted toward the positions reports actually cite would test
  the player-facing claims more directly and was not done.
- **The 100 % is on 169 moves**, which bounds the failure rate under ~2 % rather than establishing
  zero. It also only covers moves the swarm *labelled* as errors — a suggestion attached to a move
  that depth 22 thinks was fine is a different question, and one the 90 % figure already speaks to.
- **This is engine-against-engine.** It cannot detect an error the engine makes at both depths, and
  it says nothing about whether the *claim kinds* — hanging pieces, early errors, time budget — are
  the right way to describe a player. Criterion 2 needs a human for that.
