---
id: cas-agent-s5
title: 'Agent S5 — Pawn-structure weaknesses'
desc: 'The first Tier 2 section: what the player concedes, not what they have. Its central claim is deliberately weaker than it looks.'
updated: 1786233600000
created: 1786233600000
---

# Agent S5 — Pawn-structure weaknesses

**Section:** [[domain.sections]] → S5 · **Status:** **built and assessed — partly suppressed**
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **§ 9.1 ran first, and it changed what shipped.** The question was whether the deviation exists at
> all. Across the 38-player reference, p90/median spread:
>
> | claim | spread | | for comparison | spread |
> |---|---|---|---|---|
> | `concedes_weakness.doubled` | **1.20** | | `long_think_error` | 1.60 |
> | `concedes_weakness.any` | **1.24** | | `endgame_error.any` | 1.70 |
> | `concedes_weakness.isolated` | 1.40 | | `early_error.any` | 1.70 |
> | `concedes_weakness.backward` | **1.85** | | `early_error.black` | 1.92 |
>
> **Players concede structure at very nearly the same rate.** Only `backward` varies like the claims
> known to discriminate. So the section ships with a `MIN_PEER_RATIO` guard, and on real players
> `backward` fired 5 times and `isolated` twice — while **`doubled` and the pooled `any` fired for
> nobody**, exactly as their spread predicted. The design's own kill-switch worked, and it worked
> selectively rather than as a yes/no.
>
> **Coverage:** players advised 16 → **19**, silent 22 → **19**, claim kinds 11 → **13**, overlap
> 0.09 → **0.08**.
>
> **This is where L-022 met its opposite.** L-022 says small denominators cause silence. S5's
> denominators are **526 per player** — five times any other claim — and the failure mode inverts:
> the confidence policy's FOCUS tier is a *significance* test with no floor on *magnitude*, so a
> 1.2× deviation would have cleared it comfortably and been reported as a finding. Registered as
> **D12**, because the fix belongs to the policy rather than to this section.

## Why this agent, now, and the two results that constrain it

First Tier 2 section. Two prior measurements shape it more than the catalogue entry does, and both are
negative:

- **[[experiments.e02-positional-detectors]] / L-007** — the detectors work (16/16 hand-verified) and
  detection is not a coaching signal. Isolated pawns appear in **74.7 % of positions and 96 % of
  games**. *Presence carries almost no diagnostic information.*
- **[[experiments.e03-relevance-weighting]]** — weighting a feature by its association with the
  player's own errors **does not work**. Pooled lifts 0.87–1.26; the one striking phase-stratified
  effect reversed sign on held-out players. Game phase predicts errors better than the entire
  positional vocabulary.

[[domain.sections]]'s own re-scope note draws the conclusion: Tier 2 sections must justify themselves
on **peer-deviation** grounds — *"you concede this more than your rating peers"* — and not on
error-prediction grounds, because error prediction was tested and failed.

## 1 · Remit

**What the player's own play produces in their own camp.** Not which structures they *have* — that
is 96 % of games — but which weaknesses their moves **create**.

Presence is a property of the position, most of it inherited from the opening and the opponent.
Creation is a property of the player, which is the only thing worth coaching. This distinction is the
entire reason the section is buildable at all after E02.

**Explicitly not its business.** Whether a structure is *good* — an isolated queen's pawn is a
weakness and a dynamic asset depending on everything else — and what to do about it. S5 counts what
the player's moves leave behind.

## 2 · Knowledge organisation

Three detectors, ported from E02's experiment code rather than rewritten, since they are already
hand-verified and their definitions are stated and reviewable:

| feature | definition |
|---|---|
| `isolated` | a pawn with no friendly pawn on either adjacent file |
| `backward` | behind its neighbours, undefendable by pawn, and its advance square is covered by an enemy pawn |
| `doubled` | two or more friendly pawns on one file — **new**, and trivially exact |

`doubled` is added because it is the most *self-inflicted* of the three: it usually arrives by a
recapture the player chose. The E02 outpost and rook-file detectors are **not** ported — they are
assets rather than weaknesses, and this section is about what goes wrong.

## 3 · Agent type

**Deterministic detectors plus statistics.** No model, and **no engine calls of its own** — the
position after the player's move is already the `fen_before` of the next observation, the same
property that makes S1 free.

## 4 · Knowledge maintenance

The detectors are the tunable state and the risk, exactly as in S1. `isolated` and `backward` arrive
hand-verified from E02. **`doubled` is new and ships with unit tests only**, which is weaker; it is
also the least ambiguous of the three, so the trade is stated rather than hidden.

## 5 · Tools

`chesscoach.structure` (the ported detectors), `chesscoach.analysis.observations`,
`chesscoach.sections.base`, `chesscoach.confidence`, `chesscoach.peers`.

## 6 · General instruction

1. **Count creation, never presence.** A weakness absent before the player's move and present after
   it, in the player's own camp.
2. **Peer-compare or stay silent.** Everybody has isolated pawns (R-14).
3. **Own camp only.** A weakness in the opponent's position is not this player's problem, and
   attributing the opponent's structure to this player's play is not defensible.
4. **Zero findings is a valid output.**

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core — `fen_before`, `mover_is_white`, `ply` |
| corpus, provenance, band, time_control, peers | | as every section |

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `concedes_weakness` | `any` | the pooled claim — how often the player's moves create a structural weakness |
| `concedes_weakness` | `isolated` / `backward` / `doubled` | the same, per feature |

Aggregate-first per L-022, and `drop_redundant_aggregates()` already handles the pooled/specific
overlap that S4 found on real players.

**`gap_type` is `unknown`, `determined_by = inferred`.**

## 9 · Efficacy measure

1. **Does the deviation exist at all?** Before anything else: if every player concedes at the same
   rate, there is no diagnosis here and the section should not ship. The peer reference answers this
   directly and cheaply, and it is the first thing to look at.
2. **Does it move E08's coverage**, without raising overlap?
3. **Does the per-feature split fire**, or is this S3's material classes again?
4. **Base-rate sanity** — `doubled` should be the commonest concession, `backward` the rarest.

## 10 · Cost profile

Zero marginal cost. Three pure board functions per diagnosable move, no engine, no model.

## The limitation that matters most, stated before building

**S5 can say a player is unusual. It cannot say it costs them anything.**

That is not a hedge, it is E03's result. Peer deviation establishes that a player concedes more
isolated pawns than their rating peers; it establishes nothing about whether fixing that would win
them a single game, because the one experiment that looked for a link between structural features and
this band's errors **found none**.

Every other section's claim carries an implicit "and this is costing you" that survives scrutiny —
S1's missed tactics are missed *points*, S2's clock errors are *errors*, S3 and S4 measure *mistakes*
in a condition. **S5's claim is the only one whose subject is not itself a mistake.** Creating an
isolated pawn is not an error; it is a choice that the literature says is often bad and that this
project's own data has not shown to be.

Consequences, applied rather than noted:

- The **report must not imply cost**. Phrasing says what was measured — *"you end up with these more
  often than players at your level"* — and not *"this is losing you games"*.
- This is the section where **V9 probes matter most**, because asking *"why did you allow this?"*
  distinguishes a deliberate structural choice from an unnoticed concession, and no amount of
  position data will.
- If the deviation turns out not to exist (§ 9.1), **the honest outcome is not to ship it**, and that
  possibility is real enough to be worth stating in advance.

## Known limitations, recorded before building

- **Creation is attributed to the mover**, but a pawn structure changes for reasons the mover did not
  choose — a forced recapture is still counted as a concession.
- **No judgement of whether the structure was worth it.** A player who concedes doubled pawns for the
  bishop pair is doing something respectable and will be counted identically to one who does it by
  accident.
- **Three features is not a pawn-structure vocabulary.** Passed pawns, hanging pawns, pawn islands
  and majorities are all absent; the catalogue asks for more than this section measures.
- **`doubled` is unverified against real games**, unlike the two ported detectors.
