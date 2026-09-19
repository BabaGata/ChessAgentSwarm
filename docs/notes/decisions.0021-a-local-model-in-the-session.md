---
id: cas-adr-0021
title: 'ADR-0021 — A local model in the coaching session, checked, never the only voice'
desc: 'The session gains a model-written summary, follow-up questions and practice positions; every model sentence is checked against its source and the template report still follows in full.'
updated: 1789862400000
created: 1789862400000
---

# ADR-0021 — A local model in the coaching session

**Status:** accepted · **Date:** 2026-09-19 · **Builds on:**
[[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]] · **Design:**
[[design.narrated-session]] · **Evidence:** [[experiments.e92-narrated-session]]

## Context

The delivered `coach` ran no model: the report was templates and the prober was off. The author asked
for the model to write the results, answer follow-up questions, and for the prober to be used
practically.

## Decision

- The model writes one or two sentences per planned finding from a fact sheet built from the
  measurement, kept only if no number, move or square is absent from the sheet and novelty is under
  0.45. The summary is printed above the **full template report**, labelled as the model's.
- Follow-up questions are answered from the report, checked the same way; a question asking what a
  chess idea *is* goes only to the book graph (`answering`), with attribution; otherwise a fixed
  refusal.
- The prober's move check becomes practice from the player's own games. It records answers and
  changes no finding (D10 open).
- Each part can be switched off and degrades to the previous session with one line saying why.

## Alternatives rejected

- **Model writes the whole report.** E92's whole-report summary was wrong in 3 of 8 read by hand
  while passing the check; the report stays the auditable artefact.
- **Model answers chess questions itself.** R-03; E92's first run produced a wrong definition that
  passed the check.

## Consequences

The session now uses a local model (C1 holds: 1.9 GB, ~8 s per summary, ~4 s per answer). Residue:
a sentence that reverses a relation using the source's own words passes the check (1 in 8 in E92).

## Reopen when

A check that can compare relations, not only vocabulary and numbers, exists; or a reader audit of the
shipped summaries finds more than 1 in 8 wrong.
