---
id: cas-exp-e31
title: 'E31 — The swarm sees 80 % of what a reviewer sees and can name 10 % of it'
desc: 'Per-game annotation instead of a ranked top three. Detection is good, naming is the weak layer, every pawn note is unnameable, and the reviewer works two win-probability points finer than the error labels.'
updated: 1788350400000
created: 1787097600000
---

# E31 — Move-level agreement, from per-game annotation

> **Corrected 2026-09-02 by [[experiments.e82-move-number-rerun]].** The join between the reviewer's
> noted move numbers and the swarm's observations used `ply // 2 + 1`, which puts **every Black move
> one too high** — the formula `phrasing.move_number` was fixed for and this script kept its own copy
> of. **The headline "detection 80 %, naming 10 %" was `bjagus` alone and is now 100 % and 60 %.**
> Across all six players with notes it is **76 % detection and 37 % naming**, against 76 % and 35 %
> before — so the aggregate barely moves while the per-player numbers move a great deal, in both
> directions. Some of the old detections were coincidences of the off-by-one landing on a
> neighbouring ply.

**Answers:** does the swarm *see* what a reviewer sees, separately from whether it *says* it ·
**Date:** 2026-08-15 · **Status:** done — **detection 80 %, naming 10 %**

## Why the instrument changed

Twenty games into `bjagus`, the reviewer stopped filling in the ranked top three and wrote down every
mistake they noticed, game by game, adding move numbers from game 8 onward. Their reason is the
result:

> "Comparing all noticed mistakes by the game I think should work better to get the overview of the
> system functioning while combining top 3 is just prioritization calculation."

That is exactly right, and it separates two things the pre-registered instrument confounds:

| | |
|---|---|
| **detection** | did the swarm see this mistake at all? |
| **prioritisation** | did it choose to tell the player about it? |

A top-three comparison can only measure the second, and it fails **silently** when the first is
fine — which is what happened on `bernes`, where the pattern was detected, priced, and discarded by
the ranking ([[decisions.0010-three-priorities-and-the-cost-pool]]).

It also produces far more evidence per hour: **36 notes across 18 games, 20 of them checkable against
a specific ply**, against 3 data points from a ranked list.

## Result — the analysis core is good and the vocabulary is not

20 notes carrying a move number, checked against the swarm's own labels within ±1 move.

| | | |
|---|--:|---|
| the swarm flagged that same move | **16 / 20 — 80 %** | **detection** |
| …and named the same pattern | **2 / 20 — 10 %** | **naming** |
| …but had no name for it | 14 / 20 — 70 % | |
| the swarm saw nothing there | 4 / 20 — 20 % | |

**The first run of this scored it as 25 % agreement and that number was wrong.** It collapsed "saw
the mistake, could not name it" into "missed", which is the difference between a broken analysis core
and a thin vocabulary. They need opposite fixes and only one of them is a real problem.

## Correction, 2026-08-16 — every naming figure in this note was ~3× too low

`compare.py` built its motif index from the player's **own best move only**, never from the
opponent's best reply — so the entire `allowed_motif` direction was invisible to it, and every note
of the form *"loosing a pawn"* scored unnamed by construction. A comment in the code claimed both
directions were included; the code never did.

| player | naming as published | naming corrected |
|---|--:|--:|
| `bjagus` | 10 % | **30 %** |
| `cademan` | 8 % | **37 %** |
| `Crossfire1983` | 0 % | **8 %** |

Detection figures are unaffected — they depend only on whether the move carried a label.
[[experiments.e32-hanging-pawn-screen]] and [[experiments.e33-error-threshold]] both inherited the
bad number and are corrected in place. The lesson is L-041.

## Three players, 2026-08-16 — detection varies, naming does not

| player | notes with a move | detection | naming | pawn notes unnamed |
|---|--:|--:|--:|--:|
| `bjagus` (20 games) | 20 | **80 %** | 10 % | 9 / 9 |
| `cademan` (20 games) | 60 | **57 %** | 8 % | 23 / 23 |
| `Crossfire1983` (10 games) | 26 | **42 %** | 0 % | 13 / 13 |

**Naming is flat and low everywhere: 5 of 106 move-level notes.** Detection swings widely, and the
swing tracks how much of the reviewer's attention is on **pawn-sized material** — `Crossfire1983`'s
notes are half pawn-related and its detection is lowest. Both barriers are the same class of
observation hitting two different walls: `HANGING_MIN_VALUE = 3` denies it a *name*, and
`INACCURACY_WP = 10.0` often denies it a *label* as well, because dropping one pawn in a balanced
middlegame is frequently worth less than ten points of win probability.

**45 of 45 pawn notes across three players are unnameable.** That is no longer a curiosity of one
player's games.

The reviewer's own vocabulary also turned out to be **more precise than the first mapping allowed**.
They consistently distinguish *"missing a piece winning motif"* (their own chance, not taken) from
*"missing a piece loosing threat"* (a threat against them, not seen) — which is exactly the
`missed_motif` / `allowed_motif` split. The first version of `compare.py` collapsed both and left 44
notes unmapped; the table now honours the distinction.

## Three specific findings

### Every pawn note is unnameable — 9 of 9

`HANGING_MIN_VALUE = 3` excludes free pawns from the hanging-piece motif.
[[experiments.e30-hanging-definition]] tested widening it and found the change makes claims *less*
peer-unusual, so it was refused. E31 comes at the same constant from the other side: the reviewer
wrote "loosing pawn" or equivalent **nine times**, and the swarm has no name for a single one of them
— while flagging the error underneath most of them.

The two results are not in conflict, and together they say something neither says alone: **the pawn
exclusion is right for ranking and wrong for naming.** E30 is about which claims should compete for a
priority slot; E31 is about whether the report can describe what happened. A motif is doing both jobs
and can only be tuned for one.

### The reviewer works about twice as fine as the error labels

The four notes where the swarm "saw nothing" are not blind spots. Every one is a **sub-threshold
loss**:

| note | loss at that move |
|---|--:|
| game 11, move 26 | **9.3 wp** |
| game 9, move 17 | 1.4 wp (and 7.2 wp at move 18) |
| game 12, move 11 | 0.0 wp (5.7 wp at move 12) |
| game 12, move 14 | 0.0 wp (4.5 wp at move 15) |

`INACCURACY_WP = 10.0`, so a move costing 9.3 points of win probability carries no label at all. The
reviewer is reliably noticing mistakes in the **4–10 wp band**, which sits entirely below where the
swarm begins to call anything an error. Those losses are computed and then discarded.

Nothing here says the threshold is wrong — labelling every 5 wp move would flood the evidence — but
it does mean the two are not measuring the same thing, and any future agreement figure has to be
read with that offset in mind.

### Instant moves: 4 of 4 confirmed, and the counts are extreme

The reviewer flagged "instant moves" as a game-level habit four times. The swarm counted **16–20
moves under two seconds in each of those games**. Perfect agreement, and the only category where a
game-level note was checkable at all.

## What it says about the instrument

- **Move numbers are the whole difference.** The 20 notes carrying one produced 20 comparisons; the
  10 without produced none. Form A now asks for them explicitly and shows the shape.
- **Per-game annotation is now Part 1 of Form A**, with the ranked three demoted to Part 2 and filled
  in *from* the notes rather than instead of them.
- **The binding cost is the reviewer's time: 2 h 30 for 20 games.** Twelve players at full depth is
  roughly 37 hours and is not going to happen. Twenty games each for three or four players is about
  ten hours and yields 60–80 checkable move-level notes — an order of magnitude more evidence than
  the pre-registered design, for a quarter of the effort. Recorded here; the protocol change is not
  made unilaterally.

## Honest limitations

- **One player, one reviewer, 20 games.** Everything here is a single case.
- **The mapping from the reviewer's words to claim keys is mine**, written after seeing their notes.
  It is in `compare.py` as an explicit table so it can be argued with, but it is not blind.
- **±1 move tolerance** is generous, and with errors as common as they are in this band some matches
  will be coincidental. The 80 % is an upper bound on detection.
- **Two notes describe things no detector exists for** — "giving up good bishop for a bad knight",
  "giving up good piece for a bad one" — piece-quality judgements the swarm has no representation of
  at all. Those are not failures of naming but genuine absences.
- **The `concedes_weakness` claims could not be checked properly**: structure concessions are not
  necessarily errors, so they do not appear in the error-keyed index this comparison uses. Two of the
  four "saw nothing" verdicts are isolated-pawn notes and may be artefacts of that.
