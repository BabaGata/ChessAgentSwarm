---
id: cas-adr-0016
title: 'ADR-0016 — SQLite for what the swarm did, JSON for what it reads'
desc: 'Agent output goes into a SQLite file written as the run proceeds; the opening book stays JSON because it is a load format, not a query format. Measured before deciding: 0.04 s to load, 1.2 ms per game walked.'
updated: 1788480000000
created: 1788480000000
---

# ADR-0016 — SQLite for what the swarm did, JSON for what it reads

**Status:** accepted · **Date:** 2026-08-28 · **Follows:**
[[decisions.0015-a-learned-skip-list-and-a-bullet-brief]]

## Context

The swarm's own output was not stored at all. A run cost five fetches and ten model calls, passed
`Candidate → Reading → Brief` between agents as objects in memory, and left nothing behind but a text
file an experiment script happened to write. Re-running an opening paid the whole bill again.

The author set the constraint: *"I want the swarm to be able to be checked by humans for what is it
doing but the easiness of the readability for human is not the priority, but performance is, if the
human has to search some database instead of just read txt files directly this is ok."*

And asked whether the opening book should move too.

## Decision

**SQLite for the agents' output. JSON stays for the opening book.**

They are different kinds of data and the difference is what decides it:

| | the book | the runs |
|---|---|---|
| shape | immutable reference, regenerated from source in 1 s | append-only history that must accumulate |
| access | every position, in a tight loop | occasionally, by opening or by run |
| the question asked | *"what is this position called?"* | *"show every point ever dropped for novelty"* |
| what it needs | a dict | indexes and transactions |

**The book was measured before being defended**, rather than argued about:

| | |
|---|--:|
| file size | 1.46 MB |
| parse + index | **0.04 s** |
| peak memory | 4.4 MB |
| **per game walked** | **1.2 ms** |
| rewrite to add one opening | 18 ms |

**JSON is a load format here, not a query format.** It is parsed once into dicts at startup and every
theory check afterwards is a dict lookup on an EPD string — SQLite cannot beat that without being
loaded into memory anyway, at which point the refactor buys nothing. Extension is 18 ms and happens
per new opening, not per game, so that is not where it hurts either. It would justify moving at
around 100 MB, when the load cost becomes seconds per process — and for query speed or extension,
never.

**`sqlite3` is in the standard library**, so this adds no dependency, which matters for C1 and for an
examiner reproducing the work from an empty directory.

## Consequences

- `chesscoach/runstore.py` — `run`, `page`, `note`, `point`, indexed on the columns the questions
  use. WAL mode, so `dump_run.py` never blocks a running swarm.
- **Written as the run proceeds, and the run row is opened *before* the search.** The first version
  opened it after `scout.find`, which was wrong for the exact reason this store exists: a
  rate-limited search left **no row at all**, so the commonest failure here was invisible rather than
  visible as a run with zero pages. Pinned in a test.
- **Dropped points are stored with their reasons.** Why the swarm rejects things is invisible in the
  brief and is what tuning needs. It paid immediately: across five real runs the top drop reason is
  *"repeats a point already made"* (7), more than every grounding failure combined — which no text
  report could have shown.
- **The store is optional.** With none supplied the swarm behaves exactly as before and persists
  nothing, so tests stay fast.
- **`data/runs.db` is gitignored**, like every other data artefact. `dump_run.py` is the reviewable
  form, and it prints sentences in full where the old reports cropped them to 88 characters for
  column alignment.

## What this does not settle

**Nothing reads the store yet.** The report still re-derives a brief rather than looking for a recent
one, so the cost saving the store makes possible has not been taken. That is the next step and it
needs a staleness rule — how old a brief may be before it is worth paying for again.
