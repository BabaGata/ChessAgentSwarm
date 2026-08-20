---
id: cas-exp-e40
title: 'E40 — The ranking can be derived, and derived it agrees with the swarm 0 times in 6'
desc: 'Part 2 of Form A is blank for all twelve players while 270 move-level notes exist. Deriving the ranking from those notes costs the reviewer nothing — and shows their attention is on material while the swarm prioritises phase, process and position.'
updated: 1787875200000
created: 1787875200000
---

# E40 — Does the ranked top three need asking for, or can it be derived?

**Answers:** the reviewer's *"is it even needed to compare the top 3 instead of noticed error by
noticed error?"* · **Code:** `experiments/e40-derived-ranking/` · **Date:** 2026-08-19 ·
**Status:** done — **the instrument goes, the test stays, and it immediately earns its keep**

## The question, and the half of it that is right

The two tests measure different layers:

| | |
|---|---|
| **move by move** | **detection and naming** — did the swarm see this mistake, does it have a word for it. 270 annotated moves, matched windows, well powered ([[experiments.e31-move-level-agreement]]) |
| **top three** | **prioritisation** — of everything wrong with this player, did the swarm pick the right thing to work on. That is the arbiter, and nothing else tests it |

So the *question* is worth keeping. What was wrong is the **instrument**: asking a reviewer to
synthesise a ranking in their head from twenty games read over two and a half hours, then scoring
twelve binary outcomes against it.

The evidence that it was the wrong ask is blunt: **Part 2 of Form A is blank for all twelve players**
while 270 move-level notes exist. The reviewer voted with their pen.

**So derive it.** Aggregate each annotated mistake to a claim family, count, rank. A remembered
judgement becomes a measured one, it costs the reviewer nothing further, and it rests on 270
observations rather than 12.

## Result — 0 of 6, and the pattern is not noise

Six annotated players, swarm run on the **same twenty games** (E39's fix), same full-size reference:

| player | reviewer's derived three | swarm's three | overlap |
|---|---|---|--:|
| bjagus | hangingPiece, hangingPawn, concedes_weakness | allows_square, advantage_error, early_error | 0 |
| cademan | hangingPawn, hangingPiece, fork | advantage_error, early_error, **fork** | 1 |
| Crossfire1983 | hangingPawn, hangingPiece, fork | allows_pressure, early_error, moved_into_attack | 0 |
| goydorak | hangingPawn, hangingPiece, allows_pressure | early_error, **hangingPiece**, pin | 1 |
| Hirsican | hangingPiece, hangingPawn, allows_pressure | fork, advantage_error, long_think_error | 0 |
| maikel5 | hangingPawn, allows_pressure, pin | endgame_error, discoveredAttack, capturingDefender | 0 |

| | |
|---|--:|
| swarm's top finding inside the reviewer's derived three | **0 / 6** |
| median overlap of the two top-threes | **0.0 / 3** |

**The reviewer's attention is on material.** `hangingPawn` or `hangingPiece` is first or second for
**five of six** players, and appears in every single derived three.

**The swarm's priorities are somewhere else entirely** — phase (`early_error`, `endgame_error`),
process (`long_think_error`, `advantage_error`), and position (`allows_square`, `allows_pressure`).

## Why, and it is the same finding for the third time

The two rankings answer different questions.

- The reviewer's derived ranking counts **absolute frequency**: what they saw go wrong most often.
- The swarm ranks by **peer-relative excess**: what this player does more than others at their level.

Everyone in this band drops material. So material loss, however frequent and however costly, rarely
clears a peer comparison — and the arbiter is built to rank on exactly the quantity that material
loss is *not* unusual on.

This project has now arrived at that wall three times from three directions:

- [[experiments.e25-shared-weaknesses]] — the band's most expensive shared weakness was advised to
  nobody, and the band-notes section was built to say it out loud.
- [[decisions.0010-three-priorities-and-the-cost-pool]] — a player's single most expensive pattern
  was measured, priced and discarded because it was not unusual, so a cost pool was added.
- **E40** — with both of those shipped, the reviewer's top concern still fails to reach the
  swarm's top three for six players out of six.

The cost pool was supposed to catch this and does not, because it only fills slots the peer-relative
ranking leaves empty — and with the full-size reference those slots are now mostly filled by claims
that *are* peer-unusual.

## The instrument change

**Part 2 of Form A is withdrawn as a reviewer task** and the ranking is derived from Part 1 instead.
The pre-registered threshold is untouched: the swarm's top finding must appear in the reviewer's
three for ≥ 7 of 12. What changes is where the reviewer's three comes from — their own notes rather
than their own memory — which makes it more evidence, not less.

## Honest limitations, and they are serious

- **A quarter of the notes could not be mapped** — 74 of 291, and for two players it is worse than
  half (`goydorak` 23/41, `maikel5` 10/20). The derived ranking for those two rests on a minority of
  what they wrote, and the vocabulary table doing the mapping is written by the agent after reading
  the notes (E31's stated weakest link). **A different mapping could move these results.**
- **Counting is not ranking.** A human weighs importance — frequency × severity × how fixable — and
  this derivation uses frequency alone. A cost-weighted variant is the obvious next version and is
  not run here.
- **Six players, not twelve**, and all six are the ones annotated first, which is not a random half.
- **0/6 is a floor, not an estimate.** With n=6 the interval is wide; what the result establishes is
  a *direction*, and the direction is consistent across every player.
- **This does not say the swarm is wrong.** Being unusual for your level and being what you most often
  get wrong are different things, and the swarm was built to report the first deliberately. What E40
  shows is that the two diverge almost completely at this band — which is a finding about the design,
  not a bug in it.
