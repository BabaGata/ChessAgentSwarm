---
id: cas-adr-0009
title: 'ADR-0009 — Build the prober before more sections'
desc: 'The next M4 iteration is the prober, not S3–S11. Depth of assessment beats breadth of diagnosis.'
updated: 1785456000000
created: 1785456000000
---

# ADR-0009 — Build the prober before more sections

**Date:** 2026-08-03 · **Status:** accepted

## Context

[[mission]] M7 read *"repeat until every section has an agent"*, which made coverage of
[[domain.sections]] the finish line. Two of eleven sections are built. Taken literally, the mission
schedules nine more detectors and never schedules the prober or the explainer at all.

Meanwhile [[state]]'s scorecard has four dimensions at zero — D1 skill assessment, D2 knowledge
assessment, D3 style profiling, D12 dialogue — and they are not four independent gaps. **Every one of
them requires asking the player something**, and nothing in the system asks anything.

Three further facts made the choice concrete:

- Every finding the swarm produces carries `gap_type: unknown`. S1's design note states that no
  section agent can do better, because a missed tactic cannot distinguish *doesn't know the pattern*
  from *knew it and didn't see it* (L-002).
- The last six commits were all the same forty lines of the planner. The calibration work was worth
  doing — it produced the project's strongest negative result — but it had reached diminishing
  returns, and R-08 (*thesis-time overrun: infinite refinement of the loop instead of building*) was
  materialising quietly.
- The thesis subject is an **agent swarm**. Every component built so far is deterministic, so the
  system is currently better described as a pipeline of detectors. The prober is the first component
  that takes an open-ended input it cannot enumerate in advance.

## Decision

**The next M4 iteration is the prober** ([[capacity.agents.prober]]). Sections S3–S11 are deferred
until at least one player-facing agent exists.

M7's termination condition is rewritten: *until the swarm serves the vision well* — sections that
earn their place, plus the player-facing agents — rather than *until every section has an agent*.

## Alternatives considered

**More sections (S3 endgames, S4 openings).** Rejected: widens D4, the strongest dimension, at 3/5,
while four dimensions sit at 0. Each new section also inherits the full calibration burden — peer
rates, precision screening, confidence thresholds — so the marginal cost is not small.

**The explainer first.** Genuinely close, and cheaper. It would move D8 explainability and make the
system demonstrable, which has real thesis value. Rejected because it can only present what the
profile already contains, and what the profile contains is `gap_type: unknown` on every finding. The
explainer built after the prober has something to explain; built before, it is formatting.

**Continue calibrating (finish D8 power, model the D9 depth curve).** Rejected as the *primary*
line, and folded in instead: D9 is being answered as a by-product of data already collected, and D8
is one analysis run. Neither is allowed to grow into another six-commit sequence.

## Consequences

**Makes easy:** the knowledge/skill distinction, which is the precondition for V2 and for prescribing
correctly rather than plausibly; the first honest measurement of session cost (C4), which is
currently unknown rather than zero; and a demonstrable end-to-end coaching session for the thesis.

**Makes hard:** the swarm's diagnostic vocabulary stays at six claim kinds from two sections for
longer. A player whose real weakness is endgame technique will still be told about tactics or the
clock, or nothing at all.

**Forecloses little.** The prober consumes findings and writes `gap_type`; it does not constrain what
future sections may diagnose. ADR-0006's additivity means sections can still be added one line at a
time.

**Introduces a genuinely new cost class.** This is the first component with non-zero marginal cost
and the first with a reproducibility caveat — a stored diagnosis can change when a model is updated.
Both are recorded in the agent note and must be measured, not assumed (C1, C4).

## Vision link

V9 directly; V2 via V9 — it is the only route to it. V8 is unblocked downstream.

## Revisit when

- The prober's efficacy measure (agent note § 9) comes back negative — specifically if probing
  changes nothing downstream, in which case breadth was the better bet after all.
- A free-tier or local model proves unable to classify answers at acceptable agreement, making V9
  infeasible under C1. That would be a constraint conflict and would go back to [[vision]], not just
  to this ADR.
