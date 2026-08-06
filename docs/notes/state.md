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
| D1 | V1 skill assessment | **3** | **+3** | **built and cross-validated** → [[experiments.e13-strength-signal]]. Rating estimated from blunder rate alone at **±103 points held-out** (60 % within 100, 89 % within 200) against a naive baseline of 162, with the rating hidden from the estimator. Reported as a range, refuses below 200 moves, admits extrapolation. Not 4: **the vision asks for strength *and its variance*** and this gives every player the same population-level error bar regardless of how much evidence they brought — known to be wrong |
| D2 | V2 knowledge assessment | **2** | **+2** | **the prober works end to end** — probe selection, move check, a local model classifying reasons at kappa 0.74 with zero false-ignorance (E07), `gap_type` written back. Not 3: the rubric's answer set is written and labelled by the author and the figure is in-sample, so it may not yet change a real player's finding |
| D3 | V3 style profiling | **2** | **+2** | **built, and half of it deliberately refused** → [[experiments.e14-style-dimensions]]. One measured tendency — how much of a player's game is spent with the queens off — that varies between players (1.40) and is **independent of strength** (r = −0.069). Four of six candidates turned out to be strength wearing a style label. Not 3: **the performance half does not survive** — everyone errs ~20 % less with queens off and players barely differ, so the report says what a player tends to do and refuses to say whether it suits them |
| D4 | V4 gap detection | **5** | **+1** | **seven sections, and on 150-game histories the swarm advises 70 of 84 players (83 %)** with 27 distinct claim kinds and overlap 0.05 — louder, broader and more specific at once, and 113/113 grounded. The lever was corpus depth, not more sections: six sections moved coverage 24 → 53 %, depth alone moved it 53 → **83 %** (E12). Held back from a clean 5 by the honest caveat: **a real user brings 24 games, not 150**, and at that depth it is still 53 % |
| D5 | V5 prioritisation | **3** | **+1** | **the swarm now ranks by what a weakness costs** → [[experiments.e15-expected-gain]]. Every claim whose instances are mistakes carries the win probability given away on exactly those moves, and the arbiter orders confidence → can it state a cost → the cost → how unusual. It **changed the advice for 33 of 84 players** without collapsing it (11 claim kinds and 7 sections before and after). Not 4: it is an **accounting** cost, not a forecast — nothing shows a player who fixes the priciest weakness gains more than one who fixes another, and the four positional sections cannot price themselves at all, so they now lose slots by policy rather than by measurement |
| D6 | V6 path planning | **2** | **+2** | plans built and persisted, every step carrying a machine-checkable progress sign and a derived check point. No time estimates — D5 is unresolved and inventing them was refused |
| D7 | V7 progress tracking | **3** | **+1** | **restored, on evidence this time.** 57 predictions from 84 players with ~150-game histories; the constant is cross-validated at 2 *and* 5 folds with a fold spread of 0.011, and a held-out false-positive rate of **15 %** is stated in the output. Not 4: the test's **power is unmeasured** — no coached cohort exists, so nothing shows a real improvement could clear the bar (**D8**) |
| D8 | V8 explainability | **3** | — | the report exists, is deterministic, and is **13/13 grounded** on real players (E08 D4). **The 3 claimed last cycle was not earned**: reading a real report found Lichess theme keys in player-facing prose — *"a `trappedPiece` punishes you"* — which the groundedness metric scored 100 % on, because it only checks citation. Fixed (`phrasing.subject_name`), so the score now stands. Not 4: the report states measurements without explaining *why these one or two* were chosen over the rest, and the arbiter's reasoning is invisible |
| D9 | C1–C4 cost profile | **3** | **+1** | **a whole session has now been run end to end and timed.** `cli coach` takes a username and produces a report: **7.6 s** for 60 games on a warm cache, and for a fresh player the cost is dominated by engine analysis — E01's 89 s per 50 games at depth 15, so roughly two minutes. Probes add ~2.7 s each (E07). **Zero cash throughout.** Not 4: the figure is one player on one machine, and no cold-cache session has been timed cleanly |
| D10 | Evaluation capability | **4** | **+1** | both sides of the progress check measured (E05, E06), and the **anti-pattern family D is now built and run** (E08) — the metrics that were designed cycles ago and blocked on a language layer. They caught a self-flattering score and nearly caused a misreading, which is what an evaluation capability is for |
| D11 | Process & documentation health | 4 | — | cycle held up under real work, including reversing its own mis-framed question |
| D12 | V9 dialogue & active assessment | **3** | **+1** | **the whole interaction exists**: four context questions before the analysis, probes after it, both feeding the profile, and probe results now reaching the diagnosis inside a coaching session. Answers accumulate as a dataset by-product. Not 4: the classifier's rubric is still the author's own (D10), and the dialogue is four fixed questions rather than anything adaptive |

**Total: 37 / 60**, and **no dimension is at zero.** It has gone 17 → 16 → 17 → 16
→ 17 → 18 → 20 → 22 → 25 → 26 → 27 → 28 → 29 → 32 → 34 → 36 → 37, and every move was forced by a
measurement:
down when E05 showed the verdicts meant nothing, up when the target rule was recalibrated, down
again when cross-validation showed that calibration was itself optimistic, and up now that 57
predictions can support what 13 could not, and again now that both sides of the progress check are
measured rather than one. A scorecard that only went up would not be measuring anything.

The loop is closed — diagnose, prioritise, predict, check — and the prediction is now both demanding
and **quantified**: about 15 % of untreated players meet it, held out rather than in-sample.

**No dimension is at zero**, down from four earlier in the project. The empty column — everything
requiring the player to be *asked* something — has filled, and the loop runs end to end: analyse →
diagnose → prioritise → **ask** → plan → **report** → check.

**V1–V8 are now all built.** Nothing in the vision is missing a mechanism; what remains is that
several of the mechanisms are weaker than the vision asks for, which is what the scores say.

Two honest qualifiers. **The prober's rubric is still the author's own** (D10), so the asking is
load-bearing but validated in-sample. And **the swarm is silent for 14 of 84 players on deep
histories, and for 43 % at the 24 games a real user actually brings** ([[experiments.e16-shallow-corpus]])
— not wrong, not generic, not overloaded, just quiet. Every one of those silent players has a median
of **7** patterns the swarm can see and cannot confirm, so the silence is a measurement limit rather
than a verdict. That is the binding constraint, and it is deliberately parked (P2).

The +1 this cycle is D5 prioritisation, and it closed the last structural gap in the vision.

The uncomfortable part of this cycle is not the score. Expected-gain reasoning had been treated as
blocked ever since E03 failed to link a feature to errors — for two scorecard cycles the note read
*"no expected-gain reasoning"* as though the measurement had settled it. It had not. E03 asked a
**predictive** question and this asks an **accounting** one, and the second was a sum over evidence
the profile had been carrying the whole time (L-028). A failed experiment had been quietly promoted
into a boundary.

What changed is smaller than it sounds and more important than it looks: the swarm can now say *"this
is costing you four points a game"* instead of *"you do this 1.8× more than your peers"* — the
difference between something interesting and a reason to spend a month on it.

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

0. **~~P0 — D12: does `focus` need a magnitude floor?~~ Done 2026-08-05.** Yes, and it has one:
   `FOCUS_MARGIN = 1.25` on the point estimate, alongside the interval test. Chosen from the data —
   the smallest ratio among the swarm's 40 real findings is 1.40 — so it **removed nothing**, and
   re-measurement confirmed 19 advised / 13 kinds / 0.08 overlap unchanged. The defect was real and
   *latent*: no section had a large enough denominator to trip it until S5 (L-023).

0. **~~P0 — Stop adding sections; rebuild on the deep histories.~~ Done 2026-08-06** →
   [[experiments.e12-corpus-depth]]. Coverage **53 % → 83 %**, claim kinds 16 → 27, overlap 0.06 →
   0.05. Six sections had moved coverage 24 → 53 %; depth alone moved it further, in 45 minutes of
   mostly-cached engine time and with no new diagnostic capability (L-026).

0. **~~P0 — V1 skill assessment.~~ Done 2026-08-06** → [[experiments.e13-strength-signal]]. Rating
   estimated from blunder rate to **±103 points held-out**, reported as a range, with the rating
   hidden from the estimator.

0. **~~P0 — The context questions.~~ Done 2026-08-06.** Four questions before the analysis, every one
   skippable. Study time sizes the plan; the rest make the report honest, and `plays_elsewhere` turns
   an inherited blind spot into a stated one. D5 1 → 2, D12 2 → 3.

0. **~~P1 — V3 style profiling.~~ Done 2026-08-06** → [[experiments.e14-style-dimensions]]. One
   tendency of six candidates; four were strength wearing a style label, and the performance half is
   refused because players barely differ on it. **No scorecard dimension is at zero any more.**

0. **~~P1 — Expected-gain reasoning (D5).~~ Done 2026-08-06** → [[experiments.e15-expected-gain]].
   Not blocked by E03 after all: that asked whether a feature *predicts* errors, this sums what the
   *known* errors cost. Advice changed for **33 of 84 players**, claim kinds and sections unchanged,
   `advantage_error` 1 → 9 and `opening_disadvantage` 11 → 4. D5 2 → 3.

0. **P0 — Evaluated 2026-08-06, awaiting the author's decision** →
   [[design.short-history-prioritisation]]. A proposal to set the minimum history at 20 games and
   rank by an importance score (rate + severity + recency + game length) instead of gating.
   Measured rather than argued: scoring **does** degrade gracefully where gating cliffs, severity is
   the strong ingredient (**65 %** stable at 20 games) and occurrence rate ranks **at chance**
   (6 % against 4 %) — but severity alone names the same weakness for **70 %** of players (E17), so
   **E15's raw-cost ranking needs to become peer-relative**; that is a defect in work shipped the
   same day. Recency has nothing to act on for the median player (a 20-game window spans 23 days)
   and starting clock is inert on a corpus that is 74 % `600+0`. Cheapest real win found along the
   way: **8.0 % of games are berserked and 2.2 % abandoned**, unfiltered, biasing exactly the
   time-pressure signals under discussion.

   **Follow-up, and the biggest finding of the two:** the starting-clock weight is inert *because
   the fetch discards blitz*, and that filter costs a **median 82 % of a player's games** — measured
   over the same 84 players, who are the rapid-inclined end of the band to begin with. The swarm
   looks at roughly one game in five. That points at **admitting blitz stratified by time control**
   — never blended, so E01's objection stands — as the largest available lever on the binding
   constraint, with a cheap screen to run first: does a claim's blitz-versus-rapid gap vary *between
   players*, or is it a constant of chess (L-023, L-025)?

0. **P2 — Deferred by the author 2026-08-06: what to do about the 24-game user.** The swarm works on
   150-game histories and is silent for **43 %** of players at 24 (E16; E12 said 47 % on a different
   population). That is a constraint on *who it can help*, and it is deliberately parked until the
   system is complete rather than solved now. **E16 narrows the options**: every silent player has a
   median of **7** real patterns the corpus cannot confirm, so there is something to say and not
   enough evidence to say it. Relaxing `FOCUS_DISTINCT_GAMES` is now ruled out — it is 3 % of the
   problem. What remains: require a minimum history and say so; pool evidence across related claims
   to raise events per corpus; or report the unconfirmable patterns explicitly as *"suspected, not
   established"*, which is a change to the confidence vocabulary rather than to its thresholds.

0. **P1 — D12 reopens as a calibration question.** The magnitude floor was a safety net chosen to cut
   nothing; on deep corpora the finding distribution is **truncated exactly at it** (minimum ratio
   1.25, the floor). It now decides what the weakest advice sounds like — 11 advised findings sit
   below 1.4, against 1 before. Left at 1.25 because the arbiter's two-priority cap filters the
   weakest anyway, but the value should be revisited against real players rather than against the
   finding distribution.

0. **~~P1 — The binding constraint is `FOCUS_DISTINCT_GAMES = 5`.~~ Measured and wrong. Corrected
   2026-08-06** → [[experiments.e16-shallow-corpus]]. That was generalised from S6's experience
   without a census. Instrumenting every gate at 24 games: among silent players, the sole blocker was
   **the event occurring in fewer than 3 games (83 claims)** or **the interval failing to exclude the
   baseline (69)** — 96 % between them. `FOCUS_DISTINCT_GAMES` accounted for **5 claims, 3 %**.
   Moving that threshold would move almost none of the problem. The lever is **events per corpus**,
   which means games or better-pooled evidence — not looser thresholds, since the two gates that
   actually bind are the ones stopping the swarm inventing patterns from three data points.

0. **P0 — Answers from people who are not the author.** ~40 of them, labelled by someone else. This
   is the only thing standing between the prober and real use, and it is **not a modelling problem**:
   E07 settled the model (`llama3.1:8b-instruct-q6_K`, kappa 0.74, zero false-ignorance). What is
   weak is the *ground truth* — the answer set is written by me, labelled by me, and the figure is
   in-sample because the refusal split came after seeing which items failed. A better model cannot
   fix any of that. Until it is fixed, [[capacity.agents.prober]] § 4's gate stays shut and no probe
   may change a `gap_type` on real data.

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
