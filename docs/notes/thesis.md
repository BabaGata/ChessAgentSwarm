---
id: cas-thesis
title: Thesis
desc: 'The written thesis: structure, where each chapter draws from, and the rules that keep it from claiming more than the vault does.'
updated: 1789257600000
created: 1788780000000
---

# Thesis

The Croatian-language diploma thesis (*diplomski rad*), written in LaTeX against the FIDIT template.
Lives in `Masters-thesis/`, which is **gitignored** — nothing there is committed with the code.

**Working title:** *Roj agenata za personalizirano šahovsko podučavanje*

## The mission gap this exposed — closed 2026-09-08

M1–M7 contained **no step for writing the thesis**, and the thesis is the project's actual
deliverable. Now **M8 — write the thesis**, added to [[mission]] with
[[decisions.0018-the-thesis-is-a-mission-step]]. It serves [[vision]] success criterion 6 (a third
party can reproduce this from the vault) and constraint C5 (auditable reasoning — the thesis *is* the
audit, made external), and it moves scorecard dimension **D11**.

**It runs alongside M7, not after it.** A thesis written at the end is written from memory of the
project rather than from its record, and the gaps it finds arrive too late to fix.

## The one rule

**The thesis may never claim more than [[state]] does.** R-06 in reverse. Three consequences already
applied while drafting:

- The planner's untreated-share figure (15–23 %) is **currently withdrawn** in the product, because
  `calibration_is_stale()` fires — `INACCURACY_WP` moved 10.0 → 5.0. The thesis says so rather than
  quoting the number as live.
- The determinism claim is **split**: byte-identical on a warm cache, and *not* reproducible when the
  cache is rebuilt in a different order ([[experiments.e91-fixed-depth-is-not-reproducible]]).
- E31's headline is the **corrected** one — 76 % detection / 37 % naming across six players, not the
  pre-[[experiments.e82-move-number-rerun]] "80 / 10" from one player.

## Structure

| # | Chapter | Draws from |
|---|---|---|
| 1 | Uvod | [[vision]], `README` |
| 2 | Pregled područja | [[domain.prior-art]], [[domain.expertise-research]], [[domain.coaching]], [[domain.sources]] |
| 3 | Metodologija: projekt kao adaptivni sustav | [[process]], [[decisions.0001-adaptive-documentation-driven-process]], [[learning.lessons]], [[state]] |
| 4 | Zahtjevi i arhitektura | [[architecture]] and children, ADR-0002/0006/0007/0008 |
| 5 | Domensko znanje | [[domain.sections]], [[capacity.knowledge]], [[design.knowledge-base]], [[experiments.e63-knowledge-swarm]] |
| 6 | Implementacija | `chesscoach/`, [[architecture]] § status |
| 7 | Evaluacija | [[evaluation]], [[evaluation.expert-review]], E26/E27/E29/E31/E86 |
| 8 | Rezultati i rasprava | [[state]], E05, E20, E21, E27, E91 |
| 9 | Zaključak | [[state]], [[open-questions]] |
| A–E | Prilozi | real report from `expert-review/`, `docs/samples/sample-profile.json`, all 87 experiments, all 18 ADRs, terminology |

The chapter order puts **the process** (3) before the product (4–6) because the process is a claimed
contribution, and leads chapter 8 with the **negative result** rather than filing it under
limitations.

## The Word build

Overleaf's free tier could not build it, so the .docx is generated from the same `.tex` sources by
`tools/build_docx.py`. **The LaTeX remains the master copy**; the `.docx` is generated and hand-edits
to it are discarded by the next build. Rebuild with `python tools/build_docx.py`.

### Pandoc was tried and rejected, 2026-09-09

Pandoc 3.11 was installed and tested against the same sources. Its Word *internals* are better —
real Body Text / First Paragraph / Source Code / Table Caption / Definition styles, native Word
equations instead of pictures of equations, a live table of contents. It lost on **layout**, which is
what a thesis cover is:

- it put the **table of contents before the title page**;
- it flattened the cover to **half a page**, dropping the centring and the type sizes from
  `\begin{center}`;
- it put both logos **side by side in the middle** instead of at the page corners;
- **a table containing `\multicolumn` was dropped whole**, without a warning — the section
  catalogue disappeared from chapter 5 and the build still reported success. Caught only by counting
  `tabular` environments in the source against tables in the output, 26 against 25.

Five of those were fixable by preprocessing, and were. The cover was not: pandoc discards the
positioning, so it has to be rebuilt afterwards either way. At that point the generic tool is doing
less than the specific one, so the specific one stays.

### The heading-font trap

Both builds rendered headings in the wrong font, and the cause is worth keeping. Word's built-in
Heading styles carry `w:asciiTheme="majorHAnsi"`, and **the theme attribute wins over the explicit
`w:ascii`**. Setting `style.font.name` in python-docx therefore changes nothing on screen — the
headings keep rendering in the theme's Calibri Light beside a Times New Roman body. The fix is to
delete the four `*Theme` attributes from the style's `rFonts`, which `_force_font` now does.

### The layout the cover needs

A4 less the margins is about 700pt of height. The cover's gaps are sized to add up to that, allowing
for the title wrapping to two lines, so it fills the page instead of stopping halfway. The logos sit
in a **borderless two-column table** — a single centred paragraph cannot put one at each outer edge.

A defect in the source turned up along the way: `report.tex` held `\supervisor{... \ ...}` with a
single backslash, so both mentors ran onto one line. A lost escape from the original heredoc write,
and it would have shown in the PDF too.

Output: 15 chapters, 36 tables (one is the logo layout), 6 images, ~21,700 words, 49 references.

### Tests on the .docx, 2026-09-09

`tools/test_docx.py` -- 19 tests, run with `python -m pytest tools/test_docx.py -q`.
Written because the author reported the file would not open, and a generic Word
error message says nothing about which part disagrees with which.

**They found no corruption.** Every package-integrity test passes: the zip is
sound, every part has a content type, every relationship target exists, every
`r:id` used is declared, and -- the usual cause of a Word repair prompt -- every
table row's cells add up to its declared grid width. So the file is structurally
valid and the failure to open is environmental, most likely Protected View on a
file downloaded from a browser. **Asked, not assumed.**

What the tests do guard, beyond the package:

- **content completeness** -- chapters 1-9 then A-E, table count equal to
  `tabular` + `longtable` + `lstlisting` in the sources plus the logo row, no
  leftover LaTeX, every cited number present in the bibliography;
- **the links**, with the expectation derived from the sources rather than
  guessed: one `ch_` link per chapter, and one `ref_` link per `\cite` key.
  The first version of that test asserted a made-up threshold of 80 and failed
  at 56 -- when the real answer was 56 of 56. A test with an invented
  expectation reports a defect that is not there;
- **heading fonts are not theme fonts**, so the Calibri-Light regression cannot
  come back silently.

### What was added for the reader

- The contents list and every citation are now **internal hyperlinks** --
  bookmarks on headings and on bibliography entries, `w:hyperlink w:anchor`
  built by hand since python-docx has no API for one. The bibliography is in the
  contents too; a reader looks for it there.
- **"Motor" is now defined where it is first used.** It appeared in the
  introduction and was only explained in chapter 2, which is backwards. The
  introduction now says what a chess engine is in one clause, chapter 2 gives it
  a paragraph including what it does *not* do (it does not write the text the
  player reads), and the glossary carries it with `ocjena` and `dubina`.

### Conformance with the faculty template, 2026-09-09

`Masters-thesis/Predložak za diplomski rad.docx` states the required formatting
in prose. The build now follows it, and `tools/test_docx.py` asserts each value
so it cannot drift back.

| the template asks for | was | now |
|---|---|---|
| body Times New Roman 12, spacing **1.15**, 0 before / **6pt** after, justified | spacing 1.4, 8pt after | fixed |
| headings **Arial bold** 16 / 14 / 12, spacing 0-12 / 18-6 / 6-6 | Times New Roman 20 / 14 / 12.5 | fixed |
| figures and tables numbered **by order of appearance**, not per chapter | per chapter (2.1, 3.4) | fixed |
| captions **centred, Times New Roman 10**, "Tablica 1. Naziv" | bold, left, "Tablica 2.1: Naziv" | fixed |
| page number **in the footer, right-aligned**, arabic from chapter 1, none on the cover | none at all | fixed, via a section break |
| code in Consolas **9pt** | 8.5pt | fixed |
| **Literatura**, **Popis tablica**, **Popis slika**, **Popis priloga** | only "Izvori" | fixed |
| section numbers written **2.1.** with a trailing dot | 2.1 | fixed |
| **every figure mentioned in the text** ("Na Slici 4. prikazano je") | **no figure was referenced anywhere** | fixed |
| keywords separated by **semicolons** | commas | fixed |

**The Arial headings settle an earlier complaint.** The author reported that the
headings were in a different font from the body and read it as a defect. Half of
that was a defect -- the theme font made them Calibri Light -- and half is what
the faculty requires: Arial headings against a Times New Roman body. They now
differ *on purpose*.

### Still not conforming, and needing a decision

- **Zadatak diplomskog rada** -- the template wants the mentor's original task
  sheet bound in after the title page. It cannot be generated; a physical or
  supplied page.
- **Appendices are lettered A-E**, while the template writes "Prilozi (1, 2,
  ...)". Letters are the LaTeX convention and avoid colliding with chapter
  numbers; the template is not emphatic. Left as letters, flagged rather than
  changed silently.
- **The cover** carries faculty and department where the template lists "naziv
  studija i studijske grupe". Whether "Sveučilišni diplomski studij Informatika"
  should appear verbatim is the author's call.
- **IEEE reference formatting** is close but not audited entry by entry.

## Mechanics

- `report.tex` — preamble and `\input` only. Chapters in `Poglavlja/`.
- **`Src/brojke.tex` holds every measured number as a macro.** No figure is typed into prose. When a
  measurement is redone, one file changes. 58 macros, each with its source note in a comment.
- `listings`, not `minted` — minted needs `--shell-escape`, which Overleaf makes awkward.
- `parskip`, because the class sets `\parindent` to 0 and blank-line paragraphs otherwise run together.
- No LaTeX toolchain on this machine; **the PDF has never been produced.** A script checks labels,
  citations, macro definitions and environment balance, and the `.docx` build is the second check —
  it parses the same sources and fails loudly on anything it cannot read.

## Open

- The **supervisor field is the template's default** and needs the real names.
- Two figures exist (the scorecard trajectory and the layer diagram). Candidates for more, each
  already measured: split-half agreement, the cost profile cold against warm, and the strength
  estimate against actual rating.
- Chapter 7–8 numbers will move when the detector regeneration now running lands. That is one edit to
  `Src/brojke.tex`.
- The system's own output is **English**; the thesis says so rather than translating the sample
  report. Whether to translate the product is not decided.
