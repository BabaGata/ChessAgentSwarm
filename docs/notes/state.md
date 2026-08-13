---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785255200000
created: 1785254500000
---

# State

**Snapshot date:** 2026-08-08
**Active mission step:** **M6/M7** — maintain, then repeat M4 with the next capability
**Last commit:** `feat(M6): refit the strength estimate for blitz, and make it name its speed`
**Scale:** 8,100 lines in `chesscoach/`, 849 tests at 85 % coverage, 25 experiments, 83 vault notes

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
| Peer reference corpus | **built, widened, stratified** | `chesscoach/peers.py` — **84 players**, band 1400–1800, **rapid *and* blitz strata** (schema v2), carrying per-claim **rates and costs**, depth 15, leave-one-out |
| Parallel analysis | **built** | `chesscoach/analysis/parallel.py` — corpus-wide dedup + prefetch. ~3× on a cold cache, measured |
| Confidence policy | **enforced at runtime** | `chesscoach/confidence.py` — tiers, distinct-game counts, split-half replication as a promotion requirement. Shrinkage was tried here and **reverted** (E20) |
| **Sections S3–S6, S8** | **built, each screened first** | endgame technique, opening outcomes, pawn structure, squares and files, attack and defence. **Seven sections total**; S7 screened and deliberately not built |
| **Arbiter + planner** | **built** | one or two priorities, ranked by peer-relative recoverable cost; every step carries a falsifiable target and a check point |
| **Explainer** | **built** | the report a person reads: strength, style, findings with cited positions, plan, band notes, limits |
| **Prober (V9)** | **built** | probe selection, move check, a local model classifying reasons at kappa 0.74, `gap_type` written back |
| **V1 strength / V3 style** | **built, per speed** | two fitted lines (rapid ±103, blitz ±123); one style tendency, mix-matched to the player's speeds |
| **Band-level notes** | **built** | what the whole rating band loses most to — five screened claims, never competing for a priority (E25) |
| **Speed pooling** | **built** | blitz joins the corpus; the baseline stays per-speed by direct standardisation. 24-game coverage 50 % → **79 %** |
| **Corpus hygiene** | **built** | berserked and abandoned games excluded, counted, and disclosed to the player |
| **One-command session** | **built** | `cli coach` — username in, report out; verified end to end on a live player, deterministic across runs |

## Distance to vision

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | **2** | **−1** | **down, on the first external test it has ever had** → [[experiments.e27-held-out]]. On 30 players fetched after every constant was frozen, **rapid is excellent (MAE 50 against 133 for guessing) and blitz is barely an estimator (150 against 157)**, with a systematic −88 bias reading strangers as weaker than they are. Blitz *ranks* players well (r = +0.83) and its scale is compressed 1.5×, which is slope attenuation — invisible to cross-validation because folds could not widen the rating range (L-036). The promise is corrected (`typical_error` 123 → 150, and the report now calls the blitz reading rough); **the line is deliberately not rescaled on the set that measures it**. Back to 3 when blitz is refit on a wide-range sample and validated on a further held-out set. Original build below: |
| | *(D1, as built)* | | | **built, cross-validated, and fitted per speed** → [[experiments.e13-strength-signal]]. Rating from blunder rate alone, with the rating hidden from the estimator: **rapid ±103** held out, **blitz ±123** (a flatter line — blunders separate players less when everyone rushes), against a blitz baseline of 141. Reported as a range, **names which speed it means**, refuses below 200 moves *within* that speed rather than blending two rating scales, admits extrapolation. Not 4: **the vision asks for strength *and its variance*** and every player still gets the same population-level error bar regardless of how much evidence they brought |
| D2 | V2 knowledge assessment | **2** | **+2** | **the prober works end to end** — probe selection, move check, a local model classifying reasons at kappa 0.74 with zero false-ignorance (E07), `gap_type` written back. Not 3: the rubric's answer set is written and labelled by the author and the figure is in-sample, so it may not yet change a real player's finding |
| D3 | V3 style profiling | **2** | — | **built, half deliberately refused, and now compared against the right population** → [[experiments.e14-style-dimensions]]. One measured tendency — how much of a game is spent with the queens off — that varies between players (1.40) and is **independent of strength** (r = −0.069). Four of six candidates were strength wearing a style label. A live session found it comparing an all-blitz player against the *rapid* population (I-03); it is now mix-matched like every other comparison. Not 3: **the performance half does not survive** — everyone errs ~20 % less with queens off and players barely differ, so the report says what a player tends to do and refuses to say whether it suits them |
| D4 | V4 gap detection | **5** | — | **seven sections, and the shallow-corpus caveat that held this back is gone.** On 150-game histories 70 of 84 players advised (83 %); on the **24 games a real user brings, 50 % → 79 %** once the player's other speeds are pooled in, with claim kinds 20 → 25 and overlap unchanged at 0.09 ([[experiments.e21-pooled-speeds]]). Groundedness 113/113. The lever was never more sections: six sections moved coverage 24 → 53 %, corpus depth and then speed pooling did the rest |
| D5 | V5 prioritisation | **3** | — | **ranks by what a weakness costs *above what it costs peers*** → [[experiments.e15-expected-gain]], corrected by [[experiments.e17-ranking-stability]]. Raw cost named one claim to 70 % of players; the excess over the population is what a plan can honestly promise, and the report states all three numbers. Occurrence rate is kept as a gate and **demoted as a ranking signal**, because it ranks at chance (6 % against 4 %). A band-level section now carries the expensive weaknesses everyone shares, which peer-relative ranking is blind to by construction (E25). Not 4: it is an **accounting** cost, not a forecast — nothing shows fixing the priciest weakness gains more than fixing another — and the vision asks for gain *per unit of study time*, which needs D5's unresolved question about how long anything takes |
| D6 | V6 path planning | **2** | **+2** | plans built and persisted, every step carrying a machine-checkable progress sign and a derived check point. No time estimates — D5 is unresolved and inventing them was refused |
| D7 | V7 progress tracking | **3** | **+1** | **restored, on evidence this time.** 57 predictions from 84 players with ~150-game histories; the constant is cross-validated at 2 *and* 5 folds with a fold spread of 0.011, and a held-out false-positive rate of **15 %** is stated in the output. Not 4: the test's **power is unmeasured** — no coached cohort exists, so nothing shows a real improvement could clear the bar (**D8**) |
| D8 | V8 explainability | **3** | — | the report exists, is deterministic, and is **13/13 grounded** on real players (E08 D4). **The 3 claimed last cycle was not earned**: reading a real report found Lichess theme keys in player-facing prose — *"a `trappedPiece` punishes you"* — which the groundedness metric scored 100 % on, because it only checks citation. Fixed (`phrasing.subject_name`), so the score now stands. Not 4: the report states measurements without explaining *why these one or two* were chosen over the rest, and the arbiter's reasoning is invisible |
| D9 | C1–C4 cost profile | **4** | **+1** | **re-timed 2026-08-06 against a genuinely empty cache**, which is what the previous 3 was missing. A new player, 60 pooled games: **5 s fetch + 76 s analysis ≈ 81 s**, of which 98 % is the engine. The same player again: **1.5 s**. A deep 197-game pooled corpus: **232 s cold, 2.9 s warm**. Cold scales at **~1.2 s per game**, so the 300-game accumulation ceiling is ~6 min for someone starting from nothing. Probes add ~2.7 s each (E07). **Zero cash throughout.** **A correction:** pooling speeds was expected to multiply session cost ~5× and does not — `--games 60` still fetches 60 games, it changes *which* 60, and only `--previous` raises the count. Not 5: one player on one machine, and the 300-game ceiling is extrapolated from 197 rather than measured |
| D10 | Evaluation capability | **5** | **+1** | both sides of the progress check measured (E05, E06), the **anti-pattern family D** built and run (E08), depth-robustness tested from both directions ([[experiments.e26-depth-robustness]]), and now **the pipeline run end to end on 30 players it was never built on** ([[experiments.e27-held-out]]) — which promptly caught a real generalisation failure in V1-blitz that cross-validation could not see. **An evaluation capability that only ever confirms is not one**; this one has now demoted a dimension on its own evidence. Not held back: the remaining gap is not a missing *measurement* but a missing *judge* — criteria 2 and 3 need a person, which is a resource problem rather than a capability one |
| D11 | Process & documentation health | **3** | **−1** | **down, and the reason is this table.** The cycle kept working — E20 was withdrawn on evidence, step 7 refused before it was built, three lessons recorded about misreading our own measurements. But across seven steps of the short-history plan the **scorecard rows went stale while the narrative below them was updated every cycle**: D4 still claimed 53 % coverage after pooling took it to 79 %, D5 still described raw cost, and *"What exists"* carried `Any agent | no` beneath seven built sections. The rule says close no cycle without updating [[state]]; it was honoured in the part that reads like prose and not in the part that reads like a score. Reconciled 2026-08-08 |
| D12 | V9 dialogue & active assessment | **3** | **+1** | **the whole interaction exists**: four context questions before the analysis, probes after it, both feeding the profile, and probe results now reaching the diagnosis inside a coaching session. Answers accumulate as a dataset by-product. Not 4: the classifier's rubric is still the author's own (D10), and the dialogue is four fixed questions rather than anything adaptive |

**Total: 37 / 60**, and **no dimension is at zero.** It has gone 17 → 16 → 17 → 16
→ 17 → 18 → 20 → 22 → 25 → 26 → 27 → 28 → 29 → 32 → 34 → 36 → 37 → 38 → **37**, and every move was
forced by a measurement:
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
load-bearing but validated in-sample. And **the swarm is still silent for about a fifth of players
at 24 games** — down from 43 % once their other speeds are pooled in
([[experiments.e21-pooled-speeds]]), and every silent player has patterns the swarm can see and
cannot confirm, so the silence is a measurement limit rather than a verdict.

**The move this cycle is D11 down one**, which is the whole point of scoring the process alongside
the product: the work was sound and the record of it was not.

**And the gap that now dominates everything is external validity.** Of the six success criteria in
[[vision]], three are measured — the strength estimate against real ratings, the cost, and
reproducibility from this vault. **Three are not**: whether the weaknesses the swarm names match what
a strong independent reviewer would name (criterion 2), whether the path reads as reasonable and
specific to a strong player (criterion 3), and whether following it beats a control (criterion 4).

**Criterion 2 now has its first evidence**, and it is favourable:
[[experiments.e26-depth-robustness]] re-labelled 1,200 sampled moves at depth 22 and **90 % of the
errors survived, 97 % of blunders, with an implied rate ratio of 1.05**. That is engine against
engine — it establishes the *foundation* is not an artefact of the depth setting, and it cannot say
whether hanging pieces and early errors are the right way to describe a player. Only a person can.
The one number that looked like a dent — the report's suggested move still being the engine's top
choice only **78 %** of the time — was chased down and is not one: on every sampled move where the
report offers an alternative, **169 of 169**, that alternative still beats what the player actually
played, by a median of **17.8 win-probability points**. The report never claimed the move was
optimal, only that it was better, and that claim holds.

So the honest position: everything measurable without a human has now been measured. **Criteria 2 and
3 — a strong player reading a dozen reports — are the gate, and they are the one thing on this list
that cannot be done alone.**

**The review is prepared and pre-registered** → [[evaluation.expert-review]]. Protocol, sample and
**pass thresholds fixed before any reviewer was approached**, because deciding what counts as a pass
after reading the answers is how a review becomes a testimonial. Twelve players drawn from the E27
held-out set — including the two the swarm was silent about and the weakest finding that still
shipped, so it cannot be run on the flattering cases. The reviewer writes their **own** diagnosis
before seeing the system's, in a separate folder, because *"would you have said this?"* and *"do you
agree with this?"* are different measurements. Build it with
`experiments/e28-expert-review/prepare.py`; it costs about 15–20 minutes per player of the
reviewer's time.

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
| Domain knowledge (coaching) | **4** | **+2** | **F2 largely closed 2026-08-14** → [[domain.expertise-research]]. The decisions the code rests on are traced to Gobet & Charness (2006), read directly from the PDF and quoted verbatim: pattern recognition over search depth (Chase & Simon; 300,000 chunks; a 1600→2300 player with **no significant increase in search depth**), the small cost of playing fast (**5.02 → 6.85 blunders per 1,000 moves for a sixfold cut in thinking time**, which independently corroborates E19), narrow transfer (Didierjean et al.), and ~1,000 hours to master. Not 5: the **four-way gap taxonomy still has no traced source** despite driving `GapTypeHypothesis`, and the procedural claims (lesson shape, the anti-pattern list) remain on coaching sites |
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

0. **P0 — The short-history plan is adopted and step 1 of 7 is built (2026-08-06)** →
   [[design.short-history-prioritisation]] § The solution. Five layers — supply, estimation,
   ranking, speaking, re-evaluation — sequenced so steps 1–4 need no new data and no architectural
   commitment, and the cheap screen deciding step 5's shape comes before step 5.
   **Step 1 done:** contaminated games excluded in `build_corpus` with the reasons counted and
   disclosed in the report (schema v10). 583 games (5.1 %), 55 of 84 players affected, worst case
   48.8 %. Coverage 70 → **69** advised and overlap 0.06 → **0.05**: it costs coverage and buys
   correctness, and `advantage_error` fell from 9 advised to 7 — the predicted berserk bias,
   confirmed, on the very claim E17 had flagged as over-selected.
   **Step 1b done** → [[experiments.e18-excluded-as-finding]], from the author's objection that
   excluding games throws away a finding. Right, and it splits: the **berserk habit** fails the cost
   screen (error rate only **1.04×** the player's own normal games — the habit varies, the harm does
   not) and is **disclosed rather than diagnosed**; the **time-budget chain** — clock spent early,
   mistakes twenty moves later — screens at **1.91×**, the best spread in the project, independent
   of `time_pressure_error` at **+0.204**, and is built as S2's fourth condition. 27 claim kinds now,
   2 players advised on it.
   **Step 2 done** → [[experiments.e19-blitz-stratum]]. **Answer: pool.** Blitz predicts a player's
   rapid behaviour as well as rapid predicts itself — **93 % of the reliability ceiling** — so step 5
   is one corpus with per-speed baselines, not three corpora with three references. It nearly went
   the other way: the raw blitz~rapid correlation is **+0.17**, which reads as "different construct"
   until rapid is correlated with *itself* at the same sample size and returns **+0.19** (L-031).
   The automaticity hypothesis is **refuted** — the gap's between-player variation is 2.39× against a
   2.08× noise floor.
   **Step 3 done.** The peer reference now carries cost per claim (peer schema v2, v1 still
   readable), `Measurement.peer_cost_per_game` and `excess_cost_per_game` exist (profile schema v11),
   and the arbiter ranks by the **excess** over peers rather than the raw cost. `advantage_error`
   lost 43 % of its advised slots (7 → 4). **Its definition of done was wrong**: E17's 70 %
   concentration was measured with the gates *forced open*, and production concentration was already
   13 % (L-032). The larger gain is in the report, which used to promise the whole cost back and now
   states what is recoverable — *"costing you 24.3 a game; players at your level lose 10.5, so
   roughly 13.8 is what fixing this could get back."* Still unverified: whether peer-relative
   severity keeps severity's 65 % stability gate-free.
   **Step 4 built, measured and WITHDRAWN** → [[experiments.e20-shrinkage]]. Replacing the interval
   test with a posterior shrunk toward the peers **halves** coverage at 24 games — 50 % of players
   spoken to becomes **26 %** against its own control — and costs on the deep corpus too (69 → 57
   advised). A Wilson bound uses the player's own games; a shrunk posterior pulls toward the
   population and is therefore *more* conservative, not less (L-033). Reverted. Kept:
   `chesscoach/shrinkage.py` with 29 tests, now the single shrinkage formula in the system since
   `expected_rate` calls it instead of doing the update by hand.
   **A 20-game minimum has lost the mechanism that was to justify it** and is an aspiration again.
   **Step 5 done, and it is the one that worked** → [[experiments.e21-pooled-speeds]]. Blitz is
   pooled into the corpus while the baseline stays per-speed, rebuilt for each player's own speed mix
   by direct standardisation, so E01's rule is kept rather than overruled. At **24 rapid games**:
   players advised **50 % → 79 %**, distinct claim kinds 20 → 25, overlap 0.08 → 0.09, groundedness
   113/113. More players *and* more claim variety, which is the opposite of buying coverage with
   generic output. **Three failures at the policy end and one success at the supply end** is now the
   strongest evidence in the project for where the constraint lives.
   **Step 6 done** → [[experiments.e22-accumulating-corpus]], and smaller than the plan implied. The
   corpus was **sliding**: at a fixed window twenty new games pushed twenty old ones out, so a
   returning player was diagnosed on no more evidence than the first time. `coach --previous` now
   grows the window to cover the old corpus plus the new games, capped at 300 for C1. **No game
   store was needed** — Lichess is the archive, so this was a request-size problem, not a storage
   one; and `check-progress` already measured over the new games only, so the harder half of that
   layer predated the plan proposing it. Measured warm: a **197-game pooled session costs 2.2 s**,
   2.9× the games for 1.6× the time, because a returning player's old games are exactly the ones
   already in the cache.
   **Step 7 refused on evidence** → [[experiments.e23-recency]]. Screened before building: games
   **over a year old** predict a player's recent claim rates about as well as games two months old
   (r +0.23 against +0.29, ceiling +0.19). Decay would have spent effective sample size — the
   binding constraint — for no measured gain. L-034: improvement changes a player's *level*, not the
   *shape* of their weaknesses, which is also why diagnosis against a peer population does not need
   to discount old games.

   **The plan is closed. Seven steps: four built, one withdrawn, one refused, one found already
   done.**

   | | |
   |---|---|
   | 1 exclude contaminated games | built — 583 games, coverage −1, correctness + |
   | 1b the time-budget claim | built — 1.91× spread, S2's fourth condition |
   | 2 blitz/rapid screen | **pool**, 93 % of the reliability ceiling |
   | 3 peer-relative severity | built — `advantage_error` 7 → 4 advised |
   | 4 shrinkage | **withdrawn** — halved coverage (E20) |
   | 5 pool the speeds | built — **50 % → 79 %** advised at 24 games |
   | 6 accumulate the corpus | built — and needed no game store |
   | 7 recency decay | **refused** — old games still describe the player |

   **The headline: a 24-game history now gets 79 % of players advised, against 50 % before, with
   more claim kinds and unchanged overlap.** Every gain came from the supply side; every attempt at
   the policy end failed.

0. **A live end-to-end session, 2026-08-08, and it found two defects.** `cli coach` run on a real
   player from a live fetch: 59 games, four context questions, strength, style, one finding, a plan,
   band notes, report — exit 0. **The player's 59 most recent games were entirely blitz**, which is
   step 5 working exactly as intended: before it they would have been diagnosed on stale rapid games
   from months earlier. Two defects the corpus could never have surfaced, because every corpus player
   has a rapid history (I-03, I-04): style compared an all-blitz player against the **rapid**
   population, and the report stated a rating estimate fitted on rapid games without qualifying it.
   Both fixed, and **the blitz refit is now done too** → [[experiments.e13-strength-signal]] § blitz:
   `1841.3 − 12045.1 × blunder_rate`, held out **±123** against rapid's ±103. Blitz is genuinely
   harder to read — a much flatter line, because blunder rate separates players less when everyone is
   rushing — and it still beats guessing the median (141) clearly. The estimate is **per speed and
   names its speed**, and `MIN_MOVES` applies within that speed, so a genuinely split player is
   refused rather than handed an average of two rating scales that sit ~80 points apart.
   The live player's estimate moved 1645 → **1594** against an actual blitz rating of ~1783 — so the
   refit went the *wrong way for them*, which is recorded rather than buried: one player is not
   evidence against a fit cross-validated on 81, and their blitz rating sits *above* their rapid one,
   the opposite of the population trend the line encodes.

0. **A band-level section, from the author's objection to peer-relative severity** →
   [[experiments.e25-shared-weaknesses]]. A weakness *everyone* at the level shares has almost no
   excess over peers, so it sinks and is never said — and `instant_move_error`, at **16.1 points of
   win probability a game, the most expensive claim measured anywhere in this project**, was advised
   to nobody for exactly that reason. E25 screened which shared claims are worth saying anyway:
   the median claim's correlation with rating is **−0.42**, but only **+0.15** once the player's
   overall error rate is divided out, so nearly all apparent learning is just general improvement.
   **Five of 27 survive** and only those appear, in a separate section worded as a statement about a
   population, capped at three, never becoming findings. The anti-pattern family is **identical**
   before and after — 66 advised, 25 kinds, overlap 0.09, 113/113 grounded.

0. **~~Outstanding: D9 needs re-timing.~~ Done 2026-08-06**, and the worry behind it was misplaced.
   Pooling speeds does **not** multiply a session's cost: `--games 60` still fetches 60 games, it
   changes *which* 60, and only `--previous` raises the count. Measured against an empty cache —
   a new player costs **~81 s** (5 s fetch, 76 s engine) and a returning one **1.5–3 s** plus
   whatever they have played since, at ~1.2 s per new game. D9 3 → 4.

0. **Superseded — the evaluation that produced the plan above** →
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
