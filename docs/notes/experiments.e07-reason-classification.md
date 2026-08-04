---
id: cas-exp-e07
title: 'E07 — Which classifier may decide a player’s gap type?'
desc: 'The prober’s rubric, measured. A 3B model matches an 8B; the real gain came from noticing the design asked one question to do two jobs.'
updated: 1785628800000
created: 1785628800000
---

# E07 — Which classifier may decide a player's gap type?

**Answers:** [[capacity.agents.prober]] § 4 and § 9 level 2 · **Code:** `experiments/e07-reason-classification/`
**Date:** 2026-08-04 · **Status:** done — **a model is chosen and the gate stays shut**

## Question

The prober delegates exactly one step to a language model: *does this sentence name that reason?*
The agent note forbids any probe result changing a finding until that step has a **measured agreement
figure**. This measures it, for every option available locally, against the same hand-labelled
answers.

Cohen's **kappa** as well as raw accuracy, because the label distribution is uneven (28 yes / 11 no /
7 unclear) and a classifier answering "yes" to everything would score respectably on accuracy alone.

## Method

46 hand-labelled answers (`answers.jsonl`), built to include the cases the design predicts are hard:
the concept named **without the word** ("his knight can't move or he loses the queen" *is* a pin),
**broken English** which must not be scored as ignorance, **false friends** (calling a skewer a pin),
and **refusals**.

Four classifiers behind one Protocol, so this is an ablation rather than a demo:

| | what it is |
|---|---|
| `KeywordFloor` | substring matching — present to be beaten |
| `EmbeddingBaseline` | `mxbai-embed-large` cosine similarity; deterministic, no generation |
| `OllamaClassifier` | `llama3.1:8b-instruct-q6_K`, temperature 0, fixed seed |
| `OllamaClassifier` | `llama3.2:3b` |

## Result

**First run:**

| classifier | acc | kappa | false-ignorance |
|---|---|---|---|
| keyword floor | 50 % | 0.25 | 16 |
| embedding baseline | 57 % | 0.30 | 12 |
| llama3.1:8b | 65 % | 0.30 | 0 |
| llama3.2:3b | 72 % | 0.47 | 3 |

Inspecting the disagreements showed the same failure in **all four**: every classifier returned
*no* for refusals — "I don't know", "?", "intuition" — where the label was *unclear*. Seven of 46,
failing identically everywhere.

**That is not a model weakness. It was a design flaw.** *Did the player offer a reason at all* is a
property of the utterance, not of its chess content, and the inference table treats **declined** and
**named the wrong tactic** as opposite cases — one is `unknown`, the other `fragile`. Asking a
chess-reason classifier to decide both collapses them.

Split into a deterministic `declines_to_answer()` check applied before any classifier runs:

| classifier | acc | kappa | false-ignorance | s/call |
|---|---|---|---|---|
| keyword floor | 65 % | 0.49 | **16** | 0.00 |
| embedding baseline | 72 % | 0.56 | 12 | 3.78 |
| **llama3.1:8b-instruct-q6_K** | **87 %** | **0.74** | **0** | 2.66 |
| llama3.2:3b | 87 % | **0.76** | 3 | 2.16 |

## What was decided

**`llama3.1:8b-instruct-q6_K` ships**, despite `llama3.2:3b` scoring marginally higher on kappa.
0.74 against 0.76 on 46 items is well inside noise; **0 false-ignorance against 3 is not.**
Marking a player who understood the pattern as not knowing it sends them to study something that was
never wrong — the same asymmetry that makes [[capacity.agents.s1-tactical-gaps]] § 6 prefer
conservative detectors. Where the two are otherwise level, the one that never makes the costly error
wins.

**The language model earns its place.** It beats the embedding baseline 0.74 to 0.56, which was the
ablation the baseline existed to force. Had it not, the honest outcome would have been to ship the
embeddings and drop the model entirely — cheaper, deterministic, and C1-friendlier.

**The keyword floor failed exactly as predicted**, and the number is worth keeping: 16 of 28 players
who gave a correct reason would have been recorded as having a knowledge gap. That is the concrete
cost of the "just match the word" design the agent note rejected in advance.

## Why the gate stays shut

Agreement of 0.74 is *substantial* on the usual reading, and it is **not enough to start acting on
findings**, for three reasons that are all about the labels rather than the model:

1. **The answers are constructed, not collected.** I wrote them, imagining how players talk. They
   almost certainly under-represent how strange real answers are.
2. **I labelled them myself.** § 4 asks for agreement between the model and a *human rater*; here the
   rater also wrote the items and designed the system. That is the weakest form of the check.
3. **The figure is in-sample.** The refusal split was made *after* seeing which items failed. The
   architectural argument for it stands on its own — one question doing two jobs — but the 0.74 was
   measured on the set that revealed the problem, and L-018 is explicit about what that is worth.

So the prober can now be wired end to end, and **may not yet change a `gap_type` on real data**. The
next step is not a better model. It is 40 answers from people who are not me.

## Honest limitations

- **English only**, and the refusal list is a fixed set of phrases that will miss unseen ones. It is
  deliberately in one place so it can be replaced by a model call when it proves too brittle.
- **Reason descriptions are mine**, and the embedding baseline is only as good as they are — a
  different phrasing of "what a pin is" would move its threshold.
- **The threshold 0.62 was not tuned**, so the baseline is if anything under-sold. Since it lost
  anyway, tuning it would only strengthen the conclusion the other way.
- **Per-call latency is 2–3 s on this machine**, so 2–6 probes cost under 20 s. Comfortably inside
  C1, but it is the first non-zero runtime cost in the project.
