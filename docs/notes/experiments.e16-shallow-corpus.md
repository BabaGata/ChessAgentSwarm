---
id: cas-exp-e16
title: 'E16 — Why the swarm is silent for 43% of players at 24 games'
desc: 'Not FOCUS_DISTINCT_GAMES, which state.md had been asserting from one section. The events are too rare and the interval too wide — 96% of the silence.'
updated: 1786492800000
created: 1786492800000
---

# E16 — Why the swarm is silent at 24 games

**Answers:** a direct question from the author · **Date:** 2026-08-06 · **Status:** done —
**it corrects a claim the vault had been repeating**

## Question

[[experiments.e12-corpus-depth]] measured *that* coverage falls to about half when a player brings 24
games instead of 150. It never measured **why**. [[state]] has been naming the reason —
`FOCUS_DISTINCT_GAMES = 5` — on the strength of S6's experience, generalised to the whole swarm
without a census.

There are five gates between a claim and a player, and they fail for different reasons:

| gate | opens with more games? |
|---|---|
| `WATCH_DISTINCT_GAMES = 3` — the pattern must occur in 3 separate games | yes |
| `FOCUS_DISTINCT_GAMES = 5` | yes |
| `FOCUS_GAMES_WITH_DATA = 20` | yes |
| `ci95[0] > baseline` — a Wilson bound, which widens as n falls | yes |
| `FOCUS_MARGIN = 1.25` — magnitude | **no, ever** |

The distinction decides what to do about it. A claim blocked by **magnitude** should stay unsaid
however many games arrive; a claim blocked by **evidence** is one the corpus is hiding.

## Method

The same 84 deep histories, truncated to each player's **most recent 24 games**, rebuilt against the
same peer reference. `assign_tier` is wrapped so every decision it makes is recorded with the reasons
the policy itself emits — so the census cannot drift from the code.

A controlled comparison rather than a real cohort: these are the same players, thinned, which
isolates corpus depth from everything else about who they are.

## Result — 43 % silent, and not for the recorded reason

**48 of 84 spoken to (57 %), 36 told nothing (43 %).**

Among the **silent** players, counting only claims blocked by exactly one gate — the ones a single
change would release:

| sole blocker | claims | |
|---|--:|---|
| **seen in fewer than 3 separate games** | **83** | the event is simply too rare in 24 games |
| **interval does not exclude the baseline** | **69** | too few opportunities to be sure |
| `FOCUS_DISTINCT_GAMES = 5` | **5** | |
| did not replicate across a split | 1 | |

**`FOCUS_DISTINCT_GAMES` accounts for 3 % of it.** The two rarity-and-precision gates account for
**96 %**. Both are pure sample-size effects, and neither is the threshold the vault named.

## Result — the magnitude floor never acts alone

`FOCUS_MARGIN` fired 327 times across all players and was the **sole** blocker **zero** times. Every
claim too small to be worth saying was also statistically shaky. D12's floor is therefore not
silencing anyone it would not have been silent about anyway — which is what it was chosen to do, now
confirmed at a corpus depth it was never tested against.

## Result — nobody is silent for lack of faults

| among the 36 silent players | |
|---|--:|
| had a real pattern held back **only** by thin evidence | **36 / 36** |
| had a real pattern that is genuinely too small to say | 36 / 36 |
| had **nothing** to say even with more games | **0 / 36** |
| median recoverable claims per silent player | **7** |

Every silent player has candidate weaknesses the swarm can see and cannot confirm — a median of seven
each. The silence is a measurement limit, not a verdict that the player is fine. That is the right
behaviour and a poor experience, and it is the gap between the two that P2 is about.

## A class of silence this nearly missed

Sections that decline **wholesale** return before the confidence policy is consulted, so they are
invisible to a census built on `assign_tier` alone. Counted separately: **1 of 84**, S2 for a single
player whose games carried no clocks. The concern that S3 would abandon endgames wholesale at 24
games did not materialise — that was the gate fixed earlier this cycle, and the fix holds.

## Consequences

1. **[[state]]'s "binding constraint is `FOCUS_DISTINCT_GAMES`" is wrong** and is corrected. Raising
   or lowering that threshold would move 3 % of the problem.
2. **The lever is events per corpus**, which means games — or claims that pool more evidence per
   game. Loosening thresholds is the option this rules *out*: the gates that bind are the two that
   exist to stop the swarm inventing patterns from three data points, and relaxing those buys
   coverage with exactly the credibility the project refuses to spend.
3. **D12's floor is confirmed harmless** at depth, which was an open calibration question.

## Honest limitations

- **Truncated histories are not new players.** A real 24-game user may be newer, more erratic, or
  playing a different pool; this isolates depth and nothing else.
- **43 % here against 47 % in E12** — different populations (84 thinned players against 38 genuinely
  shallow ones) and different measures (assertable findings against plan steps). Neither is wrong;
  they are not the same number.
- **No sweep.** This says *why* 24 games is too few, not *how many* would be enough. The obvious next
  measurement is the same census at 40, 60 and 100 games, which the warm cache makes cheap.
