---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-07-28
**Active mission step:** M1 — [[mission.step-01-foundations]] (nearly closed)
**Last commit:** `research(M1): E01 engine throughput and diagnosis stability`

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
| Measured evidence | **first experiment done** | [[experiments.e01-engine-throughput]] |
| Section catalogue | no | M2 |
| Architecture design | partial | [[decisions.0002-compute-first-speak-last]] accepted; player-profile schema (C1) undesigned |
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
| Domain knowledge (chess) | 3 | +1 | first primary source held and used; contested claims now sourced rather than asserted |
| Domain knowledge (coaching) | 2 | — | still secondary sources; F2 outstanding |
| Signal & tooling knowledge | 4 | +1 | engine + API verified by running them; throughput and label stability measured |
| Prior-art knowledge | 5 | +4 | all five read; adopt/avoid/differentiate recorded |
| Architecture | 2 | +1 | ADR-0002 accepted on evidence; profile schema still open |
| Evaluation design | 1 | — | intent only |

## Next logical steps (priority order)

1. **P0 — Author decisions B1–B3** ([[open-questions]] § B). Target band, game source, whether
   over-the-board players are in scope. These are not researchable; they gate M2's priorities and
   M3's scope. Recommendations are recorded against each.
2. **P1 — E02: positional feature detectors** (question D4, now well-framed). Take 3–4 concepts from
   the free corpus — knight outpost, isolated queen's pawn, backward pawn, open-file control — write
   conservative detectors over `python-chess`, and check them by hand against real games. Report
   precision honestly. This is the project's biggest technical risk and it is now cheap to probe.
3. **P2 — Close M1: read the free primary sources** (F2). Capablanca is held; Nimzowitsch next,
   for the positional vocabulary P1 needs.
4. **P3 — M2 section catalogue**, built on K1–K10, the four gap types, and the puzzle-theme
   vocabulary — which already supplies a ready-made tactical section boundary.
5. **P4 — C2 minimum-sample policy.** Promoted in importance by E01: it is what makes claims survive
   a change of analysis parameters. Adopt the shape of prior art's escalation tiers and validate
   thresholds on our own data.

## Open questions

Full register with owners and resolution paths: **[[open-questions]]**.
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
