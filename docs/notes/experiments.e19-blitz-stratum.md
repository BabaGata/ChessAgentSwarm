---
id: cas-exp-e19
title: 'E19 — Blitz is the same player, and step 5 just got much cheaper'
desc: 'Blitz predicts rapid as well as rapid predicts itself (93% of the ceiling). Pool the evidence, stratify the baseline. The automaticity hypothesis died.'
updated: 1786492800000
created: 1786492800000
---

# E19 — Blitz is the same player

**Answers:** step 2 of [[design.short-history-prioritisation]] · **Date:** 2026-08-06 ·
**Status:** done — **decisive, and it reverses the naive reading**

## Question

Step 5 would admit the ~82 % of a player's games the swarm discards. Its shape depends on one thing:
**does a claim's blitz-versus-rapid gap vary between players, or is it a constant of chess?**

| answer | consequence |
|---|---|
| constant | **pool** — one corpus, ~5× the evidence, E16's rarity gate attacked directly |
| varies | **stratify** — three corpora and three references, but the gap becomes diagnostic |

## Method

The same 84 players at both speeds, **matched game counts** (median 40 each) so neither sample size
nor recency differs between strata. Gates forced open. 40 blitz games per player fetched — about
4,000 games and two hours of uncached engine time, the first real compute cost since E12.

## The trap this nearly fell into

The first pass looked conclusive in the wrong direction:

    blitz rate ~ rapid rate    median r +0.17

Read naively, that says blitz measures something else entirely, and step 5 must stratify. **It says
nothing of the kind.** At ~40 games these rates are noisy, and noise attenuates any correlation
toward zero. The tell was in the per-claim table: **r tracks the claim's denominator, not the
speed.**

| claim | opportunities per game | r |
|---|---|--:|
| `early_error.white` | every game has an opening | **+0.67** |
| `instant_move_error` | frequent | +0.58 |
| `opening_disadvantage` | every game | +0.54 |
| `allowed_motif.fork` | rare | **+0.02** |
| `missed_motif.capturingDefender` | rare | −0.02 |

So the question is not "is the correlation high" but **"is it lower than rapid's correlation with
itself at the same sample size?"** Rapid was therefore split into two disjoint 40-game windows and
correlated against itself, giving the ceiling that noise permits.

## Result — pool

| | |
|---|--:|
| blitz predicts rapid | median r **+0.21** |
| **rapid predicts itself** (the ceiling) | median r **+0.19** |
| **share of the ceiling blitz recovers** | **93 %** |
| gap between speeds | median **1.06×**, range 0.69–1.25× |
| how much that gap varies between players | spread 2.39× |
| **the same, rapid against itself** | spread **2.08×** — what noise alone produces |
| mean own rating, blitz | 1547 |
| mean own rating, rapid | 1628 |

**Blitz predicts a player's rapid behaviour as well as rapid itself does.** On the well-measured
claims it recovers 99 % of the ceiling (`early_error`), 85 % (`opening_disadvantage`), 75 %
(`instant_move_error`). The apparent per-player variation in the gap is 2.39× against a noise floor
of 2.08× — almost all of it is noise.

**Blitz is the same player, playing faster, making 6 % more mistakes.**

## What this changes about step 5

It gets **much cheaper and much simpler than the design assumed.** No second and third corpus, no
separate profiles, no separate diagnosis per speed:

> **Pool the evidence, stratify the baseline.** One corpus containing every speed, so opportunities
> per claim rise ~5× and the rarity gate that silences 43 % of players is hit directly. The peer
> comparison stays per-speed, because a 1.06× offset applied to a player whose speed mix differs from
> the population's would otherwise bias the rate.

E01's objection is honoured rather than overruled: the rates are still never blended across speeds
*for comparison*. What is pooled is the **evidence**, which was never what E01 was about.

## The automaticity hypothesis is dead

[[design.short-history-prioritisation]] proposed that the blitz-versus-rapid gap might separate
knowledge that is present-but-not-automatic from knowledge that is absent — the SKILL/FRAGILE
distinction the prober currently has to ask about, obtained free from games.

**It does not.** The gap's between-player variation is 2.39× against a 2.08× noise floor. There is
almost no per-player signal in it to diagnose with. Recorded as a refuted hypothesis rather than
quietly dropped: it was stated in the design note, it was cheap to test, and it failed.

## Honest limitations

- **Players are 81 rating points weaker in blitz** (1547 against 1628), so they face weaker
  opposition, which offsets some of the speed handicap. The true speed penalty at constant opposition
  is therefore **larger than 1.06×**, and the offset needs calibrating against opponent rating rather
  than taken from this figure.
- **A residual 2.39× against 2.08× is not zero.** Most of the gap variation is noise; "almost all" is
  not "all", and a better-powered study might find a small real per-player component.
- **Bullet was not tested.** Only blitz. The boundary between "same player, faster" and "a different
  game" is somewhere, and this locates it below rapid but not where.
- **~5× the games is ~5× the engine time**, which is the first genuine challenge to C1/D9 in a while
  and is not yet measured for a fresh player.
- **40 blitz games per player is itself a shallow stratum.** The ceiling being low (+0.19) is a
  statement about how noisy these rates are at 40 games — which is the same finding E16 and E17 keep
  producing from different directions.
