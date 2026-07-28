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

- [ ] Every question 1–13 has an answer or an explicit "unknown / deferred" with a reason.
- [ ] [[domain.chess-concepts]] exists: the concept landscape with dependency structure.
- [ ] [[domain.coaching]] exists: assessment, diagnosis, sequencing, progress-tracking practice.
- [ ] [[domain.signals]] exists: what is computable from games, with the free tooling that does it.
- [ ] [[domain.sources]] exists: source list with a quality note on each.
- [ ] Contested / low-evidence claims are marked as such.
- [ ] [[state]] scorecard and [[capacity.knowledge]] updated; findings that change [[vision]] or
      [[mission]] have been applied or explicitly rejected in [[decisions]].

## Working log

| Date | Activity | Outcome |
|---|---|---|
| 2026-07-28 | Step opened; documentation spine created | Questions 1–13 framed |
