---
id: cas-adr-0020
title: 'ADR-0020 — Writing the thesis is no longer a mission step'
desc: 'M8 is removed from the mission. The thesis document is written and maintained outside the project cycle; the mission returns to building, measuring and maintaining the swarm.'
updated: 1789430400000
created: 1789430400000
---

# ADR-0020 — Writing the thesis is no longer a mission step

**Date:** 2026-09-15 · **Status:** accepted · **Decided by:** the thesis author ·
**Supersedes:** [[decisions.0018-the-thesis-is-a-mission-step]]

## Context

[[decisions.0018-the-thesis-is-a-mission-step]] added **M8 — write the thesis** on 2026-09-08, running
alongside M7. By 2026-09-15 the thesis had a full draft, its figures had been refreshed from the
current code, and it was ready for submission.

## Decision

The author asked for writing the thesis document to be removed from the vision and mission. M8 is
deleted from [[mission]].

[[vision]] needed no change: it never made the thesis a goal. It mentions the thesis only as context —
C1's *"thesis project, no funded infrastructure"* and the author as the person who can restate the
goal — and both remain true.

## Consequences

- [[mission]] lists M1–M7. Constraint C5 (auditable) and success criterion 6 (reproducible from this
  vault), which the alignment table had credited to M8, are credited to **M6**, whose every cycle
  updates and commits the vault.
- The three thesis tasks in [[state]]'s priorities — compile it and supply the supervisor names, carry
  the regenerated figures into it, draw the missing figures — are removed.
- [[thesis]] is kept as a record of how the document was structured and built, and so is every past
  commit labelled `M8`. Neither is rewritten.
- The rule ADR-0018 introduced — *the thesis may never claim more than [[state]] does* — no longer
  binds a project step. It remains good advice for anyone editing the document.
