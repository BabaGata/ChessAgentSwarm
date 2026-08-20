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
| E31 | does the swarm *see* what a reviewer sees, separately from whether it *says* it? | done — **detection 42–80 %, naming 0–10 %** across three players. The analysis core lands on the same move; it rarely has a matching name. **45 of 45 pawn notes unnameable**, and the reviewer works below `INACCURACY_WP` | [[experiments.e31-move-level-agreement]] |
| E33 | what does lowering the error threshold buy, and what does it cost? | done — **detection 58 % → 89 %, naming flat at 8–9 %**, and discrimination does *not* collapse (best at 5.0). Refutes E32's own hypothesis: the naming gap was never the threshold. **Screened, not applied** — it would invalidate E05's cross-validated constant and every peer reference | [[experiments.e33-error-threshold]] |
| E32 | does a free-pawn detector earn its place? | done — **ships on the screen, fails its own motivation.** Spread 1.53× / 1.38×, inside the range of every shipping claim, and players miss free pawns **twice as often as free pieces**. But it named **1 of 45** reviewer notes: 24 sit below the label threshold so no motif ever runs, and the rest are named by *mechanism* where the reviewer named the *outcome* | [[experiments.e32-hanging-pawn-screen]] |
| E34 | which causes of material loss survive both screens? | done — **two of four**; `left_hanging` and `ignored_threat` are the overall error rate renamed. **S7 reopens** on the slot E10 emptied | [[experiments.e34-material-causes]] |
| E35 | should a sacrifice and a miscounted exchange be one claim or two? | done — **two**, on the reviewer's distinction. Splitting *raised* the spread of both halves: combined 1.75× becomes **2.71× and 1.84×** | [[experiments.e35-attacking-style]] |
| E36 | is material lost directly the same as material lost in a sequence? | done — **the distinction is real and separates nobody**: **88.5 %** of material goes to a sequence, every player 81–93 % (spread 1.02×). No claim ships, and it corrects a measurement E35 had refused on broken grounds | [[experiments.e36-forced-sequences]] |
| E37 | what is inside the sequence bucket? | done — tactics **54.7 %**, exchanges **31.9 %**, pure forcing **2.8 %**, unattributed 10.7 %. **Pins outrank forks 1.6 : 1.** No claim survives both screens | [[experiments.e37-loss-mechanism]] |
| E38 | can the exchange claim be formulated so it survives? | done — **three formulations, all refused.** Tightening the denominator fixed discrimination and never fixed independence. Refutes the forks-are-easier hypothesis: forks are missed **more** (32.1 % vs 27.1 %); pins simply arise 2.5× as often. Produced **L-042** | [[experiments.e38-exchange-sequences]] |
| E39 | does a 20-game read measure the same system as a 50-game report? | done — **no, three times in four.** The swarm changes its own leading finding 75 % of the time between the two, so most of what the review would measure is sampling | [[experiments.e39-review-window]] |
| E40 | is the ranked top three needed, or can it be derived from the notes? | done — **derived, and it agrees with the swarm 0 times in 6** | [[experiments.e40-derived-ranking]] |
| E41 | would ranking by cost beat ranking by peer-relative excess? | done — **refused: also 0/6, worse overlap.** Two rules disagreeing about everything and agreeing on the answer relocated the defect: **5 of 12 material claims never become candidates**, 7 are above peers and expensive but blocked by `FOCUS_GAMES_WITH_DATA = 20` against a 20-game window, and in the cost pool they lose to `early_error`, which **contains** them | [[experiments.e41-cost-ranking]] |

| E42 | how much do the swarm's claims describe the same moves? | done — **almost none, which refutes E41's explanation.** 501 cross-section pairs, median **3 %** coverage, **0** reaching 80 %. Threshold calibrated against the convention the project already uses (60 %); the rule ships and changes **1 player of 12** | [[experiments.e42-claim-overlap]] |


## Conventions

- Code lives in `experiments/<id>/`, results in `experiments/<id>/results/`.
- **Data is never committed** — games are re-fetchable, and the repo stays small.
- Results notes record the *setup* precisely enough to reproduce: engine build, depth, threads,
  hash, sample size and how the sample was chosen.
- Negative and inconvenient results are recorded with the same prominence as convenient ones.
