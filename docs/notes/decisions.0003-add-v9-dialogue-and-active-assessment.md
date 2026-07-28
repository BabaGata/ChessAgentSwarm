---
id: cas-adr-0003
title: 'ADR-0003 — Add V9: dialogue & active assessment to the vision'
desc: 'M1 research showed passive game analysis cannot separate knowledge gaps from skill gaps, so interaction is a core capability, not a presentation layer.'
updated: 1785254600000
created: 1785254600000
---

# ADR-0003 — Add V9: dialogue & active assessment to the vision

**Date:** 2026-07-28 · **Status:** accepted

## Context

[[vision]] originally listed eight capabilities, all of which describe *analysis* of the player.
[[mission]] already carried a "gap watch" noting that player-facing interaction quality was not
explicitly scheduled anywhere.

M1 research turned that suspicion into a finding (L-002 in [[learning.lessons]]): the same observable
error has at least four distinct causes — knowledge gap, skill gap, process/habit gap, psychological
gap — and **games alone cannot distinguish them**. Absence of a move is weak evidence of not knowing
it, and a correct move may be played for the wrong reason. Coaching sources independently describe
assessment as a dialogue that continues over weeks, not a one-off analysis.

If interaction had stayed unnamed in the vision, it would have been designed late, as a UI concern,
and V2 (knowledge assessment) and V4 (gap detection) would have been quietly unachievable.

## Decision

Add **V9 — Dialogue & active assessment** to [[vision]]: the system must ask the player what games
cannot reveal, and probe knowledge with positions where the player supplies a move *and its reason*.

Add the matching dimension **D12** to the [[state]] scorecard (total becomes 60).

## Alternatives considered

- **Leave it implicit inside V2/V4.** Rejected: those read as analysis capabilities, and what is not
  named does not get scheduled, evaluated, or scored.
- **Treat it as an M3 architecture concern only.** Rejected: it is a property of the finished system,
  which is what the vision describes; architecture is *how*, not *what*.

## Consequences

- **Easier:** M3 must now design an interaction protocol, and it will be evaluated like any other
  capability rather than assumed.
- **Harder:** adds a capability that is genuinely hard to evaluate — probe quality is subjective.
  [[evaluation]] must grow a method for it.
- **Cost:** dialogue means LLM calls in a player-facing loop, which pushes against C1. ADR-0002's
  "compute first, speak last" split is what keeps this affordable; the two ADRs are coupled.

## Vision link

Enables V2 and V4 to be honestly achievable; adds V9 itself.

## Revisit when

Probe-based assessment proves unreliable in practice (players answer to please, or cannot articulate
reasons), in which case V9 should be narrowed to context questions only.
