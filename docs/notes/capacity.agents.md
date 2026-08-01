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
| **S2 decision process & clock behaviour** | S2 | **built, scored** | [[capacity.agents.s2-decision-process]] · found the planted weakness at 5.54× lift with 0 spurious findings; asserts one claim kind for 16 % of 38 real players |
| **S1 tactical pattern gaps** | S1 | **designed** | [[capacity.agents.s1-tactical-gaps]] · the answer to S2's narrowness, and the first real test that sections are additive |

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

**Decided in M3:** a staged blackboard — agents read and write [[architecture.player-profile]] and
never message each other ([[decisions.0006-staged-blackboard-orchestration]]). The full agent
contract, including the rules that agents may return zero findings and may not call a language model
in the diagnosis stage, is in [[architecture.orchestration]].
