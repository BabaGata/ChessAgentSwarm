---
id: cas-capacity-agents
title: Agents
desc: 'Inventory of the swarm agents: remit, inputs, outputs, tools, efficacy measure.'
updated: 1785254500000
created: 1785254500000
---

# Agents

The swarm's roster. **Currently empty** — the first agent is built in mission step M4, after the
section catalogue (M2) and the swarm design (M3) exist.

Each agent gets its own note `capacity.agents.<name>` and a row here.

## Roster

| Agent | Section ([[domain.sections]]) | Status | Note |
|---|---|---|---|
| — | — | — | none yet |

## Required fields for every agent

Copied from [[mission]] M4 — an agent is not "designed" until all of these are answered:

1. **Remit** — which knowledge section it owns, and its boundary (what it must *not* do).
2. **Knowledge organisation** — how its knowledge lives in the knowledge base, and why that shape.
3. **Agent type** — deterministic tool-runner, retrieval-grounded reasoner, LLM planner, classifier…
   chosen to fit the task, not by default.
4. **Knowledge maintenance process** — how its knowledge is created, validated and kept current.
5. **Tools** — engine, database, dataset, other agents.
6. **General instruction** — the system prompt / behavioural contract.
7. **Inputs** — exactly what must be passed to it, and by whom.
8. **Outputs** — the artefact it produces, its schema, and who consumes it.
9. **Efficacy measure** — how we know it is doing its job well ([[evaluation]]).
10. **Cost profile** — expected calls/compute per invocation (C1).

## Orchestration

Defined in M3. Until then, open: whether the swarm is a pipeline, a blackboard, a
planner-with-specialists, or a debate/critique arrangement. Record the choice in [[decisions]].
