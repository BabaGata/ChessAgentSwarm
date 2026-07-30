---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-07-28
**Active mission step:** **M6/M7** — maintain, then repeat M4 with the next capability
([[mission.step-05-assess-s2]] done)
**Last commit:** `feat(M5): orchestrator, and two defects found by real players`

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
| Architecture **built** | **skeleton done** | `chesscoach/` — ingest, analysis core, profile, CLI. Sections, arbiter and language layer outstanding |
| Evaluation harness | **built, before the first agent** | `chesscoach/evaluation/` — split-half (B1), planted weaknesses (family C), ground-truth scoring, fixture verification |
| **First agent (S2)** | **built, scored, assessed on real data** | finds the planted weakness at 5.54× with 0 spurious; **says nothing about any of 7 real players**, which is honest and is the ceiling described in [[mission.step-05-assess-s2]] |
| Orchestration | **built** | `chesscoach/orchestrator.py` — fan-out, failure isolation, section-scoped replacement. Findings now reach the profile |
| Shared pipeline | **built** | `chesscoach/pipeline.py` — engine/cache session and provenance, extracted in M6 from three copies |
| Peer reference corpus | **built and widened** | `chesscoach/peers.py` — **38 players, ~820 games**, band 1400–1800 rapid, depth 15, leave-one-out. Population rates converged (17.7 % → 17.8 %); borderline verdicts did not (L-013) |
| Parallel analysis | **built** | `chesscoach/analysis/parallel.py` — corpus-wide dedup + prefetch. ~3× on a cold cache, measured |
| Confidence policy | **enforced at runtime** | `chesscoach/confidence.py` — tiers, distinct-game counts, split-half replication as a promotion requirement |
| Production code | **yes, first** | design note existed first, so the guardrail held |
| Any agent | no | M4 |
| Evaluation harness | no | designed in M3 |
| Production code | none | only experiment harnesses, which are measurement tools |

## Distance to vision

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | 0 | — | nothing built |
| D2 | V2 knowledge assessment | 0 | — | method identified (probes), unbuilt |
| D3 | V3 style profiling | 0 | — | operational definition drafted |
| D4 | V4 gap detection | **2** | **+1** | verified against ground truth, and now **population-relative**: two real players carry a claim that survives comparison with their peers. One of eleven sections |
| D5 | V5 prioritisation | 0 | — | band table gives a starting heuristic |
| D6 | V6 path planning | 0 | — | |
| D7 | V7 progress tracking | 0 | — | leading indicators identified |
| D8 | V8 explainability | **1** | **+1** | findings carry evidence and provenance, enforced by the schema; nothing presents them to a player yet |
| D9 | C1–C4 cost profile | **1** | **+1** | analysis and diagnosis both run at zero cash and seconds of wall clock; the language layer is unbuilt, so the session total is still unmeasured |
| D10 | Evaluation capability | **2** | **+2** | harness built *and used* — it caught a fixture confound before it became a false result |
| D11 | Process & documentation health | 4 | — | cycle held up under real work, including reversing its own mis-framed question |
| D12 | V9 dialogue & active assessment | 0 | — | |

**Total: 10 / 60** (was 9). Eight of twelve dimensions remain at zero, which is the honest picture:
one section of eleven exists, and nothing yet speaks to a player in words.

What changed this cycle is smaller than it sounds and more important than it looks: the system can
now distinguish *"you do this"* from *"players at your level do this"*, which is the difference
between a description and a diagnosis.

## Capacity readiness

This is what actually moved this cycle.

| Capacity dimension | Score 0–5 | Δ | Note |
|---|:--:|:--:|---|
| Domain knowledge (chess) | 4 | +1 | primary sources in use; positional vocabulary assembled and rated for detectability |
| Domain knowledge (coaching) | 2 | — | still secondary sources; F2 partially addressed |
| Signal & tooling knowledge | 5 | +1 | engine, API, tactical and positional detection all verified **by running them** |
| Prior-art knowledge | 5 | — | complete |
| Architecture | 4 | +1 | fully specified — profile schema, orchestration, interaction, confidence, storage — and each choice traced to a measurement or a rejected alternative. Not yet built |
| Evaluation design | 4 | +1 | design space mapped; harness built and proven useful. Predictive-validity (A1) and anti-pattern (D) families still unbuilt |

## Next logical steps (priority order)

1. **P0 — M4 again: build S1 (tactical pattern gaps).** Now the clearest priority rather than the
   next in line. Across 38 players S2 produces **one kind of claim**, for 16 % of them; a system that
   can only say "you err after long thinks" is not a coach. S1 is the richest section, its free
   labelled vocabulary is already mapped in [[domain.puzzle-themes]], and every piece of machinery it
   needs — profile, confidence, peers, orchestrator, evaluation — now exists.
2. **P1 — Implement evaluation metric D1 (inter-player divergence).** It would have caught M5's
   base-rate finding automatically instead of by eye, and it would have flagged the
   one-claim-kind problem above without a manual sweep.
3. **P2 — Validate the remaining confidence thresholds.** `PRIORITY_MARGIN` was set from measurement
   (L-013); the rest are still provisional and the split-half harness exists to check them.
4. **P3 — Widen the reference further and add time controls.** 38 players is workable for rapid;
   blitz and classical have no reference at all, and S2's time-pressure condition needs a shorter
   time control before it can be tested on real data.
4. **P3 — Peer reference rates.** Build the rating-band reference population once from the Lichess
   open database. Serves C6's remaining route *and* evaluation metric D2.
5. **P4 — Per-position parallelism** in the analysis core. The seam exists (the analyser is
   injected); E01 measured that per-game parallelism is dominated by the longest game. Not urgent —
   the current speed is already comfortable.
6. **P5 — Close M1's last item:** verify *My System*'s Part-2 chapter list against the text.

## Open questions

Full register with owners and resolution paths: **[[open-questions]]**.
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
