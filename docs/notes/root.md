---
id: blf84wfu7atn2xwrylvtdaw
title: Chess Agent Swarm
desc: 'Adaptive agent swarm that coaches chess players. Diploma thesis knowledge base and project control room.'
updated: 1785254500000
created: 1785254488385
---

# Chess Agent Swarm

Diploma thesis project: an **agent swarm that acts as a chess coach**, built and steered as an
**adaptive system**.

This vault is not a side-artifact of the project — it *is* the steering mechanism. Every planning,
execution and review cycle reads from and writes back to these notes.

## The adaptive-system frame

| Element | Meaning here | Note |
|---|---|---|
| **Vision** | The desired end state. Changes rarely, and only deliberately. | [[vision]] |
| **Mission** | The iterative steps that move us toward the vision. Reviewed whenever it stops serving the vision. | [[mission]] |
| **Capacity** | Everything we can act with: agents, tools, knowledge, infrastructure, budget. | [[capacity]] |
| **Learning** | The process that updates capacity so it serves the vision better. | [[learning]] |
| **State** | Where we actually are right now, and how far that is from the vision. | [[state]] |

> Building the **capacity**, by running **learning** loops, executing **mission** steps, to reach the **vision**.

## Control-room notes

- [[vision]] — desired result, constraints, success criteria, non-goals
- [[mission]] — the 7 iterative steps, the active step, alignment argument
- [[state]] — current state, distance-to-vision scorecard, next steps & priorities
- [[open-questions]] — the live register of unknowns: owner, what it blocks, how it resolves
- [[capacity]] — inventory of agents, tools, knowledge, infrastructure
- [[learning]] — how capacity gets improved; [[learning.lessons]], [[learning.risks]]
- [[process]] — the operating cycle every unit of work follows
- [[architecture]] — the system design: profile, orchestration, interaction, confidence
- [[evaluation]] — how we measure whether the swarm actually coaches well
- [[experiments]] — measured experiments and what changed because of them
- [[decisions]] — decision log (ADRs)
- [[domain]] — chess & coaching knowledge base (the swarm's subject matter)
- [[glossary]] — shared vocabulary

## How to work in this project

Run the `adaptive-cycle` skill (`/adaptive-cycle`). It encodes the mandatory loop:

```
orient → plan → align → execute → verify → document → commit → review course
```

Never start implementation work without orienting on [[vision]], [[mission]] and [[state]] first.
Never finish a unit of work without writing back to [[state]] and committing.
