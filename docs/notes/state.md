---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-08-03
**Active mission step:** **M6/M7** — maintain, then repeat M4 with the next capability
([[mission.step-05-assess-s2]] done)
**Last commit:** `chore(M3): deeper histories for more players, and a run that survives a crash`

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
| **S2 decision process** | **built, scored, assessed** | finds the planted weakness at 5.54× with 0 spurious. One working detector in practice |
| **S1 tactical gaps** | **built, assessed** | eight motif detectors, precision-gated by E04; took the swarm from 1 claim kind to **6** → [[mission.step-07-second-iteration]] |
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
| D2 | V2 knowledge assessment | **1** | **+1** | **the prober's deterministic core exists** — probe selection, move check, inference table, `gap_type` written back (`chesscoach/prober.py`, 28 tests). Not 2: no model sits behind the classifier seam yet and the rubric is unvalidated, so no real player has been asked anything |
| D3 | V3 style profiling | 0 | — | operational definition drafted |
| D4 | V4 gap detection | **3** | **+1** | **two sections, six claim kinds**, peer-compared, detectors precision-gated. 9 of 38 real players carry a finding; one carries a three-part profile |
| D5 | V5 prioritisation | **1** | **+1** | arbiter built: picks one or two from a multi-part profile, deterministically, with stated reasons. No time estimates or expected-gain reasoning yet |
| D6 | V6 path planning | **2** | **+2** | plans built and persisted, every step carrying a machine-checkable progress sign and a derived check point. No time estimates — D5 is unresolved and inventing them was refused |
| D7 | V7 progress tracking | **3** | **+1** | **restored, on evidence this time.** 57 predictions from 84 players with ~150-game histories; the constant is cross-validated at 2 *and* 5 folds with a fold spread of 0.011, and a held-out false-positive rate of **15 %** is stated in the output. Not 4: the test's **power is unmeasured** — no coached cohort exists, so nothing shows a real improvement could clear the bar (**D8**) |
| D8 | V8 explainability | **1** | **+1** | findings carry evidence and provenance, enforced by the schema; nothing presents them to a player yet |
| D9 | C1–C4 cost profile | **1** | **+1** | analysis and diagnosis both run at zero cash and seconds of wall clock; the language layer is unbuilt, so the session total is still unmeasured |
| D10 | Evaluation capability | **3** | **+1** | harness built *and used*; **both sides of the progress check are now measured** — false-positive rate (E05) and power (E06), the latter with its confound tested rather than conceded |
| D11 | Process & documentation health | 4 | — | cycle held up under real work, including reversing its own mis-framed question |
| D12 | V9 dialogue & active assessment | **1** | **+1** | probe generation is real and bounded, and a probe can overturn the finding that produced it. Nothing yet conducts a session, and the context questions (interaction step 2) are unbuilt |

**Total: 20 / 60.** It has gone 17 → 16 → 17 → 16 → 17 → 18 → 20, and every move was forced by a measurement:
down when E05 showed the verdicts meant nothing, up when the target rule was recalibrated, down
again when cross-validation showed that calibration was itself optimistic, and up now that 57
predictions can support what 13 could not, and again now that both sides of the progress check are
measured rather than one. A scorecard that only went up would not be measuring anything.

The loop is closed — diagnose, prioritise, predict, check — and the prediction is now both demanding
and **quantified**: about 15 % of untreated players meet it, held out rather than in-sample.

**Two of twelve dimensions remain at zero**, down from four: D1 skill assessment and D3 style
profiling. D2 and D12 moved off zero for the first time because the prober's core exists — the swarm
can now *form a question*, even though it cannot yet interpret the answer. That is the empty column
starting to fill, and it is the first movement there in the project's history.

The uncomfortable part of this cycle is not the score. Deepening the histories did not just add
predictions, it **moved the effect being measured** — drift fell from +11.2 points to +4.8, and the
old constant turned out to be unmeetable rather than conservative (1 of 52). The control was as
sample-dependent as the thing it controlled for (L-019).

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

0. **P0 — Put a model behind the classifier seam, and validate it.** The prober cannot be used on a
   real player until both exist. Two decisions are open and the first is the author's:
   **which model** — a local small model is preferred under C1 and is plausibly sufficient, since the
   task is short-text classification against a supplied label rather than chess reasoning — and
   **the hand-labelled answer set** with inter-rater agreement, which [[capacity.agents.prober]] § 4
   requires *before* any probe result may change a finding. Building the classifier without the
   answer set would produce a system that looks finished and cannot be believed.

1. **~~P0 — More predictions, so the constant can be calibrated at all.~~ Done 2026-08-03.**
   84 players, ~150 games each, 57 predictions. Fold spread 0.011; the constant is now estimated
   rather than guessed, and it moved 0.34 → 0.58 because the drift it corrects for was largely an
   artefact of the old sample's thinness (L-019).
2. **~~P0 — The constant is depth-dependent and the planner ignores that.~~ Done 2026-08-03 (D9).**
   Isolated properly: same players, outcome period whole, measurement period capped. Real, monotone,
   modest — fitted constant 0.488 → 0.594. **It also corrected L-019**, which had attributed a
   cross-corpus difference entirely to depth: 0.34 was never a fitted value, and drift at K=30 is
   +7.4 % rather than +11.2 %. Resolved by stating the measured **range (15–23 %)** in the output
   rather than fitting a curve through four points.
3. **~~P0 — The test's power is unknown.~~ Partly answered 2026-08-03 (D8)** →
   [[experiments.e06-progress-power]]. **The target is reachable** — improvers met it 25 % against
   8 %, and the regression confound is measurably absent. But p = 0.120 on 7 met events: suggestive,
   not established. Enough to justify building the prober, not enough to claim the swarm's targets
   detect improvement. Closing it properly needs a treated cohort (outside C1) or far more data.
2. **P1 — External validation of the detectors** against the CC0 puzzle themes. The strongest
   evidence available, because the labels are independent of me; E04 hand-checked only two motifs
   thoroughly. Needs the puzzle dump, for validation only.
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
Resolved this cycle: A1, A2, C5, D1, D2, E1, F1. Reframed: D4. Added: C7 constraint, and
**D8** (the progress check's power) and **D9** (the constant is depth-dependent) — both surfaced by
fixing the calibration, which is the usual pattern: resolving a question exposes the two behind it.
Author-owned and waiting: B1–B5.

## Blockers

None technical. B1–B3 are waiting on the thesis author, but P1 and P2 can proceed without them.
