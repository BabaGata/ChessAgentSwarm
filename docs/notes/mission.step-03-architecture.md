---
id: cas-mission-m3
title: 'M3 — Swarm architecture'
desc: 'Design the whole system: profile schema, orchestration, interaction, confidence, storage.'
updated: 1785256700000
created: 1785256700000
---

# M3 — Swarm architecture

**Status:** design done; build and test outstanding
**Parent:** [[mission]] · **Delivers:** [[architecture]] and its children

## Goal

Design the system that turns a player's games into a coaching path: how agents are orchestrated,
how their knowledge is combined, how the player interacts, where knowledge lives, and how efficacy
is measured. Build it, test it, improve it.

## Alignment check

- **Serves:** every vision item — this is the step where V1–V9 acquire a mechanism. Most directly
  V8 (evidence-carrying findings) and V9 (probe protocol), and C1 (the cost architecture).
- **Moves:** architecture capacity, and unblocks the vision scorecard, which cannot move until
  agents exist (M4).
- **Cheaper alternative considered:** build S2 first and let the architecture emerge from it.
  Rejected — the profile schema is the integration contract for eleven agents, and a schema
  reverse-engineered from the first agent would encode that agent's accidents. But the concern
  behind it is fair, so the design is deliberately thin: the `claim.kind` enum is left open and grows
  with each section rather than being guessed now.
- **Forecloses:** emergent cross-agent reasoning (ADR-0006, accepted knowingly); concurrent
  multi-user use (ADR-0007, a stated non-goal).
- **Made more aligned by:** requiring `progress_sign` on every plan step, which converts V6/V7 from
  aspiration into something the system can be measurably wrong about; and by requiring
  `gap_type.determined_by`, which stops V9's contribution from silently evaporating into inference.

## Decisions taken

| Question | Decision | Record |
|---|---|---|
| C1 player profile schema | typed Findings with evidence, provenance, uncertainty and context; persistent | [[architecture.player-profile]] |
| C3 orchestration pattern | staged blackboard; no inter-agent messaging | [[decisions.0006-staged-blackboard-orchestration]] |
| C2 confidence policy | tiers with distinct-game minimums, peer comparison, held-out replication | [[architecture.confidence]] |
| B4 report vs conversation | both — report is the artefact, dialogue is the assessment | [[architecture.interaction]] |
| storage | SQLite position cache keyed by (position, engine, depth); JSON profiles | [[decisions.0007-storage-sqlite-cache-json-profile]] |

## What each experiment forced into the design

Recorded explicitly, because a design that cannot name its evidence is a design built on taste:

| Evidence | Design consequence |
|---|---|
| E01 — 50 games in ~90 s | the analysis core can be deterministic and exhaustive; no sampling shortcuts needed |
| E01 — labels shift with depth | depth is part of the cache **key** and of every finding's provenance; profiles at different depths never merge |
| E01 — longest game dominates wall time | parallelise per position, not per game |
| E02 — features detectable, base rates enormous | findings need `peer_rate`; presence alone may not be asserted |
| E03 — error-association is a weak signal | relevance rests on peer deviation; `claim.context` is part of the claim's identity |
| E03 — a striking effect reversed on held-out players | replication is a **promotion requirement**, not a review nicety |
| Prior art — all five are stateless | the profile persists across sessions; that is what V7 needs |
| Prior art — one LLM call per game | rejected; language layer reads the profile, so tokens scale with findings |

## Definition of done

- [x] Player profile schema specified, with the failure each field prevents.
- [x] Orchestration pattern chosen, with the rejected alternatives and their reasons.
- [x] Interaction and probe protocol specified, including what a probe can overturn.
- [x] Confidence policy with concrete (provisional) thresholds and a validation plan.
- [x] Storage decided; cost budget stated against measurements.
- [x] **Built** — skeleton implementing ingest → analysis core → profile, with the schema as code.
      `chesscoach/` package, CLI runs layers 1→2→4 end to end.
- [x] **Tested** — 74 tests, 85 % coverage. Determinism, cache correctness and profile round-trip all
      covered; determinism additionally verified on real games (byte-identical profile across runs).
- [x] **Evaluation harness** — planted-weakness generator, split-half check, ground-truth scoring
      and fixture verification, all built before the first agent ([[evaluation]] build order).
      Verified end to end: planted moves 7.7 % error rate vs 4.3 % baseline, lift 1.81×.
- [ ] Confidence thresholds validated against real data ([[architecture.confidence]] — currently
      provisional).

## Working log

| Date | Activity | Alignment check | Outcome |
|---|---|---|---|
| 2026-07-28 | Designed the architecture from E01–E03 evidence and prior-art gaps | see above | 4 architecture notes, 2 ADRs; C1, C2, C3, B4 resolved |
| 2026-07-28 | Built the evaluation harness before the first agent | Serves [[evaluation]] and C2's runtime rule — the split-half check is both, so it is built once and used twice. Building it first paid immediately: checking the fixture against the analysis core exposed that it was unrealistically clean (L-009), which an agent-first order would have discovered only after an agent had been scored against it | 3 modules, 2 CLI commands, 40 new tests; fixture verified at 1.81× lift |
| 2026-07-28 | Built the skeleton test-first: ingest, analysis core, profile, CLI | Serves C5 (auditable) and unblocks M4; the profile schema had to exist as code before any agent could emit findings. Cheaper alternative — build S2 first and let the schema emerge — was rejected in the step's alignment check, and building confirmed the call: two design improvements (pure `to_position_eval`, injected analyser) came from testability pressure that an agent-first order would have applied too late | 74 tests, 85 % coverage; 1,860 real moves analysed; identical profile across runs |
