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

### A1 — A real opening book, from a free local file

`lichess-org/chess-openings` is a CC0 TSV of ~3,500 named lines. Match each game against it and the
**exact ply where the player left book** falls out.

> *"Your knowledge of the Scandinavian ends around move 7. Players at your level get to move 10."*

- **Cost:** one ~1 MB download, cached; zero engine time.
- **Risk:** it is a *master-line* book, so leaving it at move 7 is unremarkable at 1400–1800 — the
  claim has to rest on the **peer comparison**, not the absolute depth. Also a new external
  dependency, and C7 wants sources recorded with an evidence class.

### A2 — A book derived from the peers themselves

Build a position-frequency table from the **existing 136-player reference corpus**: a position many
peers reach is book *at this level*. The player leaves shared knowledge where their positions stop
being common.

> *"By move 8 you are in positions almost nobody at your level plays. Your peers stay on known
> ground until move 11."*

- **Cost:** zero new data. One pass over a corpus already on disk, cacheable.
- **Risk:** ~4,000 games is thin beyond about move 8 — though that is *exactly* where the claim
  lives, so the thinness may not bite. Untested, and that is the main unknown.
- **Fit:** measures "known at your level" rather than "known to masters", which is the more
  defensible comparison for a coaching claim and matches every other claim in this project.

### A3 — No book at all: outcome per opening

ECO code and opening name are **already populated in every game** (Lichess supplies them; verified,
20/20). Group by opening, measure the evaluation where the opening window ends.

> *"In the Scandinavian, which you play in 7 of your 20 games, you come out of the opening worse than
> your peers do in theirs."*

- **Cost:** almost nothing. The data is parsed and sitting unused.
- **Risk:** none to speak of.
- **Weakness:** it cannot separate *"does not know the moves"* from *"knows the moves and not the
  ideas"* — which is precisely the distinction the author asked for.

### Comparison

| | actionable | cost | new dependency | separates line-knowledge from ideas |
|---|---|---|---|---|
| A1 book file | **highest** | low | yes | yes |
| A2 peer book | high | **none** | no | yes |
| A3 outcome only | medium | **none** | no | **no** |

**Recommendation: A3 first, then A2.** A3 is nearly free, uses parsed data that is currently
discarded, and is already a large improvement — naming the opening beats naming the move number. A2
then supplies the missing half, and **the two together give the distinction the author wants for
free**:

| left book | outcome | conclusion |
|---|---|---|
| early | worse | **the line** — learn more moves of it |
| late | worse | **the ideas** — you know the moves and not the plans |
| early | fine | nothing to say; leaving book early is not a fault |

A1 is held in reserve: if A2's corpus proves too thin to locate the exit ply, the TSV replaces the
peer-derived book with no change to the claim shape.

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
