---
id: cas-adr-0006
title: 'ADR-0006 — Staged blackboard orchestration, no inter-agent conversation'
desc: 'Agents communicate only through the shared player profile, in stages, and never message each other.'
updated: 1785256500000
created: 1785256500000
---

# ADR-0006 — Staged blackboard orchestration

**Date:** 2026-07-28 · **Status:** accepted

## Context

The project is an "agent swarm", and the default reading of that phrase in 2026 is agents that talk
to each other — debating, critiquing, negotiating a conclusion. Before adopting that by reflex, it
has to be checked against what this system actually needs.

Three things constrain the choice. Diagnosis is **deterministic computation**
([[decisions.0002-compute-first-speak-last]]). Each agent must be **independently evaluable**, since
[[mission]] M5 asks after every agent whether it earned its place. And cost must scale with
information, not with activity (C1).

## Decision

**Staged blackboard.** Agents read and write the shared [[architecture.player-profile]] and
communicate only through it. Section agents run in parallel and in isolation within a stage. **No
agent sends a message to another agent.** Language models appear only in the final stages
(prober, planner, explainer), operating on the profile.

## Alternatives considered

- **Conversational multi-agent swarm.** Rejected on four counts: cost scales with chatter;
  stochastic conversation breaks the determinism [[evaluation]]'s B4 requires; ablation (B3) becomes
  meaningless once agents influence each other; and a claim that emerged from a negotiation traces to
  a transcript rather than to evidence, which fails V8. Decisively, it buys nothing here — the agents
  measure different things about the same games, so there is nothing to argue about.
- **Single planner with tools.** The prior-art design: one model call per game. It works, and it is
  precisely what cannot be evaluated or improved per component ([[domain.prior-art]]).
- **Linear pipeline.** Rejected: sections do not feed one another, so ordering them invents a
  dependency and adds latency.

## Consequences

- **Easier:** ablation becomes a filter on `section`; determinism is achievable; cost is predictable;
  a new section agent is additive and cannot break existing ones.
- **Harder:** the profile schema carries the entire integration burden. Any cross-agent insight must
  be expressed as data, or it cannot be expressed at all.
- **Forecloses:** genuinely emergent cross-agent reasoning. Accepted deliberately — that is the part
  that cannot be evaluated, and an unevaluable coaching claim is worth less than no claim.
- **Risk:** if some diagnosis genuinely requires two sections to reason jointly, this design cannot
  express it. The escape hatch is a dedicated agent that reads several sections' findings from the
  profile — still no messaging.

## Vision link

Serves C1 (cost), C5 (auditable), V8 (explainability), and makes M5's per-agent assessment possible
at all.

## Revisit when

A finding demonstrably requires joint reasoning between sections that cannot be expressed as a
derived agent reading the blackboard.
