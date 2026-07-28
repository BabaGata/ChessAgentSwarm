---
id: cas-capacity
title: Capacity
desc: 'Everything the project can act with: agents, tools, knowledge, infrastructure, budget.'
updated: 1785254500000
created: 1785254500000
---

# Capacity

Capacity is the **ability to act** toward [[vision]]. [[learning]] is the process that grows it.
Executing a [[mission]] step consumes capacity and — if the cycle is run properly — leaves more of it.

## Composition

| Kind | Note | Question it answers |
|---|---|---|
| Agents | [[capacity.agents]] | Who can do work in the swarm? |
| Tools | [[capacity.tools]] | What can they act with? |
| Knowledge | [[capacity.knowledge]] | What does the system know? |
| Infrastructure | this note, below | Where does it run, at what cost? |

## Infrastructure & budget

| Item | Current | Constraint |
|---|---|---|
| Compute | one developer laptop (Windows 11) | C2 — no cluster |
| Money | ~0 | C1 — free tiers, local models, open data only |
| Storage | local filesystem + git | keep the knowledge base file-based and diffable as long as possible |
| Runtime language | undecided (Python likely, for engine + data ecosystem) | decide in M3, log in [[decisions]] |

**Cost discipline:** any design that requires a paid API call per player-move, or a large model call
in an inner loop, is presumed to violate C1 until proven otherwise. Prefer, in order:
1. deterministic computation (engine, statistics, database lookups),
2. small local models,
3. cached / precomputed LLM output,
4. free-tier LLM calls in outer loops only.

## Capacity gaps (what we most lack right now)

| Gap | Blocks | Planned fix |
|---|---|---|
| No chess/coaching domain knowledge | M2, M3, everything | M1 research |
| No player-game data pipeline | V1, V2, V4 | M3 architecture |
| No evaluation harness | knowing whether anything works | M3, per [[evaluation]] |
| No decision on model/runtime stack | M3, M4 | ADR at end of M1 |
