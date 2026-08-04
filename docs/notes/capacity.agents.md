---
id: cas-capacity-agents
title: Agents
desc: 'Inventory of the swarm agents: remit, inputs, outputs, tools, efficacy measure.'
updated: 1785254500000
created: 1785254500000
---

# Agents

The swarm's roster. Each agent gets its own note `capacity.agents.<name>` and a row here.

Two kinds live here, and the distinction matters more than the count. **Section agents** own a slice
of [[domain.sections]] and are deterministic by decision
([[decisions.0002-compute-first-speak-last]]). **Player-facing agents** sit outside that catalogue,
run after diagnosis, and are the only place a language model is permitted.

## Roster

| Agent | Kind | Status | Note |
|---|---|---|---|
| **S2 decision process & clock behaviour** | section | **built, scored** | [[capacity.agents.s2-decision-process]] · found the planted weakness at 5.54× lift with 0 spurious findings; asserts one claim kind for 16 % of 38 real players |
| **S1 tactical pattern gaps** | section | **built, assessed** | [[capacity.agents.s1-tactical-gaps]] · eight motif detectors; took the swarm from 1 claim kind to 6. Adding it was a one-line change, which tested ADR-0006's additivity claim |
| **P prober** | player-facing | **core built; classifier and rubric outstanding** | [[capacity.agents.prober]] · the first agent containing a language model, and the only route to V2. Turns `gap_type: unknown` into knowledge / skill / fragile. The deterministic spine and the model seam exist; the model behind the seam and its validation do not |
| **E explainer** | player-facing | not designed | V8. Blocked on nothing but priority; the report constraints already exist in [[architecture.interaction]] § 7 |

**Nine of eleven sections remain unbuilt** ([[domain.sections]]). That is deliberate: breadth of
diagnosis was widened once (S1) and then paused, because a system that diagnoses eleven things and
cannot ask the player about any of them is further from the vision than one that diagnoses two and
can.

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
