---
id: cas-exp-e33
title: 'E33 — Lowering the error threshold buys detection, not naming, and discrimination survives'
desc: 'From 10 wp to 3 wp, agreement with the reviewer rises 58% to 89% while naming stays flat at 8-9%. Claims still separate players. The blast radius, not the screen, is what should decide it.'
updated: 1788357600000
created: 1787270400000
---

# E33 — What does lowering the error threshold buy, and what does it cost?

> **Corrected 2026-09-02 by [[experiments.e82-move-number-rerun]].** This screen joined the
> reviewer's noted move numbers with `ply // 2 + 1`, one too high for every Black move.
> **The checkable notes go from 106 to 134** — a quarter of the reviewer's notes were not joining at
> all — while the rates barely move (at 3 wp: 89 % → 90 % detected, 42 % → **45 %** named). The
> conclusion holds and is slightly stronger. **The discrimination spreads did move**: at 10 wp,
> `missed_motif` 1.53× → **1.28×** and `allowed_motif` 1.38× → **1.13×**, which is close to the band
> E09 used to reject detectors outright.

**Answers:** the open question left by [[experiments.e32-hanging-pawn-screen]] ·
**Date:** 2026-08-16 · **Status:** done — **favourable on the screen; not applied**

## The question

`INACCURACY_WP = 10.0` decides what counts as a mistake at all, and everything inherits it: no label
means **no motif detector ever runs**, `allowed_motif` denominators are the player's error count, and
S2 sorts errors by the clock.

E32 found 24 of 45 reviewer pawn notes sitting below that line — for `Crossfire1983` the median
noticed mistake cost **8.9 wp**, so most of what a strong club player writes down is invisible by
construction. Lowering the floor is the obvious move, and obvious moves are what this project
screens.

Analysis ran **once** per player; thresholds were applied by relabelling the stored `loss_wp`, which
is exact and free. The `mistake` band was scaled with the floor rather than left at 20, so the tiers
do not overlap strangely at 3.0. `blunder` stays at 30, so V1's strength estimate — which reads
blunder rate — is untouched at every threshold.

## Correction, 2026-08-16 — the first version of this note was wrong

Published claiming **naming is flat at 8–9 %** across every threshold, and concluding that the
threshold was not what held naming back. Both statements came from a **bug in the comparison
harness**, found while diagnosing why naming was stuck.

S1 measures two directions: `missed_motif` from the player's own best move, `allowed_motif` from the
**opponent's best reply**. `compare.py` only ever built the first. Every note of the form *"loosing a
pawn"* — the allowed direction, and most of what the reviewer writes — was scored unnamed **by
construction**. A comment in the code claimed both directions were included; the code never did.

Corrected figures below. Naming is roughly **three times higher** than reported and **rises with the
threshold rather than staying flat**. Everything downstream of the old number is corrected with it:
[[experiments.e31-move-level-agreement]] and [[experiments.e32-hanging-pawn-screen]] both carried it.

## Result

**Volume and cost**, 12 players:

| threshold | moves called an error | mean cost of one |
|--:|--:|--:|
| **10.0** (ships) | 9.0 % | 22.3 wp |
| 7.0 | 13.7 % | 17.6 wp |
| **5.0** | 19.2 % | 14.2 wp |
| 3.0 | 27.8 % | 11.0 wp |

**Agreement** with the reviewer, 106 move-level notes across three annotated players:

| threshold | detected | named |
|--:|--:|--:|
| **10.0** (ships) | 61 (**58 %**) | 30 (**28 %**) |
| 7.0 | 74 (70 %) | 35 (33 %) |
| **5.0** | 83 (**78 %**) | 40 (**38 %**) |
| 3.0 | 94 (**89 %**) | 45 (**42 %**) |

**Discrimination**, p90 ÷ median — the L-024 screen. The expected failure mode was spreads collapsing
toward 1.00× as cheap errors flooded the evidence:

| threshold | missed hangingPawn | allowed hangingPawn | missed fork | allowed hangingPiece | instant move |
|--:|--:|--:|--:|--:|--:|
| 10.0 | 1.53× | 1.38× | 1.40× | 1.56× | **1.91×** |
| 7.0 | 1.25× | 1.53× | 1.55× | 1.39× | 1.74× |
| **5.0** | **1.75×** | **1.59×** | **1.59×** | **1.64×** | 1.59× |
| 3.0 | 1.65× | 1.56× | 1.40× | 1.55× | 1.40× |

## Two findings, and the second is the important one

**1. The veto did not happen.** Discrimination does not collapse. It wobbles without trend, and at
5.0 four of the five watched claims reach their *best* spread of any threshold tested. The one clear
casualty is `instant_move_error`, falling 1.91× → 1.40× as the floor drops — which makes sense, since
a habit defined by speed rather than by severity gains the most noise from admitting small errors.

**2. Naming rises with the threshold: 28 % → 42 %.** E32's hypothesis was right after all, and the
first version of this note wrongly refuted it: 45 of 106 reviewer notes sit below the 10 wp line, no
detector runs on them, and dropping the floor to 3.0 recovers most of that — **15 more notes named,
a 50 % relative gain**.

Detection and naming are still *distinct*, and the gap between them stays wide at every threshold —
89 % seen against 42 % named at the floor. But they are not independent: roughly **a third of every
detection gained turns into a naming gained**, because a labelled move is a move the motif detectors
are finally allowed to look at.

Naming is therefore limited by two things at once, and the threshold is the larger of them. What
remains after it is the vocabulary itself, quantified in the diagnosis below.

## What actually limits naming — the four levers, sized

Every unnamed note at the shipping threshold, classified. 106 move-level notes, three players.

| | | share | what would fix it |
|---|--:|--:|---|
| **named correctly** | 30 | 28 % | — |
| **below the label threshold** | 45 | **42 %** | lower `INACCURACY_WP`; measured above, 28 % → 42 % naming |
| **error, but no motif covers it** | 16 | 15 % | more or broader motifs |
| **a motif fired, a different one** | 15 | 14 % | ~~a claim measured in *material*~~ — **refused**, below |

Supporting figure: of **225 labelled errors** across these players, only **122 (54 %) carry any motif
at all**. Nearly half of what the swarm already calls a mistake is tactically anonymous to it, before
the reviewer is consulted at all.

**The material-outcome claim is refused, 2026-08-16.** The 14 % where a motif fired and disagreed are
cases where the reviewer named *what was lost* and the swarm named *what won it* — "loosing a pawn"
against "a pin". The obvious remedy is a claim measured in material delta. The author's ruling:

> "material-outcome claim should not be implemented, mechanism is more informative than the material
> claim"

That is the right call and worth recording as a principle rather than a preference. *"You dropped a
pawn"* names a symptom the player already knows about — they watched it happen — while *"a pin won
it"* names the thing that can be trained. A report full of material outcomes would be a scoreboard;
V8 asks for an explanation. It also protects against the failure this project keeps rediscovering:
a claim ranking by size rather than by mechanism ends up telling everyone the same thing (E17).

The consequence is that this 14 % is **accepted as permanent disagreement**, not treated as a defect.
Reviewer and swarm will keep describing the same move differently, and the reviewer's instruction to
name the material lost stays in Form A precisely so the two can be lined up.

**A structural gap, smaller than it looks.** Motifs are computed on the engine's best move and on the
opponent's best reply — **never on the move the player actually played**. So "placing a piece on the
attacked square", a property of the played move, has nowhere to land. Checked directly: of the 15
different-motif cases, the played move carries what the reviewer described in **1**. Real, worth
fixing for the sentences it would enable, and not a large lever.

## Applied, 2026-08-16 — `INACCURACY_WP = 5.0`

The author's decision after seeing the corrected figures. `MISTAKE_WP` moves to 17.5, the value this
experiment screened, keeping the bands evenly spaced; the boundary is close to cosmetic since every
measurement in the swarm turns on `label is not None`. `BLUNDER_WP` is untouched at 30, so V1's
strength estimate — which reads blunder rate — is unaffected.

**What this invalidates, and what was done about it.**

`NO_CHANGE_RATIO = 0.58` was fitted at a 10 wp floor across 57 predictions
([[experiments.e05-natural-drift]]). Refitting needs the 84-player corpus, which is deliberately not
committed, so it is **outstanding**. Rather than let a stale constant quietly produce a confident
verdict, `labels.NO_CHANGE_RATIO_FITTED_AT_WP` records the floor it was fitted at and
`calibration_is_stale()` compares it with the floor in use. While they disagree the plan **withdraws
the "15–23 % of players reach this without changing anything" figure and says why**:

```
fork missed when available: below 14.6% over the next 20 games
  (measured 30.3%, ~25.2% if nothing changes; the share of players who reach
   this without changing anything has not been recalibrated since the error
   threshold moved, so it is not quoted)
```

The target itself is unchanged and still falsifiable — only the false-positive rate is withdrawn,
because that number was measured against a different definition of "an error". `test_planner`'s
assertion was rewritten to encode the **rule** rather than the moment: refit E05, update the marker,
and it starts checking the quoted range again automatically.

**Peer references must be rebuilt** — rates are no more comparable across thresholds than across
depths (E01) — and every coverage, overlap and cost figure in the vault now describes the old floor
until re-measured.

## Consequence — the screen said yes; the blast radius decided how

The screen is favourable and it is **not** what should decide this. Lowering the floor has a blast
radius the screen does not measure:

- **[[experiments.e05-natural-drift]]'s `NO_CHANGE_RATIO = 0.58` was fitted at threshold 10**, from 57
  predictions cross-validated at 2 and 5 folds. Change what counts as an error and that constant is
  describing a different quantity. The progress check is the one part of this system that can be
  proven wrong, and its calibration is not something to invalidate as a side effect.
- **Every peer reference must be rebuilt.** Rates are not comparable across thresholds any more than
  across depths (E01).
- **Every figure in the vault shifts** — coverage, overlap, groundedness, the anti-pattern family, the
  cost-per-game numbers the arbiter ranks on.
- **"You went wrong on one move in four"** is a different kind of statement to a player than "one in
  eleven", and nothing here says which is more useful to receive.

**If it is changed, 5.0 is the value the evidence points at**: detection 78 %, the best discrimination
of the four thresholds, and a mean error still costing 14.2 wp rather than 11.0. 3.0 buys 11 more
points of detection for a quarter of all moves being errors and the sharpest dilution of cost.

Recorded as a decision for the author rather than taken here, with the refit work stated so it is
priced honestly rather than discovered afterwards.

## Follow-up, 2026-08-17 — is the threshold fixed, and is that fair to stronger players?

Asked by the reviewer:

> "Players in the upper range of the skill level do less mistakes and of the less severity, and they
> lose by doing multiple inaccurate moves but those are not much severe. Is the threshold permanent
> or is it set up dynamically for the players?"

**It is permanent.** `INACCURACY_WP = 5.0`, `MISTAKE_WP = 17.5`, `BLUNDER_WP = 30.0`, identical for
every player. Nothing anywhere adapts them.

**The observation behind the question is correct on all three axes.** Twelve players, sorted by
rating:

| | correlation with rating |
|---|--:|
| error rate | **−0.84** |
| **median** loss of an error | **−0.74** |
| mean loss of an error | **−0.86** |
| share of errors in the smallest band (5–10 wp) | **+0.70** |

`Sheriwoyama` (2033) has 58 % of their errors in the 5–10 wp band and 5 % blunders;
`Maximilian_Honigtopf` (1171) has 46 % and 14 %. Stronger players do not merely err less — their
errors are *smaller*, and the difference is large.

**Which retrospectively justifies this experiment more than its own screen did.** At the old 10 wp
floor that smallest band was **entirely invisible**, and it is 46–58 % of all errors. Lowering the
floor did not affect players evenly: it recovered proportionally more of what a strong player does
wrong, because that is where a strong player's mistakes live.

**A per-player threshold is still refused, for two reasons that are not about effort.**

1. **It would break the peer comparison, which is the whole mechanism.** Every claim in this project
   is a rate compared against a population rate. If each player's rate were computed against a
   different definition of "error", those rates would not be comparable — the same objection E01
   raises about comparing across engine depths, and the same one `build-peer-reference` enforces by
   refusing to mix strata.
2. **It would be circular.** V1 estimates a player's rating *from their blunder rate*
   ([[experiments.e13-strength-signal]]). A rating-dependent threshold would make the estimate an
   input to its own input.

**The right answer to the observation is a claim, not a moving threshold.** "Your mistakes are many
and small" against "few and catastrophic" is a real, measurable difference between players that the
swarm currently cannot say — it reports rates and costs, never the *shape* of a player's error
distribution. That is a candidate for a future screen rather than a change to the constants, and it
would have to clear the same bar everything else does: does it distinguish players once general
error-proneness is divided out? Given median loss correlates −0.74 with rating and error rate −0.84,
the honest prior is that it mostly would not.

## Honest limitations

- **Agreement is measured on three players' notes** and rests on the phrase table written after
  reading them (E31's stated weakest link).
- **The `mistake` band was rescaled** rather than held fixed; a different choice there would move the
  middle tier's counts, though not the error/non-error split these figures turn on.
- **Discrimination is measured on 12 players**, so a 1.25× against a 1.59× is not a reliable ordering
  — only the absence of a collapse is.
- **Nothing here measures whether a lower floor makes the advice better**, only whether the swarm
  sees more and can still tell players apart.
