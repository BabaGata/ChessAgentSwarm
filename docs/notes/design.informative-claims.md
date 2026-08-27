---
id: cas-design-informative-claims
title: 'Design — from claims that are true to claims that can be worked on'
desc: 'The reviewer marked four claims. One detector is wrong (0/5, verified), two are true but not actionable, one is fine (4/5). Options for each, compared, with a recommendation and a sequence.'
updated: 1788307200000
created: 1788307200000
---

# Design — from claims that are true to claims that can be worked on

**Answers:** the author's *"see what are the ways to make detection more correct or if what is
detected is not really informative plan on how it could be more informative"* ·
**Status:** design, no code yet · **Feeds:** D17, D19, D20

## What the marks actually say

23 marks on `experiments/e46-motif-precision/results/detection-sheet.txt`, four claims covered:

| claim | ✓ | ✗ | ? | reading |
|---|--:|--:|--:|---|
| `allowed_motif.hangingPawn` | **4** | 1 | 0 | **works.** Leave it alone |
| `advantage_error.clear` | 0 | 0 | **5** | fires on real errors, **names nothing** |
| `early_error.white` | 0 | **4** | 1 | fires on real errors, **explains them wrongly** |
| `moved_into_attack` | 0 | **5** | 0 | **broken** |

**These are three different problems**, and conflating them would produce three wrong fixes. One
detector is incorrect. Two are correct-but-empty. One is fine.

## Problem 1 — `moved_into_attack` is broken, and the cause is verified

All five rejected instances are **captures with `exchange_value >= 0`**, reproduced from the
author's own counterexamples:

| player | move | capture | exchange_value | swap on destination | fires |
|---|---|---|--:|--:|---|
| Maximilian_Honigtopf | bxc3 | yes | **+2** | 1 | yes |
| Odin5306 | Nxg3 | yes | **0** | 3 | yes |
| Odin5306 | **Bxd8+** | yes | **+6** | 3 | yes |
| Odin5306 | Bxf3 | yes | **0** | 3 | yes |
| simonvj | Bxe5 | yes | **+1** | 2 | yes |

`Bxd8+` **wins a queen** and is reported as *"you put the piece you have just moved on a square where
it can be won."*

The code excludes only *losing* captures:

```python
if exchange_value(board, move) < 0 and board.is_capture(move):
    return False
return _swap(after, move.to_square) >= MATERIAL_LOSS
```

An even-or-better capture falls through to a test that measures **the recapture in isolation** and
ignores what was captured. Every ordinary trade fires. The author's word for all five was
"exchange", four times over.

**This is not an option to weigh — it is a fix.** `exchange_value` already nets the whole sequence,
and for a quiet move it equals `-swap` on the destination, so **one test covers both cases**:

- `moved_into_attack` = **quiet** move with `exchange_value < 0`
- `miscounted_exchange` = **capture** with `exchange_value < 0`

A clean partition, no overlap, and it restores what the docstring always claimed.

## Problem 2 — `early_error` explains errors it detects correctly

The author's objection is not that the moves are fine. It is the *story*: "the edge of your
repertoire" around move 15, when *"most players at this level will get out of the opening lines
before move 8 or just until the castling."* Their notes name the real causes — *"white is not
defending the king, that is the issue"*, *"he is out of the opening for plenty of moves already"*.

Three ways to replace the story. All three keep the same detection and change what is concluded from
it.

> **Options A1–A3 were superseded on 2026-08-23 by the author, and the reason is the important part.**
> The peer-derived book (A2) was recommended and is **refused**: *"Checking whether they deviate from
> what they usually do is not something that will help them if what they usually do is not good from
> the beginning."*
>
> That is correct and it generalises. **Peer-relative is the right frame for "is this unusual" and the
> wrong frame for "is this right."** A band that leaves theory at move 6 is not a standard to measure
> against; matching it is not a target. Everything else in this project is peer-relative, which is why
> the mistake was easy to make. Recorded as **L-045**.
>
> A3 survives — it refers only to how the player *fares*, never to what peers *play*.

### The replacement — three layers, all free, all verified to exist

The requirement is not only *where* knowledge ends but *what is missing*: **the main ideas for the
player and the main responses for the opponent**, so the system can teach the ideas rather than
report a deviation.

**Layer 1 — the lines.** `lichess-org/chess-openings`, **CC0 public domain**. Five TSVs, columns
`ECO`, `name`, `pgn`, `uci`, `epd`. The **`epd` column is the key**: entries are keyed by *position*,
so transpositions resolve for free and no move-sequence matching is needed.

**Layer 2 — the ideas.** Wikibooks *Chess Opening Theory*, **CC BY-SA 4.0**. The URL path *is* the
move sequence (`/1._e4/1...e5/2._Nf3/2...Nc6/3._Bc4`), so lookup is direct. Verified on the Italian:
prose plans for the side to move — *"From c4 the Bishop controls d5 and pressures Black's f7-pawn"*,
*"a swift attack on f7 and building a big centre with c3 and d4"* — **and named main responses for
the opponent**: 3…Nf6 Two Knights, 3…Bc5 Giuoco Piano, 3…Be7 Hungarian, 3…h6, 3…d6, 3…Nd4, 3…f5.
Exactly the pair asked for.

**Layer 3 — what opponents actually play at this level.**
`explorer.lichess.ovh/lichess?fen=…&speeds=rapid,blitz&ratings=1400,1600` — free, no auth. Returns
the move distribution **and results** filtered to the player's own band. Theory says what *should* be
played; this says what they will actually face, and at 1500 the two differ.

### What a claim built on these looks like

> *"You play the Scandinavian in 7 of your 20 games. You leave theory at **move 6** — the book
> continuation is …Nf6 — and in 4 of those 7 you were already worse by move 12. The idea you are
> missing: [quoted, attributed]. At your level **38 %** of opponents continue with Bd2."*

Against *"you go wrong early as White"*, that is the whole distance being asked for.

### The costs, stated before anything is built

- **Scope.** A download, a parser, a local store, a cached crawler, position→entry matching, and a
  section to speak it. **Days, not hours** — the largest new capability since the sections themselves.
- **Licence, and it needs an ADR.** CC0 for Layer 1 is unencumbered. **CC BY-SA 4.0 for Layer 2 is
  not**: attribution is mandatory and share-alike propagates to whatever embeds the text. Every stored
  excerpt carries its source URL. This is what keeps the ideas on the right side of **R-03** — quoted
  from a citable source, never generated and **never paraphrased**, because paraphrase is exactly
  where folklore re-enters.
- **Coverage is unknown, and it is the pre-check.** Wikibooks is uneven. **Before building**: take the
  positions the twelve review players actually reach and measure what fraction have a real page. At
  20 % Layer 2 is decoration; at 80 % it carries the claim.
- **Network stays in the outer loop.** Crawl once, cache to disk, never fetch during analysis (C1).

### Comparison

| | actionable | cost | licence | teaches the ideas |
|---|---|---|---|---|
| **L1 lines (CC0)** | high | low | **unencumbered** | no |
| **L2 ideas (Wikibooks)** | **highest** | moderate | CC BY-SA — attribution + share-alike | **yes** |
| **L3 explorer API** | high | low | free API | says what they will face |
| ~~peer-derived book~~ | — | — | — | **refused: a relative reference cannot say what is right** |
| A3 outcome per opening | medium | **none** | — | no — but free, worth doing anyway |

**Recommendation: A3 now, then L1 + L2, L3 last.** A3 is nearly free and ships regardless. **L1 is
load-bearing** — it turns "you go wrong early" into "you leave the Scandinavian at move 6", the whole
change in kind, and CC0 means no licence question. **L2 is what was actually asked for**, gated on the
coverage pre-check. L3 is the smallest addition and the easiest to defer.

L1 with A3 gives the distinction, now against theory rather than against the band:

| left theory | outcome | conclusion |
|---|---|---|
| early | worse | **the line** — learn more of it, and L2 supplies why the moves matter |
| late | worse | **the ideas** — knows the moves, not the plans. L2 is the whole answer |
| early | fine | nothing to say. Leaving theory early is not a fault by itself, and a claim treating it as one would measure conformity rather than skill — the error the peer book made |

## Problem 3 — `advantage_error` detects real errors and names none

Every one of the five is `[?]`, and the author's notes are the answer: *"didn't defend pawn
properly"*, *"allowed black to deform his pawn structure"*, *"didn't defend king properly"*,
*"deformed pawn structure"*, *"didn't defend king properly"*. **They are not unsure whether the
moves are errors. They are unsure what the claim is telling them.**

### B1 — Say what the error was, conditioned on being ahead

Intersect the existing per-move detectors with "the player is winning". No new detector.

> *"When you are already better, your mistakes are king-safety mistakes — 6 of your 9."*

- **Cost:** near zero. A conditioning and composition step over detectors that exist.
- **Risk:** each (player × ahead × error-kind) bucket is small and may not clear the confidence gate.
  That is a real possibility and it is measurable before committing.
- **Fit:** three of the author's five notes are king or pawn defence. This is their observation,
  mechanised.

### B2 — A defensive resource was available and was not played

Detect that the engine's best move **defended** something under threat and the player's did not.

> *"In 7 of your winning positions there was a move that dealt with the threat, and you played
> something else."*

- **Cost:** moderate — needs a "this move defends" predicate, which does not exist.
- **Risk:** lower than it looks. L-042 says claims about what *befell* the player are the error rate
  renamed, while claims about what the player *did* are independent — and "played the ambitious move
  instead of the safe one" is action-shaped, so it has a real chance of surviving the screens.
- **Fit:** the closest literal match to *"you forget to defend."*

### B3 — Conversion ("you fail to convert winning positions")

**Refused before it is built.** It restates the outcome in different words and is exactly the shape
the author is objecting to. Recording it so it is not proposed again.

### Comparison

| | actionable | cost | new detector | survives the screens? |
|---|---|---|---|---|
| B1 name the error kind | high | **none** | no | **unknown — measurable first** |
| B2 defensive resource | **highest** | moderate | yes | plausible (L-042) |
| B3 conversion | low | none | no | irrelevant — refused |

**Recommendation: B1 first**, because it costs nothing and its whole risk (thin buckets) can be
measured before a line of production code is written. **B2 if B1's buckets are too thin**, which is
the likely outcome and worth knowing early.

## Sequence, and why this order

1. **Fix `moved_into_attack`** — verified defect, one-line test change, largest precision gain
   available. Then re-run the sheet so the author re-checks a detector that has actually changed.
2. **Screen B1** — cheap, and it either supplies `advantage_error`'s missing content or rules itself
   out in an afternoon.
3. **Build A3** — free, uses discarded data, improves the weakest-explained claim.
4. **Screen A2** — the one genuinely uncertain piece, and the one that makes A3 actionable.
5. **B2 / A1** only if 2 and 4 fail.

**What this does not touch:** `allowed_motif.hangingPawn` scored 4/5 and should be left alone. The
temptation to improve a working detector while the tools are out is how a 4/5 becomes a 2/5.

## The rule underneath all of this

The author's objection generalises past these two claims: **a claim that names a
*circumstance* is not actionable; a claim that names a *behaviour* is.** "You go wrong early" and
"you go wrong when winning" are circumstances. "You leave the Scandinavian at move 7" and "when
ahead, you stop defending the king" are behaviours. Every future claim should be read against that
test before it is built — and several shipping claims would fail it, which is worth its own pass
later.
