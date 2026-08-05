---
id: cas-agent-s4
title: 'Agent S4 — Opening repertoire outcomes'
desc: 'The fourth section: not opening theory, opening results. Subdivided by colour rather than by opening, because that is where the denominators are.'
updated: 1786147200000
created: 1786147200000
---

# Agent S4 — Opening repertoire outcomes

**Section:** [[domain.sections]] → S4 · **Status:** **built and assessed**
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **Built.** `chesscoach/sections/s4_opening_outcomes.py`, 23 tests. Registration one line again.
>
> | | before S4 | after S4 |
> |---|---|---|
> | players advised (of 38) | 12 | **16** |
> | silent | 26 | **22** |
> | distinct claim kinds | 8 | **11** |
> | mean pairwise overlap | 0.14 | **0.09** |
>
> **The subdivision fired, which is the result that matters.** `early_error.black` was advised to 4
> players and `.white` to 3 — where S3's five material classes fired for **nobody**. Choosing the
> split by denominator (colour: two buckets, half the data each) rather than by chess taxonomy
> (opening name: a dozen buckets, two games each) is L-022 applied at design time instead of
> discovered afterwards. This is the section that tested that lesson, and it held.
>
> **The § 8 redundancy risk materialised and is fixed.** Two of sixteen advised players were told
> both *"you go wrong early"* and *"you go wrong early as White"*. `drop_redundant_aggregates()` in
> `sections/base.py` keeps the specific claim, because it names the same problem and says where to
> look. Distinct claim kinds went **up** as a result (10 → 11): suppressing the pooled claim let
> other findings through the arbiter. E08 gained a **D6** metric so the next section with this shape
> is checked automatically rather than by eye.

## Why this agent, now

Next in the M4 order, and the section that can settle a contested claim *per player*:
[[domain.chess-concepts]] § E records the widely repeated "openings don't matter below 1800", asserted
on both sides and evidenced on neither. S4 does not take a position — it measures whether **this**
player is losing anything before move 15 and reports what it finds.

Coverage is also still the binding constraint: [[experiments.e08-anti-patterns]] leaves **26 of 38
players told nothing**, and S3 moved that by three.

## The subdivision question, decided first

L-022 is the lesson this section is most exposed to. The catalogue asks for *"which openings cost
them"* — and **opening name is exactly the subdivision the data cannot carry**. A player with 24
games spread over a dozen ECO codes has two games per bucket; every per-opening claim would fire for
nobody, which is what S3's five material classes did.

So S4 subdivides by **colour**, not by opening:

| claim | denominator | why it survives |
|---|---|---|
| `early_error.any` | the player's diagnosable moves before move 15 | ~250 per 24-game corpus |
| `early_error.white` / `.black` | the same, split by side | ~125 each — still large |
| `opening_disadvantage.any` | games reaching move 15 | ~24 — small, but it is a per-*game* claim |

Colour is a real repertoire boundary — a player's white and black repertoires are different bodies
of knowledge, and *"your problems are on the black side"* is directly actionable. It is also a
**two**-way split, which is the most the evidence supports.

**Per-opening claims are deferred, with a stated condition rather than a vague one:** they become
viable at roughly 100+ games per player, which the deep histories fetched for E05 already have. Not
built here because the peer reference is 24-game corpora and a claim whose peer rate cannot be
computed is not a claim.

## 1 · Remit

**What the player's openings cost them, measured in their own games.** Errors before move 15, split
by colour, and how often they emerge from the opening already worse.

**Explicitly not its business.** Opening *theory* — what should be played — is not here and may never
be; that is a recommendation problem, not a diagnosis, and it is where an LLM coach produces the most
confident nonsense. S4 says *where* points are going, not what to play instead.

## 2 · Knowledge organisation

Almost none of its own. The opening window is a ply range; colour comes from the game; the
disadvantage threshold is a number.

**Opening names are not used at all, which is a correction to this note's first draft.** It planned
to carry ECO codes into evidence so a report could say *"in your game against X, a Sicilian"*. But
`Observation` does not hold them and neither does `Corpus` — they live on `GameRecord`, which no
section sees. Getting them here means widening a core type for one consumer's cosmetic text, which
§ 7 of this very note forbids. Dropped rather than justified after the fact: the claims are about
*when* and *which colour*, and none of them needs an opening name.

## 3 · Agent type

**Deterministic, statistics over existing observations.** No model, no new engine calls.

## 4 · Knowledge maintenance

The tunable state is `OPENING_END_PLY` and `OPENING_DISADVANTAGE_CP`. Move 15 is the catalogue's own
figure and is conventional rather than derived; it is stated here so that if it is ever tuned, the
tuning is visible. Both are checked against real base rates before the agent ships.

## 5 · Tools

`chesscoach.analysis.observations`, `chesscoach.sections.base.diagnosable`, `chesscoach.confidence`,
`chesscoach.peers`, and the `eco` / `opening` headers already parsed by `chesscoach.ingest.pgn`.

## 6 · General instruction

1. **The opening window starts after the grace plies.** `diagnosable()` already skips the first eight
   because book moves carry little information; S4 does not reach behind that.
2. **Peer-compare or stay silent.** Everybody errs in the opening (R-14).
3. **Never name an opening as the cause.** The evidence may name it; the claim may not.
4. **Zero findings is a valid output**, and a player whose games end before move 15 gets
   `insufficient_data`, not congratulations.

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core — `ply`, `label`, `score_cp_before`, `mover_is_white` |
| corpus, provenance | | ingest / analysis |
| band, time_control, peers | | [[architecture.peer-reference]] |

Opening names are **not** in `Observation`, not in `Corpus`, and are deliberately not added to
either: they are a property of the game, and no claim here needs them (§ 2).

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `early_error` | `any` | error rate before move 15 — the load-bearing claim |
| `early_error` | `white` / `black` | the same, by side of the board |
| `opening_disadvantage` | `any` | share of games already clearly worse at move 15 |

**`gap_type` is `unknown`, `determined_by = inferred`.** An early error cannot distinguish *does not
know this opening* from *knows it and went wrong* — and here the distinction matters more than
usual, because the two remedies (learn a line, versus stop rushing) are opposites. Good probe
material.

**The `any`-versus-colour redundancy is real here**, unlike in S3 where the classes never fired. If a
player errs far more as black, both `any` and `black` can clear the gate and say one thing twice. The
arbiter prefers diversity across kinds and not within one, so **this must be checked on real players**
and, if it happens, the fix is to suppress `any` when a colour fires.

## 9 · Efficacy measure

1. **Does it move E08's coverage number**, and does the advice stay specific (overlap did not rise)?
2. **Does the colour split ever fire?** If `white`/`black` never clear the gate, the subdivision was
   another L-022 mistake and should be dropped rather than kept for tidiness.
3. **Base-rate sanity.** Opening error rates should sit *below* middlegame rates — book moves and
   familiar structures are easier. A section reporting the opening as the most error-prone phase is
   more likely to be wrong than interesting.
4. **Split-half replication and peer comparison**, as the confidence policy requires.

## 10 · Cost profile

Zero marginal cost. No engine calls, no model calls; a ply comparison and a sign test per move.

## Known limitations, recorded before building

- **"Before move 15" is a convention, not a discovery.** The real end of the opening varies by
  opening and by player, and a fixed ply is a crude proxy for it.
- **`opening_disadvantage` has a game-sized denominator**, so it needs a lot of games to clear the
  confidence gate and will be the first thing to go quiet on small corpora.
- **No per-opening claim**, so the section cannot answer *which* opening is the problem — only
  whether the opening phase is. That is the honest limit of 24-game corpora and it is stated in the
  output rather than worked around.
- **Colour is confounded with opponent choice**: as black the player faces what they are given, so a
  black-side finding may be about what opponents play rather than about their repertoire.
- **Errors before move 15 are not necessarily opening errors** — an early tactical oversight is S1's
  business, and the same move can appear in both sections. That is the design (sections answer
  different questions about the same move), but it means S4's claim is *when*, not *why*.
