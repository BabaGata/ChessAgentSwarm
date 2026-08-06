---
id: cas-exp-e17
title: 'E17 — Ranking stability at 20 games, and the stability/specificity trade'
desc: 'Deviation ranking is barely above chance (6% vs 4%). Severity is stable (65%) because it tells 70% of players the same thing. Neither signal is acceptable alone.'
updated: 1786492800000
created: 1786492800000
---

# E17 — Ranking stability at 20 games

**Answers:** the author's proposal to score rather than gate · **Date:** 2026-08-06 ·
**Status:** done — **it reframes the question and corrects E15**

## Question

The proposal: set the minimum history to **20 games**, and rank mistakes by an **importance score**
— occurrence rate, severity, recency, game length — instead of requiring claims to clear confidence
criteria. The stated motivation is that a re-evaluation after coaching can only ever bring ~20 new
games, so a system built on evidence thresholds will go quiet exactly when it is asked to check its
own work.

Underneath the choice of weights is a prior question that decides everything: **is a ranking from 20
games stable at all?** A score is a point estimate, and ranking by a point estimate from a small
sample selects for whichever claim is noisiest — R-15 acting at *selection* time rather than at
re-measurement time.

## Method

Each of the 84 deep histories split into two **disjoint, adjacent** windows of equal size — the most
recent *n* games, and the *n* before them. Every candidate claim forced past the gates, since
removing them is what is proposed. Each window's claims ranked three ways, and the two rankings
compared:

| score | |
|---|---|
| `deviation` | rate ÷ peer rate — what the arbiter ranked on before E15 |
| `severity` | win probability given away per game — what E15 added |
| `deviation × severity` | the proposal's core |

Against a chance baseline: one claim drawn at random from the same pool (24–26 claims, so ~4 %).

## Result — the two signals fail in opposite directions

| window | score | players | top-1 agree | top-2 agree | chance |
|--:|---|--:|--:|--:|--:|
| 20 | deviation | 84 | **6 %** | 8 % | 4 % |
| 20 | severity | 84 | **65 %** | 57 % | 4 % |
| 20 | deviation × severity | 84 | 21 % | 37 % | 4 % |
| 60 | deviation | 69 | **10 %** | 17 % | 3 % |
| 60 | severity | 69 | **74 %** | 74 % | 4 % |
| 60 | deviation × severity | 69 | 54 % | 62 % | 4 % |

**Deviation ranking is barely distinguishable from drawing a claim at random** — 6 % against 4 % at
20 games, and only 10 % against 3 % at 60. This is not a tie-breaking artifact: **100 % of a
player's claims hold a distinct deviation score**, so the ordering is real and it is real noise.

Then the catch:

| score at 20 games | distinct winners over 84 players | most common top claim |
|---|--:|--:|
| deviation | **21** | 12 % |
| severity | **6** | **70 %** — `advantage_error.clear` |
| deviation × severity | 18 | 40 % |

**Severity is stable because it is nearly a constant.** Seventy per cent of players get the same top
claim, and only six claims ever win. That is anti-pattern D2 in [[evaluation]] — *a claim made to
most players is a description, not a diagnosis* — and R-14, which has already materialised twice in
this project.

So:

- **deviation** — specific and unreliable: it tells each player something different, and it is the
  wrong different thing.
- **severity** — reliable and generic: it is right about what costs the most, and it is nearly the
  same answer for everyone.
- **their product** — inherits some of each: 21 % stable, 40 % concentration.

Neither is acceptable alone, and multiplying them is not the fix.

## What this corrects about E15

[[experiments.e15-expected-gain]], built earlier the same day, ranks by **raw** cost. E17 says that
ranking is stable and **too generic**: `advantage_error` went from 1 advised slot to 9 there, which
was recorded as the intended effect, and E17 shows the effect does not stop where it was assumed to.
D5's mechanism is right and its **quantity is not peer-relative**, which is the same mistake L-012
recorded for rates and which the peer reference was built to fix.

The correction is stated rather than built: **severity must be measured against peers too** — not
*"this costs you 25 points a game"* but *"this costs you 25 where players at your level lose 9"*.
The peer reference carries per-claim rates and **not** per-claim costs, so this needs the reference
rebuilt with cost aggregated. Modest work, not free.

## What this supports in the proposal

**Scoring degrades gracefully where gating cliffs.** Severity ranking keeps 88 % of its 60-game
stability at 20 games (65 % against 74 %), while gating drops from advising 83 % of players to 57 %
over the same change in depth ([[experiments.e16-shallow-corpus]]). The author's core intuition —
that a threshold system fails abruptly at short histories while a score bends — is **measured and
correct**.

**And occurrence rate really is the weak ingredient**, more so than the proposal assumed: it is not
that rate should be *supplemented* by severity, it is that rate alone ranks at chance.

## Honest limitations

- **Stability is not correctness.** Two windows agreeing says the measurement is reproducible, not
  that it identifies what would most help the player. Nothing here establishes that.
- **Adjacent windows are not independent.** Games 130–150 and 110–130 come from the same period of a
  player's life; a genuinely improving player would make the two windows differ for real reasons, so
  these agreement figures are, if anything, **optimistic**.
- **Recency and game length are not tested here**, only rate and severity. See
  [[design.short-history-prioritisation]] for what the corpus says about whether those two have
  anything to act on.
- **The gates were forced open**, so these rankings include claims the live system would never
  assert. That is the proposal's world, not the current one.
