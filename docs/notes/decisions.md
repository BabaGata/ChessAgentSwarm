---
id: cas-decisions
title: Decisions
desc: 'Decision log — every choice that constrains future work, with its context and consequences.'
updated: 1785254500000
created: 1785254500000
---

# Decisions

Architecture/direction decision records. A decision belongs here if reversing it later would cost
real work, or if a future reader would otherwise ask *"why on earth is it like this?"*.

## Log

| ID | Date | Decision | Status |
|---|---|---|---|
| [[decisions.0001-adaptive-documentation-driven-process]] | 2026-07-28 | Steer the project as an adaptive system through a Dendron vault + enforced cycle | accepted |
| [[decisions.0002-compute-first-speak-last]] | 2026-07-28 | Deterministic analysis core produces a structured player profile; LLMs operate only on the summary | **proposed** (decide in M3) |
| [[decisions.0003-add-v9-dialogue-and-active-assessment]] | 2026-07-28 | Add V9 (dialogue & active assessment) to the vision — passive analysis cannot separate knowledge gaps from skill gaps | accepted |
| [[decisions.0004-free-research-materials]] | 2026-07-28 | Add C7 — build the knowledge base from freely obtainable sources; paid material only to unblock | accepted |

## Template

```
### ADR-NNNN — <title>
**Date:** · **Status:** proposed | accepted | superseded by ADR-MMMM | rejected
**Context:** the forces at play, what we knew at the time
**Decision:** what we chose
**Alternatives considered:** and why they lost
**Consequences:** what this makes easy, what it makes hard, what it forecloses
**Vision link:** which V/C item this serves
**Revisit when:** the condition that should reopen this
```
