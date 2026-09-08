---
id: cas-thesis
title: Thesis
desc: 'The written thesis: structure, where each chapter draws from, and the rules that keep it from claiming more than the vault does.'
updated: 1788825600000
created: 1788780000000
---

# Thesis

The Croatian-language diploma thesis (*diplomski rad*), written in LaTeX against the FIDIT template.
Lives in `FIDIT_template_hrv/`, which is **gitignored** — it syncs to Overleaf separately, so nothing
here is committed with the code.

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

## Mechanics

- `report.tex` — preamble and `\input` only. Chapters in `Poglavlja/`.
- **`Src/brojke.tex` holds every measured number as a macro.** No figure is typed into prose. When a
  measurement is redone, one file changes. 58 macros, each with its source note in a comment.
- `listings`, not `minted` — minted needs `--shell-escape`, which Overleaf makes awkward.
- `parskip`, because the class sets `\parindent` to 0 and blank-line paragraphs otherwise run together.
- No LaTeX toolchain on this machine; **compilation is Overleaf-only and unverified locally.** A
  script checks labels, citations, macro definitions and environment balance instead.

## Open

- The **supervisor field is the template's default** and needs the real names.
- Figures beyond the scorecard trajectory are not drawn yet; candidates are the split-half agreement,
  the cost profile, and the strength estimate against actual rating.
- Chapter 7–8 numbers will move when the detector regeneration now running lands. That is one edit to
  `Src/brojke.tex`.
- The system's own output is **English**; the thesis says so rather than translating the sample
  report. Whether to translate the product is not decided.
