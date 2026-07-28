---
id: cas-capacity-tools
title: Tools
desc: 'External tools, engines, datasets and services available to the project and the swarm.'
updated: 1785254500000
created: 1785254500000
---

# Tools

Candidate and adopted tooling. Everything here must satisfy C1 (free/near-free) and C3 (open /
self-hostable) unless an explicit exception is logged in [[decisions]].

## Status legend

`candidate` — identified, not yet evaluated · `evaluated` — tested, findings recorded ·
`adopted` — in use · `rejected` — with a reason.

## Chess engines & analysis

| Tool | Status | Purpose | Notes |
|---|:--:|---|---|
| Stockfish | candidate | position evaluation, blunder detection, best-move comparison | free, local, the obvious baseline; verify licence and local run cost |
| Lichess analysis / cloud eval | candidate | precomputed evals without local compute | free API, rate-limited |

## Data sources

| Tool | Status | Purpose | Notes |
|---|:--:|---|---|
| Lichess API | candidate | player games as PGN/NDJSON with `evals`, `accuracy`, `opening`, `division` (phase) parameters; ratings | free; rate-limited — back off a full minute on HTTP 429. Parameter names taken from a third-party doc mirror, **verify against `lichess.org/api`** |
| **Lichess puzzle database** | candidate — **highest value found in M1** | ~millions of puzzles as CSV with motif **theme tags**, ratings, popularity, opening tags | **CC0 licence**, zstd-compressed. Maps directly onto the K2 motif vocabulary in [[domain.chess-concepts]]; usable both as prescribed training material and as a labelled corpus for a motif classifier |
| Lichess open database | candidate | bulk games, opening explorer | free, very large |
| Chess.com public API | candidate | player games for chess.com users | free, read-only |
| python-chess | candidate | PGN parsing, board logic, UCI engine driver | the standard glue library; near-certain adoption |

## Models & runtime

| Tool | Status | Purpose | Notes |
|---|:--:|---|---|
| Local small LLM (e.g. via Ollama) | candidate | explanation, dialogue, classification | zero marginal cost; quality must be evaluated for chess reasoning |
| Free-tier hosted LLM | candidate | outer-loop planning only | rate limits; must not sit in an inner loop |

## Project tooling (in use)

| Tool | Status | Purpose |
|---|:--:|---|
| Dendron | adopted | this knowledge base / project steering |
| git | adopted | history, checkpoints per [[process]] |
| Claude Code + `adaptive-cycle` skill | adopted | the working loop |

Every promotion from `candidate` to `adopted`/`rejected` needs a line in [[decisions]] and,
if it changes what the system can do, an update to [[capacity]].
