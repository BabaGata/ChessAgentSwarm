---
id: cas-arch-confidence
title: Confidence Policy
desc: 'When the swarm is allowed to assert a weakness — the minimum-sample and promotion rules.'
updated: 1785256300000
created: 1785256300000
---

# Confidence Policy

Resolves **C2** in [[open-questions]]. E01 promoted this from good practice to a **correctness
requirement**: per-move labels shift with analysis depth, so only aggregate claims survive their own
parameters (L-006). E03 then demonstrated the failure it prevents, on this project's own data
(L-008).

## Tiers

A finding sits in exactly one tier. Only `focus` and `priority` may be shown to the player as a
weakness; `watch` is internal.

| Tier | Meaning | Shown to player |
|---|---|---|
| `none` | measured, unremarkable | no |
| `watch` | possible pattern, insufficient evidence | no — internal only |
| `focus` | established pattern worth working on | yes |
| `priority` | established, costly, and current | yes, and eligible for the 1–2 slots |

## Promotion rules

All conditions must hold. Counts are of **distinct games**, never instances — a player who hung a
piece three times in one disastrous game does not have a pattern, they had a bad day.

| To reach | Requires |
|---|---|
| `watch` | ≥ 3 distinct games · ≥ 10 games with data for that section |
| `focus` | ≥ 5 distinct games · ≥ 20 games with data · rate CI excludes the peer rate · **rate clears it by 1.25×** · **replicated** on a held-out split |
| `priority` | `focus` conditions · ≥ 8 distinct games · **and the interval clears the comparison rate by 1.25×**, not merely touching it |

**Why `focus` needs a margin too** (added 2026-08-05, question D12). It originally required only that
the interval *exclude* the peer rate — a test of **significance** with no floor on **magnitude**.
That is equivalent to "worth telling someone" only at the sample size it was calibrated for: with
~100 opportunities per player, an effect becomes significant at about the point it becomes worth
mentioning. **S5 arrived carrying 526**, and the two came apart — its pooled claim deviates by 1.24×
at the 90th percentile, statistically solid and not worth saying (L-023).

The two margins use the same number and different statistics, which is what keeps the tiers ordered:
`focus` applies it to the **point estimate**, `priority` to the **interval's lower bound**. So
`focus` means *big enough and reliably real*; `priority` means *big enough even at the pessimistic
end*.

**The floor was measured, not chosen.** Every one of the 40 findings the swarm asserts across 38 real
players was checked: the smallest ratio is **1.40**, so 1.25 removes none of them, and re-measuring
end to end confirmed it — 19 players advised, 13 claim kinds, overlap 0.08, all unchanged. It exists
to stop the *next* large-denominator section rather than to prune the present ones.

**Why `priority` needs a margin.** It originally required only the distinct-game count, which meant a
claim whose interval grazed the population rate printed at the strongest tier. Measurement settled
it: a 0.4 percentage point change in the reference population flipped one such claim from `priority`
to nothing at all (L-013). Sample breadth and strength of evidence are different properties, and the
top tier should reflect the second. Note the consequence — because the test uses the interval's
lower bound, a player with a larger point lift can rank *below* one with a smaller but better-evidenced
one. That is intended.

**Gate:** below 10 games with data for a section, that section reports `insufficient_data` and emits
nothing. A new account produces no findings, which is correct — the alternative is a system that
invents weaknesses for anyone who shows up.

## The replication requirement

For `focus` and above, the finding must reproduce on a **held-out split of the player's own games**
(odd-numbered vs even-numbered). Measure the rate in both halves; the halves must agree in direction
and their intervals must overlap.

This is [[evaluation]]'s B1 doing double duty as a runtime rule, and it exists because of a
concrete, recorded failure: E03 found an effect with lift 2.40, a plausible mechanism and a tidy
explanation, which reversed to 0.76 on held-out players. **A plausible mechanism is not evidence;
it is what makes an artefact convincing** (L-008).

## Peer comparison

Rates are compared against a **rating-band reference population** built once from the free Lichess
open database, not against an absolute threshold. Reasons:

- E02 showed base rates are enormous — isolated pawns in 96 % of games. Absolute thresholds would
  flag everyone (R-14).
- E03 showed error-association is a weak relevance signal, which leaves *deviation from peers* as
  the most promising remaining route for C6.
- "You do this more than players at your level" is a claim a player can act on; "you do this" is not.

The same reference corpus serves as evaluation metric D2 — one artefact, two uses.

## Statistical care

- **Wilson score intervals** on every rate; they behave at small n, unlike the normal approximation.
- **Segment before comparing** — time control always, phase where E03 showed it matters. Never
  compare across time controls.
- **Rating-adjust** where opponent strength is a plausible confound.
- **Multiple comparisons are real.** A section testing many claim kinds will find something. The
  replication rule is the control; where a section screens many hypotheses, it must say so and the
  threshold tightens.

## Thresholds are provisional

Every number above is a **starting point, not a result**. They are taken from the shape of prior
art's escalation design ([[domain.prior-art]]) and must be validated against our own data before the
first agent ships — specifically by checking that split-half agreement is actually achieved at these
values, and adjusting if it is not.

Recorded as a task in [[state]] rather than left as an assumption, because thresholds that were
never tested are exactly the kind of thing that quietly becomes load-bearing.

## What the player is told

Confidence is not hidden behind a number. The explainer states the evidence in plain terms —
*"in 9 of your last 47 rapid games"* — because a coach who says "you sometimes miss forks" is not
saying anything, and a coach who says "you miss forks 19 % of the time (CI 11–31 %)" is not talking
to a person.
