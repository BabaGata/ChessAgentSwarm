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

## Result 5 — the prose is there and is the right kind; the harvest is not yet done

E47b measured whether pages *exist*. This tried to read them, for the fifteen
opening families these twelve players actually reach, ranked by games.

**Every one of the fifteen has an article**, and the fallback depths are better than the aggregate
suggested — French 8 plies, Vienna 8, Slav 8, Sicilian 7, Caro-Kann 6, Scandinavian 5. Only four of
fifteen fall back to the generic 2-ply level.

**And the content is the right kind.** Retrieved for the Italian
(`.../2. Nf3/2...Nc6/3. Bc4`), **5,754 characters**:

> *"White develops the bishop to a good square where it controls a valuable diagonal. From c4 the
> Bishop controls d5 and pressures Black's f7-pawn, the most vulnerable pawn in Blacks position."*

with named replies for the opponent — 3…Nf6 Two Knights, 3…Bc5 Giuoco Piano, 3…Be7 Hungarian, and
four more. That is a plan and a set of expectations, not a move list.

**The harvest completed on the fourth attempt — 15 of 15 with prose**, 33 to 196 words each, once it
was made **resumable**: every answer written to disk the moment it arrives, so a throttled run loses
nothing and the next asks only for what is missing. That is the right shape for any harvest against a
shared resource, and it should have been the first shape rather than the fourth.

Sample, the Scandinavian at 5 plies, played 16 times across three of these players:

> *"With 3. d4, White focuses on controlling as much of the centre as they can, and opens lines to
> develop their queen and queen's bishop. This offers back the pawn, and Black's main continuation is
> to take it with 3…Nxd5, the Marshall variation… 3…Bg4 is the Portuguese gambit… With 3…g6!?, the
> Richter variation, Black prepares to fianchetto their king's bishop."*

Plans for the player, named replies for the opponent, and the idea behind each reply. Only the
Italian is thin, at 33 words.

**The route there is worth recording precisely**, because two of the
three failures looked identical to *"Wikibooks has no prose"* and none of them was:

1. **`extracts` returns one extract per request** unless `exintro` is set. Asking for twenty titles
   returned nineteen blanks. Read as a content problem; it was a request problem.
2. **`exintro` returns empty on these pages**, because they have **no lead section** — the article
   begins under a heading like `== 3. Bc4 · Italian game ==`. The intro genuinely is empty; the
   article is not. Read again as a content problem; again it was not.
3. **HTTP 429.** Full extracts force one request per title, and across several debugging runs the
   agent asked Wikimedia for too much too quickly. Backoff was added and did not clear it, because by
   then the throttle was already in place.

Three of the four failures were mine. Only the throttling was the server's, and it was provoked.

## Result 6 — Layer 3 is unavailable, and not because of anything here

`explorer.lichess.ovh` returns **401 at the nginx layer for every request**, with or without
parameters. The API is *specified* as needing no authentication, and the search that proposed it said
so. What the specification does not say is that the service has been **unresponsive since an
infrastructure incident in February 2026** — reported upstream as
[a complete outage of the explorer](https://github.com/lichess-org/lila/issues/19610).

So *"what opponents at your level actually play"* cannot be built now, and the reason is external.
Recorded as **R-17**: Layer 3 depends on a third-party service that has been down for months, and a
claim resting on it would have been unshippable through no fault of the code.

**The design does not collapse without it.** Layers 1 and 2 give the opening, the exit ply and the
ideas; Layer 3 was always the smallest addition and the easiest to defer. It should stay deferred
until the service returns, and the design note's sequencing already put it last.

## Honest limitations

- **Twelve players, 240 games.** The spread figure especially is thin.
- **Median exit around move 3 is lower than the author's own estimate of move 7.** Both can be true:
  the median is dragged down by games where an opponent plays an offbeat second or third move, while
  the author was thinking of mainline games. **Not yet reconciled**, and worth doing before the claim
  is worded, because the two numbers would produce different sentences.
- **A traced game confirms the mechanism, not the population.** The French Advance example leaves
  theory at ply 8 on 7…c4, correctly. One game is a sanity check, not evidence about twelve players.
- **Prose quality is established for exactly one article, not fifteen.** The Italian contains real
  plans; the other fourteen are unread because the harvest was rate-limited. Byte length is a poor
  proxy — a page can clear 1,500 bytes on theory tables alone — so E47b's coverage figures should be
  read as an **upper bound** until the text is actually pulled.
- **Nothing here measures whether leaving theory early is bad.** It is a knowledge-depth measurement,
  not an outcome one; the eval half (A3) is separate and unbuilt.
