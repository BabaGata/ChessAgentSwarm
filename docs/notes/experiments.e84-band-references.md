---
id: cas-exp-e84
title: 'E84 — Three rating bands, and a denominator that was built, measured and reverted'
desc: 'The band guard blocking the rebuild is answered by building three overlapping bands instead of one, so a 1900 player is compared against 1600-2000. D2s motif-specific allowed_motif denominator was measured on the result and reverted: same band and speed, it cost three claims their separation, left two unmeasurable, and improved none.'
updated: 1788606000000
created: 1788638400000
---

# E84 — Three bands, and reverting D2

**Answers:** the blocked rebuild in [[design.claims-that-do-not-separate]] ·
**Code:** `experiments/e84-band-references/` · **Date:** 2026-09-05 ·
**Status:** **band split adopted. D2 reverted.**

## The block, and the way through it

D2 changed what `allowed_motif`'s denominator counts, so every reference on disk was stale for those
claims and had to be rebuilt. The band guard refused: **15 of 65 blitz players sit outside
1400-1800**, from 720 to 2006. Building one band and discarding them is correct and wasteful.

The corpus supports three, and the author chose three:

| band | blitz | rapid |
|---|--:|--:|
| 1200-1600 | 44 | 40 |
| 1400-1800 | 50 | 51 |
| 1600-2000 | 31 | 46 |

**The bands overlap on purpose.** `declared_band_is_wrong` reads the player's median rating against
the band plus `BAND_EDGE_TOLERANCE`, so a 1500 player belongs in both 1200-1600 and 1400-1800. These
are overlapping windows on one population, not a partition of it.

**The third band is the point.** The guard's own docstring records what the single band cost: of the
twelve review players, *"the three strongest — 1930, 1988, 1988 — came out with **no findings at
all**, which the report renders as nothing being unusual about their play. It is not a statement
about their play."* That is the same failure the author raised about `maikel5`.

## D2 was measured on the result, and it is a regression

Holding **band and speed constant** — 1400-1800 blitz, the same players, only the denominator
differing — D2 (formulation **B**) against the original (**A**):

| claim | A rate | A disp | A players | B rate | B disp | B players | |
|---|--:|--:|--:|--:|--:|--:|---|
| `hangingPiece` | 0.105 | 1.83 | 65 | 0.853 | 1.61 | 50 | separates both |
| `trappedPiece` | 0.035 | 1.56 | 63 | 0.192 | 1.54 | 49 | separates both |
| `discoveredAttack` | 0.029 | 1.36 | 64 | 0.239 | 1.51 | 47 | separates both |
| `capturingDefender` | 0.072 | 1.25 | 65 | 0.533 | 1.27 | 49 | flat both |
| **`hangingPawn`** | 0.118 | **1.75** | 65 | 0.524 | **1.16** | 50 | **separated → flat** |
| **`fork`** | 0.033 | **1.42** | 64 | 0.659 | 1.50 | **17** | **separated → flat** |
| **`pin`** | 0.051 | **1.35** | 65 | 0.102 | **1.10** | 50 | **separated → flat** |
| **`skewer`** | 0.010 | 0.62 | 49 | 0.200 | — | **2** | **unmeasurable** |
| **`backRankMate`** | 0.007 | 0.22 | 14 | **1.000** | — | **0** | **degenerate** |

**Three claims lost their separation, two became unmeasurable, and none improved.**

## Why it failed, precisely

D2's argument was that `missed_motif` conditions on the motif being available, so `allowed_motif`
should too. **The analogy is where it broke**, and the asymmetry is exact:

- In `missed_motif`, the denominator is *"the engine's best move executes X"* and the numerator adds
  *"and the player erred"*. **The thing that varies is the player's move.**
- In `allowed_motif` under B, the denominator is *"X was available"* and the numerator is *"the
  engine's best reply took it"*. **The thing that varies is the engine's choice.**

Once the position exists, whether the available tactic is objectively best is not something the
player influences. Two consequences follow, and both appeared:

**Saturation.** `_is_back_rank_mate` requires `after.is_checkmate()`, and an engine always plays an
available mate. So `P(best reply executes it | some reply executes it)` is **1.000 by construction**,
for every player, permanently — no amount of data can make that claim separate anyone. `hangingPiece`
reached 0.853 by the same mechanism.

**Power collapse.** The denominator falls from "all your errors" to "errors where X happened to be
available", which for a rare motif is almost nothing: `backRankMate` 14 players → **0**, `skewer`
49 → **2**, `fork` 64 → **17**.

## The three formulations, for the record

| | instance | denominator | what varies |
|---|---|---|---|
| **A** — shipped, restored | best reply executes X | all errors | mixture |
| **B** — built, reverted | best reply executes X | errors where X available | **the engine's choice** |
| **C** — not built | error **left X available** | all errors | **the player's move** |

**A ≈ C × B.** The original conflates *"did you leave it there"* with *"was taking it best"*, which
is why a motif flat under C is flat under A.

**C is not adopted here.** It puts the player back as the actor, has a strictly larger numerator than
A and so more power, and cannot saturate. It also changes what the claim *means* — from "what
punished you" to "what you left available" — which is an editorial decision, not an arithmetic one,
and it is the author's. It does not solve rarity: a motif seldom available stays a rare event.

## What is kept

- **The three-band reference**, which is independent of D2 and answers a block that predates it.
- **`merged_with` carries the older input's schema version.** It rebuilt the reference without it, so
  merging an older file into a current one produced something labelled current while holding older
  cells. Found while building D2's guard and kept after reverting it, because it is wrong regardless
  of what any version means.
- **D1 is untouched.** Nine claims still make no peer comparison; that rests on E83, not on D2.

## The bands were the point: twelve more claims do not separate

With the reference rebuilt on the restored denominator, E83's screen could finally be run **within
band** rather than on a pool spanning 720 to 2006. A pooled null over players with genuinely
different rates **inflates** dispersion, so the pooled figures were the optimistic side of a bracket.

**Twelve verdicts moved. Every one of them from separating to flat, with no recoveries.** A
consistent direction across twelve independent claims is the signature of a systematic effect, not of
noise.

| claim | pooled | within band | players |
|---|--:|--:|--:|
| `concedes_weakness.backward` | 1.84 | **1.06** | 50 |
| `missed_motif.hangingPiece` | 1.89 | **1.24** | 50 |
| `allowed_motif.discoveredAttack` | 1.76 | **1.24** | 49 |
| `executed_motif.trappedPiece` | 1.66 | **1.09** | 24 |
| `sacrificed_for_attack` | 2.05 | **1.24** | 50 |
| `allows_square.any` | 1.47 | **1.10** | 50 |
| `concedes_weakness.any` | 1.36 | **1.07** | 50 |
| `allowed_motif.capturingDefender` | 1.44 | **1.31** | 50 |
| `allowed_motif.pin` | 1.33 | **1.25** | 50 |
| `executed_motif.hangingPiece` | 1.44 | **1.29** | 50 |
| `executed_motif.pin` | 1.44 | **1.28** | 50 |
| `executed_motif.fork` | 1.62 | **1.47** | 12 |

**Within band is the test that matches the claim.** A peer lookup is keyed on
`(band, speed, claim)`, so *"you do this more than your peers"* is a statement about the player's own
band. Separation has to hold there or the sentence has nothing under it.

### Flat, or only fifty players instead of eighty-three?

Fewer players means less power, so the same question E83 asked is asked again. **Eleven of the twelve
are genuinely flat**, at smallest-visible-differences of **1.04–1.30×** — inside the band E83 itself
called conclusive. Only `sacrificed_for_attack.own_move` at **1.39×** is underpowered, and it is
marked inconclusive rather than settled.

### What the register becomes

**10 entries → 21**, of which **16 are asserted** (five `executed_motif` claims are never reported).
27 claims still separate within band; 5 are too thin in any single stratum to say either way, and are
**not** withheld — unmeasured is not a verdict.

The register is now **generated** by `experiments/e84-band-references/register.py` rather than typed,
because the design note required it to be evidence rather than opinion and a hand-typed list drifts
from the reference it claims to describe.

## Honest limitations

- **The comparison is one stratum.** 1400-1800 blitz was chosen because it is the only band the old
  reference covers, so it is the only place A and B can be compared on the same players. The
  direction is consistent across 1200-1600 blitz, but that is corroboration, not replication.
- **B is not disproved as an idea, only as this claim's denominator.** A conditional rate is the
  right shape when the player is the one acting on the condition, which is why `missed_motif` keeps
  it.
- **E83's verdicts stand as measured**, since A is restored. They were computed on a band-mixed pool,
  which inflates dispersion, so the flat verdicts remain conservative and the separating ones remain
  the optimistic side of the bracket.
- **One stratum carries most of the within-band verdicts.** `1400-1800|blitz` has the most players,
  and `best_within_band` reports the largest stratum rather than combining them — recombining is the
  mixing being measured. A claim flat there could separate in another band, and that is not tested.
- **The screen is still dispersion**, which says players differ, not that a claim measures a skill.
  `plays_queenless` reaches 36.9× within band and is a style variable.
