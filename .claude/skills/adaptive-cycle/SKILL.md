---
name: adaptive-cycle
description: >-
  The mandatory work cycle for the Chess Agent Swarm thesis project. Use for EVERY unit of work in
  this repo — research, design, code, refactor, or documentation. Reads the Dendron vault in
  docs/notes to orient on vision/mission/state, plans the step, checks it against the vision,
  executes it, verifies it, writes the documentation back, assesses refactoring, commits, and
  reviews whether the mission or vision now needs revision. Invoke at the START of a unit of work,
  not at the end.
---

# Adaptive Cycle

This project is steered as an adaptive system. **Vision** = the goal, **mission** = the steps,
**capacity** = agents/tools/knowledge, **learning** = the process that grows capacity. The Dendron
vault in `docs/notes/` is the authority on project state — your session memory is not.

Run all nine phases, in order. Phases 5–8 are where the value is; a cycle that stops after
"it works" has failed.

---

## Phase 0 — Orient (always, no exceptions)

Read, in this order:

1. `docs/notes/vision.md` — the goal, its capabilities V1–V8 and constraints C1–C6
2. `docs/notes/mission.md` — the steps and which one is **active**
3. `docs/notes/state.md` — the scorecard, next priorities, open questions, blockers
4. The active mission-step note, `docs/notes/mission.step-NN-*.md`
5. `docs/notes/learning.risks.md` — so you do not re-run a known failure

Then state in one short paragraph: the active step, the top priority from `state.md`, and how the
current request relates to them. **If the request does not relate to the active step, say so and ask
whether the mission should change — do not silently work off-plan.**

## Phase 1 — Plan

Produce a concrete plan for this unit of work:

- What will exist when it is done (artefacts, files, notes)
- **Definition of done** — checkable, not vibes
- The order of operations and what could go wrong
- Estimated cost profile if it involves runtime work (constraint C1)

For anything non-trivial, present the plan before executing it.

## Phase 2 — Align (the discipline that makes this an adaptive system)

Answer these in writing, in the mission-step note's working log:

1. **Which V1–V8 capability or C1–C6 constraint does this serve?** If none — stop, do not do it.
2. **Which `state.md` scorecard dimension does it move, and by how much?**
3. **Is there a cheaper or more direct way to move that same dimension?** If yes, switch to it.
4. **What does it foreclose?** Architecture, cost profile, scope lock-in.
5. **Can it be made more aligned** by widening or narrowing it slightly? Apply the improvement.

Only then proceed.

## Phase 3 — Execute

- **Research and reuse before building.** Search for existing implementations, libraries, datasets
  and open-source projects that already solve ≥80% of the problem. Prefer adopting a proven approach
  over net-new code. Free/open only (C1, C3).
- **Tests first** where code is involved: failing test → minimal implementation → refactor.
- Keep files small and cohesive (target 200–400 lines, hard max 800; functions <50 lines).
- Handle errors explicitly; never swallow them.
- For domain (chess/coaching) knowledge: record **source + evidence class + strength band +
  testability** for every claim. See `docs/notes/capacity.knowledge.md`.

## Phase 4 — Verify

Get evidence. Per `docs/notes/evaluation.md`:

- Code → run the tests, report real output. Failures are reported as failures, never smoothed over.
- Agent work → its declared efficacy measure; ablate it if the question is whether it earns its place.
- Research → every question in the step's "questions this step must answer" is answered or explicitly
  marked unknown, with a reason.
- Cost → measured, not assumed, whenever runtime behaviour changed.

## Phase 5 — Document (mandatory)

Write back to the vault. At minimum:

| Note | Update when |
|---|---|
| `state.md` | **every cycle** — what exists, scorecard, next steps, open questions, blockers |
| the active mission-step note | **every cycle** — working log row, definition-of-done checkboxes |
| `capacity.*.md` | a tool/agent/knowledge was added, evaluated, adopted or rejected |
| `learning.lessons.md` | something generalisable was learned (L-NNN entry) |
| `learning.risks.md` | an issue occurred (with a *prevention measure*) or a new risk appeared |
| `decisions.md` + an ADR note | a choice was made that is expensive to reverse |
| `domain.*` | new chess/coaching knowledge |
| `glossary.md` | a new term is now in use |

Rules: update the `updated:` frontmatter; cross-link with `[[wikilinks]]`; keep notes describing
**reality**, and mark intent as intent. Templates: `references/note-templates.md`.

## Phase 6 — Maintain

Assess refactoring explicitly — **need**, **usefulness**, **possibility**:

- *Need*: duplication, over-long files/functions, names that no longer match what the thing became,
  a boundary that has clearly moved?
- *Usefulness*: does it pay off given the next planned step, or is it polish?
- *Possibility*: is there enough test coverage / a clear contract to do it safely?

Do it now, or record in `state.md` why not. "No refactor needed" is a valid answer that must be
**stated**, not assumed. Also check the vault itself: notes that grew too long, hierarchies that
should split, stale claims.

## Phase 7 — Commit

```
<type>(<mission-step>): <what changed>

<why, and what it moves toward the vision>
```

Types: `feat` `fix` `docs` `refactor` `test` `chore` `research` `design`.
Example: `research(M1): chess concept landscape and prerequisite structure`

Commit after every meaningful unit of work, and always at the end of a cycle. Never commit a vault
that contradicts the code.

## Phase 8 — Review course (the phase everyone skips)

Answer explicitly:

1. Did this cycle move a scorecard dimension? Which, and by how much?
2. Did anything surface that contradicts an assumption in `vision.md` or `mission.md`?
3. Is the active mission step still the highest-value thing to do next?
4. Is the next step still the next step?

**Revise `vision.md` / `mission.md` immediately** — not "later" — if:

- new domain information contradicts an assumption baked into either;
- a constraint proved impossible, or turned out to be far cheaper than assumed;
- a mission step's definition of done no longer implies progress toward the vision;
- **two consecutive cycles moved no scorecard dimension** (strong signal the mission is wrong);
- the thesis author restated the goal.

Any revision gets an ADR in `decisions.md`. Then report to the user: what changed, what the state
is now, and what the next step is.

---

## Guardrails

- **No code before its design note exists.** M1–M3 produce knowledge and design; code starts at M4.
- **Cost first.** A design needing a paid or large-model call in an inner loop is presumed to violate
  C1 until measured otherwise.
- **No unfalsifiable coaching.** Every recommendation the swarm makes must cite evidence from the
  player's own games (V8).
- **No folklore laundering.** LLM-generated chess advice is not a source. Cite real sources.
- **Never mark done what is not verified.** Partial work stays open, with the gap stated.
- **Do not expand scope** because something adjacent is interesting — check it against phase 2.

## Reference

- `references/note-templates.md` — frontmatter and note templates (ADR, lesson, agent, mission step)
- `docs/notes/process.md` — the human-readable specification of this cycle
