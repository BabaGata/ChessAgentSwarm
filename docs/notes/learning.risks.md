---
id: cas-learning-risks
title: Risks, Issues & Prevention
desc: 'Known risks and encountered blockers, each with a prevention measure.'
updated: 1785254500000
created: 1785254500000
---

# Risks, Issues & Prevention

Two sections: **anticipated risks** (not yet materialised) and **encountered issues** (they did).
Every encountered issue must end with a prevention measure that changes something concrete — a rule
in [[process]], a check in the `adaptive-cycle` skill, a test, or a design constraint.

## Anticipated risks

| ID | Risk | Impact | Likelihood | Prevention / early warning |
|---|---|---|---|---|
| R-01 | **Cost creep** — the design quietly becomes LLM-call-heavy and violates C1 | high | high | Cost per operation is estimated at design time and measured in [[evaluation]]; D9 scorecard dimension makes it visible every cycle |
| R-02 | **Unfalsifiable coaching output** — the swarm produces plausible advice nobody can verify | high | high | V8 explainability is a vision capability, not a nice-to-have; every recommendation must cite evidence from the player's own games |
| R-03 | **Folklore laundering** — LLM-generated chess advice presented as expert knowledge | high | medium | Evidence-class marking in [[capacity.knowledge]]; sources recorded in [[domain.sources]] |
| R-04 | **Agent sprawl** — one agent per section produces a swarm too large to orchestrate or evaluate | medium | medium | M2 orders sections by priority; build agents in priority order and re-assess the swarm each M5 rather than building all of them |
| R-05 | **Scope drift into engine work** | medium | medium | Explicit non-goal in [[vision]]; use existing engines |
| R-06 | **Documentation rot** — notes describe an intended system, not the real one | high | medium | [[state]] is rewritten every cycle with evidence; the cycle does not close without it |
| R-07 | **Codebase getting out of hand** | medium | medium | Refactoring assessment is a mandatory step of every cycle before commit ([[process]]) |
| R-08 | **Thesis-time overrun** — infinite refinement of the loop instead of building | high | medium | Each mission step has a definition of done; C6 requires each step to end on something usable |
| R-09 | **Evaluation without ground truth** — no way to tell good coaching from bad | high | high | [[evaluation]] must define proxies (engine agreement, rating trajectory, expert review) before M4 builds anything |
| R-10 | **Player data privacy** — handling real players' games and profiles | medium | low | Use public games only; no personal data beyond public usernames; state this in the thesis |

## Encountered issues

| ID | Date | Issue | Root cause | Fix | Prevention applied |
|---|---|---|---|---|---|
| — | — | none yet | | | |
