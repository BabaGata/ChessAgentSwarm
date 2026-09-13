---
name: human-prose
description: Review and revise Croatian (or English) prose so it reads as written by this author rather than by a language model. Use when writing or editing the thesis in Masters-thesis/, or any prose that will carry the author's name. Detects the measurable tells of AI writing - em-dash asides, negative parallelism, rule-of-three, dramatic fragments - and rewrites toward the author's own measured baseline.
---

# Human prose

A language model has a recognisable prose style, and a diploma thesis carrying
the author's name should not have it. This skill measures the difference against
**the author's own writing** and closes it.

The point is not to defeat a detector. It is that the thesis should sound like
the person defending it.

## The baseline: measured, not guessed

From the author's earlier reports in `Primjeri/` (4,039 words across two
documents):

| marker | author | early thesis draft | ratio |
|---|--:|--:|--:|
| em-dash asides (`---`) | 1 per **1,010** words | 1 per **135** words | **7.5x** |
| dramatic one-line fragments | ~0 | frequent | -- |
| negative parallelism (`nije X nego Y`) | rare | frequent | -- |

Re-measure with `python .claude/skills/human-prose/check_prose.py <paths>`
before and after revising. The em-dash rate is the single most useful number:
**aim for under 1 per 600 words**, and never more than one aside in a paragraph.

## What the author's writing actually does

Read `Primjeri/MR_sah_predikcija/report.tex` and
`Primjeri/TIW_Zavrsni_Dokumentacija_AgataVujic/report.tex` before a revision
pass. The pattern:

- **Long sentences joined with `i`, `te`, `ali`, `koji`.** Clauses accumulate;
  they are not chopped for effect.
- **Causal connectives carry the argument**: `Iz tog razloga`, `S obzirom da`,
  `Dakle`, `Potom`, `Kako bi se`, `Nakon toga`.
- **Parenthetical material goes in commas or brackets**, never in dashes.
- **Concessions are spelled out**: *"iako ne moraju biti komplicirani kao što
  nije ni moja implementacija"*.
- **Plain vocabulary.** No flourish, no metaphor reaching for weight.
- **Honest endings, stated flatly**: *"Ovo se na žalost ne može baš lako
  dokazati tako da nikad nećemo saznati."*

## The tells to remove

Sourced from Wikipedia's *Signs of AI writing* and the reporting listed in
`references/sources.md`.

### 1. The em-dash aside (the strongest signal here)

The model interrupts a sentence to insert an explanation between dashes. In
Croatian this construction is genuinely uncommon, so it stands out badly.

> **Before:** Šahovski poslužitelji nude analizu partije šahovskim motorom ---
> programom koji za svaku poziciju izračuna najbolji potez i brojčanu ocjenu tko
> stoji bolje --- ali ta analiza radi nad jednom partijom.

> **After:** Šahovski poslužitelji nude analizu partije šahovskim motorom, a to
> je program koji za svaku poziciju izračuna najbolji potez i ocjenu tko stoji
> bolje. Ta analiza ipak radi nad jednom partijom.

Three ways out, in order of preference: **split into two sentences**, **use a
relative clause** (`a to je`, `koji`, `pri čemu`), or **use brackets** when the
aside is short and genuinely secondary.

### 2. Negative parallelism

`nije X nego Y`, `ne samo X nego i Y`, `X, a ne Y`. The model reaches for it to
sound balanced. Keep at most one per chapter, and only where the contrast is the
actual point.

### 3. Dramatic fragments and one-sentence paragraphs

A short sentence dropped after a long one for weight. *"I to je rezultat."*
*"Nijedan nije."* The author does not write this way. Fold the fragment into the
sentence before it.

### 4. The rule of three

Triplets of adjectives or clauses, especially when the third adds nothing.
Two is usually enough; if the third earns its place, keep it.

### 5. Colon-for-drama

`Rezultat je jasan: ...`. Occasionally fine, but the model uses it constantly.
Prefer a full stop or `Dakle`.

### 6. Bold as emphasis

Bold has a job in a thesis: terms being defined, and results. Bolding a whole
clause for rhetorical stress is a model habit. Strip it unless it marks a term
or a number.

### 7. Copula avoidance and vague significance

`predstavlja`, `služi kao` where `je` would do; `čime se naglašava`, `što
odražava širi trend`. Say the plain thing.

## Serbian words in Croatian text

`python .claude/skills/human-prose/check_croatian.py <paths>`

A model trained mostly on the larger Serbian and Bosnian web corpora slips
ekavica, Serbian lexis and the `da` + present construction into Croatian. The
script matches **whole words only**, and that is the point: the first version
used stems and flagged `detektor` as `dete`, `rečenica` as `reč`, `vremenski` as
`vreme` and `također` as `takođe`. It reported 133 hits of which about three were
real. **A checker that is wrong nine times in ten trains you to ignore it**, so
prefer a narrow pattern that misses something to a broad one that cries wolf.

Two traps worth remembering, both found this way:

- **Oblique cases are often shared.** Croatian `vrijeme` has genitive `vremena`,
  identical to Serbian. Only the nominative `vreme` is a tell.
- **A Serbian noun can be a Croatian verb.** `prevodi` is the noun *prijevod*
  in Serbian and the verb *prevoditi* in Croatian. Match the noun's case forms,
  not the bare stem.

The construction to watch for beyond vocabulary is `treba da` + present where
Croatian takes an infinitive or `da bi`.

## Procedure

1. **Measure first.** `python .claude/skills/human-prose/check_prose.py <file>`
   prints a rate per marker and points at the worst lines.
2. **Read two of the author's own pages** before editing, to load the voice.
3. **Revise the highest-density paragraphs first.** Density matters more than
   any single instance; a chapter with 30 asides is the problem, one aside is not.
4. **While revising, check the paragraph is actually clear.** These two jobs
   belong together: an aside often hides a sentence that never said its point
   plainly. If a paragraph needs two readings, rewrite it.
5. **Do not flatten the content.** Hedges, negative results and stated limits are
   the author's own voice and the thesis's argument. Remove the *mannerism*, keep
   the *honesty*.
6. **Measure again**, and rebuild whatever the prose feeds
   (`python tools/build_docx.py` for the thesis).

## What not to do

- Do not swap `---` for ` - ` or `–`. That keeps the construction and only
  changes the character; the checker counts those too.
- Do not remove precision to sound casual. Numbers, sources and qualifications
  stay.
- Do not rewrite quoted material, code, captions of code listings, or the
  author's own sentences quoted from the vault.

## Measuring against the author's own writing

`python .claude/skills/human-prose/check_style.py`

Counts, per 1000 words, the constructions that separate this project's drafts
from the author's earlier reports in `Primjeri/`, and prints both tables so the
gap is visible rather than argued about.

What her writing does **not** contain, at all:

| construction | typical draft | her reports |
|---|---|---|
| `nije X, nego Y` | 2.0 | 0.0 |
| `..., a ne Y` | 4.6 | 0.0 |
| bold run-in at the start of a paragraph | 3.1 | 0.0 |
| italics for stress on an ordinary word | 6.6 | 0.0 |
| colon inside a sentence | 8.3 | 1.1 |

What her writing does contain, and the drafts did not:

| construction | typical draft | her reports |
|---|---|---|
| `kako bi ...` (purpose clause) | 0.1 | 6.0 |
| `iz tog razloga` | 0.0 | 1.4 |
| `s obzirom da` | 0.0 | 0.7 |

The rewrite is not about hitting those numbers exactly. A text that matched a
profile perfectly would be its own kind of artefact, and some of these
constructions are legitimate in a technical chapter where they would be out of
place in a project report. The point is the direction: prefer a purpose clause
or a `jer` clause over a contrast, and let the sentence carry the emphasis
instead of the font.
