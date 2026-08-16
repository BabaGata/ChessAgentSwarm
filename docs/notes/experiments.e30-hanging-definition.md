---
id: cas-exp-e30
title: 'E30 — Counting pawns as hanging material explains what the reviewer saw, and confirms neither of their claims'
desc: 'The reviewer counted pawns and pieces together; the detector counts pieces only. Including pawns doubles the numbers, makes both claims LESS unusual, and leaves the contradiction standing.'
updated: 1787011200000
created: 1787011200000
---

# E30 — Does "hanging piece" mean pieces, or pieces and pawns?

**Answers:** the open disagreement from the first expert review · **Date:** 2026-08-15 ·
**Status:** done — **the definition explains the *perception*, and rescues neither claim**

## The question

The reviewer's Form A for `bernes` named **undefended pieces** as the main weakness and **missing
hanging pieces** as the second. The system reported neither, and for the second it actively
disagreed: 3 misses in 77 chances, **3.9 %**, at or below the population.

The reviewer then supplied the thing that made this answerable — what they had been counting:

> "For bernes hanging pieces I included what I found for pawns and pieces together."

`chesscoach/tactics.py` sets `HANGING_MIN_VALUE = 3`, so free **pawns are excluded by
construction**, with a recorded reason from E04:

> "You hang pieces" is not a claim about pawns. Measured on real games, free pawn grabs were the
> bulk of this motif's firings.

That reason is about the **precision of the phrase**, not about whether the pawns matter. So the two
sides were never measuring the same thing, and the disagreement stops being a matter of opinion.

## Method

All twelve expert-review players, same band, same depth 15, so the rates are comparable (E01). S1's
own counting, with `HANGING_MIN_VALUE` swapped underneath it — 3 (ships) against 1 (admits pawns).
Both directions, because the reviewer named both.

## Result — the numbers roughly double, and bernes moves the *wrong* way

**Not taking free material** (`missed_motif.hangingPiece`)

| | bernes | population median | ratio |
|---|--:|--:|--:|
| pieces only | 3.9 % (3/77) | 3.7 % | **1.06×** |
| pieces + pawns | 5.5 % (7/127) | 6.4 % | **0.86×** |

**Handing over free material** (`allowed_motif.hangingPiece`)

| | bernes | population median | ratio |
|---|--:|--:|--:|
| pieces only | 10.7 % (12/112) | 7.7 % | **1.40×** |
| pieces + pawns | 19.6 % (22/112) | 17.6 % | **1.11×** |

Three things follow, and the first two are inconvenient for the reviewer's reading:

1. **The reviewer's second claim is not rescued.** Under *their own definition* bernes misses free
   material at 5.5 % against a population median of 6.4 % — **better than their level**, and further
   below it than under the narrow definition. The system's contradiction stands under both readings.
2. **Widening the detector would have buried the first claim, not surfaced it.** Everyone hands over
   free pawns: the population median more than doubles, 7.7 % → 17.6 %. Bernes' deviation shrinks
   from 1.40× to 1.11×. Had the swarm counted pawns all along, `allowed_motif.hangingPiece` would
   have been *further* from assertable, not closer.
3. **E04's stated reason is confirmed.** Opportunities roughly double when pawns count (bernes
   77 → 127, goydorak 97 → 178). Free pawn grabs really are the bulk of the motif's firings.

## What it does explain: why a human sees it and the system does not

Under the reviewer's definition bernes hands over free material on **19.6 % of their errors — about
one in five**. Scanning twenty games, that is unmissable, and naming it as the main weakness is a
completely reasonable reading of what is on the board.

The system saw the same games and reported nothing, because 19.6 % against 17.6 % is ordinary. The
reviewer was reading **absolute frequency**; the swarm was ranking **relative frequency**. Both are
correct measurements of different things.

This is [[learning.lessons]] L-039 arriving on a second axis. The first version was about a gate
being the only door; this one is about the *quantity being ranked* — and it is the same failure,
because a player who does an expensive thing one time in five does not care that everyone else does
too. [[decisions.0010-three-priorities-and-the-cost-pool]] already fixed the consequence: the cost
pool now reports `allowed_motif.hangingPiece` for bernes at 7.3 wp/game, labelled *ordinary for your
level*. E30 says that fix was aimed correctly, and that **widening the detector would not have been
an alternative route to it**.

## Consequence

**`HANGING_MIN_VALUE` stays at 3.** Changing it would make the phrase less accurate (a report saying
"you hang pieces" about a pawn is wrong), would make both of the reviewer's claims *less* likely to
be reported, and would inflate every hanging-piece opportunity count by ~65 % for no diagnostic gain.
The evidence points the opposite way from the change it was gathered to test.

**Recorded in the review instead.** The disagreement on the reviewer's second claim is now measured
under both definitions and stands. Form A gained a question — *"anything you counted here that a
computer might define differently?"* — because one sentence from the reviewer converted an
unresolvable difference of opinion into a short experiment with a number at the end.

## Honest limitations

- **Twelve players is a small population** and the median is doing a lot of work. The direction of
  every effect is large enough to survive it; the exact ratios are not.
- **These twelve are the review sample**, drawn from the same 84-player corpus everything else was
  built on, so this is not out-of-sample in the E27 sense.
- **`allowed_motif` denominators are the player's errors**, so the pieces+pawns column shares its
  denominator with the pieces-only column. The missed column does not — its opportunities grow with
  the definition, which is why its rates move less than the raw counts suggest.
- **The reviewer read roughly the first 20 of 53 games.** That is enough to see a one-in-five
  pattern and not enough to rank three of them, which is its own finding about the instrument rather
  than about the reviewer.
- **Nothing here says the reviewer misread the games.** They reported what they saw, and E30 shows
  what they saw was real and correctly perceived. What it was not is *unusual*.
