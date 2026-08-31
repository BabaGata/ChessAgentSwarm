---
id: cas-exp-e74
title: 'E74 — The two-ply search removes another 29 % of what the cheap screen let through'
desc: 'The precise half of the rook-seventh correction, built because E66 measured the cheap screen removing only half. It removes 29 % of what reaches it at 1.2 ms a search, and the claim now fires on 40 % of arrivals instead of all of them.'
updated: 1788210000000
created: 1788210000000
---

# E74 — Was the rook preventable? The search, built and measured

**Answers:** [[design.detectors-name-consequences]] § 4, the half [[experiments.e66-rook-seventh-and-doubled]] left owed ·
**Code:** `chesscoach/squares.py`, `experiments/e74-rook-seventh-precise/` ·
**Date:** 2026-08-31 · **Status:** **built, wired, measured**

## Why it was still owed

> *"This should be counted only if there was a real opportunity to block the rook from coming to the
> seventh file a move before or 2 moves before."*

The author gave a cheap proxy and a precise rule. The design note proposed the cheap one first and
said the precise one would be unnecessary **only if the cheap one removed most of the firings**. E66
measured it removing **52 %**, and recorded the conclusion honestly: half is not most.

## What the search is

From the position **before the player's move**, over the player's own legal moves: is there one after
which **no** enemy reply lands a rook on the seventh? Two plies, which is what the design note scoped
— the author also mentioned *"2 moves before"*, and four plies is a different cost.

## What it buys

72 players, 68,984 player moves with an answer, every position where a rook **arrived**:

| | | |
|---|--:|--:|
| arrivals | **764** | |
| screened out (≥ 3 open files) | 336 | 44 % |
| survive the screen | 428 | 56 % |
| **… and were preventable — still fire** | **304** | **40 %** |
| **… and were not — newly removed** | **124** | **16 %** |

**The search removes 29 % of what reaches it.** More than a quarter of the arrivals the cheap screen
passed were unpreventable anyway, and the claim used to fire on every one of them. E66's call was
right: the screen was not enough.

The claim now fires on **40 % of arrivals** where it once fired on 100 %.

## Cost (C1)

**1.2 ms per search, 0.5 s across 428 searches**, and the search runs only on arrivals that survive
the cheap screen — never on the 68,984 moves, never on the 336 the screen already answered. It is
deterministic computation, the top tier of C1's preference order, with no engine and no model.

## Read against positions

E66's stated gap was that *"neither correction has been read against positions"*. `results/removed-
sample.txt` carries twelve positions the search newly removes, as FENs, for exactly that.

One was checked by hand while writing this. In
`2r3k1/p4ppp/1p6/4R3/P3P3/2P2N2/6PP/6K1 b - - 0 25`, White's rook on e5 plays **Re7** after *every
one* of Black's legal moves — king moves, rook moves along the eighth, `Rc7`. There is no defence and
the old claim told the player there was.

## Honest limitations

- **The rule asks whether the arrival was possible, not whether it was good.** In the position above,
  `Re8` meets `Re7` with `Rxe7` — the arrival becomes a bad idea without becoming illegal, and this
  search still calls it unpreventable. A practical reading would remove more. Making that judgement
  needs an engine inside a section, which C1 does not allow here, and the choice is recorded rather
  than hidden.
- **The mirror image: a preventing move need not be good either.** A player who could only have
  stopped the rook by hanging a queen is told they could have stopped it.
- **Two plies, not four.** The author said *"a move before or 2 moves before"* and this is the first
  half. Whether the second half is worth its cost is unmeasured.
- **Corpus is `corpus-rapid`, 30 games per player, one band.** The 29 % is a rate over 428 searches,
  not a property of chess.
- **Nobody has marked the sample yet.** The rule agreeing with me on one position is not evidence;
  it is the reason to hand over twelve.
