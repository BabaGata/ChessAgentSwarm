---
id: cas-agent-s3
title: 'Agent S3 — Endgame technique & conversion'
desc: 'The third section: where errors concentrate once the pieces come off, and whether an advantage survives contact.'
updated: 1786060800000
created: 1786060800000
---

# Agent S3 — Endgame technique & conversion

**Section:** [[domain.sections]] → S3 · **Status:** **built and assessed**
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **Built.** `chesscoach/sections/s3_endgame_technique.py`, 28 tests. Registration was a one-line
> change to `default_agents()` — ADR-0006's additivity claim tested a second time and holding.
>
> **Assessed against § 9's first measure, which was coverage:**
>
> | | before S3 | after S3 |
> |---|---|---|
> | players advised (of 38) | 9 | **12** |
> | silent | 29 | **26** |
> | distinct claim kinds | 6 | **8** |
> | mean pairwise overlap | 0.24 | **0.14** |
> | `long_think` share of advice | 56 % (flagged by D2) | 42 % (not flagged) |
>
> **Real but modest.** It moved coverage from 24 % to 32 % of players and diluted the long-think
> dominance that E08 flagged. It did not solve the problem it was chosen for.
>
> **The material classes contributed nothing.** All five fired for zero players; every S3 finding
> came from the pooled `endgame_error.any`. The design predicted that finer classes would fire for
> nobody and chose five coarse ones — **even five is too many**, and the pooled claim is doing all
> the work. The `any`-versus-class redundancy risk in § 8 never materialised, for the same reason.

## Why this agent, now

[[experiments.e08-anti-patterns]] measured the swarm's binding constraint: it is **silent for 29 of
38 real players**, on fourteen findings between them. Not generic (overlap 0.24), not overloaded
(never more than two priorities), fully grounded (13/13) — just quiet. Detected counts equal advised
counts for every claim kind, so the arbiter is not being fussy; almost nothing clears the confidence
gate.

So this section is chosen for **coverage**, and its design is shaped by that: the failure mode to
avoid is adding six more claim kinds that each fire for one player in forty.

S3 is next in the M4 order ([[domain.sections]]) and it is also the right one on its merits — the
endgame is where [[domain.coaching]]'s sources and Capablanca agree the band's points actually leak,
and it is diagnosable from data already in every `Observation`.

## 1 · Remit

**Where the player's errors concentrate once material comes off, and whether an advantage survives.**

- **by material type** — are rook endgames the problem, or pawn endgames, or all of them?
- **advantage retention** — do they go wrong more often than peers when they are clearly better?

**Explicitly not its business.** *Which tactic* they missed in the endgame is S1's. *Whether the
clock caused it* is S2's. S3 owns **where** and **under what advantage**, not what pattern and not
why.

## 2 · Knowledge organisation

Material class is computed from the position, not looked up — a coarse partition by which non-pawn
piece types remain:

| class | on the board |
|---|---|
| `pawn` | kings and pawns only |
| `rook` | rooks, no minors, no queens |
| `minor` | bishops and/or knights, no rooks, no queens |
| `rook_minor` | rooks and minors together |
| `queen` | any queen still on |

Deliberately five, and deliberately not split by colour, count, or bishop pair. Finer classes are
more useful to a coach and would fire for nobody: the denominator is the point, and E08 is the
evidence for that.

Prescription maps onto the CC0 endgame theme tags (`rookEndgame`, `pawnEndgame`, `queenEndgame`,
`knightEndgame`, `bishopEndgame`), so the same vocabulary that names the weakness selects the
training material — the property that made S1 the cheapest section to prescribe from.

## 3 · Agent type

**Deterministic, statistics over existing observations.** No model, no new engine calls — a material
class is a property of the FEN, which every `Observation` already carries.

## 4 · Knowledge maintenance

Almost none, which is the advantage of this section over S1. There are no detectors to calibrate and
nothing to over-fire: piece counting is exact. The tunable state is the class boundaries and
`ADVANTAGE_CP`, both of which are stated here and checked against real base rates before the agent
ships.

## 5 · Tools

`chesscoach.analysis.observations`, `chesscoach.sections.base.diagnosable`, `python-chess` for FEN
parsing, `chesscoach.confidence`, `chesscoach.peers`. **No engine calls of its own.**

## 6 · General instruction

1. **Rates are per diagnosable move in that condition**, never per game and never per move overall.
2. **Peer-compare or stay silent.** "You make mistakes in rook endgames" is true of everyone
   (R-14); only deviation from the band is a diagnosis.
3. **Never report a class with too few opportunities** — the confidence policy decides, not the
   agent, but the agent must not manufacture a denominator to get past it.
4. **Zero findings is a valid output**, and `insufficient_data` is distinct from "your endgames are
   fine" — a player whose games rarely reach an endgame must be told that, not congratulated.

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core — `fen_before`, `phase`, `score_cp_before`, `label` |
| corpus, provenance | | ingest / analysis |
| band, time_control, peers | | [[architecture.peer-reference]] |

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `endgame_error` | `any` | error rate across all endgame moves — the high-denominator claim |
| `endgame_error` | material class | error rate in that class of endgame |
| `advantage_error` | `clear` | error rate while clearly better but not yet decided |

**`gap_type` is `unknown`, `determined_by = inferred`**, as for S1 — an endgame error cannot
distinguish *does not know the technique* from *knew it and miscalculated*. That is what a V9 probe
is for, and S3's positions are good probe material precisely because endgame technique is teachable
and checkable.

### Why `any` exists, and the risk it carries

E08's finding is that per-thing denominators are too thin to clear the gate. `endgame_error.any`
pools them, so it is the claim most likely to be able to speak at all.

**The risk is redundancy:** `endgame_error.any` and `endgame_error.rook` can both fire for the same
player, and a report saying "you err in endgames" *and* "you err in rook endgames" has said one thing
twice. The arbiter prefers diversity across kinds, which does not help within a kind. **This must be
checked on real players in the M5 assessment**, and if it happens the fix is to suppress `any` when a
class fires rather than to drop either.

### Conversion — what is measurable, and what the catalogue asked for

[[domain.sections]] gives S3 "conversion of winning positions". **That is not measurable under the
current eligibility rule, and the rule is right.** `diagnosable()` excludes positions beyond
`DECIDED_CP = 500` because win probability compresses at the extremes (L-009): an error at +8 barely
moves it, so errors in won positions are simultaneously cheap to make and nearly invisible to
measure. Overriding it for this section would reintroduce the exact effect that constant exists to
prevent, and would produce a "conversion" rate made mostly of measurement artefact.

So S3 measures **advantage retention** instead: the error rate while the player is clearly better
(`ADVANTAGE_CP = 150` up to `DECIDED_CP`) rather than while winning. It is a narrower claim, it is
honestly named, and it answers the coaching question one step earlier — *do you go wrong when you are
on top?* True conversion needs either an evaluation-trajectory measure that does not depend on
per-move labels, or the result-based version whose confound is the opponent. Recorded as a limitation
rather than solved.

## 9 · Efficacy measure

1. **Does it move E08's coverage number?** The section exists because 29 of 38 players are told
   nothing. If S3 does not reduce that materially, it has failed at the thing it was chosen for,
   whatever its internal statistics look like. This is the measure that decides whether it ships.
2. **Base-rate sanity.** Endgame error rates should order themselves the way a player would expect —
   pawn endgames the most punishing per move, queen endgames the most volatile. A class that comes
   out flat against the others is a sign the partition is wrong.
3. **Split-half replication and peer comparison**, as the confidence policy already requires.
4. **Redundancy check** — how often do `any` and a class fire together (§ 8).

## 10 · Cost profile

Zero marginal cost. No engine calls, no model calls, one FEN parse per diagnosable endgame move.

## What building it found

**Most endgames arrive already decided, so the endgame is largely undiagnosable.** For one real
player, **3 of 24 games** reached an endgame that was still inside `DECIDED_CP`. This is structural
rather than a tuning problem: `diagnosable()`'s window exists because win-probability labels
compress at the extremes (L-009), and the endgame is exactly where games are most often already
past that. **An eligibility rule designed for the middlegame removes most of the endgame.**

That is the real reason S3's endgame half is thin — not the material split, which was merely wasted
on top of it. It is worth an open question of its own rather than a footnote: either endgame errors
need a label that does not depend on win-probability deltas, or the endgame is a phase this project
can describe but not diagnose.

**A gating bug, found only by running it on real players.** The section gate counted *games that
reached a diagnosable endgame*, which suppressed `advantage_error` — a claim that is deliberately
**not** endgame-restricted. One player had 12 distinct games and 130 opportunities of it blocked by
an endgame count of 3. The gate now counts every diagnosable game, as S1's does, and per-claim
specificity is left to `distinct_games` where the confidence policy already enforces it.

**Evidence bunching.** A claim seen in five games cited three examples from the *same* game, which
invites a reader to dismiss a real pattern as one bad day — the mirror image of cherry-picking, and
just as misleading. Sampling now takes one example per game before filling.

## Known limitations, recorded before building

- **`phase` is a coarse count of non-pawn pieces**, so "endgame" here means *material is low*, not
  *the game has the character of an endgame*. A queen-and-rooks position with few minors may be
  classified endgame while playing like a middlegame.
- **True conversion is not measured**, only advantage retention (§ 8).
- **Material class is computed at the position, not at the point of simplification.** The catalogue
  asked for the latter; it is a different and harder question — *which endgame did you choose to go
  into?* — and belongs to a planning section, not this one.
- **Endgame reach varies enormously by player.** An attacking player who wins or loses by move 30
  will produce `insufficient_data` here, and that is the correct output rather than a failure.
- **Peer rates for endgame classes do not exist yet** and must be built into the reference before
  any finding can be asserted — the same dependency S1 had.
