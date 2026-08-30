---
id: cas-exp-e64
title: 'E64 — Public-domain chess books, and the discovery that the claim names are ours'
desc: 'Three Gutenberg books by Capablanca, Edward Lasker and Staunton, wired in as a curated source that bypasses the web-relevance machinery. They cover castling, development and pins heavily and the modern tactical vocabulary not at all — skewer and outpost appear zero times. And they exposed something bigger: nine of fourteen claim keys are this project''s jargon, which no source defines.'
updated: 1789084800000
created: 1789084800000
---

# E64 — Books as a source

**Answers:** the author's *"can you find some chess books and use them for a information resource"* ·
**Code:** `chesscoach/books.py`, `data/books/` · **Date:** 2026-08-31 ·
**Status:** wired and citing properly — **and the definitions are still wrong, for a reason worth
more than the books**

## The shelf

Three Project Gutenberg texts, out of copyright, downloaded once and read from disk. Free in the way
C7 means it: no key, no rate limit, no signup an examiner cannot reproduce.

| book | year |
|---|---|
| José Raúl Capablanca, *Chess Fundamentals* | 1921 |
| Edward Lasker, *Chess Strategy* | 1915 |
| Howard Staunton, *The Blue Book of Chess* | 1848 |

**They are a curated shelf, so they bypass the relevance gate.** Everything built to keep out a
Beyoncé film, a Go wiki and a libertarian-communism essay is machinery for the open web; a passage of
Capablanca can say "chess" zero times and still be Capablanca.

## What they cover, measured before anything was built on them

| | fork | skewer | outpost | pin | castl | develop |
|---|--:|--:|--:|--:|--:|--:|
| Capablanca | 0 | 0 | 0 | 35 | 15 | 68 |
| Ed. Lasker | 1 | 0 | 0 | 68 | 235 | 214 |
| Staunton | 0 | 0 | 0 | 18 | 281 | 6 |

**The modern tactical vocabulary postdates them.** "Skewer" and "outpost" appear **zero** times in all
three; "fork" once across 1.4 MB of chess writing.

So books are not a replacement for the web — **they are its complement**, and the complement is exact:
they are strong precisely where the web returned nothing (castling, development, pins) and absent
precisely where the web succeeded (fork, hanging piece).

## Two things they broke, and one they didn't

**Descriptive notation.** `_SPECIFIC` knew algebraic and caught none of `P-K4`, `Kt-KB3`, `QR-Q1`,
`B x Kt` or Capablanca's spaced `Kt - K B 3`. Without it, *"Kt - Q B 3 This developing move at the
same time defends the King's Pawn"* read as a general statement about development when it is a note
on one move of one game. Adding it cut the surviving sentences about castling and development from
68 → 17 in Capablanca and 273 → 58 in Lasker.

**Front matter outranked the book.** Ranking passages by term count put a **table of contents** and
the **e-text header** first: a contents page names every subject in the book exactly once, so on a
term count it beats the chapter that explains one of them. Passages are now ranked by how many of
their *sentences* both mention a term and read as prose. A contents page scores zero.

**And the citations are real.** An entry now reads
`Edward Lasker, Chess Strategy (1915) book://edward-lasker-chess-strategy#169` — a source a reader
can actually chase, which `chessjournal.com` never was.

## The definitions are still wrong, and that is the finding

| claim | what it drafted from the books |
|---|---|
| `late_castling` | *"A player who makes an illegal move with a piece must retract that move…"* |
| `slow_development` | *"If, on the other hand, Black exchanges pawns in order to free the Knight…"* |

The first is the **touch-move rule**. The second is a game note.

**The retrieval was not the problem.** Asked for `late_castling`, the library returns the passage
containing Lasker's actual definition — *"…what is termed 'castling,' in which the King and either
Rook can be moved simultaneously…"*. The right passage arrives and the wrong sentence leaves it.

But underneath that is something larger:

> **Nine of the fourteen claim keys are this project's own jargon, and no source defines them.**

`late_castling`, `slow_development`, `repeat_move`, `pawn_error`, `allows_square`, `allows_pressure`,
`moved_into_attack`, `long_think_error`, `capturingDefender` — these are names this project invented
for things it measures. Capablanca has a chapter on **castling**; nobody has ever written a
definition of **late castling**, because it is not a term. The knowledge base has been asking the
literature to define words the literature has never used, and the nine refusals in E63 are that,
not a failure of retrieval.

**The likely fix is structural**: entries for **concepts** the literature does define — castling,
development, the pin, the fork — with each claim *pointing at* a concept rather than owning a
definition. `late_castling`, `slow_development`, `repeat_move` and `pawn_error` would all point at
development. That is a design change and it is not made here.

## Consequence

- **The books ship** as a curated source, ahead of the web, with real citations.
- **They will not help the tactical claims** and the counts say so in advance, which is better than
  discovering it per claim.
- **The concept/claim split is the next design question**, and it explains a result that had been
  filed as a retrieval problem for two experiments.

## Honest limitations

- **Three books, all pre-1930.** Their chess is sound and their vocabulary is a century old.
- **No entry drawn from a book has been read against its source page.** The locator makes that
  possible for the first time and nobody has done it.
- **The concept/claim diagnosis is an inference from nine refusals**, not a measurement. The test
  would be building two concept entries and seeing whether they succeed where the claim keys failed.
