---
id: cas-evaluation
title: Evaluation
desc: 'How the efficacy of individual agents and of the whole swarm is measured — the design options and the chosen strategy.'
updated: 1785255700000
created: 1785254500000
---

# Evaluation

Nothing here is "done" because it looks done. This note defines how we get evidence.

**Why it carries unusual weight:** [[domain.prior-art]] found that **none of the five existing LLM
chess coaches evaluates whether its coaching is correct.** They test code, not advice. Evaluation is
therefore not a supporting chore in this project — it is the contribution claim.

The hard part is stated plainly: **there is no ground truth for coaching quality.** Expert review
does not scale, rating change is slow, noisy and confounded by everything the player does elsewhere.
The design below is a way of getting evidence anyway.

## The design space

### Family A — Predictive validity *(free, scalable, automatic)*

The strongest family, because the data generates its own ground truth. The unifying idea: **a real
weakness predicts; noise does not.**

| # | Method | What it tests | Cost |
|---|---|---|---|
| A1 | **Held-out error prediction.** Diagnose on games 1…N, then predict which error types appear in games N+1…N+M. Measure lift over the player's own base rate. | V4 gap detection — the core claim | free |
| A2 | **Blind rating estimation.** Estimate strength with the rating hidden; compare to the player's established rating across many players. | V1 skill assessment | free, large N |
| A3 | **Puzzle-outcome prediction.** Predict which puzzle themes the player fails, check against their actual Lichess puzzle history. | V2 knowledge assessment, per-theme | free where history is public |
| A4 | **Player fingerprinting.** Given a profile and two unseen games, identify which is the player's. | whether the profile captures anything *individual* rather than band-generic | free |

**A1 is the centrepiece.** It converts "is this diagnosis true?" — unanswerable — into "is this
diagnosis predictive?" — measurable, on data we already have.

### Family B — Internal validity *(free, automatic, runs every cycle)*

| # | Method | What it tests |
|---|---|---|
| B1 | **Split-half reproducibility.** Diagnose on odd-numbered games and even-numbered games separately; measure agreement. | whether a diagnosis is a property of the player or of the sample — directly validates the C2 minimum-sample rule |
| B2 | **Perturbation robustness.** Re-run at different engine depths. E01 showed per-move labels shift; top-level diagnoses must not. | that conclusions survive their own parameters (L-006) |
| B3 | **Agent ablation.** Remove an agent; does A1's predictive lift drop? | whether each agent earns its place, or is decorative |
| B4 | **Determinism.** Same input, same output. | reproducibility for the thesis |

B1 is cheap, powerful, and produces a strong thesis figure. It is the single best defence against
R-13 (statistical overclaiming).

### Family C — Constructed ground truth *(free, and genuinely underused)*

| # | Method | Idea |
|---|---|---|
| C1 | **Planted-weakness players.** Generate games where one side has a *known, constructed* deficiency — e.g. an engine forced to overlook a motif class, play at reduced depth in a phase, or move instantly under a time model. The weakness is then known by construction. | Does the swarm find the planted weakness, and not invent others? |
| C2 | **Population base-rate control.** Compare the player against rating peers from the free Lichess database. | Doubles as the relevance mechanism for open question C6 — the same corpus serves both |

C1 is the only route to *actual* ground truth that costs nothing, and it tests both sensitivity
(finds the planted flaw) and specificity (does not hallucinate others).

### Family D — Anti-pattern detection *(free, automatic, and specific to this failure mode)*

These test for the ways an LLM coach fails that correctness checks miss:

| # | Metric | Catches |
|---|---|---|
| D1 | **Inter-player divergence.** How different is the advice given to different players? A generic coach produces near-identical text for everyone. | R-12 — the "recite level-appropriate advice" failure |
| D2 | **Base-rate specificity.** Is the claim true of most of the peer population? If so it is a description, not a diagnosis. | R-14 — true-but-useless output ("you have an isolated pawn", true in 96 % of games) |
| D3 | **Priority count.** Does the output name more than one or two priorities? | the "list nine weaknesses" anti-pattern ([[domain.coaching]] § 4) |
| D4 | **Groundedness.** Fraction of statements citing a specific game and position. | V8 explainability — mechanically checkable |
| D5 | **Coverage.** Fraction of the player's actual errors the swarm can explain at all. | silent blind spots |

D1 and D2 are cheap, novel, and directly target the two failure modes this project has already
demonstrated or predicted. They deserve to be in the thesis.

### Family E — Human judgement *(expensive; milestones only)*

| # | Method | Notes |
|---|---|---|
| E1 | **Blind rubric review.** A strong player scores plans on reasonable / ordered / specific, without knowing which system produced them. | include a **control**: generic band-appropriate advice, and a **naive baseline**: raw LLM-over-games, of which prior art supplies a working example |
| E2 | **Pairwise preference.** Which of these two reports is more useful? | easier for a reviewer than absolute scoring, and more reliable |

Small N, milestone gates only. The control and baseline conditions matter more than the sample size:
without them a reviewer's "this seems reasonable" means nothing.

### Family F — Longitudinal *(the real thing; slow)*

| # | Method | Feasibility |
|---|---|---|
| F1 | **Predicted progress signs.** Each plan step ships with an observable sign; did it appear in later games? | feasible if started early — and it is the only test of V6/V7 |
| F2 | **Rating trajectory vs. control.** | underpowered and confounded; report as future work, honestly |

### Family G — Cost & operational *(always on)*

Cost per session in cash and wall clock, tokens per player, engine seconds. Constraint C1 is a
requirement, so it is measured every cycle, not assumed.

## Chosen strategy

Three tiers, so that cheap evidence runs constantly and expensive evidence is spent where it counts:

| Tier | When | Contents |
|---|---|---|
| **T0 — automatic, every cycle** | every agent change | B1 split-half, B2 perturbation, B4 determinism, D1–D5 anti-patterns, G cost |
| **T1 — per agent and per milestone** | when an agent is built or changed | A1 held-out prediction, A3 puzzle prediction, B3 ablation, C1 planted weakness |
| **T2 — milestone only** | a few times in the project | A2 rating estimation at scale, E1 blind rubric review with control and naive baseline, F1 progress signs |

**Build order:** C1 (planted-weakness generator) and B1 (split-half) come first, before the first
agent, so that S2 has something to be measured against on the day it exists. An evaluation harness
written after the agents is an evaluation harness shaped by the agents.

## Implementation status

Built **before the first agent**, deliberately — an evaluation harness written after the agents is
an evaluation harness shaped by the agents. `chesscoach/evaluation/`:

| Design | Code | Status |
|---|---|---|
| B1 split-half replication | `splithalf.py` | built — generic over any measure; also the runtime promotion rule in [[architecture.confidence]] |
| C1 planted-weakness players | `planted.py`, `choosers.py` | built — seeded, reproducible, with background noise |
| scoring against ground truth | `scoring.py` | built — sensitivity *and* specificity, counting only findings a player would be shown |
| fixture verification | `cli.py check-eval-set` | built — confirms a planted flaw is visible before anything is scored against it |
| A1 held-out error prediction | — | next, once an agent emits findings |
| D1–D5 anti-pattern metrics | — | needs the language layer to exist |
| C2 peer reference population | — | P3 in [[state]]; doubles as C6's remaining route |

**Verified end to end:** 12 generated games, 142 planted mistakes, checked against the analysis core
at depth 12 — planted moves show a 7.7 % error rate against 4.3 % for the same player's other moves,
a lift of 1.81×. That is a genuine but modest signal, which is what a realistic diagnosis problem
looks like.

Getting there required a correction worth recording (L-009): the first fixture scored 16.9 % against
**0.0 %**, because outside the planted condition the flawed player played the engine's own move. No
real player is perfect except in one condition, and an agent measured against that fixture would have
been flattered. `background_severity` fixed it.

## Test data discipline

- Held-out players, never used while designing prompts, thresholds or knowledge.
- Segmented by time control; never mix bullet with classical (E01, [[domain.signals]]).
- Analysis depth recorded with every stored result; profiles at different depths are not comparable.
- Public games only, public usernames only (R-10).

## Honest open problems

- **A1 assumes error types are stable over weeks.** If a player is actively improving, a
  correct diagnosis may fail to predict *because the coaching worked*. Confounded in the direction
  that makes the system look worse, which is at least the safe direction.
- **C1's planted weaknesses are artificial.** An engine told to play badly does not fail the way a
  human fails. It tests the detector, not the coaching.
- **Win-probability labels compress in decided positions** (L-009). A weakness planted late in an
  already-lost game is nearly invisible, so measured severity understates planted severity. A future
  refinement is to score only while the game is still competitive — noted rather than solved.
- **Nothing here measures whether the player actually improves.** Only F1/F2 do, and both are weak
  within a thesis timeline. This limitation must be stated in the thesis rather than papered over.
