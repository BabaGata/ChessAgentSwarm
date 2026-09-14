---
id: cas-adr-0019
title: 'ADR-0019 — Fork and skewer are split by geometry, against the endorsed definition'
desc: 'A slider attacking two pieces on one line through it is recorded as a skewer, not a fork. The author chose their own rule over the Lichess puzzle-theme definition the vocabulary is drawn from, knowing that the motif key is also the puzzle filter the exercise sends the player to.'
updated: 2026-09-14
created: 2026-09-08
---

# ADR-0019 — Fork and skewer are split by geometry

**Date:** 2026-09-08 · **Status:** accepted · **Decided by:** the thesis author

## Context

The first scored round of [[experiments.e55-detector-precision]] put `missed_motif.fork` at **25 %**
precision (2 of 8) and **condemned** it.

> **Correction, 2026-09-14.** The scorer did not recognise claim names containing spaces or
> apostrophes and credited `out_of_book.Queen's Pawn Game`'s marks to the claim above it. Fork's own
> marks were **1 of 5, 20 %** — still condemned, so the decision below is unaffected. Option 3's
> counterfactual changes more: all four of fork's rejections were *"this is a skewer"*, so leaving the
> code alone and reading them as vocabulary would have put it at **5 of 5**, not 63 %.

Six of the ten rejected fork rows across both directions carried one reason, written by the author on
the sheet:

> *"This is a skewer, fork is only when one of the involved pieces is not aligned on the same
> line/diagonal."*

> *"Just a note, forks are usually done by knights, pawns and sometimes queens, skewers are usually
> done by rooks, bishops and queens."*

Every one of the six has the same geometry: a **slider** attacking two pieces that lie on **one line
through it**, usually in opposite directions, usually with the king as one of them.

| the position | the author's mark |
|---|---|
| `Rd1+` — forker `rd1`, targets `Bb1`, `Kg1` | skewer |
| `Bg5+` — forker `bg5`, targets `Kc1`, `Qh6` | skewer |
| `Rxd4` — forker `rd4`, targets `Pc4`, `Pe4` | skewer |
| `Bxg7` — forker `Bg7`, targets `ph6`, `rf8` | skewer |
| `b6` — forker `pb6`, targets `Qa5`, `Nc5` | **fork** (accepted) |
| `Qxh3+` — forker `qh3`, targets `Kh1`, `Pf3` | **fork** (accepted) |
| `Nxb4+` — forker `nb4`, targets `Pa2`, `Kc6` | **fork** (accepted) |

## The conflict

The motif vocabulary is the **Lichess puzzle theme list**, and `data/knowledge.json` carries both
definitions verbatim, sourced and endorsed:

- **fork** — *"A move where a piece attacks two or more opposing pieces simultaneously."* No geometry
  in it at all.
- **skewer** — *"a high value piece being attacked, moving out the way, and allowing a lower value
  piece **behind it** to be captured or attacked, the inverse of a pin."* Behind, and high-then-low.

**Under both, all six of the author's rejections are forks.** The detector was following the endorsed
source; the marks were not.

Hard rule 7 makes this a decision rather than a bug report: a chess claim carries a source, and here
there are two sources that disagree — a public expert-consensus list and the thesis author, who is a
rated player reading their own games.

## What it costs, which is why it was put to the author

**The motif key is also the exercise.** `planner._action` renders `missed_motif.<subject>` as *"Drill
`<subject>` puzzles"*, and `<subject>` is passed to the Lichess puzzle theme filter. Relabelling these
positions `skewer` sends the player to puzzles built on the **front-and-behind** geometry, which is
not what their own games looked like.

Measured before deciding: **43 of 237 fork firings (18 %)** have the one-line shape, against 61
firings of `skewer` itself — so `skewer`'s volume roughly doubles and `fork`'s falls by a fifth.

Three options were put to the author:

1. keep Lichess, record the geometry separately, and split only the *advice*;
2. follow the author's rule and relabel;
3. leave the code alone and record the disagreement — which alone would have taken
   `missed_motif.fork` from 25 % to 63 % and off the condemned list.

## Decision

**Option 2.** The author's rule is the project's rule.

The reasoning that makes it defensible rather than merely deferential: the two shapes are different
**recognition skills**, which is what a coaching claim is for. Spotting a knight fork is pattern
recognition on the knight's move shape. Spotting *"my rook can drop onto that rank and hit two things
along it"* is line vision — the same skill as seeing pins and skewers. Grouping by what the player has
to learn to see is a better grouping for coaching than grouping by the puzzle database's tag, even
though the tag is what the puzzle database will filter on.

## Consequences

- `_all_on_one_line` decides the name; `_fork_on_one_line` is one predicate used from both sides, so
  `_is_fork` and `_is_skewer` cannot drift into claiming the same move or neither. That shared
  predicate is L-060's lesson applied in advance.
- **The material test does not change.** Only the name moves. A position that was not a fork does not
  become a skewer. Measured over 60 games: `fork` **237 → 185**, `skewer` **61 → 110**. The 52-out
  against 49-in is not a leak — 3 of the moved positions were already skewers by the front-and-behind
  rule, so they kept a name they had. No position is left named neither.
- *"Forks are usually done by knights, pawns and sometimes queens"* falls **out of the geometry**
  rather than being written in as a list of piece types — a knight can never attack along a line from
  its own square, so the rule can never fire for one.
- **`data/knowledge.json` was rewritten.** `fork` keeps the Lichess sentence, because every move the
  detector still calls a fork is a fork under it; the deviation is recorded in its `note`. `skewer`
  **could not** keep it — the detector now fires on a shape that sentence does not describe, and
  serving it to a player looking at their own game would show them a definition their position does
  not match. It carries an author-written definition covering both shapes, sourced to the marked
  sheet, with the Lichess source retained beneath it.
- **The puzzle-filter mismatch is accepted and unfixed.** It is recorded in the `skewer` entry's note
  so the next person meets it rather than rediscovers it. The obvious follow-up — an exercise for
  `skewer` that names the two geometries rather than passing the key straight to a filter — is not
  built.
- **The peer reference and the separation register are stale** for `fork` and `skewer` and must be
  rebuilt (L-058). Nothing quoting those two rates is trustworthy until then.

## What would reverse this

A measurement that the relabelled positions **behave differently from skewers** for the players who
have them — if a player weak on one-line double attacks is not the same player weak on front-and-
behind skewers, the grouping is wrong whatever it is called, and the split should be by geometry into
*three* names rather than two.
