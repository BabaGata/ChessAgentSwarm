---
id: cas-learning
title: Learning
desc: 'The process by which project capacity is updated so it serves the vision better.'
updated: 1785254500000
created: 1785254500000
---

# Learning

Learning is the adaptive loop of this project: the deliberate process of updating [[capacity]]
(knowledge, tools, agents, architecture, and the process itself) so that it serves [[vision]] better.

Without it, executing [[mission]] steps is just activity. With it, every step leaves the project
*more able* than it found it.

## The loop

```
        ┌──────────────────────────────────────────────┐
        │                                              │
   [[vision]] ──> [[mission]] ──> execute ──> observe ──┤
        ▲                                    │         │
        │                                    ▼         │
        └────── review course <──── [[state]] + evidence
                                             │
                                             ▼
                                       update [[capacity]]
```

1. **Execute** a unit of work from the active mission step.
2. **Observe** — what actually happened, measured, not assumed ([[evaluation]]).
3. **Update state** — rewrite [[state]], including the distance-to-vision scorecard.
4. **Update capacity** — record the new tool/agent/knowledge, or the newly discovered gap.
5. **Extract the lesson** — what generalises? → [[learning.lessons]]
6. **Extract the risk** — what nearly went wrong, and how to prevent a repeat? → [[learning.risks]]
7. **Review course** — did this move us toward the vision? Does mission or vision need revision?

Step 7 is the one that is usually skipped and the one that matters most.

## What counts as learning

| Signal | Where it goes |
|---|---|
| A technique worked / failed | [[learning.lessons]] |
| A recurring failure mode | [[learning.risks]] + a preventive rule in [[process]] |
| A new fact about chess or coaching | [[domain]] + possibly a [[vision]] review |
| A tool proved good/bad | [[capacity.tools]] + [[decisions]] |
| A design choice was made | [[decisions]] |
| The plan was wrong | [[mission]] revision + [[decisions]] |

## Anti-patterns this loop exists to prevent

- **Drift** — many small steps, no one checking they point at the vision.
- **Silent scope creep** — building capability nobody asked for because it was interesting.
- **Undocumented tacit knowledge** — a design that only works because of something learned and
  never written down.
- **Ceremony without observation** — updating notes without measuring anything, producing
  confident-looking documentation about an unverified system.
- **Sunk-cost mission** — continuing a step because it was planned, after it stopped serving the vision.
