---
id: cas-adr-0017
title: 'ADR-0017 — Constrain the answer with a schema, and keep the prose parser behind it'
desc: 'Ollama''s format field makes malformed answers unrepresentable rather than unlikely. Adopted on construction rather than on measurement: the parse rate was already 100 % because the prose fallback was catching everything.'
updated: 1788566400000
created: 1788566400000
---

# ADR-0017 — Constrain the answer with a schema

**Status:** accepted · **Date:** 2026-08-29 · **Follows:**
[[decisions.0014-three-agents-for-the-opening-brief]]

## Context

Five agents each hand-parsed a model's prose, and the parsers were where the failures lived:
`NONE` where a list of integers was required, the literal `"3, NONE"`, and prose whose digits were
read as indices — *"break with c5"* selecting sentence five
([[experiments.e51-llm-selection-and-search]], [[experiments.e52-opening-swarm]]).

A framework was considered first and refused: orchestration is three sequential calls, the hard part
is verification which no framework supplies, and every dependency is a reproducibility risk against
success criterion 6. **Ollama's own `format` field solves the actual problem for free** — it is one
key in the request body `ollama.py` already builds with `urllib`.

## Decision

**Ask with a JSON Schema; read the JSON; fall back to reading the prose.**

    schema -> as_json -> the agent's own parser if that returned None

**The schema is the primary path and the prose parsers are kept, not deleted.** A schema is a
request rather than a guarantee: support varies by model, and Ollama Cloud has none. A model that
ignores it must behave exactly as it did before — and E54 shows the fallback still doing real work,
since the new prompt without the schema returns `keep 10\nkeep 11`, which is neither JSON nor the
old comma format and survives only because the number-scraper catches it.

**Bounds are still applied after the schema.** A schema can require integers; it cannot know how many
sentences were offered, so an out-of-range index is dropped rather than clamped, exactly as before.
`True` is excluded explicitly, because it is an `int` in Python and would select sentence one.

**Every property is required.** An optional field is how a model returns half an answer, and half an
answer is what this is here to prevent.

## Consequences

- `ollama.generate(..., schema=...)`, `as_json`, `ints`, `strings`, `schema_of`, `array_of`. Eight
  call sites across `opening_swarm`, `plan_selector`, `opening_search` and `opening_summary`.
- **No index examples in prompts.** The schema carries the shape; an example carries an answer, and
  one cost three briefs of five before it was found (L-048).
- **`classifiers.py` stays on its own client, deliberately.** Its agreement with the author is
  measured at kappa 0.74 (E07); changing how its answer is read would put that figure in question.

## What this does not settle

**It was adopted on construction, not on measurement.** The parse rate was 100 % in every arm, so
the schema could not raise it — the failure it targets had already been fixed by E52's prompt
reframe. It ships because the failure becomes structurally impossible for any model and any prompt
regression, which is a weaker claim than "it fixed something" and is the honest one.
