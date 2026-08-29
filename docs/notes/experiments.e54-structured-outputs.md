---
id: cas-exp-e54
title: 'E54 — The schema changed no parse rate, and the example in the prompt broke everything'
desc: 'Schema-constrained decoding measured no improvement in parse rate, because the prose fallback was already catching everything. The example added alongside it anchored the model to answer {"keep": [3, 11, 24]} on every page, which cost three briefs of five until it was found.'
updated: 1788566400000
created: 1788566400000
---

# E54 — Does a JSON Schema fix answers the parser could not read?

**Answers:** the author's *"ok implement structured outputs now"* · **Code:** `chesscoach/ollama.py`,
`experiments/e54-structured-outputs/` · **Date:** 2026-08-29 ·
**Status:** done — **adopted on construction, not on measurement, and the note says which**

## What it was supposed to fix

[[experiments.e51-llm-selection-and-search]] and [[experiments.e52-opening-swarm]] measured three
failure shapes, all of them the model answering in a form the caller could not read: `NONE` where a
list of integers was required, the literal `"3, NONE"`, and prose whose digits a number-scraper read
as indices — *"break with c5"* selecting sentence five.

Ollama's `format` constrains decoding at the token level, so those become **unrepresentable** rather
than discouraged. No dependency: it is one field in the request body `ollama.py` already builds.

## Result one — no measurable improvement, and the reason matters

Three arms on the same pages, because two would have been confounded — the prompt was rewritten at
the same time as the schema was added, and a first two-arm run credited the schema with both.

| arm | parsed | s/call |
|---|--:|--:|
| **old** — the prompt that shipped before | **8 / 8** | 2.7 |
| **asked** — new prompt, no schema | **8 / 8** | 2.5 |
| **forced** — new prompt + schema | **8 / 8** | 2.6 |

**The parse rate was already 100 %, so the schema could not raise it.** The failure it targets had
already been fixed by the prompt reframe in E52 — filtering to ranking — which is why it could not
be reproduced even at 50 sentences, the chunk size where the collapse originally happened.

**What the arms do show is in the raw answers, not the counts:**

    old      '17,21,22,24'                      bare numbers
    asked    'keep 10\\nkeep 11\\nkeep 12'        NOT JSON -- rescued by the scraper
    forced   '{"keep": [10, 11, 12, 13]}'       well-formed by construction

Without the schema the new prompt produces something that is neither JSON nor the old comma format,
and works only because the legacy number-scraper happens to catch it. **The prompt and the schema are
coherent together and the prompt alone is worse than what it replaced.**

So the schema ships **because the failure becomes structurally impossible**, not because it fixed a
measured one. That distinction is the finding.

## Result two — the example in the prompt was doing real harm

The rewritten prompt showed the shape by example: `Answer as JSON with their numbers:
{"keep": [3, 11, 24]}`. Across three different pages the model answered:

    {"keep": [3, 11, 24]}
    {"keep": [3, 11, 24]}
    {"keep": [3, 11, 24]}

**It was copying the example rather than choosing.** The old prompt, with no example, returned varied
indices — `0, 1, 7, 22`, `1, 4, 9, 14`.

Cost: the offline swarm fell from **five briefs of five to two**, and reproduced at two on a re-run,
so it was a regression rather than noise. Removing the example restored **5 of 5** and took notes
from ~30 before schemas, to 43 with the anchor, to **71** without it.

**A format example is few-shot data, not documentation.** → **L-048**

## Result three — the schema does not degrade what the model writes

The offline fall had two candidate causes, because the Assessor's schema also changed which notes the
Compiler received. The run store separated them exactly: notes replayed **verbatim** from stored
runs, compiled twice, nothing else different.

| | points kept | dropped |
|---|--:|--:|
| with the schema | **12** | 6 |
| without | **12** | 5 |

Identical. Constrained decoding costs nothing in point quality here, and the regression was entirely
the anchored selection.

*(This is the run store paying for itself three days after being built: the comparison is only exact
because the notes were kept.)*

## Consequence

- **Ship it.** `ollama.generate(..., schema=...)`, plus `as_json`, `ints`, `strings`, `schema_of` and
  `array_of`. Eight call sites across five agents.
- **The prose parsers stay as the fallback and are tested on both paths.** A schema is a request:
  support varies by model and Ollama Cloud has none. A model that ignores it must behave exactly as
  it did before, which is what the fallback guarantees — and the *asked* arm above shows the fallback
  still doing real work.
- **No index examples in prompts.** The schema carries the shape; an example carries an answer.
- **`classifiers.py` is deliberately untouched.** Its agreement with the author is measured at
  kappa 0.74 (E07) and changing how its answer is read would put that figure back in question.

## Honest limitations

- **Eight pages, two models, one machine.** The parse rate was 100 % everywhere, so this measured a
  ceiling rather than a difference.
- **The schema's value is an argument, not a number.** It makes a class of failure impossible; it did
  not fix one that was still happening.
- **Latency is within noise** — 2.5 to 2.7 s per call across all three arms.
