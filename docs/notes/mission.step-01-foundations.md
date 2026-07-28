---
id: cas-mission-m1
title: 'M1 — Chess & Coaching Foundations'
desc: 'Active mission step: build the general overview of knowledge the swarm needs to coach chess effectively.'
updated: 1785254500000
created: 1785254500000
---

# M1 — Chess & Coaching Foundations

**Status:** wip
**Parent:** [[mission]]
**Outputs into:** [[domain]]

## Goal of this step

Build a general overview of the knowledge an agent swarm needs in order to coach chess players
effectively — the chess concepts themselves, *and* the pedagogy of how those concepts are taught,
diagnosed and sequenced by real coaches.

This step produces understanding, not code. It is the input to M2 (chunking into prioritised
sections) and therefore silently determines the entire agent topology. Getting it wrong is
expensive; getting it *approximately* right and revisable is the target.

## Questions this step must answer

**Chess content**
1. What are the domains of chess knowledge (openings, tactics, strategy, endgames, calculation,
   positional judgement, prophylaxis, planning, time management, psychology)?
2. Within each, what are the *concepts* — the smallest teachable units?
3. How do concepts depend on each other (prerequisite structure)?
4. Which concepts matter at which strength band? What is actually the binding constraint at
   ~800, ~1200, ~1600, ~2000 Elo?

**Coaching practice**
5. How do strong coaches assess a new student? What do they look at first?
6. How do they diagnose *why* a player loses — the difference between a knowledge gap, a skill gap,
   a habit/process gap, and a psychological gap?
7. How do they sequence improvement? What are the accepted study-time allocations by level?
8. What are the recognised anti-patterns (e.g. opening theory obsession at low ratings)?
9. How is progress measured other than rating? What are leading indicators?
10. What does "style" mean operationally, and how is a repertoire matched to a player?

**Evidence & data**
11. What signals are extractable from a player's games automatically (engine eval swings, ACPL,
    time usage, phase-wise performance, tactical motif classification, opening repertoire stats)?
12. What free data and tooling exist (Lichess API/database, Stockfish, puzzle datasets with motif
    tags, opening books/explorers)?
13. Which of the coaching diagnoses above are computable from those signals, and which need
    a language model, and which need the player to answer questions?

## Method

1. Desk research: chess pedagogy sources, established improvement literature, coach-written
   material, and technical documentation for free tooling.
2. Record findings as notes under [[domain]], one note per coherent area, with sources.
3. Explicitly separate **claim** from **evidence quality** — chess improvement advice is full of
   confident folklore. Mark contested claims.
4. Map every finding to the question numbers above; note which questions stay unanswered.
5. Map findings to [[vision]] capabilities V1–V8 — knowledge that serves none of them is out of scope.

## Definition of done

- [x] Every question 1–13 has an answer or an explicit "unknown / deferred" with a reason.
      *(1–4 answered first-pass; 5–10 answered first-pass; 11–13 answered well. Remaining unknowns
      listed under "Open items" in each domain note and as P2 in [[state]].)*
- [x] [[domain.chess-concepts]] exists: the concept landscape with dependency structure.
- [x] [[domain.coaching]] exists: assessment, diagnosis, sequencing, progress-tracking practice.
- [x] [[domain.signals]] exists: what is computable from games, with the free tooling that does it.
- [x] [[domain.sources]] exists: source list with a quality note on each.
- [x] Contested / low-evidence claims are marked as such.
- [x] [[state]] scorecard and [[capacity.knowledge]] updated; findings that change [[vision]] or
      [[mission]] have been applied or explicitly rejected in [[decisions]].
- [x] **Prior art actually read** — all five, → [[domain.prior-art]].
- [x] **Engine cost measured** — → [[experiments.e01-engine-throughput]]. 50 games in 89 s at
      depth 15, zero cash cost. Also measured that analysis depth changes the *diagnosis*, which
      changed the architecture more than the cost figure did.
- [ ] Primary sources read — Capablanca held and used; Nimzowitsch outstanding (F2, now under
      constraint C7).

**Step status: nearly closed.** One item remains, and it no longer blocks M2 — the section catalogue
can be built on the puzzle-theme vocabulary and the K1–K10 map, with Nimzowitsch feeding the
positional sections when read.

## Findings that changed the plan

| Finding | Consequence |
|---|---|
| Lichess puzzle DB is CC0 **with motif theme tags** | free labelled corpus that maps onto the tactical motif vocabulary — the strongest asset found; shapes M2 and the first agent |
| Passive game analysis cannot separate knowledge gaps from skill gaps | the swarm needs **active assessment** (probe positions), so interaction is a core capability, not a UI afterthought → [[mission]] M3 brief updated, L-002 |
| ~All diagnostic signals are deterministic computation | **compute first, speak last** architecture → [[decisions.0002-compute-first-speak-last]] (proposed), L-003 |
| Coaches produce *one* diagnosis, not a list | an LLM coach's default behaviour (list nine weaknesses) is a known anti-pattern; must be designed against |
| Advice differs sharply by strength band | argues for choosing one band for the first slice; recommendation 1400–1800 |
| Tactics are machine-labelled, strategy is not | asymmetry that will likely determine which agent is buildable first |

## Working log

| Date | Activity | Alignment check | Outcome |
|---|---|---|---|
| 2026-07-28 | Step opened; documentation spine created | serves C5/C6; moves D11 | Questions 1–13 framed |
| 2026-07-28 | First research pass: chess concepts, coaching practice, computable signals, tooling, prior art | Serves V1–V4 (defines *what* must be assessed) and C1 (identifies how much can be done without LLM calls). Moves capacity dimensions, not the vision scorecard — expected for M1. Cheaper alternative considered: skip straight to M2/M3 and design from general knowledge — rejected, because the section catalogue determines the entire agent topology (L-001) and would then rest on unsourced assumption. Narrowed the pass to *coach-diagnosable* structure rather than a full chess encyclopaedia. | 4 domain notes; 3 open items; 1 proposed ADR; 3 lessons |
