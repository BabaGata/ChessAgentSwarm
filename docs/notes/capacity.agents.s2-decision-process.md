---
id: cas-agent-s2
title: 'Agent S2 — Decision process & clock behaviour'
desc: 'The first agent: diagnoses the habits that produce errors regardless of chess knowledge.'
updated: 1785257000000
created: 1785257000000
---

# Agent S2 — Decision process & clock behaviour

**Section:** [[domain.sections]] → S2 · **Status:** built, scored, assessed on real data
**Built in:** [[mission.step-04-first-agent]] · **Assessed in:** [[mission.step-05-assess-s2]]

> **Current behaviour, honestly stated.** S2 finds the planted weakness at 5.54× with zero spurious
> findings, and says **nothing about any of seven real players**. Two of its three conditions are
> either rarely triggered (time pressure, in 600+0 arena games) or withheld as
> selection-confounded (long think). It is a correct agent whose useful range is currently narrow,
> and it widens when the rating-peer corpus exists.

The first agent, chosen ahead of the richer tactical section on purpose: it is the cheapest to
build, needs no engine for most of its signal, targets the **process gap** that content-based
coaching never reaches, and is the one thing an LLM-only coach cannot do at all, because it needs
the data rather than the position. The first agent's job is to make the architecture real.

## 1 · Remit

The habits that produce errors **regardless of chess knowledge**:

- moving instantly in positions that deserved thought;
- error rate collapsing when the clock is low;
- the long-think-then-bad-move signature (Kotov syndrome, [[domain.chess-concepts]] K9).

**Explicitly not its business:** *why* a move was wrong. That a knight fork was missed belongs to S1.
S2 only says *under what conditions* this player's decisions get worse. The two together are what
separates "you miss forks" from "you miss forks when you have under a minute", and only the second
is actionable as a habit change.

## 2 · Knowledge organisation

S2 has no knowledge base. It holds **thresholds and definitions**, nothing about chess. Everything it
knows about the player is derived at run time from observations. That is a property of the section,
not a shortcut: process gaps are defined by measurement, not by chess content.

## 3 · Agent type

**Deterministic statistical detector.** No language model, no retrieval. Rules in
[[architecture.orchestration]] forbid a model call in the diagnosis stage anyway, but here it would
also be pointless — the entire signal is arithmetic over timestamps.

## 4 · Knowledge maintenance

Thresholds are the only tunable state, and they are **provisional until validated**:

| Threshold | Value | Basis |
|---|---|---|
| time pressure | clock ≤ 60 s | convention; should scale with the time control — recorded as a known refinement |
| instant move | ≤ 2 s spent | short enough that no real decision occurred |
| long think | ≥ 3× the player's own median think time | adaptive, so it means the same for a fast and a slow player |
| opening grace | first 8 plies ignored | book moves are legitimately instant |

Validated by the split-half harness once real findings exist, per [[architecture.confidence]].

## 5 · Tools

`chesscoach.analysis` observations (which carry the clock), `chesscoach.confidence` for tiering,
`chesscoach.evaluation.splithalf` for the replication requirement. No engine call of its own — it
reads evaluations the analysis core already produced.

## 6 · General instruction

Not a prompt; a behavioural contract, enforced by tests:

1. Emit **zero** findings when the evidence does not support one. Silence is a valid output.
2. Never assert a condition the player has fewer than 10 games of data for.
3. Compare against the player's own out-of-condition rate, and say so — this is **not** a peer
   comparison, and must not be presented as one until the reference population exists.
4. Attach randomly sampled evidence, never the worst examples.
5. Report `insufficient_data` distinctly from `no problem found`.

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core, filtered to the player |
| corpus | `Corpus` | ingest |
| provenance | engine, depth, analysed_at | analysis core |

## 8 · Outputs

`Finding`s with these claim kinds:

| `claim.kind` | Subject | Condition measured |
|---|---|---|
| `time_pressure_error` | `clock` | error rate when the clock is low vs. otherwise |
| `instant_move_error` | `instant_moves` | error rate on moves played in ≤ 2 s |
| `long_think_error` | `long_think` | error rate on moves after an unusually long think |

All three are **process** gap types by hypothesis, `determined_by = inferred` — a probe could later
confirm whether the player knows they are doing it, which is a V9 job, not S2's.

## 9 · Efficacy measure

1. **Planted-weakness score** — against the `time_pressure` evaluation set already generated and
   verified at 1.81× lift. Both halves count: does it find the planted flaw, and does it invent
   nothing else?
2. **Split-half replication** — every finding it promotes to `focus` must survive the odd/even game
   split. This is a runtime requirement, not just a test.
3. **Determinism** — same observations, same findings, including the evidence sample.
4. **Zero-finding behaviour** — given a clean player, it must return nothing.

## 10 · Cost profile

Zero marginal cost. No engine calls (it reuses the core's output), no model calls, arithmetic over a
few thousand records. Runs in well under a second.

## Known limitations, recorded before building

- The time-pressure threshold is absolute rather than scaled to the time control. A 60-second
  threshold means something different in a 3+0 game than in a 15+10 game.
- No recency streak, so `priority` is reachable only through distinct-game count. Observations do not
  currently carry a date; adding one is small but not yet needed.
- Correlation only. Errors under time pressure may be caused by the pressure, or the pressure and
  the errors may share a cause — playing positions this player finds hard. S2 states the association
  and does not claim the mechanism.
- **Selection confounding, confirmed in M5.** The long-think condition is *selected by* position
  difficulty, which also causes errors, so a within-player baseline cannot separate the two. Four of
  six real players showed it at similar magnitude — the signature of a base rate. Such conditions are
  measured and withheld until a rating-peer baseline exists (L-011).
- The time-pressure condition rarely fires in 600+0 arena games, so S2's headline capability is
  mostly untested on real data. A shorter time control would exercise it.
