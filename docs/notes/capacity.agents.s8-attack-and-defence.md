---
id: cas-agent-s8
title: 'Agent S8 — Attack & defence'
desc: 'One claim out of four candidates. The screen also produced the first result that contradicts L-024.'
updated: 1788552000000
created: 1786406400000
---

# Agent S8 — Attack & defence

> **Corrected 2026-09-04 by [[experiments.e83-spread-rescreen]].** This note calls 1.59 *"the
> weakest spread this project has shipped"*. That ranking came from a statistic bounded by 1/median,
> which rewards rare claims; on a scale-free screen `allows_pressure.king` reaches **2.44x**, above
> most of the project. **S8 is not the marginal section it describes itself as.**

**Section:** [[domain.sections]] → S8 · **Status:** **built and assessed — marginal, as predicted**
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **Built.** `chesscoach/kingsafety.py` + `chesscoach/sections/s8_attack_and_defence.py`, 24 tests.
>
> | | before S8 | after S8 |
> |---|---|---|
> | players advised (of 38) | 20 | **20 — unchanged** |
> | silent | 18 | **18 — unchanged** |
> | distinct claim kinds | 15 | **16** |
> | mean pairwise overlap | 0.06 | 0.06 |
>
> **It reached nobody new.** `allows_pressure.king` was detected for three players and advised to
> two, and every one of them was already being told something else. The section adds a claim kind and
> some depth to existing profiles; it does not move coverage at all.
>
> That is what a 1.59 spread buys, and § 10 said so before it was built — *"the weakest spread this
> project has shipped… may produce very few findings."* The prediction was right, which is worth more
> than the section is. **Whether S8 earns its place is genuinely open**, and the argument for keeping
> it is that it is cheap, correct, and independent of every other claim; the argument against is that
> it changed no player's outcome.

## What the screen said

E11 ran first, with both questions now (L-023 *does it vary*, L-025 *does it survive dividing out
what we already know*) and L-024 as the prior:

| candidate | spread | |
|---|---|---|
| `errs_under_pressure` | 1.73 | only 97 opportunities per player — too thin |
| `shield_broken` | **1.62** | a **state** claim, and it spreads |
| **`allows_king_pressure`** | **1.59** | ≈ `long_think_error` (1.60), which does produce findings |
| `pressure_penalty` — the contrast | 1.46 | median 1.23 |

**S8 is built on `allows_king_pressure` and nothing else.** One claim.

### The screen contradicted L-024, and that is worth keeping

L-024 held that claims framed as *what the opponent achieves* discriminate and claims framed as
*what the position contains* do not. `shield_broken` is squarely the second kind — the player's own
king has lost its pawn cover — and it spreads **1.62**, slightly *more* than the event claim beside
it. Holes and bad bishops did not; a bare king does.

So the prior is **useful and not a law**, and this note records the counter-example rather than
explaining it away. A plausible reading: a hole is one square among sixty-four and a broken shield is
a property of the one square that decides games, so the two are not the same kind of "position
property" at all. That is a hypothesis, not a finding.

### Why `shield_broken` is screened but not built

Three reasons, in order of weight:

1. **Its causation is ambiguous.** The detector reads a *state* — fewer than two pawns covering the
   castled king — and cannot tell *I advanced them* from *they were traded off*. The first is a
   choice and might be style; only the second is a concession.
2. **Nothing establishes it costs anything**, exactly as in S5. It correlates only **+0.210** with
   `allows_king_pressure`, so it is not even a proxy for the attack actually arriving.
3. **The event version is unscreened.** "My move broke my own shield" is the L-024-shaped form and
   would be the honest candidate; it has not been measured, and guessing it would behave like the
   state version is what the screening discipline exists to avoid.

Recorded as a live candidate for a later cycle rather than dropped.

## 1 · Remit

**How readily the player lets an attack build against their king.** One thing: the opponent bringing
a third piece to bear on the squares around it, having had fewer before.

**Explicitly not its business.** Whether the player *attacks* well — that is a different section and
a much harder measurement, since a good attack and a reckless one look alike until they resolve. Nor
sacrifice soundness, which needs material tracking the observations do not carry.

## 2 · Knowledge organisation

Almost none. The king zone is the king's square and its eight neighbours; an attacker is any enemy
piece bearing on one of them. `PRESSURE_ATTACKERS = 3` is the conventional point at which an attack
stops being an inconvenience, and it is named rather than buried so that tuning it would be visible.

## 3 · Agent type

**Deterministic, no engine calls of its own.** Attack counts are a board property, and the position
after the opponent's reply is already the `fen_before` of the observation two plies on.

## 4 · Knowledge maintenance

One threshold and one zone definition. Neither is hand-verified against real games, which is the
weak part and is stated.

## 5 · Tools

`chesscoach.kingsafety`, `chesscoach.analysis.observations`, `chesscoach.sections.base`,
`chesscoach.confidence`, `chesscoach.peers`.

## 6 · General instruction

1. **Judge across the opponent's reply** — an attack arrives on their move (E09).
2. **Count the crossing, not the state.** Pressure that was already there is not something this move
   allowed.
3. **Peer-compare or stay silent.**
4. **Zero findings is a valid output.**

## 7 · Inputs

Observations, corpus, provenance, band, time control, peers — as every section.

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `allows_pressure` | `king` | the player's move let the opponent mass a third attacker on their king |

**One claim, no subdivision.** At ~10 instances per player there is nothing to subdivide *with*
(L-022), and there is no aggregate to be redundant against (L-024's corollary in S4).

**`gap_type` is `unknown`, `determined_by = inferred`.**

## 9 · Efficacy measure

1. **Already answered:** the deviation exists at 1.59, comparable to `long_think_error`.
2. **Does it move E08's coverage** without raising overlap?
3. **Does it survive being independent?** It correlates +0.210 with `shield_broken` and is measured
   on a different quantity from every other section, so it should not duplicate an existing finding —
   worth confirming on real profiles rather than assuming.
4. **Split-half replication and peer comparison**, as the policy requires.

## 10 · Cost profile

Zero marginal cost. Two attacker scans per diagnosable move.

## Known limitations, recorded before building

- **1.59 is the weakest spread this project has shipped**, just under the 1.60 of `long_think_error`.
  It is a marginal section by construction and may produce very few findings.
- **Attacker count is crude.** A queen and a rook bearing on the king zone are worth more than two
  knights; this counts pieces, not weight.
- **Conceding pressure is not necessarily an error**, and may be a deliberate provocation. Same
  caveat as S5 and S6, same route to resolving it: a probe.
- **The section does not cover attacking**, sacrifices, or pawn storms — three of the five things
  the catalogue lists under S8.
