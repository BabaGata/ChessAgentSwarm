---
id: cas-mission
title: Mission
desc: 'The iterative steps that move the project from the current state toward the vision.'
updated: 1785254500000
created: 1785254500000
---

# Mission

The mission is the **path**, not the destination. It exists to serve [[vision]]; if a step stops
serving the vision, the step is rewritten — not obeyed out of inertia.

**Active step:** M1 — Chess & coaching foundations research → [[mission.step-01-foundations]]

## The steps

### M1 — Build the coaching knowledge overview
Investigate chess concepts, how coaches actually work with players, and good coaching practice.
Produce a general overview of the knowledge the swarm needs in order to coach effectively.
→ [[mission.step-01-foundations]]

### M2 — Chunk the knowledge into sections, ordered by priority
Break the coaching knowledge into small, cohesive sections. Order the sections by how much they
matter for coaching effectiveness (and how well they can stand alone as an agent's remit).
Output: a prioritised section catalogue in [[domain.sections]].

### M3 — Design the swarm
For the whole system, plan:
- one agent per section, and how they are orchestrated;
- how each agent's knowledge is combined and each agent best utilised;
- **how the player interacts with the swarm — including the probe/active-assessment protocol (V9),
  which M1 showed is a diagnostic capability, not a UI concern (L-002);**
- **the structured player profile schema** — the load-bearing artefact all agents read and write
  ([[decisions.0002-compute-first-speak-last]]);
- the architecture: orchestration, knowledge storage, memory, engine/data integration;
- the **minimum-sample and confidence policy** — when is the swarm allowed to assert a weakness (R-13);
- how the efficacy of the whole system is measured ([[evaluation]]).
Also decide here: the **target strength band** for the first end-to-end slice (M1 recommends
1400–1800) and whether [[decisions.0002-compute-first-speak-last]] is accepted.
Build it, test it, improve it. Move on only when it satisfies its part of the goal.

### M4 — Build one agent for one section
Plan the agent *before* building it: how its knowledge sits in the knowledge base, what kind of
agent suits the task, the processes that maintain its knowledge, its tools, its general
instruction, its required inputs, its expected outputs, and how its efficacy is assessed.
Build, test, improve. Move on when it satisfies its goal.

### M5 — Assess the new agent inside the swarm
Does information flow through correctly? Does the end result serve the goal? Did this step move us
closer to the vision or further away? Is a section missing? Do we need new external information
about chess or coaching? Has new information surfaced that should change the project's course?
Update [[state]], [[capacity]], [[learning.lessons]] accordingly.

### M6 — Maintain and commit
Maintain codebase, documentation, plan and overview. Check whether refactoring is needed / useful /
possible before the codebase gets out of hand. Then git commit.

### M7 — Repeat M4 → M5 → M6
Until every section has an agent that works well, the agents are orchestrated well, and the system
serves the vision well.

## Alignment argument (why this mission serves this vision)

| Vision capability | Served by |
|---|---|
| V1–V4 (assessment, knowledge, style, gaps) | M1, M2 define *what must be known* to assess; M4 builds the assessing agents. |
| V5–V6 (prioritisation, path planning) | M2's priority ordering feeds the planner; M3 designs the orchestration that produces a path. |
| V7 (progress tracking) | M3's architecture must include player memory/state; M5 re-checks it every cycle. |
| V8 (explainability) | M3's information-flow design + M5's "does information pass through properly" check. |
| V9 (dialogue & active assessment) | M3's interaction/probe protocol design; evaluated per-cycle from M5 onward. |
| C1–C4 (cost) | M3's architecture decisions; cost measured every M5. |
| C6 (incrementally useful) | The M4→M5→M6 loop always ends on a working, committed system. |

**Gap watch — resolved 2026-07-28.** The unscheduled "player-facing interaction" gap became a named
vision capability (V9, [[decisions.0003-add-v9-dialogue-and-active-assessment]]) and an explicit M3
deliverable. Watch continues in a narrower form: nothing in M1–M7 yet schedules work on the *quality*
of explanation once the protocol exists — if the swarm proves accurate but incomprehensible, a
dedicated step is still needed.

## Progress

| Step | Status | Note |
|---|---|---|
| M1 | wip | [[mission.step-01-foundations]] — landscape mapped; prior art, primary sources and engine-cost measurement still open |
| M2 | pending | |
| M3 | pending | |
| M4 | pending | |
| M5 | pending | |
| M6 | recurring | runs at the end of every cycle |
| M7 | pending | |

## Review triggers

Review this note when:
- [[vision]] changes.
- A step completes and the next step no longer looks like the highest-value move.
- Research or implementation reveals a missing step (like the interaction-quality gap above).
- Two consecutive cycles fail to move any [[state]] scorecard dimension.
