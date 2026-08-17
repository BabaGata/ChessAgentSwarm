---
id: cas-exp-e32
title: 'E32 — The free-pawn detector screens well and did not fix what it was built for'
desc: 'A new hangingPawn motif fires 2,482 times across 12 players and discriminates as well as the claims already shipping. It named one extra reviewer note out of 45, because the naming gap was never the vocabulary.'
updated: 1787184000000
created: 1787184000000
---

# E32 — Does the free-pawn detector earn its place?

**Answers:** the reviewer's instruction to add a detector for pawn material loss ·
**Date:** 2026-08-16 · **Status:** done — **ships on the screen, fails its own motivation**

## Why it was built

[[experiments.e31-move-level-agreement]] found **45 of 45 reviewer notes mentioning a pawn were
unnameable** across three players. `hangingPiece` excludes anything worth less than a knight, so the
engine flagged the error and the vocabulary had no word for it.

Built as a **sibling motif, not a widening**. [[experiments.e30-hanging-definition]] measured what
widening `hangingPiece` does: everyone drops free pawns, the population rate more than doubles, and
one player's deviation fell from 1.40× to 1.11×. Folding pawns in buries the piece claim to rescue
the pawn one, and a report saying *"you hang pieces"* about a pawn is wrong. Kept separate, both
claims stay true and each meets its own population.

## The screen — it passes

Twelve expert-review players, depth 15. The screen is E09/E11's: **p90 ÷ median**, because a claim
every player scores alike cannot select anyone's priority however common it is (L-024).

| claim | players | instances | opportunities | pooled | median | p90 | **spread** |
|---|--:|--:|--:|--:|--:|--:|--:|
| **`missed_motif.hangingPawn`** | 12 | 69 | 685 | 10.1 % | 9.4 % | 14.4 % | **1.53×** |
| **`allowed_motif.hangingPawn`** | 12 | 156 | 1,797 | 8.7 % | 8.0 % | 11.1 % | **1.38×** |
| `missed_motif.hangingPiece` | 12 | 47 | 935 | 5.0 % | 3.7 % | 9.5 % | 2.58× |
| `allowed_motif.hangingPiece` | 12 | 150 | 1,797 | 8.3 % | 7.7 % | 12.0 % | 1.56× |
| `missed_motif.fork` | 12 | 87 | 393 | 22.1 % | 23.0 % | 32.3 % | 1.40× |
| `allowed_motif.fork` | 12 | 175 | 1,797 | 9.7 % | 9.1 % | 13.6 % | 1.50× |

Both new claims spread inside the range of everything already shipping. And a number that validates
the reviewer's attention directly: **players miss free pawns at 10.1 % against free pieces at
5.0 %** — twice as often.

## The payoff — it did not arrive

Re-running E31 with the detector in place:

| player | pawn notes | unnamed before | unnamed after |
|---|--:|--:|--:|
| `bjagus` | 9 | 9 | **9** |
| `cademan` | 23 | 23 | **22** |
| `Crossfire1983` | 13 | 13 | **13** |

**One note out of forty-five.** The detector works — `cademan` game 16 move 10, *"Not taking a pawn
back"*, is now `hangingPawn` — and the gap it was built to close was never the vocabulary. Printing
the loss at each noted move shows two other causes, in roughly equal measure.

### 1. Half the notes are below the label threshold — 24 of 45

`INACCURACY_WP = 10.0`, and no label means **no motif detector ever runs on that move**.

| player | median loss at pawn notes | below threshold |
|---|--:|--:|
| `Crossfire1983` | **7.5 wp** | 9 / 13 |
| `bjagus` | 12.5 wp | 4 / 9 |
| `cademan` | 15.8 wp | 11 / 23 |

`Crossfire1983` is the clean case: the reviewer's median noticed mistake costs 8.9 wp, so **most of
what they wrote down is invisible to the swarm by construction**, and its detection figure (42 %) is
the lowest of the three for exactly that reason. This is the threshold finding from E31 confirmed
with the whole distribution rather than four examples.

### 2. The rest are named by **mechanism** where the reviewer named the **outcome**

Above the threshold the motif often fires and disagrees:

```
cademan  game 1  move 5   "Loosing pawn"            19.2 wp   swarm: pin
cademan  game 9  move 20  "Missing hanging pawn"    30.8 wp   swarm: pin
Crossfire game 7 move 38  "Missing a pawn loosing"  22.9 wp   swarm: fork
cademan  game 5  move 24  "Loosing a pawn"          37.5 wp   swarm: error only
```

Neither side is wrong. The reviewer records **what was lost**; the swarm records **what won it**. A
pawn dropped to a pin is a pin to the system and a lost pawn to a human, and no amount of motif
vocabulary reconciles those — they are answers to different questions.

## Consequence

**The detector ships.** It fires 2,482 times across twelve players, discriminates as well as the
claims already in the report, and gives the swarm a true sentence it previously could not say. Its
value is independent of the reviewer-agreement figure it failed to move.

**Its motivation is refuted, and recorded as such.** "Add a detector for pawn material loss" was the
right instinct aimed at the wrong layer. Closing the pawn-naming gap needs one of:

- a **lower error threshold**, which floods the evidence base for every claim and would need its own
  screen — the honest open question;
- a claim measured in **material** rather than in win probability and mechanism, which is a different
  kind of detector from anything the swarm currently has.

Neither is done here, and neither should be done on one negative result.

## Honest limitations

- **Twelve players, one band, one depth.** The spread figures are indicative.
- **The peer reference does not yet contain `hangingPawn` cells**, so until it is rebuilt these
  claims compare against the player's own baseline only, which L-012 says overstates by however much
  the behaviour is universal — and dropping pawns is very universal.
- **`allowed_motif.hangingPawn` at 1.38× is the narrowest spread of the six**, and only just inside
  the shipping range. Worth re-screening on a wider corpus before it is trusted to select a priority.
- **The naming comparison rests on a phrase table written after reading the notes**, which is E31's
  stated weakest link and applies unchanged here.
