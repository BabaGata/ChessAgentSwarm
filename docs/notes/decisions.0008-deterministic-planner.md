---
id: cas-adr-0008
title: 'ADR-0008 — The planner is deterministic'
desc: 'Plan steps are derived arithmetic, not generated prose; only the prober and explainer use a model.'
updated: 1785313600000
created: 1785313600000
---

# ADR-0008 — The planner is deterministic

**Date:** 2026-07-31 · **Status:** accepted

## Context

[[architecture]] placed layers 6–8 — prober, planner, explainer — in the language layer, as the
components that use a model. Building the planner made that look wrong for the middle one.

A plan step must carry a **progress sign** and a **check point**
([[architecture.player-profile]]): the observable thing that should change, and when to re-measure.
That requirement is what makes V6 and V7 falsifiable rather than rhetorical, and it is enforced at
construction — a `PlanStep` without them cannot be built.

A language model cannot produce that. *"You should start spotting pins more reliably within a few
weeks"* is prose; it is not checkable, and V7 has nothing to test. What V7 needs is
*"missed-pin rate below 20.9 % over your next 24 games"* — a number derived from the same
measurement that produced the finding.

## Decision

**The planner is deterministic.** Targets, check points and progress signs are computed from the
finding's own measurement. The action is selected from a small table keyed by claim kind and subject,
using the Lichess theme vocabulary that [[domain.puzzle-themes]] already mapped — so the name that
described the weakness also selects the training material.

Only the **prober** and the **explainer** use a model. The explainer may rephrase a step for a
player; it may not change what the step claims.

## Alternatives considered

- **LLM-generated plans**, which is what the prior art does. Rejected: the output is unfalsifiable by
  construction, and it would put a stochastic component in front of the one number the whole
  progress-tracking capability depends on.
- **LLM-generated action text, deterministic targets.** Tempting, and deferred rather than rejected —
  it is the explainer's job, and keeping the planner's output fully derived means a plan can be
  diffed between sessions to see what actually changed.

## Consequences

- **Easier:** V7 becomes mechanical — re-run the analysis, compare against the recorded sign. Plans
  are reproducible and diffable. Cost is zero.
- **Harder:** action text is template-shaped. Acceptable, because the template is the *content* and
  the explainer owns the phrasing.
- **Forecloses:** plans that reason about a player's circumstances in ways the schema does not carry.
  When that becomes a real limitation, the fix is to carry more in the schema, not to hand the job
  to a model.

## Two honest consequences worth stating

**Time estimates are left empty.** Open question D5 — how long coaching interventions take to show
results — is unresolved, and it is the weakest-evidenced part of the vision. The planner measures
progress in **games**, which it can derive, rather than days, which it cannot. A fabricated
"2–3 weeks" would be exactly the confident folklore this project refuses elsewhere.

**Targets halve the gap rather than closing it.** Asking a player to reach the peer rate in one
training block is not a fair expectation; halving the distance to it is observable and achievable.
The midpoint is provisional, like every other threshold here.

## Vision link

Serves V6, V7 and C1, and protects V8 by keeping the falsifiable part of the output derived.

## Revisit when

A section produces a finding whose remedy genuinely cannot be expressed as a derived target — at
which point the question is whether the schema is missing something, before it is whether a model
should write it.
