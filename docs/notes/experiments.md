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

## Conventions

- Code lives in `experiments/<id>/`, results in `experiments/<id>/results/`.
- **Data is never committed** — games are re-fetchable, and the repo stays small.
- Results notes record the *setup* precisely enough to reproduce: engine build, depth, threads,
  hash, sample size and how the sample was chosen.
- Negative and inconvenient results are recorded with the same prominence as convenient ones.
