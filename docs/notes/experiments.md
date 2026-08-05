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

## Conventions

- Code lives in `experiments/<id>/`, results in `experiments/<id>/results/`.
- **Data is never committed** — games are re-fetchable, and the repo stays small.
- Results notes record the *setup* precisely enough to reproduce: engine build, depth, threads,
  hash, sample size and how the sample was chosen.
- Negative and inconvenient results are recorded with the same prominence as convenient ones.
