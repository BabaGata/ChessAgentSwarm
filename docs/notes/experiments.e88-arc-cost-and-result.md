---
id: cas-exp-e88
title: 'E88 — What the measurement arc cost, and what it bought'
desc: 'The candidate count was predicted within 12 per cent and the wall clock was wrong by four times, for a reason E85 flagged and did not act on: candidate positions are never prefetched, so they are evaluated serially. And a plain account of what the whole arc produced, most of which is removed false confidence rather than new capability.'
updated: 1788706800000
created: 1788706800000
---

# E88 — The cost, and the result

**Covers:** [[experiments.e83-spread-rescreen]] → [[experiments.e87-seed-lichess-themes]] ·
**Date:** 2026-09-06 · **Status:** record

## The cost calculation, as it now stands

[[experiments.e85-candidate-cost]] predicted the bill for pricing punishment candidates. The rebuild
has now run, so the prediction can be scored.

| | predicted | measured | |
|---|--:|--:|---|
| evaluations, three bands | 62,600 | **69,844** | **+12 % — good** |
| wall clock | ≈ 19 min | **≈ 77 min** | **4× out** |

Evaluations are counted from the cache, which grew **283,576 → 353,420**. Wall clock is the whole
three-band rebuild, **14:35 → 16:42 = 2 h 07**, against roughly 50 minutes for the same six strata
before the rule changed.

### Why the time was wrong, and it is fixable

E85 converted its count using [[experiments.e01-engine-throughput]]'s **55 positions per second**,
which E01 measured with **18 worker processes**. It also flagged exactly this:

> *"The throughput figure is borrowed… Ten minutes is an estimate from a measured rate, not a
> measured wall clock, and the first real run should report its own."*

The flag was right and I did not act on it. The mechanism is specific: `prefetch` calls
`collect_positions(games)`, so **it only covers positions that occur in the games**. A candidate is a
reply that was *never played*, so it is in no game, is never prefetched, and is evaluated **serially**
inside `analyse_game`. Game positions ran 18-wide; candidates ran one at a time, at roughly **15 per
second**.

**This is worth fixing and is not hard.** Candidate positions are enumerable before analysis — the
same `detect_motifs` sweep that finds them costs nothing — so they could join the prefetch batch and
run at the parallel rate. **Estimated recovery: most of the 77 minutes.** Not done, and recorded as
open rather than as a plan.

### What the measurement itself cost

Nothing. E85 ran at **33,767 of 33,767 cache hits**; the audit and the seeding used no engine at all.
The only compute this arc spent was the rebuild.

## What the arc bought

Honestly: **it mostly removed false confidence.** Two changes add capability; the rest corrected
things that were wrong and are now less wrong. Both halves are stated because a record that lists
only the gains is the thing this project keeps catching itself doing.

### Corrections — things that were wrong

| finding | consequence |
|---|---|
| **The discrimination screen was measuring rarity** (E83). p90/median is bounded by 1/median, so it scored how rare a claim is; base rate correlated **−0.53**. E09's accept/reject column is perfectly rank-ordered by base rate. | The screen that decided what to build was not measuring what it claimed. Replaced with overdispersion (**+0.12**). |
| **The pool mixed rating bands** (E84). Players from 720 to 2006 in one null, which inflates dispersion. | Screened within band, **twelve verdicts moved, all the same way**, none recovered. 11 of 12 genuinely flat. |
| **D2 was a regression** (E84). The motif-specific denominator left the engine's move choice as the only thing varying. | Built, measured, **reverted**. `backRankMate` read exactly 1.000 by construction. |
| **One blunder was charged three times.** Cost went to every motif a mistake left available, and the arbiter ranks on cost. | 392 instances against 306 named across 669 errors — **86 duplicated charges removed**. |
| **Two detectors are demonstrably wrong** (E86). `fork` misses forks when a victim was already attacked; `trappedPiece` reports pieces with a safe escape. | Demonstrated on positions. **Not yet fixed.** |
| **The knowledge base was unusable** (E86). 14 entries, none endorsed, `fork` defined as a skewer. | Gate fixed, tactical half re-seeded. |

### Additions — things that are now possible

| | |
|---|---|
| **Three rating bands** instead of one | a 1900 player is compared against 1600-2000, not a population below them — the `maikel5` failure |
| **Punishments need only be worth playing** | **+20 %** more punished errors found; a good fork counts even when mate was also available |
| **Eight sourced tactical definitions** | verbatim from the Lichess theme file whose keys the detectors already use |
| **A discriminating naming gate** | rejects 12 of the 14 stored entries, keeping the two that are real definitions |

### The number that did not move

**Claims that can carry a peer comparison: 21 withheld, before and after.** The register regenerated
to the same size — `allowed_motif.pin` recovered, `allowed_motif.trappedPiece` lost.

That is the honest headline of the whole arc. The measurement is more correct in several independent
ways and **the coach cannot say more than it could before**. Correctness and discrimination are
different properties; this arc bought the first and the design said so at the outset.

**One result vindicates a refusal.** E85 measured `pin` at **49 % of the engine budget** and recorded
that skipping claims which did not currently separate would cut the bill by two thirds — then refused
it as circular, since those claims were flat *under the rule being replaced*. `allowed_motif.pin` is
that claim, and it is the one that recovered. The saving would have guaranteed never learning it.

## Open, from this record

1. **Prefetch candidate positions.** Four times the wall clock of a rebuild, for a change that
   enumerates positions already being enumerated.
2. **Fix the two demonstrated detector defects** (E86 D-1, D-2). Both have a position that reproduces
   them and neither is fixed.
3. **Nine knowledge entries still fail the gate**, and `moved_into_attack` holds nothing at all.
