---
id: cas-exp-e73
title: 'E73 — The opening-score claim is built, correct, and does not survive its own screen'
desc: 'The last of the six corrections. The threshold was calibrated, the rule was implemented and tested, and then the depth sweep found four of the five players it names flipping in and out. Held, not shipped, not deleted.'
updated: 1788206400000
created: 1788206400000
---

# E73 — You score worse in this opening than in your others

**Answers:** [[design.detectors-name-consequences]] § 1b, the last of the six corrections ·
**Code:** `experiments/e73-opening-scores/`, `chesscoach/opening_scores.py` ·
**Date:** 2026-08-31 · **Status:** **built and screened — do not ship**

## What was asked for

> *"Early error should be totally reformatted as opening error, meaning player knowing less number of
> an opening moves than peers and losing more often when playing some opening then another. Keep
> track that main openings of the players would be played much more often then other openings by the
> same player."*

1a — leaving theory early — was superseded by [[design.opening-development-signals]] and is built.
**1b is this**, and the last sentence is its whole difficulty.

## The repertoire, measured

12 players, up to 60 games each, openings grouped to the family:

- **median 17 openings per player**
- **median 2 games per opening**, mean 3.2
- **46 % of openings played exactly once**

The author's caveat is not a refinement, it is the dominant feature of the data. A single loss in a
one-game opening is a 0 % score, and without a floor those would fill every report.

## The floor: the right number, from the wrong method

The design note proposed **5** and said it should be settled by *"the distribution of per-opening
game counts"*. The distribution alone argues **against** 5 — it discards 47 % of games and leaves one
of twelve players with nothing comparable:

| floor | % games kept | players with ≥2 comparable openings |
|---|--:|--:|
| 3 | 71 % | 12 |
| 4 | 62 % | 12 |
| **5** | **53 %** | **11** |

What actually settles it is **which floor admits a finding the claim can defend**. At floor 3 the
rule fires on three extra separations and all three are **0 % over 3 games** — Wilson says they
separate, and they are precisely the tail noise the caveat excludes. At floor 5 the survivors are
**29 % over 19 games** and **17 % over 6**.

**So the proposed number was right and the stated method would not have found it.** The distribution
says what a floor *costs*; it cannot say what it *buys*.

## It fires, and it says something real

Over 60 games, floor 5, Wilson intervals disjoint:

| player | opening | score | rest |
|---|---|--:|--:|
| bernes | Caro-Kann Defense | **29 %** over 19 | 60 % over 39 |
| goydorak | Queen's Pawn Game | **17 %** over 6 | 59 % over 51 |

Both are the kind of thing a player can act on: a named opening, a score, and their own repertoire as
the yardstick.

## The note's own acceptance test: PARTIAL

> *"Testable: on the review twelve, [the replacement] must name a different set of players than the
> current `early_error` does. If it names the same people it has only been renamed."*

`early_error` names **7**. The replacement names **2**, and both are **already named by
`early_error`** — a strict subset, not a different set.

It is **not** a rename: what it says is different in kind, naming a choice rather than a
circumstance. But it reaches nobody new, so **`early_error` cannot be retired in its favour** —
5 of the 7 would be left with no opening claim at all.

*(A first version of the screen passed this at "overlapping 100 %", because it only failed on set
equality. A strict subset is the case the note was warning about, and the screen was answering a
question it had not been asked.)*

## And then the depth sweep killed it

Windows of 15 to 60 games, in steps of 5:

| | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 | 60 |
|---|--|--|--|--|--|--|--|--|--|--|
| bernes | · | **1** | · | · | · | · | · | **1** | **1** | **1** |
| maxhayastan | · | · | **1** | · | **1** | **1** | **1** | **1** | · | · |
| Hirsican | · | · | · | · | · | · | **1** | **1** | · | · |
| Odin5306 | · | · | · | · | · | · | **1** | · | · | · |
| goydorak | · | · | · | · | · | · | **1** | **1** | **1** | **1** |

**Five players named at some depth; four of them flip in and out.** bernes is named at 20, absent
for five consecutive windows, and back at 50. At 30 games the claim names **nobody**; at 45 it names
**four people**, two of whom never appear again.

A claim whose named set changes with the window is measuring the window. **R-13** and **L-008**
require an association to reproduce on a different sample before it is written down, and a different
depth of the *same* player is a weaker test than that — it is the one being failed.

## Consequence

- **`chesscoach/opening_scores.py` is built, tested (20 tests) and wired into nothing.** The
  computation is correct; the claim on top of it is not stable enough to tell anyone.
- **Kept rather than deleted**, on the reasoning that retired `advantage_error`: the instability may
  be sample size rather than the idea. goydorak and bernes are both contiguous over the last three
  windows, which is what a claim looks like just before it settles, and every corpus on hand tops out
  at 60 games per player.
- **The test that would settle it is deeper histories** — free to fetch, public games only (R-10).
  Run `depth.py` at 100+ and see whether the flipping stops.
- **`early_error` stays**, and that is now an evidenced position rather than an omission. The six
  corrections are five shipped and **one screened and held**.

## Honest limitations

- **12 players, one band, ≤60 games.** The instability could be this corpus; that is exactly the
  untested question.
- **The claim was never wired**, so nothing here says how it would rank against other claims or
  whether the arbiter would ever choose it.
- **Score is not skill.** A player scoring badly in an opening may be meeting stronger opponents in
  it; nothing here controls for that, and with 5–19 games per opening nothing could.
- **Openings come from the PGN header where present**, and the book walk otherwise. A mislabelled
  header is a mis-grouped game and this does not check them.
