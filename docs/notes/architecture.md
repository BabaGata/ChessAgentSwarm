---
id: cas-arch
title: Architecture
desc: 'The swarm design: layers, data flow, storage and cost budget — the deliverable of mission step M3.'
updated: 1785256000000
created: 1785256000000
---

# Architecture

The system design, delivered by [[mission.step-03-architecture]]. Every choice here is traceable to
something measured ([[experiments]]) or decided ([[decisions]]) rather than assumed.

## Children

- [[architecture.player-profile]] — the structured artefact every agent reads and writes (C1)
- [[architecture.orchestration]] — how agents are run and combined (C3)
- [[architecture.interaction]] — the player-facing protocol, including probes (V9, B4)
- [[architecture.confidence]] — when the swarm is allowed to assert something (C2, R-13)

## The shape, in one picture

```
 ┌──────────────┐   games (Lichess API / PGN)
 │  1 INGEST    │──────────────────────────────────────┐
 └──────────────┘                                      │
 ┌──────────────────────────────────────────────┐      │
 │  2 ANALYSIS CORE          deterministic      │<─────┘
 │  engine evals · error labels · motifs ·      │
 │  positional features · clock · repertoire    │───> analysis cache (SQLite)
 └──────────────────────────────────────────────┘
                      │  typed observations
                      ▼
 ┌──────────────────────────────────────────────┐
 │  3 SECTION AGENTS         parallel, isolated │
 │  S1 tactics · S2 process · S3 endgame · …    │
 │  each emits Findings, never prose            │
 └──────────────────────────────────────────────┘
                      │  Findings
                      ▼
 ┌──────────────────────────────────────────────┐
 │  4 PLAYER PROFILE         the blackboard     │<──── probe answers
 │  findings · confidence · provenance · history│
 └──────────────────────────────────────────────┘
             │                        ▲
             ▼                        │
 ┌────────────────────┐    ┌──────────────────────┐
 │ 5 ARBITER          │───>│ 6 PROBER    (LLM)    │  asks when a finding's
 │ picks 1–2 priorities│   │ position + "why?"    │  gap type is ambiguous
 └────────────────────┘    └──────────────────────┘
             │
             ▼
 ┌────────────────────┐    ┌──────────────────────┐
 │ 7 PLANNER   (LLM)  │───>│ 8 EXPLAINER  (LLM)   │───> report / conversation
 └────────────────────┘    └──────────────────────┘
```

Layers 1–5 are **deterministic**. Layers 6–8 are the only ones that use a language model, and they
operate on the profile — never on raw games. That is
[[decisions.0002-compute-first-speak-last]], accepted on evidence.

## Layer by layer

### 1 · Ingest
Lichess API primary, PGN upload fallback ([[decisions.0005-scope-band-source-online-only]]).
Normalises to a game corpus with a **corpus descriptor**: player, time controls, date range, game
count, rating range. Segmented by time control — never mix bullet with classical
([[domain.signals]] § 4).

### 2 · Analysis core
Pure computation, no model. Produces typed observations per position and per game:
engine evaluation and error label, tactical motif tags, positional features, clock behaviour,
phase, opening/ECO and book-exit point, conversion outcomes.

Measured cost: **~90 s for 50 games at depth 15**, single-threaded engines across parallel workers
([[experiments.e01-engine-throughput]]). Two rules that experiment forced:

- **Parallelise per position, not per game** — otherwise wall time is set by the longest game.
- **Every observation records its provenance** (engine build, depth, date). Labels shift with depth,
  so observations from different depths are never merged.

### 3 · Section agents
One per section in [[domain.sections]], run **in parallel and in isolation**. Each reads the
analysis output and emits **Findings** — typed records, never prose. They do not talk to each other;
see [[architecture.orchestration]] for why.

### 4 · Player profile
The blackboard and the system's memory. Persistent across sessions, which is what V7 requires and
what all five prior-art projects lack. Full schema in [[architecture.player-profile]].

### 5 · Arbiter
Selects **one or two** priorities from possibly dozens of findings, using confidence
([[architecture.confidence]]), band-appropriateness, prerequisite order
([[domain.chess-concepts]] § C) and expected gain. Coaches give one or two priorities, not nine —
and "list everything" is the LLM default this design exists to prevent (R-12).

### 6 · Prober
Resolves what games cannot: whether a finding is a knowledge gap, a skill gap, a process habit or a
psychological pattern (L-002). Invoked only for findings the arbiter has shortlisted, so the cost
scales with priorities, not with findings. See [[architecture.interaction]].

### 7 · Planner
Turns prioritised, gap-typed findings into an ordered path with time estimates and **predicted
progress signs** — the sign is mandatory, because without it V7 cannot check anything and the advice
is unfalsifiable (R-02).

### 8 · Explainer
Renders the profile and plan into language. Constrained to speak only about findings present in the
profile, with their evidence attached — the anti-hallucination clause borrowed from prior art.

## Storage

| Store | Contents | Why |
|---|---|---|
| **SQLite** (single file) | analysis observations, keyed by position | free, local, no server, handles millions of rows; C1/C2 |
| **JSON documents** | the player profile, one per player, versioned | human-readable, diffable, testable — a profile can be inspected and hand-checked, which prose in a database cannot |
| **Vendored corpora** | puzzle themes, opening/trap data | CC0, downloaded once, no runtime network dependency (pattern borrowed from prior art) |

**Position-level evaluation cache**, keyed by `(position, engine build, depth)`. Positions recur
across games and across players — especially in the opening — so the cache reduces cost with every
player analysed. It is also what makes re-analysis at a fixed depth reproducible, which
[[evaluation]]'s B4 determinism test needs.

## Cost budget (constraints C1–C4)

| Item | Budget | Basis |
|---|---|---|
| Engine, 50 games | ~90 s, £0 | measured, E01 |
| Section agents | deterministic, seconds | no model calls |
| Prober | ≤ ~6 exchanges per session | bounded by shortlist size |
| Planner + explainer | operate on a summary, not games | prior art runs a rich cross-game summary in ~200–250 tokens |
| **Total cash per session** | **≈ 0** | free tier or local model |

The single design property that achieves this: **token volume is a function of the number of
findings, not of the number of moves analysed.**

## How this satisfies the vision

| Item | Where |
|---|---|
| V1 skill assessment | analysis core + S-sections aggregate |
| V2 knowledge assessment | prober (6) — games alone cannot do it |
| V3 style profiling | S10 over measured tendency vs. measured performance |
| V4 gap detection | section agents (3) writing typed findings |
| V5 prioritisation | arbiter (5) |
| V6 path planning | planner (7), with mandatory progress signs |
| V7 progress tracking | persistent profile (4) + re-analysis over time |
| V8 explainability | findings carry evidence; explainer may not exceed them |
| V9 dialogue & active assessment | prober (6), [[architecture.interaction]] |
| C1–C4 cost | layers 1–5 free; 6–8 bounded — budget above |
| C5 auditable | every claim traces to positions with provenance |
| C6 incrementally useful | each section agent is independently valuable and independently ablatable |

## Implementation status

The skeleton — layers 1, 2 and 4 — is built and tested. Layers 3 and 5–8 do not exist yet.

| Design | Code | Status |
|---|---|---|
| 1 Ingest | `chesscoach/ingest/pgn.py`, `ingest/corpus.py` | built; deterministic corpus id |
| 2 Analysis core | `chesscoach/analysis/{core,engine,cache,labels,observations}.py` | built; cache keyed by (position, engine, depth) |
| 3 Section agents | `chesscoach/sections/` | **S2 and S1 built**, both assessed on real players |
| 4 Player profile | `chesscoach/profile/{models,io}.py` | built; typed findings, validation, round-trip |
| 5 Arbiter | `chesscoach/arbiter.py` | **built** — ranks by tier, then unusualness, then breadth; caps at two; prefers a second priority about something else |
| 6–8 Prober / planner / explainer | — | later in M3's build-out |
| CLI | `chesscoach/cli.py` | `analyse` runs layers 1→2→4 end to end |

**Verified by running it**, not only by tests: 24 real games, 1,860 moves, 8.8 % error rate at
depth 12; a second run over the same games completed in **0.78 s** from the cache and produced a
**byte-identical** profile — which is the B4 determinism property the evaluation plan needs.

74 tests, 85 % coverage. The uncovered remainder is the code that drives a live engine subprocess
and the CLI's top-level handler; both are exercised by the end-to-end run rather than by unit tests.

Two design notes that only became visible while building:

- **`to_position_eval` is a pure function**, separate from the engine wrapper, so the mate-clamping
  logic can be tested without a subprocess. That logic is exactly where L-005's bug lives.
- **The analyser is injected** into the analysis core rather than constructed by it. That is what
  makes the core testable without Stockfish, and it is the same seam a parallel implementation will
  use when per-position parallelism is added.

## Deliberate omissions

- **No inter-agent conversation.** Reasons in [[architecture.orchestration]].
- **No fine-tuned model.** Out of scope (ADR-0002 alternatives).
- **No web service, accounts or multi-tenancy** — vision non-goals.
- **No real-time play analysis.** Post-game only; Lichess delays live game data anyway.
