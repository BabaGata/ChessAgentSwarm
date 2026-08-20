---
id: cas-exp-e42
title: 'E42 — The claims barely overlap, which refutes E41''s explanation and shrinks its own fix'
desc: 'Built to suppress cross-section aggregates, and measured that there are almost none: 501 candidate pairs, median 3 % coverage, one pair over threshold. The rule ships anyway, calibrated against the convention the project already uses, and changes exactly one player of twelve.'
updated: 1787961600000
created: 1787961600000
---

# E42 — How much do the swarm's claims describe the same moves?

**Answers:** D15 defect (c), and the author's instruction to fix cross-section aggregate suppression ·
**Code:** `experiments/e42-claim-overlap/` · **Date:** 2026-08-20 ·
**Status:** done — **the premise was wrong, the fix ships small and honest**

## What this was built to fix, and why that was wrong

[[experiments.e41-cost-ranking]] concluded that material claims lose the cost ranking because
`early_error` **contains** them: it tallies every diagnosable error in the opening window, hung pieces
included, so a phase bucket outprices a motif by construction.

The first half is true — `s4_opening_outcomes.py:141` really does tally that way. **The conclusion
drawn from it is not.** Measuring the actual instance sets:

| across 12 players, 501 ordered cross-section pairs | |
|---|--:|
| median coverage of the wide claim by the narrow one | **3 %** |
| 90th percentile | **15 %** |
| pairs reaching 50 % | **5 (0.8 %)** |
| pairs reaching 80 % | **0** |

The claims are about **different moves**. `early_error` outprices `hangingPiece` because more errors
happen in the opening than hanging pieces anywhere, not because it swallows them. Cost ranking does
rank by category width, but width here means *how many distinct mistakes a claim covers*, which is a
much weaker objection than double-counting — and E41's defect (c) is **corrected** rather than
confirmed.

The shipped three tell the same story: 34 pairs across twelve players, **median 21 %** overlap, only
2 of 12 players with any pair sharing half of the smaller claim.

## Setting a threshold without inventing one

`drop_redundant_aggregates` already declares a pooled parent redundant against its own subdivision —
by convention, with nothing measured behind it. So measure coverage on **exactly the pairs the
project already deletes** and the convention becomes a number:

| relationship | n | median | range |
|---|--:|--:|--:|
| **pooled parent vs its own subdivision** (already deleted) | 2 | 65 % | 60–69 % |
| same kind, neither pooled — siblings | 59 | 6 % | 0–59 % |
| different sections entirely | 501 | 3 % | 0–77 % |

`REDUNDANT_COVERAGE = 0.60` is the weakest of the pairs the codebase already removes. A cross-section
rule set there **deletes nothing the codebase would not already delete if the two claims happened to
share a kind** — which is a calibration rather than a preference.

## A real bug found on the way

Of the 2 pooled-parent pairs that occurred, **2 were split across the asserted and watched pools** —
and `drop_redundant_aggregates` runs on each pool separately, so it saw neither. The within-section
rule was leaking every case it met in this sample.

It turns out to be **benign**: in both, the subdivision was the less assertable of the two, and
deleting a claim the player can be told about in favour of one they cannot would leave them with
less. The new rule declines to fire there for exactly that reason. The leak was real; the damage was
not.

## What shipped

`chesscoach/overlap.py` — `coverage()` and `drop_covered_claims()`, called once at the top of
`select_priorities` so it sees **both pools and every section**, which no section can. Three guards,
each from a failure it prevents:

- the **narrower** claim is kept, matching the within-section rule's reasoning;
- a claim is only replaced by one **at least as assertable**, so the cross-pool case cannot trade a
  sayable finding for an unsayable one;
- removal is decided against the original set, so *A covers B covers C* cannot cascade to nothing.

An exact size tie is deliberately left alone: neither claim is the narrower, and a tiebreak on id
would delete the more useful one as often as not.

## Result — one player of twelve, and that is the honest number

| | before | after |
|---|---|---|
| maxhayastan | `time_pressure_error`, `endgame_error`, `motif:pin` | **`endgame_error`, `motif:pin`, `motif:fork`** |
| the other eleven | — | **unchanged** |

77 % of maxhayastan's time-pressure errors *were* the rook-endgame moves — endgames are where the
clock runs out — so one of their three slots was spent saying the same thing twice. It now carries a
third distinct claim.

**Cost:** pure computation, no engine and no model. Serialising `instances_at` grows a real profile
from 16.4 KB to 17.9 KB (**1.09×**, 101 instances across 9 findings), well inside C1/C4.

## Honest limitations

- **Twelve players, 501 pairs, one firing.** A rule justified by a single observation is a rule
  justified thinly. What carries it is that the *threshold* is calibrated against an existing
  convention rather than against that observation.
- **A 20-game window**, so every claim's instance set is small and coverage is noisier than it looks;
  `already_redundant` has **n = 2**, which is a very thin calibration set and the weakest number in
  this note.
- **This does not address D15's other two defects**, which are the larger ones: 5 of 12 material
  claims never become candidates, and the focus gates block 7 more. Neither is touched here.
- **The premise being wrong is the main result.** The mechanism was built as instructed and is
  correct and calibrated; it simply had far less to do than E41 predicted, and saying so is the
  finding.
