---
id: cas-arch-orchestration
title: Orchestration
desc: 'How the agents are run and combined: a staged blackboard with isolated section agents and no inter-agent conversation.'
updated: 1785256200000
created: 1785256200000
---

# Orchestration

Resolves **C3** in [[open-questions]] — see [[decisions.0006-staged-blackboard-orchestration]].

## The pattern: staged blackboard

Agents communicate **only** by reading and writing [[architecture.player-profile]]. They run in
stages. Within a stage, agents are independent and parallel. **No agent ever sends a message to
another agent.**

```
stage A  analysis core            deterministic, parallel per position
stage B  section agents S1…S11    parallel, isolated — each emits Findings
stage C  arbiter                  deterministic selection of 1–2 priorities
stage D  prober                   only for shortlisted findings; may loop back to B
stage E  planner → explainer      language layer, reads profile only
```

## Why not the alternatives

**Not a conversational multi-agent swarm.** The fashionable design — agents debating, critiquing,
negotiating — fails every constraint this project has:

- *Cost.* Every exchange is a model call; the bill scales with chatter, not with information (C1).
- *Determinism.* [[evaluation]]'s B4 requires identical output for identical input. Conversation
  between stochastic agents does not give that.
- *Ablation.* B3 asks whether each agent earns its place. If agents influence one another, removing
  one changes the others' behaviour and the measurement is meaningless.
- *Explainability.* V8 requires every claim to trace to evidence. A claim that emerged from a
  negotiation traces to a transcript, which is not evidence.
- *It buys nothing here.* Diagnosis is deterministic computation (ADR-0002). There is nothing for
  the agents to argue about — they measure different things about the same games.

**Not a single planner-with-tools.** That is the prior-art design (one LLM call per game). It works,
and it is exactly what cannot be evaluated per-component or improved incrementally — the failure
mode M4/M5 exist to avoid.

**Not a linear pipeline.** Sections do not feed each other, so serialising them adds latency and a
false dependency order. They fan out from the same analysis and fan in to the same profile.

## Section agent contract

Every section agent, without exception:

| Rule | Reason |
|---|---|
| reads the analysis output and the existing profile; writes only Findings | keeps the blackboard the single source of truth |
| emits **typed** findings, never prose | [[architecture.player-profile]] design rule 1 |
| attaches evidence and provenance to every finding | V8, L-006 |
| declares its own efficacy measure | [[evaluation]] agent level |
| may return **zero** findings | an agent with nothing to report must say nothing — "always produce something" is how filler is born |
| never calls a language model in stage B | cost, determinism; the language layer is stages D–E |

The last two are the ones most likely to be violated under pressure to make a demo look impressive.

## Arbiter

Deterministic, not a model. Selects one or two priorities by:

1. **confidence tier** ([[architecture.confidence]]) — `priority` before `focus`, never `watch`;
2. **prerequisite order** — a gap whose prerequisites are missing is not actionable yet
   ([[domain.chess-concepts]] § C);
3. **band appropriateness** — the 1400–1800 binding constraints first;
4. **expected gain per study hour**, when comparable;
5. **recency and recurrence** — an active streak outranks a historical pattern.

Cap of two is a design constraint, not a tuning parameter: coaches give one or two priorities, and
"here are your nine weaknesses" is the anti-pattern (R-12, D3 in [[evaluation]]).

**Built** as `chesscoach/arbiter.py`, with two departures from the list above, both recorded rather
than quietly taken:

- **Prerequisite order is not implemented.** [[domain.chess-concepts]] § C says tactics gate
  calculation, and that practical-process skills are cross-cutting and teachable at any level — so
  between the claim kinds that currently exist, tactical and process weaknesses have **no defensible
  ordering**. Inventing one would be fabricated pedagogy. The hook is there for when a section emits
  a claim that genuinely depends on another.
- **A diversity preference was added**: the second slot prefers a different subject, because missing
  pins and conceding pins are one thing to work on rather than two.

Ranking is therefore tier → **can it state a cost** → **the cost** → unusualness (peer lift where
available) → breadth of evidence → id.

Tier comes first deliberately: on real data a `focus` finding at 3.1× peers ranks *below* a
`priority` finding at 2.6×, because strength of evidence should outrank apparent size — the same
principle as `PRIORITY_MARGIN` in [[architecture.confidence]]. A large number should not be able to
buy past weak evidence.

**Item 4 of the list above — expected gain — was built in E15** and sits directly under the tier.
`Measurement.cost_wp` holds the win probability given away on a claim's own instances, and
`cost_per_game` normalises it. It is *not* gain per study **hour**: nothing measures how long a
remedy takes ([[open-questions]] D5), and the study-time answer sizes the plan instead of dividing
the cost. A claim whose instances are not mistakes has no cost and ranks below every claim that has
one — a policy choice, argued for in the S5 design note before it was measurable, and the reason the
positional sections lose slots they previously won. See [[experiments.e15-expected-gain]].

## Ablation as a first-class property

Because findings carry `section`, removing an agent means filtering the profile. The arbiter,
planner and explainer are unchanged. That makes [[evaluation]]'s B3 a configuration flag rather than
a code branch — and an agent that cannot demonstrate lift when re-added is retired.

## Failure and partial results

- An agent that errors is **recorded as failed** for that run; the profile keeps the previous
  findings for its section, marked stale. It never silently produces nothing that looks like
  "no problems found".
- The distinction between *no finding* and *no data* is explicit: a section with insufficient games
  reports `insufficient_data`, which the explainer must surface rather than hide. Telling a player
  "your endgames are fine" when we analysed four endgames is a lie of omission.

## Scheduling

One-shot per session, not a live loop: ingest → analyse → sections → arbiter → probe → plan.
Re-runs on new games reuse the position cache, so incremental sessions cost far less than the first.
