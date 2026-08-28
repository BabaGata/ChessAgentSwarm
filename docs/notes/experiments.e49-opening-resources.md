---
id: cas-exp-e49
title: 'E49 — The plan sentences are on the page; the difficulty is the other sentences'
desc: 'Selecting a page''s plan sentences recovers both the ones the author endorsed, unfitted, and yields something on 26 of 35 pages. Reading the first run found six ways it launders junk, each now a test carrying the sentence that produced it.'
updated: 1788480000000
created: 1788480000000
---

# E49 — Can the plans be quoted from the page instead of written?

**Answers:** the author's *"I would like similar short descriptions to be in other opening resources
created by the agent … main lines fetched with maybe a few variants, short summary of the plans and
a link for further references"* · **Code:** `chesscoach/opening_plans.py`,
`chesscoach/opening_resource.py`, `experiments/e49-opening-resources/` · **Date:** 2026-08-28 ·
**Status:** done — **the mechanism works; what it yields is only as good as the page**

## The fact that decided the design, checked before any code

The two sentences the author quoted approvingly are **verbatim FreeChessTrainer text**, found at
characters 171 and 1235 of the fetched page. So the request was not *"write descriptions like
these"* — it was *"select sentences like these"*, and the second is something this project may do
while the first is R-03's folklore. → [[decisions.0012-quote-the-plans-rather-than-write-them]]

## Result one — the endorsed sentences come back, unfitted

The first rule set — the author's three objections turned into regexes — recovered **both** endorsed
sentences on the first run, with no tuning against them.

That is weaker evidence than it looks and the note says so: **the Pirc page is the calibration case
and cannot also be the proof.** What it establishes is that the rules encode what was endorsed, not
that they generalise.

## Result two — 26 of 35 pages yield a plan sentence

| | |
|---|--:|
| candidate pages read | **35** |
| yielding at least one plan sentence | **26 (74 %)** |
| families with at least one | **11 of 12** |

**The nine that yield nothing are the interesting half.** They are not extractor failures: a
reference article explains what an opening *is* and never what to aim for, which is precisely the
distinction [[experiments.e48-opening-agent]] measured but could only state as a genre judgement.
E48 found the agent had a *100 % hit rate at finding a reference and 0 % at finding instruction*;
this one puts a number on the same page-by-page.

## Result three — the first run laundered junk, and reading it is what found that

**85 % of pages yielded "something" before the output was read.** Six distinct defects, each now a
test carrying the verbatim sentence that produced it:

| what shipped | cause |
|---|---|
| *"either side can try an early break with the d-Pawn (e.g."* | the splitter cut on `e.g.` |
| *"allowing White the Maroczy bind while retaining a flexible position"* | `maroczy`, `hedgehog` were not in the jargon list — **objection 3 word for word** |
| *"(this is the key) exf6 5.Nc3 Bg7 6.g3 O-O 7.Bg2 8.e3 preparing Nge2"* | an annotated variation is grammatical |
| *"You can one day play a long positional game and the next surprise your opponent"* | passes every content rule and names nothing on the board |
| *"you can already choose from a number of good courses and books"* | `course` matched, `courses` did not |
| *"If you feel comfortable … continue with the further study of the French Defense"* | advice about studying, not about playing |

The fixes cost **85 % → 74 %**, which is the number moving in the right direction.

**The board rule is the one worth keeping.** Requiring that a plan sentence name something on the
board — a square, a piece, a side, a wing — removes the generic encouragement that marketing and
instruction share, and it is a property of chess prose rather than a blocklist that needs feeding.

**And the lookbehind bug is worth recording as itself.** `(?<!\be\.g)` looks back three characters
at `.g.` and lets the split through; the abbreviation's own full stop has to be inside the
lookbehind. Written the natural way, the fix silently does nothing.

## Result four — the moves needed the book to stop discarding them

`Opening` carried `eco`, `name`, `epd` and `plies` — everything except the moves, which an EPD
cannot be replayed back into. Adding `pgn` costs one download, since the book is regenerable.

Two corrections came from looking at real output rather than from design:

- **The main line is the *deepest* row named plainly for the family**, not the shallowest. A player
  asking what the Pirc is wants `1. e4 d6 2. d4 Nf6 3. Nc3 g6`, not `1. e4 d6`. Measured across the
  twelve families, those rows run 1–6 plies, so no depth cap is needed rather than none is wanted.
- **A row named plainly for the family is not a variation of it.** Offering them printed *"Main
  line"* three times underneath the main line, and the Classical Variation appeared twice at two
  depths.

## Consequence

- **Ship the selector and the resource assembler**, behind `reviewed=true` as everything else is:
  an unreviewed page contributes no sentences, because quoting is a stronger endorsement than
  linking, not a weaker one.
- **Production quotes two sentences, not three.** The experiment prints three so the third can be
  judged; on the endorsed Pirc page it is *"The Trainer will present key Pirc structures…"*, which
  is the publisher advertising. Two is what was endorsed and two is the default.
- **Wire `build_resource` into the report.** Not done — it is the next step, and D19's *"locate
  where the player actually left the opening book"* is the claim it attaches to.

## Honest limitations

- **Nothing here is endorsed.** No page is `reviewed=true`, so none of this reaches a player. The
  output exists to be read.
- **The extractor cannot judge chess.** Every rule is about register, vocabulary and sentence shape.
  A confidently wrong plan, plainly written, passes every test in this module.
- **Quality tracks the page, not the selector.** FireChess's London page gives
  *"complete development, castle kingside, and decide between a kingside attack or central break
  with e4"*; the Exeter essay gives sentences assuming the Hedgehog. The selector cannot fix a
  source, and the residue is why `reviewed` stays a person's job.
- **Only the quotes are cached, never the pages** — deliberately, since caching HTML would put a
  copy of ninety copyrighted articles in the repository. The cost is that a rule change means
  re-fetching all 35.
- **Twelve families, from the review twelve's repertoires.** Sixteen families with one game each are
  still uncovered, and no genuinely new player has been run through.
