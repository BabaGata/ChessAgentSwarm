---
id: cas-experiments
title: Experiments
desc: 'Measured experiments — the project’s evidence base. Each has a question, a method, results and a consequence.'
updated: 1785255100000
created: 1785255100000
---

# Experiments

Where claims in this vault get their evidence. Every experiment answers a question from
[[open-questions]], is reproducible from code in `experiments/<id>/`, and ends with a **consequence**
— what changed because of the result.

An experiment with no consequence was not worth running.

| ID | Question | Status | Note |
|---|---|---|---|
| E01 | A1 engine throughput, A2 diagnosis stability | done | [[experiments.e01-engine-throughput]] |
| E02 | D4 — are positional concepts detectable without labelled data? | done | [[experiments.e02-positional-detectors]] |
| E03 | C6 — how is a detected feature weighted for relevance? | done — **largely negative** | [[experiments.e03-relevance-weighting]] |
| E04 | do the tactical motif detectors fire sensibly on real games? | done — **two were over-firing** | [[experiments.e04-motif-precision]] |
| E05 | does the planner's target mean anything without coaching? | done — **no: 92 % met by drift**; recalibrated to 15–23 %, and D9 showed the effect's size depends on sample depth | [[experiments.e05-natural-drift]] |
| E06 | D8 — does the progress check have any *power*? | done — **suggestive, not established** (25 % vs 8 %, p = 0.12) | [[experiments.e06-progress-power]] |
| E07 | which classifier may decide a player's gap type? | done — **8B local model, kappa 0.74, zero false-ignorance**; the real find was a design flaw, not a model | [[experiments.e07-reason-classification]] |
| E08 | evaluation family D — is the swarm generic, overloaded, or ungrounded? | done — **none of those; it is silent**, for 29 of 38 players | [[experiments.e08-anti-patterns]] |
| E09 | which of S6's candidate claims distinguish players at all? | done — **two of five**, and the split says what kind of claim works (L-024) | [[experiments.e09-square-candidates]] |
| E10 | can calculation quality be measured from game records? | done — **no**, and the section was not built as a result | [[experiments.e10-calculation-candidates]] |
| E11 | which of S8's candidates survive both screening questions? | done — **one of four**, plus the first counter-example to L-024 | [[experiments.e11-attack-candidates]] |
| E12 | is the coverage constraint breadth of sections or depth of corpus? | done — **depth, decisively**: 53 % → 83 % of players advised | [[experiments.e12-corpus-depth]] |
| E13 | can playing strength be estimated from a player's own games? | done — **yes, ±103 points held-out** from blunder rate alone | [[experiments.e13-strength-signal]] |
| E14 | is there a style to measure, or only strength wearing a label? | done — **four of six were strength**; one tendency ships, the fit half is refused | [[experiments.e14-style-dimensions]] |
| E15 | can priorities be ranked by what a weakness costs rather than how unusual it is? | done — **yes, by accounting rather than prediction**; advice changed for 33 of 84 players | [[experiments.e15-expected-gain]] |
| E16 | why is the swarm silent for half of players at 24 games? | done — **rarity and interval width, 96 %**; the recorded cause `FOCUS_DISTINCT_GAMES` is 3 % | [[experiments.e16-shallow-corpus]] |
| E17 | can a weakness ranking be trusted at 20 games? | done — **severity yes (65 %), rate no (6 % vs 4 % chance)**; but severity tells 70 % of players the same thing | [[experiments.e17-ranking-stability]] |
| E18 | is there a coachable finding in the games step 1 excludes? | done — **the berserk habit no (1.04× cost), the time-budget chain yes (1.91×)**; the latter built into S2 | [[experiments.e18-excluded-as-finding]] |
| E19 | is blitz a second stratum, or the same player faster? | done — **the same player: 93 % of the reliability ceiling**. Pool the evidence, stratify the baseline | [[experiments.e19-blitz-stratum]] |
| E20 | does a shrunk posterior let the swarm speak to more players? | done — **no, the reverse**: 50 % spoken to becomes 26 %. Step 4 withdrawn | [[experiments.e20-shrinkage]] |
| E21 | does pooling a player's other speeds fix the shallow-history silence? | done — **yes, decisively**: 50 % → **79 %** advised at 24 games, with more claim kinds and unchanged overlap | [[experiments.e21-pooled-speeds]] |
| E22 | what does it take to make a returning player's corpus grow? | done — **a bigger request, not a game store**. A 197-game pooled session costs 2.2 s warm | [[experiments.e22-accumulating-corpus]] |
| E23 | should old games be discounted? | done — **no**: games over a year old predict recent play as well as recent ones. Step 7 refused | [[experiments.e23-recency]] |
| E25 | is a weakness the whole band shares still worth coaching? | done — **for 5 claims of 27**, including the most expensive one measured (`instant_move_error`, 16.1/game), which is advised to nobody | [[experiments.e25-shared-weaknesses]] |
| E26 | do the findings survive a much deeper engine? | done — **90 % of errors, 97 % of blunders**, implied rate ratio 1.05; and the suggested move still beats the played one **169/169** | [[experiments.e26-depth-robustness]] |
| E27 | does any of it hold on players it was never built on? | done — **the diagnosis yes** (86 % vs 84 % matched on corpus size, p = 0.46), **the blitz rating no** (MAE 150 against 157 for guessing) | [[experiments.e27-held-out]] |
| E29 | can the blitz line be repaired without fitting to the test set? | done — **yes**: reliability 0.641 gives a 1.56× correction, held-out data independently demands 1.48×, **MAE 149 → 129**. Rapid refuses it, which is the control | [[experiments.e29-attenuation]] |
| E30 | does "hanging piece" mean pieces, or pieces and pawns? | done — **the definition explains what the reviewer saw and rescues neither claim**: with pawns bernes hands over free material on **19.6 % of errors** (unmissable to a human) but the population does it on 17.6 %, so the deviation *shrinks* 1.40× → 1.11×. `HANGING_MIN_VALUE` stays at 3 | [[experiments.e30-hanging-definition]] |

## Conventions

- Code lives in `experiments/<id>/`, results in `experiments/<id>/results/`.
- **Data is never committed** — games are re-fetchable, and the repo stays small.
- Results notes record the *setup* precisely enough to reproduce: engine build, depth, threads,
  hash, sample size and how the sample was chosen.
- Negative and inconvenient results are recorded with the same prominence as convenient ones.
