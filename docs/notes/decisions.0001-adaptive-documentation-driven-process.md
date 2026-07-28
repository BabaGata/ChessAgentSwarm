---
id: cas-adr-0001
title: 'ADR-0001 — Adaptive, documentation-driven process'
desc: 'Steer the project as an adaptive system with a Dendron vault as the control mechanism and an enforced work cycle.'
updated: 1785254500000
created: 1785254500000
---

# ADR-0001 — Adaptive, documentation-driven process

**Date:** 2026-07-28 · **Status:** accepted

## Context

The project is expected to grow large: a swarm of many agents, a chess/coaching knowledge base, an
evaluation harness, and a thesis to write about all of it. It is built incrementally over many
sessions, with an AI assistant whose working memory does not persist between them. The main failure
mode of such a project is **drift**: many locally-sensible steps that collectively wander away from
the goal, with the rationale lost.

## Decision

Steer the project as an adaptive system with four explicit elements — **vision** (goal),
**mission** (steps), **capacity** (agents/tools/knowledge/infrastructure), **learning** (the process
that updates capacity) — all recorded in a Dendron vault under `docs/`, and enforce a fixed work
cycle (orient → plan → align → execute → verify → document → maintain → commit → review course)
via a project skill, `adaptive-cycle`.

The vault is the authority on project state. Session memory is not.

## Alternatives considered

- **Plain README + issue tracker.** Cheaper, but no place for the vision/mission/capacity
  distinction, and no natural home for domain knowledge that will grow to hundreds of notes.
- **Documentation written at the end.** Standard for a thesis, fatal for steering: the value here is
  in the *feedback*, not the artefact.
- **Free-form notes without an enforced cycle.** Notes exist but decay; the enforcement is the point.

## Consequences

- **Easier:** resuming after any gap; justifying design choices in the thesis; noticing drift early;
  onboarding a reviewer.
- **Harder:** every unit of work carries documentation overhead. Accepted deliberately — the
  thesis's subject *is* the adaptive process, so the overhead is partly the deliverable.
- **Forecloses:** casual "just hack it in" changes. That is intended.
- **Risk:** ceremony without observation (see R-06, R-08 in [[learning.risks]]) — mitigated by
  requiring evidence in [[state]] and a definition of done per mission step.

## Vision link

Serves C5 (auditable reasoning) and C6 (incrementally useful), and protects every V item from drift.

## Revisit when

The cycle demonstrably costs more than it saves — concretely: if two consecutive cycles spend more
effort on documentation than on the work being documented, without a corresponding steering benefit.
