---
id: cas-exp-e62
title: 'E62 — Reading fifteen positions found two defects that 850 measured instances did not'
desc: 'The pawn claim discriminated well and was misnamed for 40 % of what it fired on: the engine wanted another pawn move, not development. A second defect surfaced in the first sampled position — a bishop already on b4 counted as "developing". Fixing both made every claim more independent, and plans went 2/12 to 3/12.'
updated: 1788912000000
created: 1788912000000
---

# E62 — What the counts could not see

**Answers:** the author's *"check pawn claims"* · **Code:**
`chesscoach/opening_development.py`, `experiments/e58-opening-development/pawn_sample.py` ·
**Date:** 2026-08-30 · **Status:** two defects found and fixed; **every metric improved**

## The claim looked finished

E61 shipped `pawn_error` on good numbers: 24 % pooled rate, 18 of 71 rapid players clearing the
1.25× margin, r = 0.69 with the general error rate, one plan slot taken. Nothing in those figures was
wrong and nothing in them was enough.

The first thing the sample printed was not a position. It was this:

| what the engine wanted instead | share |
|---|--:|
| develops a minor | 45 % |
| **another pawn move** | **40 %** |
| something else | 11 % |
| castling | 4 % |

**Two-fifths of the instances were "you pushed the wrong pawn", filed under "you pushed a pawn
instead of developing".** Real errors, correctly counted, attributed to the wrong cause — and a plan
built on them sends the player to fix something that was not the problem.

The same check on the other two claims found the same fault, and the castling claim worst of all:

| claim | engine wanted development or castling | engine wanted another pawn move |
|---|--:|--:|
| `pawn_error` | 49 % | 40 % |
| `repeat_move` | 50 % | 28 % |
| `late_castling` cost | 53 % | 31 % |

The engine wanted **castling** on only **26 %** of the moves the castling claim was charging.

## The fix, and why it is not just a rename

Charge a habit only where the engine's own preference was **development or castling**. That is the
*"instead of"* condition the author's wording carried all along, applied to the engine's opinion
rather than only to the state of the board.

Deliberately broader than *"the engine wanted exactly this"*: a plan to castle is a slow preference
and the engine rarely insists on it at one specific ply.

## Then the first sampled position found a second defect

Position 1: Black plays `5...b5`, and the engine wanted `Bxc3` — which my check classified as
*"develops a minor"* because a bishop moved. **The bishop was already on b4.** Moving a minor is not
developing one, and the claim would have said *"you should have developed"* about a capture.

Fixed by requiring the minor to move **from its home square**. Found by reading the first position
after the counts had already been believed twice.

## Every metric improved

Median cost falls sharply — the claims are charged for far less — but everything that matters gets
better:

| habit | cost, loose → strict | **r with general error rate** |
|---|--:|--:|
| repeat instead of developing | 19.9 → **3.2** | 0.64 → **0.54** |
| pawn instead of developing | 11.4 → **2.5** | 0.65 → **0.36** |
| declined an available castle | 9.3 → **2.8** | 0.44 → **0.35** |
| all three | — | 0.73 → **0.52** |

And `pawn_error` as a rate improved most of all:

| | loose | strict |
|---|--:|--:|
| spread across the band (p10 → p90) | 12 → 36 % | **8 → 50 %** |
| spread | 24 pp | **42 pp** |
| r with general error rate | 0.69 | **0.31** |

**The claims became smaller and sharper at the same time.** A cost that shrinks by 80 % while the
correlation with general error falls from 0.69 to 0.31 is not a weaker measurement — it is the same
measurement with the borrowed strength taken out of it.

## And they reach more plans, not fewer

| | loose | strict |
|---|--:|--:|
| development claims in a plan | 2 / 12 | **3 / 12** |

Counter-intuitive until you remember the arbiter ranks on **excess over peers**, not raw cost. Peers'
costs shrank too, and what survived was the part that actually distinguishes one player from another.

One of the three arrives through the cost pool rather than by assertion — a sub-threshold development
claim filling a slot on price, which is exactly the mechanism E61's pricing unlocked.

## Consequence

- **All four development claims are strictly attributed.** Their names now match what they fire on.
- **The sample is regenerated and markable** — `results/pawn-sample.txt`, 98 instances, 15 sampled,
  every one with development or castling as the engine's own preference. What is left is the chess
  judgement the counts cannot supply: *was developing really better here, or is the engine's
  preference thin?*
- **The other three claims should get the same reading.** This one was checked because the author
  asked; nothing suggests the others are cleaner, and the castling claim's 26 % says the opposite.

## The lesson, stated plainly

**850 instances, four screens and a peer reference did not reveal either defect. Fifteen positions
did — and the second one surfaced in the very first position read.**

Every screen was measuring whether the claim *discriminates*. None could measure whether it
discriminates *for the reason its name gives*, because that comparison needs a chess judgement about
what the alternative move was. This is the same shape as L-046's six instances and the misnamed fork:
**a number that is correct and an interpretation that is wrong look identical from inside the
numbers.**

## Honest limitations

- **The engine's preference is not a chess judgement either.** Depth 15 in an opening often has
  several near-equal moves, and "the engine wanted a knight developed" may be a coin-flip between
  three reasonable plans. That is precisely what the 15 marked positions are for, and they are
  unmarked.
- **The strict costs are small** — 2.5 to 3.2 wp/game against 23 for `allowed_motif.hangingPawn`.
  They compete on excess rather than size, and that margin has not been stress-tested.
- **3 of 12 is three players.**
