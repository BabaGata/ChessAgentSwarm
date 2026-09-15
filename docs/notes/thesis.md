---
id: cas-thesis
title: Thesis
desc: 'The written thesis: structure, where each chapter draws from, and the rules that keep it from claiming more than the vault does.'
updated: 1789430400000
created: 1788780000000
---

# Thesis

The Croatian-language diploma thesis (*diplomski rad*), written in LaTeX against the FIDIT template.
Lives in `Masters-thesis/`, which is **gitignored** — nothing there is committed with the code.

**Working title:** *Roj agenata za personalizirano šahovsko podučavanje*

## The mission gap this exposed — closed 2026-09-08

> **Superseded 2026-09-15.** M8 was removed from [[mission]] at the author's request
> ([[decisions.0020-the-thesis-leaves-the-mission]]). What follows is kept as the record of why it
> was added.

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

### Resolved by the author, 2026-09-09

- **Appendices are numbered, not lettered** -- "Prilog 1" through "Prilog 5",
  as the template's "Prilozi (1, 2, ...)" asks. Headings inside an appendix are
  now **unnumbered**: numbered "3.1." there would be indistinguishable from
  section 3.1 of the body, and nothing cross-references them. Appendix bookmarks
  use an `app_` prefix for the same reason -- numbered 1..N like the chapters,
  `ch_3` would otherwise name two different places.
- **The cover carries "Sveučilišni diplomski studij Informatika"** in place of
  the department. Worth recording *why* this was ever wrong: the LaTeX class in
  `Src/template.cls` is the author's own, made a few years ago, so its
  `\department` field was never authoritative. **The faculty template is the
  authority; the LaTeX class is not.**

### Still open

- **Zadatak diplomskog rada** -- the template wants the mentor's original task
  sheet bound in after the title page. Deferred by the author; it is a supplied
  page rather than something the build can produce.
- **IEEE reference formatting** is close but not audited entry by entry.

### The prose read as model-written, 2026-09-09

The author noticed it from one construction: an explanation inserted into a
sentence between dashes. She was right, and the size of it is measurable.

| | author's own reports | thesis before | thesis after |
|---|--:|--:|--:|
| em-dash asides per 1,000 words | **0.0** (4 in 4,039 words, two in a caption) | **8.6** | **0.1** |
| one aside every ... words | ~1,010 | **116** | 8,308 |

Everything left is a table cell where the dash means "nothing here".

**The global skill `~/.claude/skills/human-prose/` was built for this**, with `check_prose.py` to
measure and `references/sources.md` for where the tells come from. The research
was done in English deliberately, since the material is far thicker there, and
the sentence-level habits carry over.

Two findings worth keeping:

- **The em dash is a stronger tell in Croatian than in English.** In English it
  is merely dense; the aside is a normal English construction. Croatian writers
  use a comma, a relative clause (`a to je`, `pri čemu`) or brackets, so the same
  habit reads as foreign. That is why it was the first thing noticed.
- **Every source says none of these markers proves anything**, and academic prose
  is false-positive-prone: formal tone, hedging and symmetry look the same either
  way. So the target is not to defeat a detector. It is that the thesis reads
  like the person defending it, measured against **her own baseline**.

The rule that kept the revision honest: **remove the mannerism, keep the
honesty.** Hedges, negative results and stated limits are the argument, not
style, and none were touched.

### Other changes in the same pass

- **One font throughout.** The template asks for Arial headings against a Times
  New Roman body; the author asked for Times New Roman everywhere, which
  overrides it. The test now asserts the override rather than the template.
- **Sažetak and Abstract** are left-aligned and share one heading shape.
- **The task sheet is embedded.** `AgataVujic_Zadatak_za_diplomski_rad.pdf` is
  rendered to an image and placed after the cover, since Word cannot hold a PDF
  as a page. It is a signed scan either way, so nothing is lost by the text not
  being selectable.

### Grounding pass, 2026-09-09

Every claim about the code, the numbers and the literature checked against the
repository, the vault and the sources. Script:
`scratchpad/verify_code_claims.py` shape, re-runnable.

**What was wrong.** One thing, and it was a real fabrication: the implementation
chapter said **"Deset detektora"** and then named nine, and `tactics.py` has
nine. Corrected to *devet*.

**What had drifted**, because the project kept moving while the thesis was
written: lines of code 23,235 → 24,170, tests 1,800 → 1,847, vault notes 169 →
173, lessons 60 → 62, ADRs 18 → 20. All live in `Src/brojke.tex`, so it was one
file. Appendix D gained the two missing ADRs so its list matches its count.

**What held.** Every module name, CLI command, motif name and constant quoted in
the thesis exists in the repository with the quoted value: the error thresholds
(5.0 / 17.5 / 30.0), `MAX_PRIORITIES = 3`, `NO_CHANGE_RATIO = 0.58`, both
strength fits including the corrected blitz intercept, the win-probability
constant, and `calibration_is_stale`. Every headline result figure traces to its
experiment note.

**The honest qualification about the bibliography.** It mixes two kinds of
source, and the difference matters at a defence:

- sources the **project actually read**, recorded in [[domain.sources]] and
  [[domain.expertise-research]] with an evidence class -- the chess, coaching and
  expertise literature, and the five prior-art projects;
- **standard background added while writing chapter 2** -- rating systems (Elo,
  Glickman), intelligent tutoring (Bloom, VanLehn, Corbett, Piech), multi-agent
  and LLM work (Erman, Nii, Wu, Hong, Qian, Park, Ji, Lewis), chess AI (Silver,
  McIlroy-Young), and statistics (Barnett, Efron, Cohen, Nosek, Spearman).

The second group is ordinary scholarship rather than a problem, and the specific
findings attributed to them were checked rather than assumed: Chase & Simon's
volume and pages, Chabris & Hearst's 5.02 against 6.85 blunders per 1,000 moves,
and Hambrick's 34 % of variance in chess, which also confirmed the journal,
volume and page range. **The author should skim that second group before the
defence**, since they are the citations she did not read during the work.

### Serbian in Croatian text

`check_croatian.py` added to the skill. Three genuine `treba da` + present
constructions found and rewritten; no Serbian vocabulary survived.

The lesson from building it is worth more than the result. The first version
matched stems and reported **133 hits of which roughly three were real** --
`detektor` flagged as `dete`, `rečenica` as `reč`, `vremenski` as `vreme`,
`također` as `takođe`. Narrowed to whole words with explicit inflections, it
reports what is actually there. Two traps it now encodes: **oblique cases are
often shared** (Croatian `vremena` is identical to Serbian, only nominative
`vreme` is a tell), and **a Serbian noun can be a Croatian verb** (`prevodi` is
*prijevod* in Serbian, *prevoditi* in Croatian).

### Croatian chess terms, 2026-09-12

The author noticed `vilica` for *fork* and was right: it is the English word
translated literally. Checked against Croatian sources rather than guessed.

| term | was | now | source |
|---|---|---|---|
| fork | vilica | **rašlje** | Chess.com's Croatian lesson is titled *Rašlje / dvostruki napad*; Croatian chess writing uses *rašlje* for one piece attacking two |
| passed pawn | prohodni pješak | **slobodni pješak** | the standard Croatian term |
| middlegame | sredina igre | **središnjica** | also the word the author used in her own earlier report |

**Confirmed correct and left alone:** `vezivanje` (pin), `otkriveni napad`
(discovered attack), `uporište` (outpost), `rupa` (hole -- Croatian sources
define an outpost as a square that is "a hole for the opponent"), `otvorena
linija`, `izolirani`/`zaostali`/`udvojeni pješak`, `rokada`, `završnica`.

**One term could not be verified:** `nabadanje` for *skewer*. Croatian chess
writing online is thin on it and no authoritative source was found either way.
Left as it is and flagged rather than changed on a guess.

### Why every page number in the contents read 1

`w:bookmarkStart` was being inserted at index 0 of the paragraph, which puts it
**before `w:pPr`**. The properties element must be the first child of a
paragraph, so Word discarded the bookmark on open, every `PAGEREF` lost its
target, and each one fell back to its placeholder. Fixed by inserting after
`w:pPr`; all 140 bookmarks now sit in a valid position.

The numbers still need one refresh in Word (`Ctrl+A`, then `F9`) the first time,
which `w:updateFields` asks for.

### Other format fixes

- **Space around tables.** A table carries no space before or after it in Word,
  so a thin empty paragraph now sits on each side. The template asks for this
  too: *"Ispred tablice ostavite jedan prazan redak"*.
- **`Opcije-za-kod.docx`** offers six ways of formatting the code blocks on the
  same snippet, plus three of them repeated on a long JSON block where they
  differ most. Built by `tools/code_style_options.py`; once chosen, the pick
  goes into `docx_writer._listing`.

### Why the page numbers stayed at 1 after the bookmark fix

The bookmark placement was one of two bugs, and fixing it was not enough.

**A field spans several runs.** `begin`, `instrText`, `separate`, the cached
result and `end` were all packed into a single `w:r`, which is malformed. Word
kept showing the cached placeholder and never recomputed the field. Each part
now sits in its own run, which is what the format requires.

Worth noting for next time: the footer's `PAGE` field was built the same wrong
way and *did* render, so "it works here" said nothing about the other one. The
difference is that `PAGE` has no `separate` and no cached result, so there was
nothing for Word to fall back to.

The numbers still want one refresh in Word the first time (`Ctrl+A`, then `F9`);
`w:updateFields` asks for it but Word does not always oblige.

### Space after tables, done properly

The first attempt added empty paragraphs on both sides. That was wrong twice
over: an ordinary paragraph already carries 6pt after it, so above the table the
gap was that 6pt **plus a whole empty line**, while below it there was nothing.

Word gives a table no space of its own, so the space is now **owed to the next
paragraph**: `_table` records a debt and whichever paragraph comes next settles
it with 12pt of `space_before`. No empty paragraphs anywhere.

The wiring had a bug worth recording: a blanket string replacement put the
"clear the debt" line into the block dispatcher as well as the constructor, so
the table set the debt and the dispatcher cleared it one line later, before any
paragraph could collect. **A replacement matched on a common line hits every
copy of it**, which is the hazard of patching by text rather than by edit.

### Code listings: option 6

The author chose the rule down the left edge over very light shading
(`FAFAF8`, rule `808080`). Listings are now **plain shaded paragraphs rather
than a one-cell table**, which has a second benefit beyond looks: a table is
held together, so a long listing was pushed whole onto the next page, while
paragraphs break across pages normally.

`test_table_count_matches_the_sources` had to change with it -- listings are no
longer tables, so the expected count is tabulars plus the logo row.

### Page numbers: the field was never the problem

Three fixes were made to the PAGEREF fields before this round (bookmark after
`w:pPr`, one run per field part, `w:updateFields` in its schema position) and
the contents still read "1" everywhere. The measurement that settled it was to
open the built file in Word over COM and ask each field what it resolved to.

The first probe said **3** for all 91 fields, which looked like a worse bug. It
was the probe: `Fields.Update()` was called before `Repaginate()`, so every
reference resolved to the page the field itself sits on. The order has to be
**repaginate, update, repaginate**, and with that the numbers were correct all
along -- 1 through 63, ascending.

So the fields were right and the *cache* was wrong. A field carries an
instruction and a cached result Word shows until it recalculates; the builder
can only write the instruction, so it cached "1". Anyone opening the file
without letting Word update fields saw "1".

`tools/paginate.py` now asks Word once after each build and writes the real
numbers into the cache, and `build_docx.py` calls it. Two tests guard it: the
cached results must take more than ten distinct values, and they must not
decrease down the list.

That was still not enough, and the reason is the sharpest thing learned here.
The file on disk held the right numbers and the author still saw "1" on every
line. **Word's update-on-open was undoing the fix.** `w:dirty` on each field
and `w:updateFields` in `settings.xml` had been added earlier to force a
recalculation, back when the cache was wrong; Word honours them before it has
laid the document out, resolves every reference to 1, and discards what
paginate measured. Both are gone, a third test fails if either returns, and
the check that matters is now made the way a reader makes it -- open the file,
change nothing, read the contents.

**Chapter 1 genuinely starts on printed page 1.** The front matter is its own
section and the body restarts numbering, so the first few contents entries read
1, 1, 1, 2 and that is correct, not the old bug.

A bug inside the fix is worth recording: the substitution used `match.group(3)`
for the closing `</w:t>`, but a named group in the middle of the pattern had
shifted the numeric indexes, so the closing tag was eaten and the page number
doubled -- `<w:t>11</w:r>`. Every group in that pattern is named now. The
existing test suite would have caught it on the next run, because it parses
`document.xml` and malformed XML cannot be parsed.

### "Igrači kojima nitko ništa nije rekao" — tko im nije rekao?

The author asked, and the phrase deserved it. E05 never contacted anyone: the
games of 32 players were split by date, a plan was built from the earlier half
and its predictions checked against the later half. Nobody was supposed to tell
them anything; there was no one in the loop at all.

Chapter 8 stated the method. The abstract, chapter 1 and chapter 9 stated only
the conclusion, and a reader who met the result there first had no way to know
what the control condition was. All three now say it: the plan was built from
older games and checked on newer ones, and no player was ever contacted or
shown a plan.

The general lesson, which is not about this sentence: **a summary that carries
a result must carry enough of the method to make the result mean something.**
Dropping the method is what made a sound finding read as a riddle.

### The word list, and what a blanket replacement costs

The author rejected nine words: objašnjavač, antiuzorci, agregira,
ponderiranje, poopćenje, atomarna, testabilni, recenzent and the unexplained
"tilt". She also asked whether "tutorski" is a Serbism.

**It is not.** *Inteligentni tutorski sustav* is the established Croatian term
for the field and is used in the faculty's own repository. It stays, and is now
glossed on first use, because nothing in the text said what it meant.

"recenzija" ran through the whole thesis, so it was replaced by script -- and
the script replaced it inside `\label{}` and `\newcommand{}` as well as in
prose. That produced labels with spaces and diacritics
(`\label{sec:stručni pregled}`), macro calls that were never defined
(`\Stručni pregledN`), noun phrases whose gender no longer agreed ("Ekspertna
stručni pregled provedena je"), and one changed fact: "Tri recenzentska
obrasca" became "Tri ocjenjivačeva obrasca", losing that ADR-0011 rests on
three filled-in **Form B/C**.

This is the same hazard as the table-spacing replacement two rounds ago, and
the second time it has cost a repair round. The rule that follows: **a
replacement that runs over LaTeX source must be anchored on the sentence, not
on the word**, and identifiers must be excluded outright. A checker now runs
before every build and fails on a `\ref` without a label, an undefined macro,
or a label that is not ASCII and space-free.

### Three passages rewritten because they did not explain themselves

- *tilt* was a borrowed poker word standing alone in a table cell. It now says
  "igranje u ljutnji nakon poraza".
- The abstract stated the 92 % control-group result without its mechanism. It
  now names regression to the mean and says what follows: a target is set on a
  weakness measured when it was extreme, re-measuring returns a lower value
  even when nothing changed, so an improvement without a control group says
  nothing.
- "Nazivi vještina i proces obrnuti su u odnosu na standardni okvir, jer
  izvještaj čita igrač, a ne inženjer sigurnosti" alluded to a mismatch instead
  of stating it. It now says which name maps to which level in Rasmussen, and
  that the names were chosen for a chess player rather than for that
  literature.

### An outside read of the thesis, and what survived checking

The author had the finished document reviewed for signs of AI authorship. The
review's own conclusion was that the *research* is clearly human and the
*prose* is not, and that the citations deserved a closer look than the prose
did. Both halves were acted on.

**Five citation findings, checked against sources rather than memory.**

- **Charness (1981) was the wrong reference** for the nine-year longitudinal
  study of a player going 1600 → 2300 without searching deeper. The study is
  **Charness (1989)**, "Expertise in chess and bridge". The vault had it right
  in [[domain.expertise-research]]; the thesis had it wrong, which means the
  error entered when the note became a chapter. Fixed, and `charness1981search`
  is no longer cited anywhere.
- **"oko 300 000 uzoraka" was "at least 300,000".** The Gobet & Charness
  chapter says *"at least 300,000 chunks are required to reach grandmaster
  level"*, verified by pulling the PDF and reading the sentence. Wording
  corrected, and the figure is now attributed to that chapter alone rather than
  co-cited with Gobet & Simon (1998), which is where the chunking claim
  belongs.
- **Glickman (1999) is the method, not evidence that Lichess uses it.** The
  Lichess FAQ states it directly, and is now cited alongside.
- **Spearman–Brown needs Brown.** Spearman (1910) alone was cited for a formula
  that is half Brown's; Brown (1910) added.
- **"Nijedan sustav ne mjeri ispravnost savjeta"** was scoped to five projects
  in the text but nowhere said which five, how they were found, when, or what
  counts as measuring correctness. All four are now stated, along with the fact
  that the repositories may have changed since.

The general lesson: **a claim that was right in the vault can still be wrong in
the thesis.** Three of these five are transcription damage, not research
damage, and none of them would have been caught by re-reading the chapter,
only by going back to the source.

### Matching the author's register, measured rather than argued

The reviewer named the prose tells without naming their frequency, so the
frequencies were counted, in the thesis and in her two earlier reports in
`Primjeri/`. The gap was not subtle.

| per 1000 words | thesis before | her reports | thesis after |
|---|---|---|---|
| `nije X, nego Y` | 2.0 | 0.0 | 1.5 |
| `..., a ne Y` | 4.6 | 0.0 | 3.7 |
| bold run-in | 3.1 | 0.0 | 1.6 |
| italics for stress | 6.6 | 0.0 | 2.1 |
| colon inside a sentence | 8.3 | 1.1 | 6.0 |
| `kako bi ...` | 0.1 | **6.0** | 0.7 |
| `iz tog razloga` | 0.0 | **1.4** | 0.1 |
| `s obzirom da` | 0.0 | **0.7** | 0.4 |

Her hallmark is the purpose clause. She explains why something was done inside
the sentence that says it was done, and she never reaches for a contrast to
make a point land. The thesis did the opposite everywhere. The rewrite pushed
chapters 1, 2, 3 and 9 and the abstract most of the way across, and took the
worst of it out of 4 to 8.

It was **deliberately not pushed to zero**. A document that matched a profile
exactly would be its own artefact, and some of these constructions are
ordinary in a technical chapter where they would be out of place in a project
report. `check_style.py` in the human-prose skill prints both tables so the
next pass argues from counts rather than impressions.

### What was left alone, and why

- **Experiment count (87 stated, IDs up to E91).** The author asked to leave it
  until the detector regeneration running in another session lands, since the
  numbers will move anyway.
- **One reviewer of twelve, who is the author.** This is a real methodological
  limit and the thesis already states it three times, in the evaluation
  chapter, in the results and in the conclusion. Nothing to fix in the writing.
- **Hambrick et al. on one third of the variance.** Checked; the citation
  supports the sentence.
- **Stockfish 18 and the CC0 licence of the Lichess database.** Both check out.

### The methodology chapter had no literature at all

The author asked whether adaptive systems were sourced anywhere. They were not.
"Adaptivni sustav" appeared six times across the abstract, chapter 1, chapter
3, chapter 9 and ADR-0001, and chapter 3 -- the chapter whose whole subject is
the process -- carried exactly **one** citation, for Dendron, the note-taking
tool. The framework that shaped the entire project was presented as if it had
been invented here.

It was not invented here. The five structures are **VMCL** (vision, mission,
capacity, learning) from Derek and Laura Cabrera, which the author learned from
the Cabrera Lab podcast. Three sources now carry it:

- **Cabrera & Cabrera (2018), *Flock Not Clock*** (Plectica Publishing) -- the
  book that sets VMCL out. The title is the argument: an organisation is a
  flock following simple rules, not a clock assembled from specified parts.
- **Cabrera, Cabrera, Powers, Solin & Kushner (2018)**, *European Journal of
  Operational Research* 268(3), 932--945 -- the peer-reviewed statement of
  VMCL, which matters for a thesis in a way a book does not. Verified by
  pulling the PDF: *"In VMCL, the word capacity refers to the ability to
  execute the mission."*
- **Cabrera, Cabrera & Powers (2015)**, *Systems Research and Behavioral
  Science* 32(5), 534--545 -- DSRP, the systems-thinking theory underneath.

**Two adaptations are now stated rather than hidden.** The project has a fifth
structure, *stanje*, which VMCL does not: in an organisation the people doing
the work are the feedback on the real state, and a one-person project needs a
written record to play that part. And VMCL's *capacity* is mostly culture,
meaning shared mental models across a group, which does not exist here, so it
was narrowed to agents, tools and recorded knowledge.

The contribution list in chapter 1 now says the project *applies* VMCL rather
than implying the framework is part of the contribution. The application to a
one-person research project is the contribution; the framework is Cabrera's.

This is the second finding of the same shape as the wrong Charness reference:
**the thesis stated something the vault knew and the chapter did not cite.**
Worth a standing check before submission -- every framework, metric and
taxonomy the thesis leans on should either carry a source or be claimed as
original on purpose.

### Every framework and measure, audited the same way

After the VMCL finding the same question was put to every named framework,
method and measure in the thesis: does a citation stand in the same paragraph,
and if not, is that on purpose? Fifty-odd terms were scanned paragraph by
paragraph, false positives discarded by hand.

**Five were used as established and cited nowhere.**

| what | now cited |
|---|---|
| win-probability formula | the Lichess accuracy page, which publishes it |
| ACPL | same page |
| Wilson intervals | Wilson (1927), JASA 22(158), 209--212 |
| the domain/student/tutor division of an ITS | Anderson, Boyle & Reiser (1985), *Science* 228 |
| architecture decision records | Nygard (2011), the essay that introduced them |

**Four are this project's own and now say so.** An absent citation reads as a
missing one unless the text claims the thing as original, so each of these got
a sentence: the nine-phase work cycle (each phase answering a way the work had
already gone wrong), the evidence classes (no such scale exists for chess
knowledge), the seven families of measures (no settled set exists for judging
chess advice), and the confidence classes (each promotion condition added after
a measurement showed what got through without it).

**One was already right.** Empirical-Bayes shrinkage carries Efron & Morris
(1975) where the method is explained in chapter 8, so its mention in chapter 3
needs nothing.

### Why the process exists, in the author's words and in the literature

The thesis gave two reasons for the process and was missing the one that
actually caused it. The author's observation, from working this way: **in long
sessions on projects with no known recipe** -- unlike, say, a web shop in a
familiar framework -- **the model gets stuck circling one problem, or takes a
direction that is locally sensible and walks the project away from what was
wanted.**

That is a working impression rather than a measurement made here, and the
chapter now says so before citing four papers that measured the surrounding
effects:

- **Arike et al. (2025)**, AIES 8(1), 192--203 -- goal drift rises with context
  length, because the model grows more prone to matching patterns in the
  context than to the task it was given. This is the closest published match to
  the observation.
- **Wang et al. (2026)**, arXiv:2604.11978 -- 3100+ trajectories, four domains:
  success falls as the horizon lengthens and the failure modes themselves shift
  with duration.
- **Liu et al. (2024)**, TACL 12, 157--173 -- a fact in the middle of a long
  context is used less well than one at either end, so a goal stated at the
  start of a long session loses weight.
- **Huang et al. (2024)**, ICLR -- without external feedback a model does not
  reliably correct its own reasoning, and sometimes makes it worse.

The four together make the design argument the chapter had been making without
support: **drift cannot be fixed by asking the model whether it has drifted.**
The correction has to be external and written down. That is exactly the three
properties the process has -- the goal lives outside the conversation and is
re-read at the start of every unit of work, alignment against the vision is
answered in writing before a plan runs, and a measurement is the gate a claim
passes to enter the state note.

Worth keeping in mind: this is the strongest justification in the thesis for
the methodology chapter existing at all, and it was missing because it was the
author's own reasoning rather than something already written in the vault.

### Five numbers were missing from the document, and the build was green

The second review found "Kappa", "Korekcija", "KorekcijaTrazena",
"PoboljsanjeBezTretmana" and "CiljTrazio" printed as words where numbers
belong, and read them as an unfinished template. They were a **converter bug**,
and the same one five times.

Every one of them sits inside `$...$`. `InlineParser._math` renders inline maths
by mapping the symbols it knows and then deleting every remaining backslash, so
`\Kappa` lost its backslash and arrived as the word. Outside maths the walker
expands macros as it meets them, which is why nothing else was affected and why
this was invisible for weeks. Macros are now expanded before any backslash is
touched.

A second, smaller thing fell out of the same line: the symbol map consumed the
space after a named command, so `\kappa = \Kappa` rendered as "κ= 0,74". The
space after a command name only terminates the name in LaTeX; on the page it is
a word space.

**The test that should have existed now does.** It reads every
`\newcommand` name out of `Src/brojke.tex` and fails if any of them appears as
a bare word anywhere in the document, paragraphs and table cells alike. Two
names are excluded by hand -- *Pouzdanost* and *Utemeljenost* are also ordinary
Croatian words that open sentences in the prose, so finding them proves
nothing. The lesson generalises past this bug: **the suite checked that content
was present and never that a placeholder was absent.**

### Two claims the thesis could not support

- **Stockfish determinism.** Chapter 2 said the engine gives the same answer
  for the same position at the same depth, and chapter 7 measures it giving
  −5 cp cold and −24 cp after other positions, because the transposition table
  carries state between calls. The thesis was contradicting itself across five
  chapters. Chapter 2 now states the limit where the claim is made rather than
  pointing forward to it.
- **"To slaganje je dokaz da je dijagnoza bila točna."** Two independent
  estimates agreeing is consistency, not proof of correctness. Softened to what
  it actually shows: two measurements that do not lean on each other, giving
  the same answer.

### Tooling named, and one record taken out of the appendix

The thesis said "a development environment with a language model" and never
named it. It now names Claude Code and the Claude family, **without a version**:
only today's session logs survive on disk, and they cannot speak for July and
August, so naming a specific model would be asserting more than can be checked.
The author chose that wording when asked. The system's own local models can be
named exactly, because they are pinned in the source, so they are.

ADR-0018, the record placing thesis writing inside mission step M8, is out of
the appendix table at the author's request. The register still holds
`\BrojADR` records and the intro now says the table lists those concerning the
system, so the count stays honest.

### All 63 sources, audited one by one

A citation map was generated from the sources themselves -- every bib key
against the sentence it supports -- so the audit is complete by construction:
**no entry in `ref.bib` is without a citation and no citation is without an
entry.** Then each was given a status by how far the check actually went:
claim read in the source (18), bibliographic record matches but the sentence
was not compared against full text (31), software or data (12), and two
findings fixed on the spot.

**Two real errors.**

- **"Charness i suradnici (1996)" was named in the text with no entry in the
  bibliography.** The claim itself is exact: Gobet & Charness (2006) report it
  word for word. The 1996 study (Charness, Krampe & Mayr, in Ericsson's *Road
  to Excellence*, 51--80) was added and cited.
- **Hambrick: "oko trećine varijance" → "oko trećine pouzdane varijance".**
  The source says *reliable* variance; dropping the word made the claim
  stronger than its source.

Three rows carry work the author has to finish, all of the same kind -- record
correct, sentence not compared with full text: Chabris & Hearst's 5.02 and 6.85
blunders per thousand moves, the strength of "slabo se prenose" in Sala &
Gobet, and a page number for the Capablanca ordering. Embrey has no year.

The audit is published as a page rather than buried here, because it is a
checklist to work through rather than a record to keep.

### Claim strength: what the evidence settles, and what it does not

The same reviewer's sharper criticism was not about AI at all. **The thesis was
more ambitious than its evidence**, and in one specific way: it demonstrated a
carefully built, heavily measured system, and then let the reader carry that
carefulness over to a question it never answered -- whether the advice is any
good for a player.

Five changes, in order of how much they matter.

- **Eighty-four players are a sample, not a population.** Every "izmjereno
  prema populaciji" was quietly borrowing the implication of a wider group to
  generalise to, which this project does not have. Renamed throughout to
  *referentni uzorak*, keeping "populacija" in the three places where it really
  means the wider group. Chapter 6 now says so outright.
- **A table of IP1--IP6 with a "Nije utvrđeno" column.** This is the single
  most useful thing added. Each research question gets its experiments, what
  the measurements establish, and what they cannot -- that the rapid held-out
  result rests on seven players, that ranking by cost was never shown to
  improve learning, that the progress check has an indication and no power
  (p = 0.12).
- **The expert review is a pilot and now says so in its own heading.** One
  reviewer, one player of twelve planned, the reviewer being the author. What
  follows from it is a list of defects it found, not a judgement of advice
  quality.
- **Multiple comparisons named.** With 87 experiments, each comparing several
  properties, phases and subsets, something will look significant on its own.
  The defence used was replication and a held-out set, **not** a formal
  correction; the thesis now says that and says p-values here are descriptive
  rather than confirmatory.
- **The conclusion separates the two deliverables.** It opens by saying they
  are not equally supported: a working prototype, and a measurement framework
  whose findings are better supported and probably transfer beyond chess. "To
  je prototip koji radi, a ne provjeren trener."

The lesson worth keeping: **a thesis full of honest sentences can still make a
dishonest impression**, if nowhere in it does a reader find the two lists side
by side.

### Numbered lists were one running sequence

The author found chapter 2's four differences numbered 18 to 21. Word's
built-in **List Number** style points every numbered paragraph at a single
`w:numId`, so each list carried on from where the last one stopped. Each
`enumerate` now gets its own `w:num` over the same abstract definition with a
`startOverride`, which restarts the count without changing how the list looks.
Verified in Word, list by list: all nine start at 1. A test fails if the number
of numbering instances stops matching the number of `enumerate` environments.

### The systematic claim pass

Two scans, run over every sentence outside code and tables.

**Claim-strength markers** -- proof verbs, guarantees, absolute quantifiers,
sweeping generalisations -- returned 59 sentences. Most were exact rather than
strong: "nijedan od pet pregledanih sustava" is a count, and "model nikada ne
vidi partije" is a property of the code. Five needed work:

- "To je najjači dostupan **dokaz** da je odluka ispravna" -- two projects
  agreeing is agreement, not a measurement. Reworded, and a missing full stop
  before it found in passing.
- "svaki sustav koji izmjeri slabost, propiše lijek i ponovno izmjeri izgledat
  će uspješno" -- true only without a control group, which was the whole point
  and was left implicit. The condition is now in the sentence, in all four
  places it appears including the English abstract.
- "potvrđeno na nepoznatim igračima" -> "vrijedi i na igračima na kojima
  sustav nije građen".
- "praznine (proces) do kojeg podučavanje sadržajem **nikada** ne dopire" ->
  "teško dopire". That was design rationale, never measured.
- A double "će" introduced by an earlier edit of mine.

**Numbers outside macros.** The project's rule is that every measured number
lives in `Src/brojke.tex`, so a literal in prose is either not a measurement or
has drifted from the one that is. The scan is clean apart from figures quoted
from cited literature (1600, 5,02, 6,85) and rating-band examples, which is
what it should be.

### Length

47 pages without appendices before this round, 46 after trimming the L-039
retelling that chapter 8 already tells in full with the numbers. The rulebook's
floor is 40 and the author's target is about 50, so the main text sits inside
the range and closer to the target than to the floor. The bulk a reader
notices is elsewhere: 11 pages of appendices and 8 of bibliography and lists,
neither of which counts toward the 40.

### The reviews, turned into a skill

Three outside reviews found, between them, a wrong reference, five numbers that
never reached the page, a contradiction spanning five chapters, and a document
more certain than its evidence. None of that was found by reading harder; it
was found by asking the same questions in the same order. That order is now
the global skill `~/.claude/skills/thesis-review/` (kept out of the repository), with a
checker that runs the mechanical half from the repository root.

Eight automated checks, each traceable to a defect a reviewer actually found:
citation map complete in both directions, a year in brackets with no cite,
macro names printed as words, measured numbers written as literals,
claim-strength markers, **claims missing their qualifier in the same
paragraph**, objected-to vocabulary, and pages against the 40-page floor.

The paragraph-pair check is the interesting one. It encodes the contradictions
directly: a sentence about the engine giving the same answer at the same depth
must have "transpozicij" or an explicit caveat nearby; the
regression-to-the-mean generalisation must carry its "no control group"
condition. That is how a five-chapter contradiction becomes a one-line rule.

Its first run found five things. Two were real -- the conclusion's second
paragraph made the general claim without its condition, and `sec:populacija`
was a label left behind when the heading was renamed two rounds earlier. Two
were the check's own false positives, fixed in the same pass, per the standing
rule that a checker wrong nine times in ten gets ignored. One was borderline
and left.

The skill also records what no check can do -- whether a citation supports
*this* sentence, whether the process has crowded out the evidence, whether a
result is a pilot -- and the judgement calls already made, so they are not
re-argued each round.

**Full round after the fixes:** every automated check clean, 35 tests pass, 0
Serbisms, 0.2 em-dash asides per 1000 words against the author's own 1.0, 46
pages without appendices.

### Did the control group simply get better?

The author asked the right question about the headline result: if those players
improved in the window, the 92 % might be real progress the system cannot see.

**They did improve, and the project had already measured it.** E06 computes
rating change per player from the PGN Elo headers over the same date split.
Over 38 players and 52 predictions, the top third gained a mean of **+141**
rating points; the other 26 lost a mean of **16**.

That was in the vault and in the experiment list and **nowhere in the results
chapter**, which is exactly where a reader meets the 92 % and forms the
objection. It is now a paragraph there.

Two things say the confound does not explain the finding:

- If rating gain were regression wearing a disguise, the gainers would be the
  players whose earlier rate was most inflated. That correlation is **+0.06**.
- The 26 players whose rating **fell** still met 3 of their 36 targets. Target
  meeting does not require improvement.

And what cannot be claimed: at the calibrated rule improvers meet 25 % against
8 % for the rest, but one-sided Fisher gives **p = 0.120**, so the difference
between the groups is not established. The 92 % itself was never broken down by
rating change and cannot be now -- the E05 PGN histories are no longer on disk,
and only 2 of the 32 players appear anywhere in `data/raw`.

One limitation is stated in the new paragraph because it is real: rating change
is measured over the same split as the finding, so the earlier period feeds
both. A cleaner design takes rating from before the measurement window.

Side note: `experiments/e06-progress-power/power.py` names this confound in a
comment -- "the confound's fingerprint" -- which is how the analysis was found
at all. Writing the objection into the code paid off months later.

### The 92 % was a 60-game number, and the thesis did not say so

Answering the author's rating question surfaced a larger omission. The vault's
E05 note records a rerun on 84 players × ~150 games in which drift without
coaching fell from +11.2 to +4.8 points: "the +11.2 was never a fact about chess
players. It was a fact about measuring them briefly." The thesis stated 92 % and
+11.2 as the result, with only a table row ("šest puta više podataka") hinting
otherwise.

Chapter 8 now says the 92 % is an upper bound from the least favourable
conditions and gives the deeper figure. The abstract says the 92 % came from
60-game histories and that players whose rating fell met their targets too.

The rating question itself is answered on the exact cohort: re-fetched for the
same window, mean rating change −2; players whose rating fell met 7 of 7
targets. E06's deeper-sample result is kept as the second check.

### Every stated calculation, recomputed

After the 92 % turned out to be 11 of 12, every sentence in the built thesis
that states a calculation was pulled out -- 101 of them, read from the .docx so
macros were already numbers -- and each was recomputed or traced to its note.
The 61 experiment figures in `brojke.tex` were matched against the note each
comment names: 52 matched directly, the other 9 were derived or traced by hand.
All values held; two comments named the wrong experiment.

**What did not hold:**

- **Blitz: "150 naspram 148 za pogađanje" joined two runs.** E27 measured 150
  against 157 for guessing; E29's held-out check 149 against 148. Written as it
  was, the estimate was *worse* than guessing in a sentence calling it barely
  better. Each figure now sits with its own baseline, and "pada sa 150 na 129"
  is 149, the E29 starting point.
- **Chabris & Hearst read their own data the other way.** The thesis said they
  confirm the pattern-recognition direction. Gobet & Charness, verbatim: "While
  they took this as evidence for the role of search, a more natural
  interpretation..." The data is theirs, the reading is Gobet & Charness's;
  attributed accordingly. The figures themselves (5.02, 6.85, a factor of six)
  are now verified in the source, which closes one of the three open rows in
  the source audit.
- **"Četiri sekcije od jedanaest nisu izgrađene" was stale** in chapters 3
  and 8. S1–S8 are built, S10 half, S9 and S11 not; chapter 5 had it right.
- **"Šest puta više predviđanja"** -- 57 against 13 is 4.4 times; it is the
  games that grew about sixfold.
- **"Za oko trećinu"** is 36 %; **"omjer 1,81"** from rounded 7.7 % and 4.3 %
  reads as 1.79, so it now says "oko 1,8".
- **Agreement:** 103 boda, 141 bod.

Also in `experiments.e05-natural-drift.md`, "every prediction's rate fell"
contradicted its own table (12 of 13).

Project-size counts have drifted -- code 24,170 → 24,686 lines, tests
1,847 → 1,885, notes 173 → 175 -- because the detector work continues in
another session. Left for the final pass, as the author asked.

### Brought to the submitted state

The other session had refreshed the counts and two passages on 2026-09-15 and
left appendix A on the August report on purpose. Reading every commit since
thesis writing began (32 outside the thesis) found what the text still
described as it used to be:

- **One 84-player reference**, when E84 had built three overlapping bands per
  speed (31–51 players each) on 2026-09-05, and chapter 9 still listed other
  bands as future work. The 84-player measurements stay described as what they
  were; the current reference is described alongside.
- **Uniform evidence sampling**, when 9cc480d made citations prefer instances
  that cost the player something (37 of 163 cited rows had cost nothing).
- **Missed motifs from the engine's top move**, when a motif-executing move
  within an inaccuracy of the best now counts, found exhaustively (10 → 32
  opportunities over 187 positions, missed pins 0 → 8).
- **The audit ending at E86**, when the author's marking rounds had since fixed
  the recapture-as-hanging-pawn bug (884 → 719), split fork from skewer,
  retired `out_of_book.any`, and made `moved_into_attack` require a winnable
  piece (18.4 % of 903 firings were not).
- **No context questions**, though four are asked before every analysis.

Appendix A keeps the August report and gains a second one: the author's own
60 blitz games. Her run had used `--band 1400-2000`, a band the reference does
not have, so it compared nothing with peers while saying it had (I-11). The
appendix shows the `1600-2000` re-run and states what the wrong band did.

### Bibliography trimmed, 63 to 51

At the author's request ("trenutačno ima previše toga") twelve sources that
supported no claim the thesis depends on were removed, each with its sentence:
de Groot 1965 and Gobet 1998 (Chase and Simon and CHREST carry the point),
Sala 2016 (Sala 2017 is the meta-analysis), Embrey (Rasmussen and Reason carry
the taxonomy), Maia's follow-up, Elo 1978 (the thesis uses Glicko-2), Piech
2015 (Corbett carries knowledge tracing), Hearsay-II's own paper (Nii
describes the model), ChatDev and generative agents (AutoGen and MetaGPT are
the examples), Wang 2026 on long-horizon failure (three findings remain) and
DSRP (nothing in the thesis used it). Checks pass; 48 pages without appendices.

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
