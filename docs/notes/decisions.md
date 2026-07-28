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
