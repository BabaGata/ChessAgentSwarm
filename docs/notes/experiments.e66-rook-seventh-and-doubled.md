---
id: cas-exp-e66
title: 'E66 — Two filters over existing detectors, and which of the author''s conditions did the work'
desc: 'Step 3 of the six corrections. The open-files screen removes 52 % of rook-on-seventh firings, so the precise two-ply version still has something left to buy. For doubled pawns the author gave two conditions and they are wildly unequal: distance removes 17 %, persistence removes 64 %.'
updated: 1789171200000
created: 1789171200000
---

# E66 — `rook_seventh` and `doubled`

**Answers:** [[design.detectors-name-consequences]] §§ 4–5, step 3 of the sequence ·
**Code:** `chesscoach/squares.py`, `chesscoach/structure.py` · **Date:** 2026-08-31 ·
**Status:** both corrected and measured; **`persistent_doubled` is not yet wired into S5**

## `rook_seventh` — the cheap screen first

> *"Whenever there are 3 or more open files there is not much possibility to block the opponent...
> This should be counted only if there was a real opportunity to block the rook from coming to the
> seventh file a move before or 2 moves before."*

The design note offered a cheap screen and a precise search, and proposed the cheap one first so the
search is only paid for if it still has something to buy.

**Implemented:** with three or more open files — the author's own threshold — the claim does not
fire at all.

Measured over 25 players' games, every position where an enemy rook stood on the seventh:

| | | |
|---|--:|--:|
| positions with a rook there | **4,077** | |
| screened out (≥ 3 open files) | **2,117** | **52 %** |
| still fire | 1,960 | 48 % |

Open files when a rook was on the seventh: `{0: 14, 1: 760, 2: 1186, 3: 906, 4: 590, 5: 285, 6: 201,
7: 98, 8: 37}`.

**The screen halves the claim, and half is not most.** The design note said that if the cheap version
removed most of the firings the precise one would have little left to buy — it removes 52 %, so
**the two-ply preventability search is still worth building.** That is the answer the note asked for
and it goes the other way from the guess.

## `doubled` — two conditions, wildly unequal

> *"This should be counted only if they are directly one in front of the other or if there is only 1
> square in between... Also the double pawns should be taken in the account if they are able to last
> for more then 3 moves, otherwise, they are in that state just until the end of exchange."*

Both are implemented. Over 569 games:

| condition | effect |
|---|--:|
| **distance** (1–2 ranks apart) | 9,378 → 7,762 counted, **−17 %** |
| **persistence** (> 3 of the player's own moves) | **64 %** of doubled files are transient |

**The second condition does almost four times the work of the first.** Most doubled pawns really are
close together, so the distance rule trims an edge; but **490 of 765 doubled files never survive
three moves** — they exist only until the end of an exchange, exactly as the author said, and the old
detector counted every one of them.

Two implementation notes, both from the author's wording rather than convenience:

- **surplus, not files** — a tripled pawn still reads as worse than a doubled one, and only pairs
  within the gap count toward it;
- **the player's own moves, not plies** — they said "moves", and a player who un-doubles at their
  next turn has held the weakness for one move rather than two;
- **runs reset** — a file doubled twice briefly is not a lasting weakness, and a counter that
  accumulated across episodes would say it was.

## What is not done

**`persistent_doubled` exists and is not wired in.** S5 calls `conceded(before, after, colour)` one
move at a time, and persistence needs the span — which the design note flagged as a structural change
before any of this started. The distance condition is live because it is a property of one position;
the persistence condition is a function with tests and no caller.

That is the honest state: the measurement is real, and **the 64 % is what the claim would lose if the
condition were wired, not what it has lost.**

## Honest limitations

- **25 players for the rook figure, 20 for the pawns.** Enough to size an effect, not to characterise
  one.
- **Neither correction has been read against positions.** The rook screen especially: "three open
  files" is the author's threshold and a reasonable proxy, and whether the rook was *actually*
  preventable in those 1,960 remaining positions is exactly the question the cheap screen does not
  ask.
- **The distance rule assumes the author's reasoning holds**, that a far-advanced doubled pawn is
  attacking rather than obstructing. That is a chess claim, sourced to them, and not independently
  checked.
