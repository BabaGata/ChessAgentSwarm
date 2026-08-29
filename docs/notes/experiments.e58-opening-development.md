---
id: cas-exp-e58
title: 'E58 — Per-opening development norms derive themselves, but the author''s two numbers do not check out'
desc: 'Openings really do differ: castling ranges from move 7 to move 17 across families, pawn share from 25 % to 41 %. So a per-opening norm is worth having and it costs nothing to derive. But the corpus puts the Ruy Lopez FASTER than the Italian, inverting the ordering the author predicted, and that disagreement has to be resolved before any claim is built on it.'
updated: 1788739200000
created: 1788739200000
---

# E58 — Deriving the per-opening norms instead of writing them down

**Answers:** [[design.opening-development-signals]] · **Code:** `chesscoach/development.py`,
`experiments/e58-opening-development/` · **Date:** 2026-08-29 ·
**Status:** measurement built and 14 tests pass — **the author's prediction does not reproduce, and
that is the result**

## What the author asked for

> *"The tests should not be general for all opening but general rules per opening. Like in italian
> game the castles should occur around move 5 and in ruy lopez in between moves 8-10."*

Two ways to obey this. **Write the numbers down per opening** — which needs a source for every one of
97 families, cannot be falsified, and is the folklore R-03 forbids. Or **derive them from the corpus**
— which costs one pass, covers every opening including the ones nobody has an intuition about, and
turns the author's two figures into a *prediction the derivation has to reproduce* rather than an
input it is fitted to.

The second was built. The prediction was then checked, and it failed.

## First: is a per-opening norm even worth having?

Yes, and this was not obvious. If every opening castled on move 10 the whole per-opening apparatus
would be dead weight. Across 2,019 games and 97 families:

| | lowest | highest |
|---|---|---|
| castles by move | **7** (Ruy Lopez, W) | **17** (Bishop's Opening, W) |
| develops by move | **10** (Queen's Gambit Declined, W) | **22** (King's Pawn Game, B) |
| pawn share of opening moves | **25 %** (Nimzowitsch Defense, B) | **41 %** (Sicilian Defense, B) |
| repeat share of opening moves | **27 %** (Horwitz Defense, W) | **46 %** (Englund Gambit, W) |
| moves still in book | **1** (Horwitz Defense, B) | **5** (Scotch Game, W) |

**Castling norms differ by a factor of two between openings.** A single global threshold would call
Bishop's Opening players catastrophically late and Ruy Lopez players fine, when both are doing what
their opening does. The author's instruction is confirmed by the data.

**And their pawn observation is confirmed directly**: *"some openings in general allow more moves
with pawns"* — Sicilian Black spends **41 %** of its opening moves on pawns, Nimzowitsch Defense Black
**25 %**. That is not noise at n=241 and n=20.

## Then: the two numbers

Stated before the corpus was asked, which is what makes this a test:

| | the author predicted | the corpus says |
|---|---|---|
| Italian Game, White castles | around move **5** | move **8** |
| Ruy Lopez, White castles | between moves **8 and 10** | move **7** |

**Neither matches, and the ordering is inverted.** The author expects the Ruy Lopez to castle *later*
than the Italian; the corpus has it castling *earlier*, and by the largest margin in the table — Ruy
Lopez White is the fastest-castling cell measured.

Three readings, and they are not equally likely:

1. **The corpus is not theory.** These are ~1600 rapid players. A norm derived from them describes
   what players like this player *do*, which is the right comparison for a peer-relative claim
   (L-045) but is not what an opening *requires*. Under this reading both numbers can be "wrong"
   about theory and still correct for the claim.
2. **The author's 8–10 may describe development, not castling.** In the Ruy Lopez the queen's knight
   goes b1–d2–f1–g3, and that manoeuvre genuinely finishes late. **The corpus puts Ruy Lopez White's
   development completion at move 14** — the same neighbourhood, one column over. If this is the
   reading, the prediction was about the wrong statistic rather than wrong.
3. **The derivation is wrong.** Not supported by anything found so far, but not excluded either.

**This is not resolvable from the data**, and it decides what the claim compares against, so it is
put to the author rather than settled here.

## A censoring bug found in this experiment's own method

The first run took the median over **only the games where castling happened**. Bishop's Opening White
came out at move 11 — while **47 % of those games never castled at all.**

Dropping them understates lateness *exactly where lateness is worst*, which is the same
right-censoring the design note refuses for the development span, committed one level up in the
analysis rather than in the measurement. Replaced with a survival median where a game that never
castled sorts after every game that did, and reports `-` when those games carry the midpoint.

**Bishop's Opening White moved from move 11 to move 17, and its development median became `-`
outright** — half of those games never complete development. The corrected numbers are one to five
moves later almost everywhere.

## What was built

`chesscoach/development.py`, 14 tests, no engine, **and no threshold in it** — it reports
`castled_at`, `developed_at`, `still_at_home`, `repeat_moves`, `pawn_moves`, `moves_in_window` and
`completed`, and judges nothing. Three cases the tests pin down because a naive walk gets them wrong:

- **a capture must clear the captured piece's record**, or the recapturing piece inherits it and its
  next move reads as a repeat;
- **castling moves a rook the move's own squares do not mention**;
- **a minor captured on its home square stops blocking development** — otherwise development never
  completes in any game where a piece is traded there.

## Consequence

- **Per-opening norms are cheap and real.** 97 families, one pass, no engine, no asserted number.
- **The claim cannot be wired up until the disagreement is resolved**, because peer-derived and
  theory-derived norms are different quantities and the choice changes what every player is told.
- **Book depth survives and is usable**: median 1–5 moves with clear per-opening spread, which is
  exactly the *"when do you stop knowing the book"* signal the author asked to keep.

## Honest limitations

- **Not split by rating band.** The peer machinery keys on band × speed × claim; this run pooled the
  whole rapid corpus. These are corpus norms, not band norms, and the numbers will move when split.
- **Family is taken from the deepest named position reached**, so a game that transposes is filed
  under where it ended up, not where it began.
- **97 families, but only 26 clear 20 games.** The long tail has no usable norm yet and will have to
  shrink toward a global prior.
- **Nothing here is a claim yet.** No player has been told anything, and the correlation screen the
  design demands has not been run.
