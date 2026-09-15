# Chess Agent Swarm

Diploma thesis project: an **agent swarm that coaches chess players**, built and steered as an
**adaptive system**.

## Before doing anything

**Invoke the `adaptive-cycle` skill** (`/adaptive-cycle`). It is the mandatory work cycle for every
unit of work in this repo — research, design, code, refactor or documentation.

The Dendron vault in `docs/notes/` is the authority on project state. Session memory is not.
Orient there first:

- `docs/notes/vision.md` — the goal: capabilities V1–V9, constraints C1–C7, success criteria
- `docs/notes/mission.md` — the 7 iterative steps and which one is **active**
- `docs/notes/state.md` — what exists, the distance-to-vision scorecard, next priorities
- `docs/notes/process.md` — the cycle, in human-readable form
- `docs/notes/learning.risks.md` — known failure modes; do not re-run them

## Hard rules

1. **Never work off-plan silently.** If a request does not serve the active mission step, say so.
2. **Never execute a plan you have not checked against the vision** (phase 2 of the cycle).
3. **Never close a cycle without updating `state.md` and committing.**
4. **No code before its design note exists.** Mission steps M1–M3 produce knowledge and design.
5. **Free or near-free only** (constraint C1). Deterministic computation > small local model >
   cached LLM output > free-tier LLM call in an outer loop.
6. **No unfalsifiable coaching output.** Every recommendation must cite evidence from the player's
   own games.
7. **Every chess claim carries a source and an evidence class.** No LLM-generated folklore
   presented as expertise.

## Commits

```
<type>(<mission-step>): <what changed>

<why, and what it moves toward the vision>
```
Types: `feat` `fix` `docs` `refactor` `test` `chore` `research` `design`
Example: `research(M1): chess concept landscape and prerequisite structure`
