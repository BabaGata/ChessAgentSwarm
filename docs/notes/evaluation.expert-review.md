---
id: cas-eval-expert-review
title: 'Expert review — protocol, pre-registered'
desc: 'How a strong player is asked to judge the reports, what counts as a pass, and what is decided before any answer is seen.'
updated: 1786752000000
created: 1786752000000
---

# Expert review

**Status:** protocol fixed, **not yet run** · **Pre-registered:** 2026-08-10, before any reviewer was
approached

Success criteria 2 and 3 in [[vision]] — *the swarm's weaknesses match those an independent strong
reviewer identifies*, and *the learning path is judged reasonable, ordered and specific* — are the
only ones that cannot be measured without a person. Everything else now has a number
([[experiments.e26-depth-robustness]], [[experiments.e27-held-out]]).

**This note is written before the reviewer is chosen, and the thresholds below are fixed now.**
Deciding what counts as a pass after reading the answers is how a review becomes a testimonial, and
this project has already caught itself grading on data it fitted to twice (L-018, L-036).

## What is being asked

Not *"is this good?"* — an expert asked that will be polite. Three specific things:

| | question | criterion |
|---|---|---|
| **A** | Given a player's games, what would **you** say their main weakness is? | 2 |
| **B** | Here is what the system said. Is it **right**, and is it what you would have prioritised? | 2 |
| **C** | Is the advice **specific, ordered and actionable**, or generic? | 3 |

**A comes before B**, always, and B is not shown until A is answered. Reversing them turns the review
into agreement with a suggestion, and the difference between *"would you have said this?"* and
*"do you agree with this?"* is the entire measurement.

## Sample

**12 players**, drawn from the **held-out 30** (E27) — players no constant in the system was chosen
on. Stratified so the review cannot be run on the flattering cases:

| | n | why |
|---|--:|---|
| the swarm gave **2 priorities** | 5 | the normal case |
| the swarm gave **1 priority** | 3 | thinner evidence |
| the swarm was **silent** | 2 | the reviewer sees what silence costs |
| **highest-confidence findings** | 1 | the best case |
| **weakest findings that still shipped** | 1 | the marginal case, deliberately included |

Selected by script, seeded, before the reviewer is contacted, and the selection recorded.

## What the reviewer gets

Per player, in this order, one at a time:

1. **The games.** A Lichess study or PGN, no annotations, no system output.
2. **Form A** — free text: main weakness, second weakness, what you would tell them to do.
3. **Only then**, the report the system produced.
4. **Form B/C** — the ratings below.

## The instrument

Each rated 1–5, with the anchors written out so two reviewers would mean the same thing:

| item | 1 | 3 | 5 |
|---|---|---|---|
| **correctness** — is the named weakness real? | contradicted by the games | present but minor | clearly a main weakness |
| **priority** — is it what you would work on first? | would not mention it | reasonable, not my first choice | exactly my first choice |
| **specificity** — could the player act on this? | generic advice | actionable with effort | concrete and immediately actionable |
| **evidence** — do the cited positions support the claim? | they do not show it | mixed | they show it plainly |
| **harm** — could following this make them worse? | yes, plainly | neutral | actively helpful |

Plus, unrated and most valuable: **"what did the system miss?"**

## Pre-registered thresholds

Fixed now. The review **passes**, for a thesis claiming a working diagnostic system, if:

| | threshold |
|---|---|
| **agreement (criterion 2)** | the system's top finding appears in the reviewer's free-text A answer for **≥ 60 %** of players (7 of 12) |
| **correctness** | median ≥ **4**, and **no player** scores 1 |
| **priority** | median ≥ **3** |
| **specificity (criterion 3)** | median ≥ **3** |
| **harm** | **zero** players scored 1 — a single "this would make them worse" is a stop, not an average |

**Below 40 % agreement the honest conclusion is that the diagnosis does not match expert judgement**,
and the thesis reports that as the result rather than as a limitation. That sentence is written now,
while it costs nothing to write.

## What the review cannot settle

- **One reviewer is one opinion.** Two would allow inter-rater agreement and there is no budget for
  it; with one, the free-text A answers matter more than the ratings, because they are less anchored.
- **A strong player is not a coach.** Playing strength and teaching judgement are different, and the
  reviewer's background should be recorded.
- **Nothing here tests whether the advice works** — criterion 4 needs a coached cohort and months,
  and is out of scope for this thesis, stated as such.
- **The reviewer sees a report, not the system.** Anything they praise or criticise about *phrasing*
  is a fact about the explainer, not about the diagnosis underneath it.

## Preparing it

`experiments/e28-expert-review/prepare.py` selects the sample, writes the reviewer's pack (games,
Form A, then the report and Form B/C), and records the selection so the sample cannot be quietly
changed afterwards.
