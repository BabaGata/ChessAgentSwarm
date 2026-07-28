# Note templates

Dendron notes live in `docs/notes/`. Filenames are the hierarchy: `domain.chess-concepts.md` is a
child of `domain.md`. Every note needs frontmatter with a **unique** `id`.

`created` / `updated` are epoch **milliseconds**. Get one with:
`node -e "console.log(Date.now())"`

## Base frontmatter

```yaml
---
id: cas-<short-unique-slug>
title: <Human Title>
desc: '<one line — this shows up in lookups, make it useful>'
updated: <epoch-ms>
created: <epoch-ms>
---
```

---

## Mission step — `mission.step-NN-<slug>.md`

```markdown
# MN — <Title>

**Status:** wip | done | blocked
**Parent:** [[mission]]
**Outputs into:** [[...]]

## Goal of this step
<what this step must achieve, and why it matters to [[vision]]>

## Questions this step must answer
1. ...

## Method
<how the work will be done>

## Definition of done
- [ ] checkable outcomes

## Working log
| Date | Activity | Alignment check (V/C served, dimension moved) | Outcome |
|---|---|---|---|
```

---

## ADR — `decisions.NNNN-<slug>.md`

```markdown
# ADR-NNNN — <title>

**Date:** YYYY-MM-DD · **Status:** proposed | accepted | superseded by ADR-MMMM | rejected

## Context
<the forces at play, what we knew at the time>

## Decision
<what we chose>

## Alternatives considered
<and why they lost>

## Consequences
<what this makes easy, what it makes hard, what it forecloses>

## Vision link
<which V1–V8 / C1–C6 item this serves>

## Revisit when
<the concrete condition that should reopen this>
```

Also add a row to the log table in `decisions.md`.

---

## Lesson — entry in `learning.lessons.md`

```markdown
### L-NNN — <short title>
**Date:** YYYY-MM-DD · **Cycle / mission step:** Mx · **Class:** technique | process | domain | tooling
**Context:** what was being attempted
**Observation:** what actually happened (with evidence)
**Lesson:** the generalisable claim
**Applied to:** the note/rule/code changed because of it
```

A lesson only belongs here if it would change what a future cycle does.

---

## Issue — row in `learning.risks.md` § Encountered issues

| ID | Date | Issue | Root cause | Fix | Prevention applied |

The **prevention applied** column must point at something concrete that changed: a rule in
`process.md`, a guardrail in the skill, a test, or a design constraint. "Be more careful" is not a
prevention measure.

---

## Agent — `capacity.agents.<name>.md`

```markdown
# Agent — <name>

**Section:** [[domain.sections]] → <section>
**Status:** designed | built | evaluated | retired

## 1 Remit
<what it owns, and explicitly what it must not do>

## 2 Knowledge organisation
<where its knowledge lives, in what shape, and why>

## 3 Agent type
<deterministic tool-runner | retrieval-grounded reasoner | LLM planner | classifier | …, and why>

## 4 Knowledge maintenance
<how its knowledge is created, validated, kept current>

## 5 Tools
## 6 General instruction
<the behavioural contract / system prompt>

## 7 Inputs
| Field | Type | From |

## 8 Outputs
| Field | Type | Consumed by |

## 9 Efficacy measure
<how we know it does its job — see [[evaluation]]>

## 10 Cost profile
<calls / compute per invocation — constraint C1>
```

An agent is not "designed" until all ten sections are answered.

---

## Domain note — `domain.<area>.md`

Every claim carries four markers:

| Claim | Source | Evidence class | Band | Testable from games? |
|---|---|---|---|---|
| ... | ... | measured / expert-consensus / single-expert / folklore | e.g. 1000–1600 | yes / no / partly |

`folklore` + untestable claims may be recorded, but must never be shown to a player as fact or
silently drive a coaching decision.
