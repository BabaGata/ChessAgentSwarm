---
id: cas-exp-e43
title: 'E43 — One gate is a units bug worth fixing, the other was never the constraint'
desc: 'Swept both focus gates. FOCUS_GAMES_WITH_DATA = 20 blocks 15 claims at a 20-game window and none at 60, and any fraction of the corpus fixes it. FOCUS_MARGIN admits +0 claims at 20 games and does not readmit the failure it guards against even at 1.10 — the agent''s hypothesis about it was wrong.'
updated: 1787961600000
created: 1787961600000
---

# E43 — Sweeping the two gates that keep expensive claims at `watch`

**Answers:** D15 defect (b) · **Code:** `experiments/e43-focus-gates/` · **Date:** 2026-08-20 ·
**Status:** done — **one fix recommended, one refused, and the refusal corrects the agent**

## The two hypotheses going in

[[experiments.e41-cost-ranking]] found seven material claims above the peer rate on every one,
costing 6.3–15.1 wp/game, and still not assertable. Two constants in `chesscoach/confidence.py` were
blamed:

- **`FOCUS_GAMES_WITH_DATA = 20` is a units bug.** `games_with_data` counts the games in which a
  *section* found any diagnosable move, so on a 20-game corpus the ceiling is 20 and ordinary
  attrition lands at 18–19. The gate demands 20 — on a 20-game read, a demand for a perfect score.
- **`FOCUS_MARGIN = 1.25` is an unvalidated threshold.** Its own comment concedes it was *"chosen to
  match PRIORITY_MARGIN rather than tuned"*, justified only by the fact that it removed none of the
  then-40 findings. A no-harm argument, not a correctness one.

**One survives measurement. The other does not.**

## Result one — the units bug is real, and entirely a small-corpus phenomenon

Claims whose **only** remaining blocker is the games floor:

| rule | at 20 games | at 60 games |
|---|--:|--:|
| **absolute 20 (shipping)** | **15** | **0** |
| fraction 0.90 / 0.80 / 0.70 | 0 | 0 |

The gate is **inert at 60 games and blocks 15 claims at 20**, which is the definition of a threshold
measuring the window rather than the evidence. Every fraction fixes it completely and they are
indistinguishable from each other, so the result does not depend on picking the fraction well.

**Window agreement** — the same claim, 20 games against 60, same verdict?

| rule | agree | of | rate |
|---|--:|--:|--:|
| absolute 20 (shipping) | 55 | 83 | **66 %** |
| any fraction | 62 | 83 | **75 %** |

That decomposes [[experiments.e39-review-window]]'s disagreement: **9 points of it were this gate**,
and the remaining 25 % is genuine sampling. The gate was contaminating the expert review, and fixing
it does not make the review agree — it removes one artefact from it.

What the fix admits at 20 games is not marginal:

| player | claim | lift | cost/game | games |
|---|---|--:|--:|--:|
| cademan | `early_error.black` | 1.38× | 22.3 | 8/18 |
| goydorak | `early_error.white` | 1.34× | 19.4 | 9/19 |
| cademan | `allowed_motif.fork` | 2.73× | 17.5 | 11/18 |
| cademan | `long_think_error` | 1.61× | 15.6 | 12/18 |
| **cademan** | **`allowed_motif.hangingPiece`** | **1.84×** | **15.1** | 9/18 |
| maxhayastan | `allowed_motif.pin` | 2.53× | 13.1 | 11/17 |
| goydorak | `allowed_motif.pin` | 2.92× | 11.6 | 12/19 |
| **bernes** | **`allowed_motif.hangingPiece`** | **2.60×** | **10.5** | 10/19 |

Two of the eight are the reviewer's own top concern, at 1.84× and 2.60× — measured, expensive, and
silenced by arithmetic about the corpus size.

## Result two — the margin was never the binding constraint

Swept at 60 games with the games floor already fixed:

| margin | advised | claims | kinds | material | top-claim share | S5 pooled back? |
|--:|--:|--:|--:|--:|--:|---|
| 1.10 | 10 | 40 | 13 | 8 | 30 % | **no** |
| 1.15 | 10 | 40 | 13 | 8 | 30 % | **no** |
| 1.25 *(shipping)* | 10 | 38 | 13 | 8 | 30 % | **no** |
| 1.30 | 10 | 37 | 12 | 8 | 30 % | no |
| 1.40 | 10 | 32 | 10 | 6 | 40 % | no |

And at the 20-game window, lowering 1.25 → 1.15 admits **+0 claims**.

**The agent's hypothesis was wrong.** Crossfire1983's `hangingPiece` (1.14×) and Hirsican's
`hangingPawn` (1.21×) were named in E41 as margin casualties. They are not: 1.14× fails 1.15 as well,
and both were *also* behind the games floor, so the margin was never what decided them. What refuses
them once the floor is fixed is the interval test — `ci95[0] <= baseline_rate` — which is the correct
reason to stay quiet about a small effect.

**And the guard it exists for does not fire.** S5's **pooled** `concedes_weakness` — the
large-denominator aggregate that deviated 1.24× at the 90th percentile and motivated the constant
(L-023, D12) — does not become assertable at any margin down to **1.10**. The four
`concedes_weakness` claims that are assertable are *subdivisions*, which were never D12's concern; an
earlier version of this experiment counted them and reported a regression that did not exist.

So the margin is **safe to lower and pointless to lower**. It stays at 1.25.

## A finding that was not being looked for

**The two strongest players in the set have nothing assertable at 60 games** — Odin5306 (1981) and
Sheriwoyama (2033), and only they. That is the reviewer's own hypothesis from
[[experiments.e41-cost-ranking]] arriving by a different route than they proposed: not that a strong
player's report falls to the cost pool, but that for the strongest the peer comparison asserts
**nothing at all**, and the entire report is whatever cost can rescue. The rating correlation E41
looked for was absent; this is the effect it was looking for, visible at the extreme rather than
across the range.

## Consequence

- **Recommended:** express the games floor as a fraction of the corpus (**0.80**, the middle of an
  interval where the choice does not matter). It is a units correction, not a loosening: it changes
  **nothing** at 60 games, where the gate already blocks nothing.
- **Refused:** any change to `FOCUS_MARGIN`. Recorded so it is not revisited on the same reasoning.
- **Not applied yet.** The author is mid-review with six of twelve players annotated, and this changes
  the reports being graded. Applying it is their call, not the agent's.
- **Correction to a cost estimate the agent gave the author:** this was described as "genuinely two
  lines: the constant and the comparison". It is not. `ClaimStats` carries `games_with_data` but not
  the corpus size, so a fractional rule needs a new field, populated at seven section call sites,
  plus the comparison. Still small, but not two lines.

## Honest limitations

- **Twelve players**, all from the review set, which is not a random sample of the band.
- **The 60-game arm is not the production path either** — `cli coach` pools speeds and can exceed 60.
  The claim established is that the gate is inert at 60 and biting at 20, not that 60 is the ceiling
  of its effect.
- **`advised` counts a player with any assertable finding**, not the quality of what they were told;
  the sweep does not re-rank or re-plan.
- **The margin arm rests on one guard case.** S5's pooled claim not returning at 1.10 is evidence
  about *that* failure, not proof that no large-denominator section could ever produce another.
