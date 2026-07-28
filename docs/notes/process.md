---
id: cas-process
title: Process
desc: 'The mandatory operating cycle every unit of work in this project follows.'
updated: 1785254500000
created: 1785254500000
---

# Process

Every unit of work — research, design, code, refactor — runs the same cycle. The cycle is
implemented as the **`adaptive-cycle` skill** (`.claude/skills/adaptive-cycle/SKILL.md`); this note
is the human-readable specification of it. If the two disagree, fix both.

## The cycle

| # | Phase | Mandatory outcome |
|---|---|---|
| 0 | **Orient** | Read [[vision]], [[mission]], [[state]]. Know the active step and the top priority. |
| 1 | **Plan** | A concrete plan for this unit of work with a definition of done. |
| 2 | **Align** | Score the plan against [[vision]]; ask *can it be made more aligned?* Improve it, then proceed. |
| 3 | **Execute** | Research-and-reuse before building. Tests before implementation where code is involved. |
| 4 | **Verify** | Evidence that it works, per [[evaluation]]. Failures reported as failures. |
| 5 | **Document** | Update [[state]] (incl. scorecard), [[capacity]], [[learning.lessons]], [[learning.risks]], [[decisions]]. |
| 6 | **Maintain** | Assess refactoring need/usefulness/possibility. Do it now or record why not. |
| 7 | **Commit** | git commit with a message referencing the mission step. |
| 8 | **Review course** | Did this move [[state]] toward [[vision]]? Do [[mission]] or [[vision]] need revision? |

Phases 5–8 are not optional cleanup. A cycle that skips them has not finished.

## The alignment check (phase 2)

For the planned unit of work, answer in writing:

1. **Which [[vision]] capability (V1–V8) or constraint (C1–C6) does this serve?**
   If the answer is "none", do not do it.
2. **How much does it move the corresponding [[state]] scorecard dimension?**
3. **Is there a cheaper or more direct way to move that same dimension?**
   If yes, that is the better plan — take it.
4. **What does it foreclose?** Does it lock in an architecture, cost profile, or scope?
5. **Could it be made more aligned** by widening or narrowing it slightly?

Record the answers in the mission-step note's working log. This is the core adaptive-system
discipline: *never execute a plan you have not tested against the goal.*

## Vision & mission review triggers

Review [[vision]] and [[mission]] immediately — not "later" — when:

- New domain information contradicts an assumption baked into either.
- A constraint proves impossible, or turns out to be cheaper than assumed.
- A mission step's definition of done no longer implies progress toward the vision.
- Two consecutive cycles move no scorecard dimension.
- The thesis author restates the goal.

Any resulting change is logged in [[decisions]].

## Refactoring assessment (phase 6)

Before every commit, ask:
- **Need** — is anything now duplicated, over-long (>800 lines/file, >50 lines/function), or
  misnamed relative to what it became?
- **Usefulness** — will refactoring now save more than it costs, given the next planned step?
- **Possibility** — is there test coverage or a clear contract that makes it safe?

Answer all three. "No refactor needed" is a valid answer that must be *stated*, not assumed.

## Commit convention

```
<type>(<mission-step>): <what changed>

<why, and what it moves toward the vision>
```
Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `research`, `design`.
Example: `research(M1): chess concept landscape and prerequisite structure`

## Documentation standards

- One idea per note; hierarchy over long notes.
- Every claim about the *system* in [[state]] carries evidence or is marked as intent.
- Every claim about *chess* carries a source and evidence class ([[capacity.knowledge]]).
- Cross-link with `[[wikilinks]]` rather than duplicating text.
- Update `updated:` frontmatter when a note's content changes materially.
- Notes describe reality; plans are marked as plans.
