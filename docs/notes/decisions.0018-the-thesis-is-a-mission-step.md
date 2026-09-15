---
id: cas-adr-0018
title: 'ADR-0018 — The thesis is a mission step, and it runs alongside'
desc: 'M8 added. Writing the thesis is a measurement instrument, not a report: its first pass forced three claims in this vault to be weakened against the code.'
updated: 1789430400000
created: 1788825600000
---

# ADR-0018 — The thesis is a mission step, and it runs alongside

**Date:** 2026-09-08 · **Status:** superseded by [[decisions.0020-the-thesis-leaves-the-mission]] (2026-09-15)
**Vision link:** C5 (auditable reasoning) and [[vision]] success criterion 6 (a third party can
reproduce this from the vault)

## Context

[[mission]] steps M1–M7 build the swarm, measure it, and repeat. **None of them produces the artefact
the project is actually assessed on.** For most of the project the deliverable was unscheduled, which
is the same shape of gap V9 had before
[[decisions.0003-add-v9-dialogue-and-active-assessment]] named it: not a disagreement about
priorities, just a thing nobody had written down as work.

The gap surfaced the way it was supposed to — the author asked for the thesis to be written, the
cycle's phase 0 found no step it served, and CLAUDE.md's first hard rule (*never work off-plan
silently*) made that a thing to say rather than a thing to route around.

## Decision

Add **M8 — write the thesis**, and run it **alongside M7 rather than after it**.

The load-bearing constraint: **the thesis may never claim more than [[state]] does.** That is R-06
pointed outward — the vault's rule against describing an intended system instead of the real one,
applied to the document that leaves the building.

## Alternatives considered

**Write it at the end, as a reporting task.** Rejected. A thesis written after the work is written
from memory of the project rather than from its record, and any gap it exposes arrives too late to
fix. It also invites the failure this project has been caught by repeatedly — a claim that reads as
settled because it was written down once, never re-checked against the code.

**Leave it off the mission and treat it as overhead.** Rejected on the hard rule. Work that does not
serve a mission step should not be done; work that is obviously necessary and serves no step means
the *mission* is wrong, not the work.

**Fold it into M6 (maintain and commit).** Rejected. M6 is per-cycle housekeeping with a definition
of done measured in minutes. Burying a months-long deliverable inside it would hide it from the
progress table, which is the specific thing that let it go unscheduled for this long.

## Consequences

**What it makes easy.** Each chapter is an external audit of the notes it draws from. That is not a
hoped-for benefit — the first pass produced three corrections, all of which had read as settled here:

| what the vault implied | what the code said |
|---|---|
| the planner quotes the untreated-share range (15–23 %) to the player | `calibration_is_stale()` fires, because `INACCURACY_WP` moved 10.0 → 5.0, so the figure is **withdrawn** at runtime and the report says so |
| the profile is deterministic — same input, byte-identical output | true only on a warm cache; rebuilt in a different order it moves a borderline claim ([[experiments.e91-fixed-depth-is-not-reproducible]]) |
| detection 80 %, naming 10 % | that was one player pre-[[experiments.e82-move-number-rerun]]; across six it is **76 % and 37 %** |

Each was individually recorded correctly somewhere in the vault. What was missing was anything that
forced them to be read *together*, which is what writing a chapter does and what a scorecard row does
not.

**What it makes hard.** Chapters go stale when measurements are redone. Mitigated structurally rather
than by discipline: every number lives as a macro in `FIDIT_template_hrv/Src/brojke.tex`, one file,
each with its source note in a comment. Redoing a measurement is one edit.

**What it forecloses.** Nothing architectural. It does add a standing obligation to every future
cycle: a measurement that changes a headline figure now has a second place to update.

## Revisit when

- The thesis is submitted — at which point M8 closes and the mission is complete rather than
  ongoing.
- Or writing a chapter stops finding anything, which would mean the audit value has been spent and
  M8 is a reporting step after all.
