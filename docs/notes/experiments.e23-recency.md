---
id: cas-exp-e23
title: 'E23 — Old games still describe the player, so step 7 is not built'
desc: 'Games over a year old predict recent play about as well as games two months old. Decay would have spent the binding constraint for no measured gain.'
updated: 1786492800000
created: 1786492800000
---

# E23 — Old games still describe the player

**Answers:** step 7 of [[design.short-history-prioritisation]] · **Date:** 2026-08-06 ·
**Status:** done — **refused on evidence; nothing built**

## Question

Step 7 proposed decaying a game's weight by its age, reasoning that players drift and a game from
years ago is a different player. Two things made it worth screening rather than building:

- decay **spends effective sample size**, which E16 found to be the binding constraint;
- [[experiments.e20-shrinkage]] was a fresh reminder that plausible reasoning about this system has
  been wrong before, in exactly this area, at exactly this cost.

So: **does an old window predict a player's recent behaviour worse than a recent window does?**

## Method

Three disjoint 40-game windows per player — recent, middle, old — with per-claim rates in each, gates
forced open. The middle-against-recent correlation is the **ceiling** noise allows at this sample
size; old-against-recent is the same measurement two windows further back. The control that
[[experiments.e19-blitz-stratum]] showed to be indispensable, applied to time instead of to speed.

## Result — age costs nothing measurable

| | |
|---|--:|
| middle window predicts recent | median r **+0.19** — the ceiling |
| **old window predicts recent** | median r **+0.24** |
| share of the ceiling the old window keeps | **87 %** |
| calendar gap to the middle window | 58 days |
| calendar gap to the old window | **129 days** |

The old window predicts recent play *as well as* the middle one — nominally better, which is noise.

And the tail, since the case that motivates decay is a *years*-old game rather than a months-old one:

| separation between windows | median r |
|---|--:|
| under a year | +0.29 |
| **over a year** | **+0.23** |

25 claims had enough players on both sides. A gap of 0.06 against a ceiling of 0.19 is not a signal.

**Nothing is built.** Decay would have cost effective sample size — the one thing E16, E20, E21 and
E22 all agree is scarce — to correct a problem that does not appear at any timescale this corpus can
measure.

## Why this is consistent with players improving

E05 measured real drift: about +4.8 rating points over 150 games. That is not contradicted here,
because the two measure different things. Drift is a change in **level**; these correlations are
about **shape** — whether the pattern of what a player is relatively bad at persists.

**It does.** A player gets better across the board while their weakness profile stays recognisably
theirs. That is also why diagnosis does not need decay even though the player is improving: every
claim is measured against a peer population, so a uniform lift moves the player and the comparison
together and cancels out.

## Honest limitations

- **Every correlation here is low in absolute terms**, because 40-game rates are noisy — the ceiling
  itself is only +0.19. This establishes there is no **large** age effect; an effect smaller than the
  measurement noise would be invisible, and one may exist.
- **The corpus limits how far back "old" reaches.** The median old window is 129 days back. The
  over-a-year split has fewer players and correspondingly weaker power.
- **A player who stopped for three years and came back was not isolated.** They exist in the corpus —
  E19 found 20-game windows spanning up to 3,254 days — but the design here averages over players
  rather than picking out the discontinuous ones, and a genuine layoff is the case where decay would
  most plausibly earn its place.
- **This tests diagnosis, not the progress check**, which already measures over new games only and is
  unaffected either way.
