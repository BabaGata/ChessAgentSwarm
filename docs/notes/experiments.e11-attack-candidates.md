---
id: cas-exp-e11
title: 'E11 — Screening S8, and a counter-example to L-024'
desc: 'One claim of four survives. A broken pawn shield spreads too, which the prior said it should not.'
updated: 1786406400000
created: 1786406400000
---

# E11 — Screening S8, and a counter-example to L-024

**Answers:** § 9.1 for S8, in advance · **Code:** `experiments/e11-attack-candidates/`
**Date:** 2026-08-05 · **Status:** done — **one candidate of four ships**

## Question

Third outing for the screen, and the first designed around **both** questions:

- **L-023** — does the candidate vary between players at all?
- **L-025** — does it survive dividing out what is already measured? S7 nearly shipped on a candidate
  that spread 1.56 and turned out to be the error rate under a better name.

With **L-024** as the prior: claims about *what the opponent achieves* have discriminated
(outposts 2.15, rooks on the seventh 1.82) where claims about *what the position contains* have not
(holes 1.25, bad bishop 1.27). So a king-shape candidate is carried alongside the attack candidate as
the control.

## Result

| candidate | median | spread | opportunities |
|---|---|---|---|
| `errs_under_pressure` | 0.1307 | 1.73 | **97** — too thin |
| `shield_broken` | 0.1682 | **1.62** | 528 |
| **`allows_king_pressure`** | 0.0191 | **1.59** | 526 |
| `errs_safe` | 0.1126 | 1.53 | 442 |
| `pressure_penalty` — the contrast | 1.23 | 1.46 | — |

`corr(errs_under_pressure, errs_safe) = +0.571` · `corr(allows_king_pressure, shield_broken) = +0.210`

## What ships, and what does not

**`allows_king_pressure` ships.** At 1.59 it sits just under `long_think_error` (1.60), which does
produce findings — so it is viable and marginal, and the section note says so rather than rounding up.

**The error-rate contrast does not.** `pressure_penalty` spreads 1.46 with a median of 1.23: players
err about a quarter more often when their king is already under pressure, and they differ little in
how much. The correlation of +0.571 between the two rates is lower than S7's +0.737, so this is a
weaker version of the same finding rather than the same finding — but not weak enough to build on.

**`errs_under_pressure` alone is too thin.** A median of 97 opportunities per player would put it at
the mercy of the distinct-game floor before the peer comparison ever spoke.

## The counter-example, which is the part worth keeping

**`shield_broken` spreads 1.62 — slightly more than the event claim beside it — and L-024 says it
should not.** It is squarely a property of the player's own position: the castled king has lost its
pawn cover. Holes did not discriminate. Bad bishops did not. A bare king does.

So the prior is **useful and not a law**, and it is recorded here as a counter-example rather than
explained away. One plausible reading, offered as a hypothesis and not a finding: a hole is one square
among sixty-four, and a broken shield is a property of *the one square that decides games*, so
calling both "position properties" may be the error. If that is right, the rule is less about
opponent-versus-position and more about **whether the property is close to the result**.

It is **not built**, for three reasons that have nothing to do with the prior:

1. **Ambiguous causation.** The detector reads a state and cannot tell *I advanced those pawns* from
   *they were traded off*. Only the second is a concession; the first might be style.
2. **No established cost**, exactly as in S5 — and at +0.210 it does not even predict the attack
   actually arriving.
3. **The event version is unscreened.** "My move broke my own shield" is the honest candidate and has
   not been measured. Guessing it behaves like the state version is what screening exists to avoid.

Recorded as a live candidate for a later cycle.

## Honest limitations

- **Attacker count is crude** — pieces, not weight. A queen and a rook count the same as two knights.
- **1.59 is the weakest spread this project has shipped.** S8 may produce very few findings.
- **Three of the catalogue's five S8 topics are untouched**: attacking, sacrifice soundness, pawn
  storms. The first two need material tracking the observations do not carry.
- **`pressure_penalty` is measured on 32 of 38 players**, since six never spent 40 diagnosable moves
  with their king under pressure.
