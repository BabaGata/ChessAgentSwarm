---
id: cas-exp-e75
title: 'E75 — Book depth is reliable, distinct, and not what killed 1a'
desc: 'The last unrun screen from E69. Book depth is a stable property of a player (split-half 0.81), correlates only -0.47 with slow_development, and is not merely rating. It survives the screen the design note demanded — but redundancy was never the argument against it, and the median player leaves theory after 5.3 plies.'
updated: 1788213600000
created: 1788213600000
---

# E75 — Does book depth have anything left to add?

**Answers:** [[design.detectors-name-consequences]] § 1a's held commitment, and the one pair
[[experiments.e69-development-correlations]] could not screen ·
**Code:** `experiments/e75-book-depth/` · **Date:** 2026-08-31 ·
**Status:** done — **it survives, and that reopens a question rather than settling one**

## The commitment

When 1a — *"you leave theory earlier than your peers"* — was superseded by
[[design.opening-development-signals]], the note did not delete it:

> ***1a is held, not deleted**: a correlation screen against `plies_in_book` decides whether book
> depth has anything left to add.*

E69 ran every other pair and stopped at this one, stating why: **book depth is not a claim in the
peer reference**, so there was no per-player rate to correlate. This computes one — 84 players from
the rapid and blitz corpora, walked through the CC0 book, no engine.

## It is a real measure

**Split-half reliability r = +0.81** over 84 players, games split odd/even rather than by time so
that a player's drift is not mistaken for the measure.

That check exists because of [[experiments.e73-opening-scores]], which had just shipped a claim that
passed every screen and then changed its named set with the window. **A measure that does not agree
with itself cannot be distinct from anything**, and this one does.

| | median | range |
|---|--:|---|
| plies in book | **5.34** | 2.07 – 8.29 |
| plies in book, own exits only | 5.32 | 2.33 – 8.13 |
| share of games the player left first | 0.52 | 0.27 – 0.81 |

## It is not a restatement of the development claims

E69's ceiling: above |r| > 0.85 two claims are one signal with two names.

| claim | vs plies in book | vs own exits | vs share left first |
|---|--:|--:|--:|
| **`slow_development.book`** | **−0.47** | **−0.49** | +0.31 |
| `repeat_move.any` | −0.35 | −0.38 | +0.33 |
| `late_castling.book` | −0.30 | −0.29 | +0.24 |
| `pawn_error.any` | −0.18 | −0.13 | +0.24 |

**Nothing is close to the ceiling.** The sign is right — deeper theory, less slow development — and
the strength is what you would expect of two measures of the same phase rather than of the same
thing. `slow_development` and book depth share about a quarter of their variance.

## And it is not simply strength

E14 found four of six style candidates were strength wearing a style label.

| | vs rating |
|---|--:|
| plies in book | **+0.37** |
| share left first | −0.21 |
| `slow_development.book` | −0.41 |
| `repeat_move.any` | −0.46 |

Book depth tracks rating **less** than two of the development claims do. It is not a rating estimate
in disguise.

## What this does and does not settle

**It settles the screen.** The design note asked whether book depth is redundant. It is not:
reliable at 0.81, distinct at −0.47, and not merely rating at +0.37. On the question that was
actually asked, 1a survives.

**It does not settle whether to build it**, because redundancy was never the argument against it.
The design note superseded 1a on two other grounds and this screen touches neither:

- **actionability** — *"you moved a piece that was already out while a knight sat at home"* names
  something repairable this week; *"you left theory at move 6"* names a moment;
- **cost** — the development signals need no book walk over the peer corpus.

**And the magnitude is small enough to matter to that judgement.** The median player leaves theory
after **5.3 plies — under move 3** — and the whole spread across 84 players is about 6 plies. A claim
built on this would be telling a player they leave theory *a move and a half* earlier than their
peers. Whether that is coaching or trivia is a chess judgement, and it is the author's.

## Consequence

- **1a stays held, and now for a stated reason**: not "it might be redundant" but "it is distinct and
  small, and the actionability argument still stands".
- **The screen the design note promised is paid.** Every pair E69 named has now been run.
- **If 1a is ever built**, the measure to use is `plies_in_book` on the player's **own** exits: it is
  marginally the stronger correlate (−0.49 against −0.47) and it is the one that measures the right
  person, which `BookWalk.left_by_white` exists to make possible.

## Honest limitations

- **The walk caps at 30 plies**, far above the 8.3 maximum observed, so no ceiling effect — but the
  book has gaps and a game can leave and re-enter theory. `plies_in_book` is the deepest named
  position, not an unbroken run.
- **84 players, two speeds, one band.** The reliability figure is the most transportable number here;
  the correlations are corpus-specific.
- **A screen shows a claim discriminates, never that its name is true** (L-050). Nothing here says
  that leaving theory early is *bad*, only that it is measurable, stable, and not something already
  being measured.
- **Rating comes from PGN headers**, so it is the player's rating at the time of each game rather
  than a single current figure.
