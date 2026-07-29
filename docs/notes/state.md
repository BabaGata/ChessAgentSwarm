---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-07-28
**Active mission step:** **M3** — [[mission.step-03-architecture]] (design done, build outstanding)
**Last commit:** `design(M3): swarm architecture`

Rewritten at the end of every cycle. The honest answer to "if someone joined today, what would they
need to know?"

## What exists

| Area | Exists | Notes |
|---|---|---|
| Documentation / steering | yes | full vault; [[open-questions]] register; 4 ADRs |
| Process automation | yes | `adaptive-cycle` skill, exercised over several cycles |
| Chess domain knowledge | first pass + primary source | [[domain.chess-concepts]], [[domain.coaching]], [[domain.signals]], [[domain.puzzle-themes]], [[domain.sources]] |
| Prior-art knowledge | **complete** | [[domain.prior-art]] — all five projects read |
| Tooling | **verified working** | Stockfish 18 driven from python-chess; Lichess API fetching real games |
| Measured evidence | **three experiments** | [[experiments.e01-engine-throughput]], [[experiments.e02-positional-detectors]], [[experiments.e03-relevance-weighting]] |
| Positional vocabulary | yes | [[domain.positional-vocabulary]] — rated for detectability |
| Section catalogue | **yes, first pass** | [[domain.sections]] — 11 sections, 3 tiers, build order set |
| Working detectors | **4, tested** | outpost, isolated pawn, backward pawn, rook on open file — experiment code, to be reimplemented in M4 |
| Scope | **decided** | [[decisions.0005-scope-band-source-online-only]] — 1400–1800, Lichess, online only |
| Architecture design | **done** | [[architecture]] + 3 children; profile schema, orchestration, interaction, confidence, storage all specified |
| Architecture **built** | no | M3's remaining half — skeleton, tests, evaluation harness |
| Any agent | no | M4 |
| Evaluation harness | no | designed in M3 |
| Production code | none | only experiment harnesses, which are measurement tools |

## Distance to vision

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | 0 | — | nothing built |
| D2 | V2 knowledge assessment | 0 | — | method identified (probes), unbuilt |
| D3 | V3 style profiling | 0 | — | operational definition drafted |
| D4 | V4 gap detection | 0 | — | signals + motif approach known, unbuilt |
| D5 | V5 prioritisation | 0 | — | band table gives a starting heuristic |
| D6 | V6 path planning | 0 | — | |
| D7 | V7 progress tracking | 0 | — | leading indicators identified |
| D8 | V8 explainability | 0 | — | |
| D9 | C1–C4 cost profile | 0 | — | *measured but not yet built into anything* — see below |
| D10 | Evaluation capability | 0 | — | confirmed novel: no prior-art project evaluates coaching correctness |
| D11 | Process & documentation health | 4 | — | cycle held up under real work, including reversing its own mis-framed question |
| D12 | V9 dialogue & active assessment | 0 | — | |

**Total: 4 / 60.** Unchanged, and correctly so — the vision scorecard measures *system capability*,
and no agent exists yet. D9 deserves comment: the cost question is now *answered* (it is negligible),
but the score stays 0 because scoring measures a working system, not knowledge about one.

## Capacity readiness

This is what actually moved this cycle.

| Capacity dimension | Score 0–5 | Δ | Note |
|---|:--:|:--:|---|
| Domain knowledge (chess) | 4 | +1 | primary sources in use; positional vocabulary assembled and rated for detectability |
| Domain knowledge (coaching) | 2 | — | still secondary sources; F2 partially addressed |
| Signal & tooling knowledge | 5 | +1 | engine, API, tactical and positional detection all verified **by running them** |
| Prior-art knowledge | 5 | — | complete |
| Architecture | 4 | +1 | fully specified — profile schema, orchestration, interaction, confidence, storage — and each choice traced to a measurement or a rejected alternative. Not yet built |
| Evaluation design | 3 | +2 | design space mapped across 7 families with a 3-tier strategy and a build order; harness not written |

## Next logical steps (priority order)

1. **P0 — Build the M3 skeleton.** Ingest → analysis core → profile, with
   [[architecture.player-profile]] as code and the SQLite cache keyed by (position, engine, depth).
   Tests: determinism, cache correctness, profile round-trip. This is the first production code in
   the project; its design note now exists, so the guardrail is satisfied.
2. **P1 — Evaluation harness, before the first agent.** Per [[evaluation]]'s build order: the
   planted-weakness generator (family C) and the split-half check (B1). E03 demonstrated why — the
   project would already have recorded a false finding without held-out replication (L-008). The
   split-half check is also a **runtime** requirement of [[architecture.confidence]], so it is built
   once and used twice.
3. **P2 — Validate the confidence thresholds.** Every number in [[architecture.confidence]] is
   provisional. Check that split-half agreement is actually achieved at those values before the
   first agent depends on them.
4. **P3 — M4: build S2** (decision process & clock behaviour), the first agent. Cheapest, needs no
   engine for most of its signal, and E03 strengthens the case: at this band, process and tactics
   look far more decisive than structure.
5. **P4 — Peer reference rates.** Build the rating-band reference population once from the Lichess
   open database. Serves C6's remaining route *and* evaluation metric D2.
6. **P5 — Close M1's last item:** verify *My System*'s Part-2 chapter list against the text.

## Open questions

Full register with owners and resolution paths: **[[open-questions]]**.
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
