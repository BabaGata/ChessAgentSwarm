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

## Amendment, 2026-08-14 — who the reviewer is

**Recorded before any answer was collected**, which is the only condition under which amending a
pre-registered protocol is legitimate.

The original design assumed a titled or otherwise clearly stronger reviewer. **No such reviewer is
available**; the author is rated ~1880 on Lichess and judged themselves too weak for the role.

**Searching for a substitute failed, and the reason is structural rather than bad luck.** Published
expert analysis of amateur play — the Lichess game-analysis forum, and the canonical books of the
genre — analyses **one game deeply** or gives **band-level advice**. This swarm diagnoses **one
player across ~60 games**. Without the same corpus there is nothing to compare, and no public source
was found that pairs an identifiable, fetchable account with a strong player's diagnosis of that
player's *recurring* weakness. The Lichess forum was checked directly: threads are mostly single
games their authors are proud of, replies are few, and no titled responders were visible.

**The review proceeds with an ~1880 reviewer, and the thesis states it.** The reasoning, so an
examiner can weigh it rather than take it on trust:

- **The task is not to out-calculate the system.** Form A asks what a player *keeps* getting wrong.
  Diagnosing recurring weakness at 1400–1800 — hangs pieces, moves instantly, collapses after move 15
  — is pattern recognition, and 1880 against 1400–1800 is roughly a normal coach-to-student gap.
- **The expertise literature supports that gap being meaningful** and the skill being pattern-based
  rather than search-based: [[domain.expertise-research]] § 1, where a player improved 1600 → 2300
  with no significant increase in depth of search.
- **Criterion 3 needs no superiority at all.** Whether advice is specific, ordered and actionable is
  a judgement any competent player can make.

**What this costs, stated plainly:** a stronger reviewer might disagree with both the swarm *and* the
reviewer, and this design cannot detect that. The agreement figure is therefore *"agreement with an
1880-rated player"*, not *"agreement with expert judgement"*, and every threshold below should be
read with that substitution made.

**Preferred if it becomes possible:** three or four reviewers at 1800–2000 rather than one. That
yields **inter-rater agreement**, which a single titled reviewer could never provide, and which would
tell us whether "the main weakness" is even a well-defined question at this level — a more useful
thing to learn than one strong opinion.

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

## Results so far — 1 of 12

### `bernes` — **disagreement**, and it changed the system

Recorded 2026-08-15, before the remaining eleven, because the finding was structural rather than a
score.

| | reviewer's Form A | the report |
|---|---|---|
| 1st | undefended pieces (losing their own) | missed forks |
| 2nd | missing hanging pieces (not taking the opponent's) | — |
| 3rd | *(forks, per the reviewer's later note)* | — |
| strength | 1650 | *(not shown — no estimate reached the report)* |

**Agreement on the top finding: no.** By the pre-registered rule this is one of twelve counted
against the ≥ 7/12 threshold, and it stays counted that way whatever follows.

The two halves failed for entirely different reasons, and separating them is the whole value:

1. **The reviewer's #1 was measured and gated out.** `allowed_motif.hangingPiece` at 10.7 % of
   errors, 10 of 53 games, **7.3 wp/game — the most expensive pattern in the player's games**, and
   1.29× the population. The interval did not clear the peer rate, so it stopped at `watch` and was
   discarded. Addressed by [[decisions.0010-three-priorities-and-the-cost-pool]]: it now appears as a
   cost-ranked priority, labelled as ordinary for the level. It is ranked **second**, behind the
   peer-relative finding — so the disagreement about *order* stands even after the fix.
2. **The reviewer's #2 the system contradicts.** `missed_motif.hangingPiece` measured **3 misses in
   77 chances — 3.9 %, against 6.9 % for peers**: this player converts free pieces slightly *better*
   than their level. Not a gating problem and not fixed. Either the reviewer is counting something
   the detector excludes — captures worth less than a minor piece, positions where taking is not the
   engine's first choice, or recaptures that leave the piece attacked — or the impression is wrong.
   **Unresolved, and it is the more interesting of the two.**

The honest reading of a single case: a strong club player leads with what is *expensive and
frequent*, and the system led with what is *unusual*. Those are different questions, and until this
review only one of them could reach the page.

### The sample's "silent" stratum no longer exists

[[decisions.0010-three-priorities-and-the-cost-pool]] takes silence from 2/12 to **0/12** across this
exact sample. The stratum was included precisely because it flatters the system least — *"the players
it had nothing to say about"* — and it now describes nobody. Their reports lead with **WHAT COSTS YOU
MOST** and state plainly that nothing about them is unusual.

This is a change to the instrument after the sample was drawn, and it is recorded as such. Form B/C's
last question — *"if the report was empty: was there something worth telling this player?"* — is now
unanswerable for those two, and the more useful question about them has become whether the
cost-ranked items are worth telling *anyone*.

### A caution about the remaining eleven

The reviewer has now seen this analysis, so their Form A answers for the other players are no longer
naive in the way `bernes`'s were. That is a real contamination of the instrument and it is recorded
rather than managed away. It argues for weighting `bernes` heavily and treating the rest as
partially anchored.

## What the review cannot settle

- **The reviewer is ~1880, not titled** (see the amendment above). This is the largest limitation and
  it is not hidden: the result is agreement with a stronger club player, not with expert judgement.
- **One reviewer is one opinion.** Two would allow inter-rater agreement and there is no budget for
  it; with one, the free-text A answers matter more than the ratings, because they are less anchored.
- **The reviewer is the system's author.** Unavoidable here, and the sharpest conflict of interest in
  the whole evaluation — which is exactly why Form A is answered before the report is opened, why the
  sample was drawn and frozen by script, and why the thresholds were fixed in advance. Those three
  precautions are doing more work than usual precisely because of this.
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
