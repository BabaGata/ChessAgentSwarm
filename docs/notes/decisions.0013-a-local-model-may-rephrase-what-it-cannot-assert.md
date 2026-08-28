---
id: cas-adr-0013
title: 'ADR-0013 — A local model may rephrase what it may not assert'
desc: 'Ollama joins the pipeline for language work only: it rewrites quoted sentences and its output is checked against them before being kept. Rephrasing is checkable and asserting is not, which is the whole line.'
updated: 1788480000000
created: 1788480000000
---

# ADR-0013 — A local model may rephrase what it may not assert

**Status:** accepted · **Date:** 2026-08-28 · **Builds on:**
[[decisions.0012-quote-the-plans-rather-than-write-them]]

## Context

The author asked for *"utilisation of ollama to handle this agent, perform web searches and combine
the information in a few sentences that sound natural."*

The complaint behind it is real and visible in
[[experiments.e49-opening-resources]]: the quoted plans work and **read like quotes** — three
sentences from two publishers in two registers, joined by nothing.

The obvious implementation is forbidden. R-03 says LLM-generated chess advice is not a source, and
ADR-0012 was written one day earlier on exactly this point. **A local model does not change the
epistemics**: `qwen3:8b` saying *"Black should aim for the c5 break"* is folklore whether it runs on
this GPU or someone's cloud.

## Decision

**Ollama is admitted for language work on supplied text, and refused as a source of chess.**

The line is *rephrasing* against *asserting*:

| asked | is it checkable? | allowed |
|---|---|---|
| *"say these sentences more plainly"* | yes — against the sentences | **yes** |
| *"explain the Pirc for a 1500"* | no — against nothing | **no** |

This is the same line `classifiers.py` already draws for the prober: *"Nothing here is ever asked
what the best move is… The reason to check against is supplied by a detector."* The model is given
the answer and asked about the words.

Every output passes `chesscoach/grounding.py` before it is kept:

- **ungrounded moves** — every square and move in the output must appear in the source. This is the
  concrete-false-claim check, and it fired on real output: `qwen2.5:3b` wrote **`f6`** into the
  Italian Game summary and the source never mentions it.
- **novelty** — the share of content words never seen in the source, capped at **0.45**, calibrated
  against two models' real output rather than chosen.

**A rejected rewrite falls back to the verbatim quotes**, which is what shipped before. Trying is
never a loss, and `Summary.accepted` records which happened so the rate is measured.

**The evidence class travels with the text.** `composed` means a local model wrote these words from
cited sentences; `quoted` means the publisher did. A reader must never be told a model's phrasing is
a publisher's.

**An unreviewed page is never handed to a model.** Rephrasing something unendorsed would launder it
into prose that no longer looks like an unreviewed quote.

## Alternatives considered

- **Free generation from model knowledge** — what was literally asked for, and what R-03 forbids.
  Rejected: it makes every sentence unfalsifiable against a source, which is the property the whole
  opening-resource design was built to have.
- **Model selects and orders, never writes** — zero new exposure, and it cannot smooth the join
  between two publishers' registers, which is the actual complaint.
- **A second model grading the first** — moves the trust problem rather than solving it. The checker
  is deterministic for that reason.

## Consequences

- `chesscoach/grounding.py`, `chesscoach/opening_summary.py`; `OpeningResource.summary` and `.prose`.
- **`qwen2.5:3b` ships**, on measurement: **88 % composed at 18 % novelty in 3.6 s** against
  `qwen3:8b`'s **38 % at 38 % in 8.2 s** ([[experiments.e50-ollama-summaries]]). The 1.9 GB model
  beat the 5.2 GB one on every axis, which is also the C1 answer.
- **Thinking is disabled.** There is nothing here to reason about, and left on it consumed the whole
  token budget and returned an empty response.
- **A summariser is optional everywhere.** With none supplied the system behaves exactly as it did
  yesterday.

## What this does not settle

**The checker does not understand a sentence.** Swapping the colours — *"White aims to undermine the
center… while Black allows the pressure"* — uses only the source's own vocabulary and squares, and
passes both tests against a page saying the opposite. **One instance was found in real output**: for
the Caro-Kann the source said *"Each creates a different type of pawn structure"* and the rewrite
said *"Black creates a different type of pawn structure"*, changing the subject of the claim.

Simple negation happens to be caught, because *"avoid"* and *"never"* are words a page recommending
a break does not use — **luck, not design**, and recorded as such.

So `grounded` means *"every concrete thing here came from the source"*, never *"this is correct"*.
`reviewed=true` remains a person's job and now carries more: approving a page means its sentences may
be **rephrased** in the author's name, not merely repeated.
