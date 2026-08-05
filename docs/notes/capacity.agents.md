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
| **S3 endgame technique** | section | **built** | [[capacity.agents.s3-endgame-technique]] · chosen for **coverage** after E08 measured the swarm silent for 29 of 38 players. Carries a pooled `endgame_error.any` claim precisely because per-thing denominators were the binding constraint. Registration was again a one-line change — ADR-0006's second test |
| **S4 opening outcomes** | section | **built** | [[capacity.agents.s4-opening-outcomes]] · errors before move 15 and how often the player emerges already worse. Subdivided by **colour rather than by opening**, applying L-022 at design time instead of discovering it afterwards |
| **S5 pawn structure** | section | **built** | [[capacity.agents.s5-pawn-structure]] · the first Tier 2 section. Counts weaknesses the player's move **creates**, not ones the position has — E02 measured presence at 96 % of games. Carries a limitation none of the others do: it can say a player is unusual, not that it costs them anything (E03) |
| **S6 squares & files** | section | **built** | [[capacity.agents.s6-squares-and-files]] · what the player lets the opponent keep — an unevictable knight, a rook on the second rank. **The first section whose claims were chosen by measurement before it was written** (E09), and the first where no claim turned out to be dead weight |
| **S8 attack & defence** | section | **built, marginal** | [[capacity.agents.s8-attack-and-defence]] · one claim of four candidates — how readily an attack assembles against the player's king. Spread 1.59, the weakest shipped, and **it reached no new players**: two findings, both for players already advised. Its place is arguable and the note says so |
| **P prober** | player-facing | **core built; classifier and rubric outstanding** | [[capacity.agents.prober]] · the first agent containing a language model, and the only route to V2. Turns `gap_type: unknown` into knowledge / skill / fragile. The deterministic spine and the model seam exist; the model behind the seam and its validation do not |
| **E explainer** | player-facing | **built, deterministic** | `chesscoach/explainer.py` · templates, not a model — it cannot invent a reason the detectors never found, and it is the baseline a generated report has to beat. Enforces [[architecture.interaction]] § 7: one or two priorities, every claim cited to a game and move, what could not be assessed named, a gap type explained only when a probe established it |

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
