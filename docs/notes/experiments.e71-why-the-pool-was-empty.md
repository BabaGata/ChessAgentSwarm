---
id: cas-exp-e71
title: 'E71 — The cost pool was empty for one reason and not the one that was guessed'
desc: 'The engine pass E70 could not run. Both inferred claims confirmed exactly; the cost pool turns out to work for 9 of 12 players; and the endgame run rule cost 6 priority slots — none of them to the calibration that was the obvious suspect.'
updated: 1788195600000
created: 1788195600000
---

# E71 — Why the cost pool was empty, measured

**Answers:** [[experiments.e70-band-mismatch]]'s two stated limitations ·
**Code:** `experiments/e71-why-the-pool-was-empty/` · **Date:** 2026-08-31 ·
**Status:** done — **both inferences confirmed, two of E70's claims corrected**

## What E70 could not do

E70 named maikel5's two claims from the detection sheet and said plainly that it was inferring
them, because no engine on the machine would run. A working Stockfish 18 arrived, so this reads the
numbers instead of reasoning about them.

## The two claims, confirmed exactly

**`time_pressure_error.clock.own`** — 15 instances in 5 of 18 games.

| | maikel5 | peers (1400–1800) |
|---|--:|--:|
| rate | 23.1 % | 25.1 % |
| **cost** | **9.28 wp/game** | 11.18 wp/game |
| exposure | 3.61/game | 2.50/game |

Gate failed: **below the peer rate, and not exposure-driven.** `driven_by_exposure` requires the
cost to exceed the peers' and his does not, so the flag is correctly False.

**And this is the finding, not a footnote.** He gives away **9.28 win-probability points a game** to
the clock, and meets time pressure **44 % more often** than the reference population, and is told
nothing — because players rated 1400–1800 give away 11.18. Every number in that comparison is
correct. The population is wrong.

**`concedes_weakness.backward.own`** — 6 instances in 5 of 18 games, rate 1.6 % against 1.0 %.
Gate failed: **unpriceable**. The section structurally cannot say what it cost, because conceding a
structure is a choice rather than a mistake, so it can never enter the cost pool at all.

One unpriceable claim and one cheaper-than-peers claim. The pool was empty because it had nothing
eligible to hold, exactly as E70 inferred.

## Correction 1 — the cost pool works, for nearly everyone

**E70 said the fallback "could not save it" and left the impression that it fails for strong players
generally. It does not.**

| | n | asserted findings | **priorities delivered** |
|---|--:|--:|--:|
| above the band | 4 | 0.25 | **1.75** |
| inside it | 6 | 0.67 | **2.67** |
| below it | 2 | 5.50 | **3.00** |

Nine of twelve players get a full three priorities. The band gradient is stark in the *asserted*
column — the diagnosis half — and **the cost pool absorbs most of it** by the time anything reaches
a player. maikel5 is the **only** player at zero, and Odin5306 and maxhayastan the only two below
three.

That makes the failure narrower and more precise than E70 described: not *"peer-relative ranking
starves strong players"* but *"the fallback needs one priceable claim that costs more than the
reference population, and a player compared against a weaker population may have none"*.

## Correction 2 — r is −0.79, not −0.88

E70 computed its correlation from E55's **sheet-build log** rather than from a diagnosis, and the
counts differ: cademan 3 asserted rather than 5, Maximilian_Honigtopf 8 rather than 6, bernes 0
rather than 1. Measured directly, **r(rating, asserted findings) = −0.79**.

The direction, the monotone gradient and the conclusion are unchanged. The number was not.

## The run rule: the obvious suspect was innocent

E70 asked how much of the silence belonged to the endgame run rule rather than the band. The band
cannot explain a *change*, because it was always wrong; the rule changed twice, and **the two
changes had to be told apart**.

| | shipped 3-in-3 | E67's 3-in-4 | no run rule |
|---|--:|--:|--:|
| maikel5 | **0** | 0 | 2 |
| maxhayastan | **1** | 1 | 3 |
| Odin5306 | **1** | 1 | 3 |

| | priority slots cost |
|---|--:|
| **E68's tightening** (3-in-4 → 3-in-3) | **0** |
| **E67 introducing the run** at all | **6** |

**E68's calibration cost nothing.** The loss belongs entirely to E67, which introduced the run on
the author's own words — *"imprecise one move after the other"* — and is therefore the intended
consequence of a change that was correct, not a regression.

This was worth measuring rather than asserting: the calibration was the recent change, the obvious
suspect, and the one I had already written down as the likely cause. It was not the cause.

## Consequence

- **maikel5's silence has two causes and both are now named.** The band gives him no claim that
  beats the reference population, and the run rule removed the endgame claims that used to fill the
  gap. Neither is a defect in the arbiter.
- **E70 is corrected** on its correlation and on how it characterised the cost pool.
- **The read-side decision is unchanged and still the author's** — and this sharpens it, because the
  thing being withheld from maikel5 is now a number: 9.28 wp/game to the clock.

## Honest limitations

- **The band's own contribution cannot be isolated by toggling**, because there is no second stratum
  to toggle to. Everything above about the band is a comparison against the *only* population that
  exists. That asymmetry is the finding rather than a gap here.
- **n = 12**, 20 games each, one time control, and the below-band group is two players.
- **This says nothing about whether the claims are true.** It says which gate each fails and why the
  pool was empty. Whether `time_pressure_error` correctly identifies time-pressure errors is the
  detection sheet's question and it is still unmarked.
- **The 9.28 wp/game figure is a cost, not a forecast.** It is what those moves gave away, not what
  fixing them would recover.
