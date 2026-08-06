---
id: cas-arch-peer
title: Peer Reference
desc: 'The rating-band reference population: what "unusual for a player at your level" means, mechanically.'
updated: 1785257900000
created: 1785257900000
---

# Peer Reference

The artefact three separate lines of work converged on in [[mission.step-05-assess-s2]]:

1. **C6** — after E03 ruled out error co-occurrence, peer deviation is the only remaining route to
   relevance weighting;
2. **[[evaluation]] D2** — base-rate specificity, the metric that catches true-but-useless output;
3. **S2's withheld conditions** — `selection_confounded` claims cannot be asserted without it.

## The problem it solves

M5 produced the clearest possible demonstration. Four of six real players showed an elevated error
rate after long thinks, at 2.1–2.9× their own baseline. Every one of those measurements was correct.
None of them was a diagnosis, because **a long think happens where the position is hard, and hard
positions produce errors** — the condition is selected by the thing that causes the outcome.

A within-player baseline cannot separate *"you are bad at this"* from *"everyone is bad at this"*.
Only a population can. That is the whole job of this component:

> **peer rate** = the rate at which players *at this level, in this time control* exhibit the same
> condition. A claim whose lift over the peer rate is ≈ 1 is a description of chess, not of the
> player.

## Design

### Separate measuring from asserting

Section agents currently do both: they compute condition rates and then decide what may be said. The
reference builder needs the first without the second — it wants every player's rates, including the
unremarkable ones, and it must not run the confidence policy at all.

So the section contract gains a second method:

```
measure(context) -> tuple[ConditionMeasurement, ...]   # raw rates, no judgement
report(context)  -> SectionReport                     # measure() + confidence policy
```

`findings()` becomes a thin layer over `measure()`. This is a better separation than the one it
replaces — the confidence policy was tangled into measurement, which is exactly why the peer
corpus could not be built without it.

### What is stored

A flat mapping, keyed by what makes rates comparable:

```
(band, time_control, claim_key) -> { rate, n_players, n_moves, ci95 }
```

`claim_key` is the existing deterministic claim identity, so a section that invents a new condition
automatically gets a slot without the store knowing anything about chess.

Stored as JSON and vendored, like the puzzle and opening corpora: built once, no runtime network
dependency, inspectable by hand.

### Leave-one-out

A player must never be compared against a population containing themselves — with a small reference
that inflates or deflates their own deviation. The store therefore keeps **per-player contributions**
rather than only the pooled rate, so a player's own contribution can be subtracted when they are the
subject.

This costs a little size and removes a whole class of quiet circularity.

### How it changes assertion

`Measurement.peer_rate` gets filled when the store has an entry. [[architecture.confidence]] then
applies the rule it was always written for — the interval must exclude the **peer** rate, not merely
the player's own baseline. For `selection_confounded` conditions this is the *only* comparison
permitted; without a peer entry they stay withheld.

## Data source

Sampled through the Lichess API, the same route as `fetch_games.py`: players are drawn from recent
arena standings inside a rating band, and their games fetched by time control. Free, already
verified working (E1), and directly comparable to the subject's own corpus.

**Not** the full open database. It is many gigabytes per month and would buy accuracy the thesis
does not need — a few hundred games per band puts the reference interval well inside the precision
any individual claim can support.

## Built — and what it changed

`chesscoach/peers.py`, plus `build-peer-reference` and an `--peers` option on `analyse`.
The section contract gained `measure()`, separating raw rates from assertion as designed.

**First reference**, from the 135 games already analysed across seven players, band 1400–1800, rapid,
depth 15:

| Condition | Population rate | Sample |
|---|---|---|
| long think → error | **17.7 %** | 140 / 789 moves, 7 players |
| instant move → error | 7.3 % | 119 / 1629 moves, 7 players |
| time pressure → error | 16.7 % | 12 / 72 moves, **2 players** |

### The effect on what gets said

Before the reference existed, four of six players had an apparent long-think weakness at 2.10–2.85×
their own baseline. Against the population:

| Player | vs own baseline | vs peers | Asserted? |
|---|---|---|---|
| esik24 | 2.85× | **1.65×** | yes |
| levit79 | 2.10× | **1.52×** | yes |
| Lipetsk-Kanst_54 | 2.22× | — | **no**, inside the population rate |
| Correlona | 2.31× | — | **no**, below the population rate |

Two claims survive, and the two that survive are **roughly half as dramatic** as they looked. The
self-baseline was overstating by exactly the amount the population shares the behaviour — which is
the whole reason M5 refused to let these be asserted.

Leave-one-out is visible in the output: esik24 is compared against 17.1 % and levit79 against 15.8 %,
because each is excluded from the population they are judged by.

## Widened to 38 players — and what that showed

Rebuilt from **38 players / ~820 games**, band 1400–1800, rapid, depth 15:

| Condition | 7 players | **38 players** | Sample |
|---|---|---|---|
| long think → error | 17.7 % | **17.8 %** | 654 / 3675 moves |
| instant move → error | 7.3 % | **7.5 %** | 575 / 7669 moves |
| time pressure → error | 16.7 % | **15.5 %** | 45 / 290 moves, 13 players |

**The population rate barely moved.** A seven-player reference already estimated it to within
0.1 points. That is a genuine and slightly surprising result: population rates converge fast.

**Individual verdicts did not.** `esik24` was asserted at `priority` against the small reference
(peer 17.1 %) and is **silent** against the wide one (peer 17.5 %). A 0.4 percentage point change in
the reference flipped the verdict, because that player's interval straddles the population rate.

The two facts are consistent and the combination is the lesson: a small reference is adequate for
*estimating the population*, and inadequate for *judging a borderline player* — because the
borderline is exactly where a small change in the reference decides the answer. See L-013.

## Widened again to 84 players / 150-game histories (2026-08-06)

Rebuilt from the E05 deep histories — **84 players, 11,890 games**, roughly **14× the evidence**
→ [[experiments.e12-corpus-depth]]. It sharpened the qualifier above rather than overturning it.

| | change from 38 → 84 players |
|---|---|
| the frequent claims (`long_think_error`, `early_error`, `concedes_weakness`, …) | **under ±5 %** |
| **the infrequent ones** | `allowed_motif.backRankMate` **−53 %** · `missed_motif.capturingDefender` **+40 %** · `endgame_error.minor` **+33 %** · `allowed_motif.skewer` **−21 %** |

**"Population rates converge fast" was measured on the frequent claims, and holds only for them.**
Every section built since — S3 through S8 — leans on infrequent ones, where 38 players were *not*
enough: a `backRankMate` peer rate that halves is the difference between a finding and silence for
anyone near the boundary.

So the reference is now built from the deep histories, and L-013's rule is restated with its scope:
a small reference estimates a *common* rate well, a *rare* rate badly, and a borderline player not at
all.

### Coverage, across 38 players

| | |
|---|---|
| a finding asserted | **6** (16 %) |
| nothing to report | 28 (74 %) |
| insufficient data | 4 (10 %) |

All six findings are the **same claim kind**. S2 has three conditions and effectively one working
detector: time pressure almost never triggers in 600+0 games, and instant moves never clear the
population rate. A coach whose only sentence is "you err after long thinks" is not yet a coach —
which is the strongest argument yet for building S1 next.

## Honest limitations, stated before building

- **The first build will be small.** Bootstrapped from the 135 games already analysed across seven
  players. That is enough to demonstrate the mechanism and to test whether the long-think effect is
  universal; it is *not* enough to be a trustworthy reference, and any finding resting on it must say
  so.
- **A band is not a population.** Players at 1400–1800 in rapid arenas are not a random sample of
  players at that level; they are a sample of people who play rapid arenas.
- **Depth-bound.** Peer rates are computed at a fixed engine depth and are not comparable across
  depths, exactly as findings are not (E01). The depth belongs in the store.
- **It does not establish causation.** "You do this more than your peers" is a stronger claim than
  "you do this", and still not "this is why you lose".
