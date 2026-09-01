---
id: cas-exp-e78
title: 'E78 — Passages follow paragraphs, and the books turned out to be double-spaced'
desc: 'Chunking was a fixed 2,400-character stride, chosen when a passage only had to contain a search term. Made paragraph-aware: passages starting mid-sentence fell from 165 of 544 to 11 of 529, and the castling query stopped returning a passage about giving odds. Two of my own mistakes on the way, both caught before they landed.'
updated: 1788271200000
created: 1788271200000
---

# E78 — Chunking at the author's own boundaries

**Answers:** the P1 raised by [[experiments.e77-retrieval-ablation]] ·
**Code:** `chesscoach/books.py`, `experiments/e78-rechunk/` · **Date:** 2026-09-01 ·
**Status:** done — **fixed, migrated, and the migration was the hard part**

## Why it mattered

E77 shipped retrieval over passages cut every 2,400 characters. That stride was chosen when a passage
only had to *contain* a search term, and it is wrong for the two things the shelf is now asked to do:

- **embedding** — a passage spanning the end of one topic and the start of another has a vector that
  means neither, which is why *"why should I castle early"* returned a passage about **giving odds**;
- **quoting** — a passage beginning *"ack would be lost, as calculation easily shows"* cannot be shown
  to a player, and showing the text is the whole point of quoting a book.

## The books are double-spaced, which made the first fix a no-op

Splitting on a blank line is correct for ordinary prose and did nothing here. Measured, the newline
runs are:

| book | run lengths |
|---|---|
| Capablanca | **2 × 2,783**, 4 × 1,637, 6 × 10 |
| Ed. Lasker | **2 × 8,574**, 4 × 2,271, 6 × 90 |
| Staunton | **2 × 9,706**, 4 × 1,507, 6 × 419 |

**A wrapped line ends with two newlines and a paragraph with four**, with no odd lengths anywhere. So
`\n\s*\n` split every *line*, turning 4,434 paragraphs into 4,434 fragments of at most 75 characters —
paragraph-aware chunking that looked like it worked and changed nothing.

The fix detects rather than assumes: **the wrap is the most common run length and a paragraph is
anything longer.** A text with only one run length has no wrap to contrast with, so every break is a
paragraph break — the ordinary single-spaced case.

## What it bought

| | before | after |
|---|--:|--:|
| passages | 544 | **529** |
| starting mid-sentence | 165 (30 %) | **11 (2 %)** |

And the query that motivated it:

> *"Why is it usually good to castle early?"*
> **Before:** a passage about the conventions for **giving odds**.
> **After:** Capablanca — *"White does not Castle yet. The reason is that he wants to deploy his
> forces first…"* — and Lasker — *"It is, of course, better to castle before playing P-Q3, as the
> opponent could at once play Kt-Q5 and utilise the pin…"*

The ablation is unchanged at **8 of 8 citations real, none invented**, which is the honest reading:
that metric measures provenance and was already saturated. What improved is what the passages are
*about*, which only a reader can see.

## The migration was the hard part

A `book://slug#7` locator is **positional**, so changing the division moves what every stored
citation points at — silently. The store held **32 book citations across 14 entries**.

`BookLibrary.citation_holds` is the invariant that made it visible: *does the passage a locator names
still contain the text quoted from it?* Written **before** the chunking changed, so the break would be
loud.

**Two mistakes of mine, both caught before they landed:**

1. **I measured the damage wrongly first**, pairing each definition against *every* locator
   individually and reporting **20 of 32 broken**. An entry citing three passages counted two
   failures even when its text was in the third. Measured per entry, **12 of 14** were anchored; one
   is web-sourced and legitimately so, one has no sources at all.
2. **The migration would have corrupted the store.** A first version re-anchored each source by the
   *entry's definition*, which rewrote all four of `long_think_error`'s sources to the single passage
   holding that one sentence — collapsing four distinct citations into four copies of one. That is a
   worse corruption than the stale locators it was fixing. Corrected to re-anchor each source by
   **its own** old text, resolved through the chunker that was in force when it was written; every
   source then moved to a nearby passage **in its own book**, which is what a boundary shift should
   look like.

**28 re-anchored, 3 already correct, 1 not.** The one is `hangingPawn`, whose definition now
**straddles** a passage boundary — it sat inside one old fixed-stride window and paragraph packing
split it. Reported rather than guessed at, which is the behaviour that matters: a citation pointing
somewhere plausible is the failure this exercise exists to avoid. **No endorsed entry was affected,
because none is endorsed yet.**

## Honest limitations

- **Overlapping windows would have avoided the straddling case** and are standard practice in
  retrieval. Not done, because they change locator semantics again and one straddled quote in
  fourteen did not justify it. Worth revisiting if extraction produces many more.
- **The legacy chunker now exists in the migration script** and must not spread: `chesscoach.books`
  should have exactly one way to divide a book, and the old one survives only to read old citations.
- **2 % still start mid-sentence** — paragraphs longer than the cap are split at sentence ends, and
  the descriptive notation in these books (`13.`, `P - B 5.`) fools a sentence splitter.
- **The improvement in retrieval quality is shown by example, not measured.** The automatic metric
  was already saturated, and what changed is relevance, which needs a reader.
