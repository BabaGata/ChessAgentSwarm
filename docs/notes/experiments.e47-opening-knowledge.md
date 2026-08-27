---
id: cas-exp-e47
title: 'E47 — The opening book classifies every game, and the exit ply does not separate players. Both matter.'
desc: 'Layer 1 built on CC0 data. 240/240 games named, exit ply spread 1.17x — below the screen every other claim must pass. The right conclusion is that the screen does not apply here, and why is the point.'
updated: 1788307200000
created: 1788307200000
---

# E47 — Does an absolute opening book say anything useful about these players?

**Answers:** Layer 1 of [[design.informative-claims]] · **Code:**
`chesscoach/openings.py`, `experiments/e47-opening-knowledge/` · **Date:** 2026-08-23 ·
**Status:** done — **built and measured; the claim survives, but not as a peer-relative one**

## What was built

`lichess-org/chess-openings`, **CC0 public domain**, 3,810 named lines, fetched and rebuilt in under
a second. Keyed by EPD, so transpositions resolve without move-order matching.

**Two indexes, and the distinction was a bug before it was a design.** A position is *in theory* if
it lies anywhere along a named line; it has a *name* only if some line ends there. Indexing endpoints
alone scored a game four moves into a mainline as out of book because no row happened to end on that
exact position — 3,810 endpoints against **7,854 positions in theory**.

An early note that the book maxes out at 16 plies was **wrong**: it came from sampling the first 400
rows, which are all A00 irregular openings and short by nature. Real depth runs to **36 plies**, and
mainlines track correctly — Ruy Lopez Closed and the Najdorf are both followed to ply 10.

## Result 1 — classification is total

**240 of 240 games named**, for all twelve players. Every game gets an opening, and the most-played
one per player is immediately legible: bernes plays the Caro-Kann in 8 of 20, simonvj the English in
10 of 20, Sheriwoyama the Sicilian in 8 of 20.

That alone replaces *"you go wrong early as White"* with *"in the Caro-Kann, which you play in 8 of
your 20 games…"*.

## Result 2 — the exit ply does not separate players

| | |
|---|--:|
| per-player median exit ply | 4.0 – 8.0 (**moves 2 – 4**) |
| spread p90 / median | **1.17×** |
| the screen used everywhere else | ≥ 1.30 |

**It fails.** And an earlier reading of 1.40× was an artefact of the endpoint-only bug — noise
inflating spread, which is worth remembering as a way a broken measurement can look *better* than a
working one.

**But the screen does not apply here, and that follows from L-045.** The ≥1.30 bar exists because a
*peer-relative* claim that cannot separate players names nobody. This claim is **absolute** by the
author's own instruction: the reference is theory, not the band. *"You leave the French at move 4 and
the mainline continues …Nc6"* is useful whether or not every other player does the same. It is
teaching, not diagnosis, and teaching does not require the pupil to be unusual.

That is a real change in what the section is for, and it should be stated plainly rather than
smuggled in: **this is the first claim in the project that is not a comparison.**

## Result 3 — the opponent leaves book more often than the player

| | |
|---|--:|
| exits caused by the player | 98 / 234 (**42 %**) |
| exits caused by the opponent | 136 / 234 (**58 %**) |

The confound flagged in design is real and is the majority case. A claim about *the player's*
knowledge must use only the 42 %; using all of it would tell a player their theory is thin when their
opponents were the ones playing sidelines.

There is a second, more interesting reading. When the **opponent** leaves book, the player is on
their own without preparation — which is precisely when the *ideas* matter more than the moves. Layer
2 is aimed at exactly that case, so the 58 % is not waste, it is a different claim.

## Result 4 — Wikibooks coverage: 40 % raw, 91 % with a fallback, and the gap is the finding

Layer 2's pre-check, queried through the MediaWiki API (50 titles a request, `missing` reported
explicitly, `length` returned alongside so a stub is distinguishable from an article).

**Asked about the deepest position still in theory — where the ideas belong — coverage is 40 % of
games.** And it collapses exactly where it is needed:

| plies | positions | with an article |
|--:|--:|--:|
| 1–2 | 25 | **100 %, 76 %** |
| 3–4 | 46 | 55 %, 38 % |
| 5–8 | 97 | 19 %, 35 %, 17 %, **5 %** |
| 9+ | 16 | **0 %** |

Wikibooks is thorough about openings and thin about *variations*, so the coverage curve runs opposite
to the depth curve. Taken at face value this kills Layer 2: the positions players actually leave
theory from are 5–8 plies deep, where coverage is 5–35 %.

**The fallback changes the answer.** The ideas of *the Scandinavian* still apply four plies into a
Scandinavian subline, so walk up the tree to the deepest ancestor that has an article:

| | |
|---|--:|
| games with usable ideas | **219 / 240 (91 %)** |
| depth of the article used, median | **3 plies** |

**But 91 % is not the number to quote, and this is where it would be easy to oversell.** 62 of 168
positions (**37 %**) fall all the way back to 2 plies — "1. e4 e5" — which names a defence and says
almost nothing specific. Weighted by whether the article is actually *about* what the player played,
the honest figure is the **63 % that reach 3 plies or deeper**, and only 22 % get to 6 or more.

A floor of 2 plies is imposed deliberately: an article on `1. e4` alone would technically raise
coverage and would be worthless.

## Consequence

- **Layer 2 is viable, with the fallback and with the specificity stated.** The claim can carry ideas
  for roughly six games in ten at a useful level of detail, and should say which opening the ideas
  are *for* — because at 2 plies that is "the French" and at 6 it is a named variation, and a reader
  cannot tell the difference from the prose alone.
- **The remaining 9 % get no ideas at all** and the section must be silent for them rather than
  reaching for something generic.
- **CC BY-SA still needs its ADR** before any text is stored or shown.

## Honest limitations

- **Twelve players, 240 games.** The spread figure especially is thin.
- **Median exit around move 3 is lower than the author's own estimate of move 7.** Both can be true:
  the median is dragged down by games where an opponent plays an offbeat second or third move, while
  the author was thinking of mainline games. **Not yet reconciled**, and worth doing before the claim
  is worded, because the two numbers would produce different sentences.
- **A traced game confirms the mechanism, not the population.** The French Advance example leaves
  theory at ply 8 on 7…c4, correctly. One game is a sanity check, not evidence about twelve players.
- **Coverage was measured on titles, not on whether the prose is any good.** A 2 kB article exists;
  whether it contains usable *plans* rather than a move list is unchecked, and that is the next thing
  to sample by hand.
- **Nothing here measures whether leaving theory early is bad.** It is a knowledge-depth measurement,
  not an outcome one; the eval half (A3) is separate and unbuilt.
