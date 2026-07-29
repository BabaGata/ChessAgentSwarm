---
id: cas-mission-m4
title: 'M4 — First agent: S2'
desc: 'Build one agent for one section: decision process & clock behaviour.'
updated: 1785257200000
created: 1785257200000
---

# M4 — First agent: S2

**Status:** built, tested, scored
**Parent:** [[mission]] · **Design:** [[capacity.agents.s2-decision-process]]

## Goal

Build the first section agent, having planned it first: knowledge organisation, agent type, tools,
instruction, inputs, outputs, efficacy measure and cost profile — the ten questions in
[[capacity.agents]] — before any code.

## Alignment check

- **Serves:** V4 (gap detection) directly; V1 and V8 through the profile it writes. It is the first
  work in the project that can move the vision scorecard rather than capacity.
- **Cheaper alternative considered:** start with S1 (tactics), which has the richer free dataset.
  Rejected in [[mission.step-02-sections]] and the rejection held up — S2 needed no engine work of
  its own, so the first agent exercised the architecture rather than a dataset integration.
- **Forecloses:** nothing. Section agents are additive by construction (ADR-0006).
- **Made more aligned by:** requiring the agent to distinguish *insufficient data* from *no problem
  found*, which is what stops silence being read as a clean bill of health.

## Result

Three conditions diagnosed: time pressure, instant moves, and the long-think-then-mistake signature.
All deterministic, no engine calls of its own, no model calls. 144 tests, 81 % coverage; the agent
module itself is at 100 %.

**Score against the planted weakness:** found the planted `time_pressure` flaw at `priority` tier —
37.7 % error rate under time pressure against 6.8 % otherwise, a 5.54× lift across 16 distinct
games — with **zero spurious findings**. Both halves of the efficacy measure passed.

## What the evaluation caught — the point of building it first

The first scored run **failed**, and the failure was the fixture's, not the agent's.

S2 reported a `long_think_error` at 2.92× and missed the planted time-pressure weakness entirely.
The cause was a confound I had built into the generator: the time model made the flawed player think
slowly for its first ten moves, so "long think" coincided exactly with "early game" — where errors
still cost win probability. The planted time-pressure errors happen late, where they compress toward
invisibility (L-009). S2 was reporting the strongest real pattern in the data. The data was wrong.

Two fixes, one on each side:

- **The fixture:** think times are now uniform by default (`--slow-think` equal to `--normal-think`),
  so a time-pressure plant cannot be confounded with a long-think signal. Time pressure is created
  by a shorter clock instead.
- **The agent:** S2 now **excludes moves played in already-decided positions** (|eval| > 500cp).
  Win probability compresses at the extremes, so errors there are cheap to make and nearly invisible
  to measure — and no coach diagnoses decision-making from a lost position. This is a genuine
  improvement that arrived only because something was measured.

After both, the same agent scored perfectly on the same kind of fixture. Note the effect of the
filter: within *competitive* positions the time-pressure error rate is 37.7 %, against 8.9 % measured
across all planted moves. The signal was there; the decided positions were burying it.

A third, smaller correction: the scorecard reported "MISSED" when the agent had actually **declined
for insufficient data** at 12 games. Declining is correct behaviour, and scoring it as a failure
would penalise honesty. `ScoreCard` now distinguishes the two.

## Definition of done

- [x] Designed before built — all ten questions answered in [[capacity.agents.s2-decision-process]].
- [x] Built test-first; agent module at 100 % coverage.
- [x] Efficacy measured against ground truth, not asserted.
- [x] Confidence policy enforced at runtime, including split-half replication.
- [x] Contract behaviours tested: zero findings when warranted, silence on thin data, no peer claim
      without a peer corpus.
- [ ] Run against **real** players' games, not only planted ones (M5).
- [ ] Ablation check — does the swarm lose anything measurable without S2? Needs a second agent.

## Working log

| Date | Activity | Alignment check | Outcome |
|---|---|---|---|
| 2026-07-28 | Designed S2, built it test-first, scored it against the planted set | see above | Found the planted weakness, 0 spurious. Fixture confound and a real agent improvement both discovered by measuring |
