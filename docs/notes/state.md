---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785254500000
created: 1785254500000
---

# State

**Snapshot date:** 2026-07-28
**Active mission step:** M1 — [[mission.step-01-foundations]]
**Last commit:** documentation spine + adaptive-cycle skill (baseline)

This note is rewritten at the end of every work cycle. It is the honest answer to
"if someone joined the project today, what would they need to know?"

## What exists

| Area | Exists | Notes |
|---|---|---|
| Documentation / steering | yes | Dendron vault with vision, mission, state, capacity, learning, process, evaluation, decisions |
| Process automation | yes | `adaptive-cycle` skill |
| Chess domain knowledge | no | M1 in progress |
| Section catalogue | no | M2 |
| Architecture design | no | M3 |
| Any agent | no | M4 |
| Evaluation harness | no | designed in M3 |
| Code | none | intentionally — no code before M1–M3 |

## Distance to vision

Each [[vision]] capability / constraint scored **0–5** (0 = nothing, 3 = works but weak,
5 = meets the success criteria). This table is the project's primary progress instrument.

| Dim | Vision item | Score | Evidence / why |
|---|---|:--:|---|
| D1 | V1 skill assessment | 0 | not started |
| D2 | V2 knowledge assessment | 0 | not started |
| D3 | V3 style profiling | 0 | not started |
| D4 | V4 gap detection | 0 | not started |
| D5 | V5 prioritisation | 0 | not started |
| D6 | V6 path planning | 0 | not started |
| D7 | V7 progress tracking | 0 | not started |
| D8 | V8 explainability | 0 | not started |
| D9 | C1–C4 cost profile | 0 | no measurements yet; no architecture to cost |
| D10 | Evaluation capability | 0 | [[evaluation]] framework drafted only as intent |
| D11 | Process & documentation health | 3 | spine exists and is coherent; unproven over cycles |

**Total: 3 / 55.** The only asset is the steering mechanism, which is exactly what M1 expects.

## Next logical steps (priority order)

1. **P0 — Run M1 research.** Answer questions 1–13 in [[mission.step-01-foundations]]; write
   [[domain.chess-concepts]], [[domain.coaching]], [[domain.signals]], [[domain.sources]].
2. **P1 — Decide the cost architecture early.** C1 (free/near-free) will constrain every later
   design choice; the signal inventory from M1 Q11–Q13 determines how much work can be done by
   deterministic tooling (engine, statistics) instead of LLM calls. Draft an ADR at the end of M1.
3. **P2 — M2 section catalogue.** Only after M1, since the sections come from the knowledge map.
4. **P3 — Decide the target player band for the first end-to-end slice.** Coaching a 900 and a 2100
   are different problems; picking one narrows M3 and M4 dramatically. Candidate: ~1000–1600, where
   diagnosis is most tractable and improvement advice is best established.

## Open questions

- Where do the player's games come from — Lichess/Chess.com import, PGN upload, or live play?
- Is the interaction conversational (chat), report-based (a document), or both?
- How much can be precomputed once (concept knowledge, puzzle motif banks) versus per-player?
- What is the minimum viable player profile that all agents read/write?

Answers land in [[decisions]] as they are made.

## Blockers

None. Research is unblocked.
