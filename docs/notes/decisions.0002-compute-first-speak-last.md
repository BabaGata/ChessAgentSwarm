---
id: cas-adr-0002
title: 'ADR-0002 — Compute first, speak last'
desc: 'Deterministic analysis produces a structured player profile; language models operate on the summary, never on raw games.'
updated: 1785254600000
created: 1785254600000
---

# ADR-0002 — Compute first, speak last

**Date:** 2026-07-28 · **Status:** **accepted** 2026-07-28

## Acceptance evidence

Proposed on reasoning, accepted the same day on evidence:

1. **Independent convergence.** Arrakis Engine, a mature shipped system, states the same "two-step
   analysis" insight as its core design ([[domain.prior-art]]). It was arrived at independently.
2. **The deterministic layer is affordable.** [[experiments.e01-engine-throughput]] measured a
   player's full recent history at 89 s (depth 15) on this laptop, at zero cash cost — so the
   compute-heavy half of the architecture costs essentially nothing.
3. **The deterministic layer is also the *trustworthy* half.** E01 showed per-move labels shift with
   analysis depth, which means claims must be aggregate and evidence-backed — something a structured
   profile supports and free-form LLM narration does not.
4. **Token cost of the language layer is small and known.** Prior art runs a rich cross-game summary
   in ~200–250 tokens.

## Context

Constraint C1 requires the system to be free or near-free to operate. The obvious architecture for
an "LLM chess coach" — feed games to a language model and ask what the player should work on — has
two fatal properties for this project: cost scales with the number of moves analysed, and the output
is unfalsifiable chess-flavoured prose (risk R-02, R-12).

M1 research ([[domain.signals]]) found that essentially every diagnostic signal a human coach uses is
**deterministically computable** from an engine, a PGN parser and statistics: phase-wise error
profiles, missed tactics, the motif of the refutation, clock behaviour, conversion rates, repertoire
performance, and style tendencies. Free tooling covers all of it (Stockfish, python-chess, Lichess
API and the CC0 puzzle database with motif tags).

## Decision

Structure the swarm in two layers:

1. **Analysis core (deterministic).** Engine + parsing + statistics produce a *structured player
   profile*: typed, evidence-carrying facts, each traceable to specific games and positions.
2. **Language layer (LLM).** Operates only on the structured profile — to explain, to conduct probe
   dialogue with the player, to plan the coaching path, and to interpret free-text answers.

A language model never reads raw game data in bulk. Token volume per player becomes roughly constant
instead of proportional to moves analysed.

## Alternatives considered

- **LLM-over-raw-games.** Simplest to build, and what most prior art does. Rejected: violates C1 at
  any real volume, and produces claims that cannot be traced to evidence (breaks V8).
- **Fully deterministic, no LLM.** Cheapest and fully auditable, but cannot conduct the probe
  dialogue that L-002 shows is necessary to separate knowledge gaps from skill gaps, and cannot
  explain findings in a way a player can act on.
- **Fine-tuned local chess model.** Attractive for C1, but a training project of its own and out of
  scope for the thesis timeline.

## Consequences

- **Easier:** cost control (C1), reproducibility, explainability (V8) — every statement in the
  profile has a position attached; evaluation, because the analysis core's outputs are typed and
  testable without a human judge.
- **Harder:** the structured player profile schema becomes a central, load-bearing design artefact
  that all agents must agree on. Getting it wrong is expensive.
- **Forecloses:** free-form "just ask the model about the game" behaviour anywhere in the system.
- **Open risk:** positional/strategic weaknesses may not be computable the way tactical ones are
  (tactics have machine-generated labels, strategy does not). If a large part of coaching turns out
  to need un-computable judgement, this ADR's balance shifts and must be revisited.

## Vision link

Serves C1–C4 (cost), V8 (explainability), and indirectly V4 (gap detection needs typed evidence).

## Revisit when

- The engine-throughput measurement (P1 in [[state]]) shows deterministic analysis is *itself* too
  expensive on the target hardware; or
- M2/M3 show that the highest-priority knowledge sections are ones no deterministic signal can reach.
