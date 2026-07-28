---
id: cas-evaluation
title: Evaluation
desc: 'How the efficacy of individual agents and of the whole swarm is measured.'
updated: 1785254500000
created: 1785254500000
---

# Evaluation

Nothing in this project is "done" because it looks done. This note defines how we get evidence.
It is drafted now as *intent*; it becomes concrete in M3, where the harness is designed and built.

## Three levels of measurement

### 1. Agent level
For each agent in [[capacity.agents]], its declared efficacy measure. Typical forms:
- **Agreement with a reference** — e.g. the tactics agent's motif labels vs. Lichess puzzle tags.
- **Determinism/consistency** — same input, same output across runs.
- **Grounding** — every claim traces to a cited position/game.
- **Cost** — calls and seconds per invocation (C1/C4).

### 2. Swarm level (information flow)
Asked at every M5:
- Does each agent receive the inputs it declares it needs?
- Is information lost, duplicated or silently contradicted between agents?
- Does the final output actually use each agent's contribution, or is some agent decorative?
- Does the end-to-end result improve when the agent is present vs. ablated? *(ablation is the
  strongest available test of whether an agent earns its place)*

### 3. Vision level (does it coach well?)
Against the [[vision]] success criteria:

| Criterion | Proxy measure | Ground truth source |
|---|---|---|
| Strength estimate correct | correlation with established rating | public rating of held-out players |
| Weaknesses correctly identified | agreement with engine-derived error profile + expert review | Stockfish analysis; a strong player's review |
| Plan is reasonable & specific | rubric-scored blind review | strong player scoring plans, some real some control |
| Plan produces predicted progress | did the predicted progress signs appear? | follow-up games of the same player |
| Cost | measured cash + wall-clock per session | instrumentation |

## Test data strategy (to be designed in M3)

- A held-out set of public players across strength bands, with their games.
- For each, a reference "what this player should work on" produced independently.
- Control condition: generic level-appropriate advice, for comparison.
- Never evaluate on the players/games used while designing prompts or knowledge.

## Open problems

- **Ground truth for coaching quality is genuinely hard** (R-09). Expert review does not scale, and
  rating change is noisy and slow. The likely answer is a layered approach: cheap automatic proxies
  every cycle, expensive expert review at milestones only.
- Rating improvement is confounded by everything the player does outside the system.
