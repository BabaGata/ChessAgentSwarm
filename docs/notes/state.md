---
id: cas-state
title: State
desc: 'Where the project actually is right now, how far that is from the vision, and what comes next.'
updated: 1785254600000
created: 1785254500000
---

# State

**Snapshot date:** 2026-07-28
**Active mission step:** M1 — [[mission.step-01-foundations]] (first research pass done, step still open)
**Last commit:** `research(M1): chess & coaching foundations — concepts, coaching practice, computable signals`

Rewritten at the end of every cycle. The honest answer to "if someone joined today, what would they
need to know?"

## What exists

| Area | Exists | Notes |
|---|---|---|
| Documentation / steering | yes | Dendron vault: vision, mission, state, capacity, learning, process, evaluation, decisions |
| Process automation | yes | `adaptive-cycle` skill; one full cycle run through it |
| Chess domain knowledge | **first pass** | [[domain.chess-concepts]], [[domain.coaching]], [[domain.signals]], [[domain.sources]] |
| Tooling inventory | **first pass** | [[capacity.tools]] — identified, none evaluated by running it |
| Section catalogue | no | M2 |
| Architecture design | no | M3 (one ADR proposed: [[decisions.0002-compute-first-speak-last]]) |
| Any agent | no | M4 |
| Evaluation harness | no | designed in M3 |
| Code | none | intentionally — no code before M1–M3 |

## Distance to vision

[[vision]] capabilities/constraints scored **0–5** (0 = nothing, 3 = works but weak, 5 = meets the
success criteria).

| Dim | Vision item | Score | Δ | Evidence / why |
|---|---|:--:|:--:|---|
| D1 | V1 skill assessment | 0 | — | signals identified, nothing built |
| D2 | V2 knowledge assessment | 0 | — | *method* now identified (probe positions) but unbuilt |
| D3 | V3 style profiling | 0 | — | operational definition drafted ([[domain.coaching]] § 6) |
| D4 | V4 gap detection | 0 | — | diagnosis taxonomy drafted, unbuilt |
| D5 | V5 prioritisation | 0 | — | band table gives a starting heuristic |
| D6 | V6 path planning | 0 | — | |
| D7 | V7 progress tracking | 0 | — | leading indicators identified |
| D8 | V8 explainability | 0 | — | |
| D9 | C1–C4 cost profile | 0 | — | no measurement yet; the key unknown is Stockfish throughput on the target laptop |
| D10 | Evaluation capability | 0 | — | |
| D11 | Process & documentation health | 4 | +1 | one full cycle executed end-to-end through the skill |
| D12 | V9 dialogue & active assessment | 0 | new | capability added this cycle, [[decisions.0003-add-v9-dialogue-and-active-assessment]] |

**Total: 4 / 60** (was 3 / 55; the denominator grew because the vision gained a capability —
that is the process working, not a regression).

**Read this correctly:** M1–M3 are *capacity-building* steps. They are expected to move [[capacity]]
without moving the vision scorecard — the scorecard only moves once agents exist (M4+). To keep
progress visible in the meantime, track capacity readiness separately:

| Capacity dimension | Score 0–5 | Note |
|---|:--:|---|
| Domain knowledge (chess) | 2 | landscape mapped; primary sources not yet read; positional-concept catalogue missing |
| Domain knowledge (coaching) | 2 | method + diagnosis taxonomy captured; no detailed published curriculum studied |
| Signal & tooling knowledge | 3 | strong; the puzzle DB + engine path is clear, unvalidated by running anything |
| Prior-art knowledge | 1 | five comparable projects identified, **none read** |
| Architecture | 1 | one proposed ADR, no design |
| Evaluation design | 1 | intent only |

**Standing rule (from the [[process]] two-cycle trigger):** if the *capacity* table also stops moving
for two consecutive cycles, that is the mission-review trigger — not the vision scorecard, which is
expected to sit at zero until M4.

## Next logical steps (priority order)

1. **P0 — Read the prior art.** [[domain.sources]] § prior art lists five comparable projects,
   notably `bleongcw/Arrakis_Engine` (recurring weakness escalation across games). The
   research-and-reuse rule says read these *before* designing anything. Cheapest possible way to
   avoid re-deriving a diagnosis pipeline.
2. **P1 — Measure the engine budget.** Time Stockfish over ~50 games at a candidate depth on the
   target laptop. This single number decides whether per-game deep analysis is feasible (C1/C2) and
   constrains every M3 architecture option. Currently the biggest unknown in the project.
3. **P2 — Close M1's remaining questions.** Primary sources for coaching pedagogy; the
   deliberate-practice figure; typical-plan catalogues per pawn structure; whether positional motifs
   can be classified without labelled data.
4. **P3 — M2 section catalogue,** built on the K1–K10 domains and the four-way gap taxonomy.
5. **P4 — Pick the target band for the first end-to-end slice.** Recommendation from M1:
   **1400–1800**, because that is the band where sources agree losses come from *individual
   recurring weaknesses* rather than generic blunders — i.e. where personalised diagnosis beats
   generic advice, which is exactly this system's claim. Decide in M3 and log an ADR.

## Open questions

**The full register lives in [[open-questions]]** — every unknown with an ID, an owner, what it
blocks and a concrete resolution path. Summary of the live ones:

- Where do the player's games come from — Lichess/Chess.com import, PGN upload, or live play?
  *(Leaning: Lichess API first — free, documented, and the puzzle/opening data shares the ecosystem.)*
- Is the interaction conversational, report-based, or both? M1 says **both are needed**: passive
  analysis cannot separate knowledge gaps from skill gaps without probes.
- How much can be precomputed once (concept knowledge, motif banks) versus per-player?
- What is the minimum viable player profile all agents read/write? *(Now the central M3 artefact —
  the four-way gap taxonomy suggests its shape.)*
- Does the swarm handle over-the-board players (no digital game record) at all, or online only?
- **Sample-size and confidence policy:** what is the minimum evidence before the swarm is allowed to
  state a weakness? Needs a concrete rule, not a judgement call.

## Blockers

None. P0 and P1 are both unblocked and cheap.
