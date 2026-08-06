---
id: cas-exp-e14
title: 'E14 — Four of six style dimensions were strength in disguise'
desc: 'V3 screened with two bars. One tendency survives; the half that says whether it suits the player does not.'
updated: 1786665600000
created: 1786665600000
---

# E14 — Four of six style dimensions were strength in disguise

**Answers:** V3 · **Code:** `experiments/e14-style-dimensions/`
**Date:** 2026-08-06 · **Status:** done — **built, and half of it refused**

## Question

V3 was the last vision capability at zero. [[domain.coaching]] § 6 is unusually directive about how
to approach it — **measured tendencies plus measured performance, not a personality label** — and
tells the reader to treat the whole idea with suspicion.

That suspicion turns into a second screening bar. A candidate style dimension must:

1. **vary between players** (L-023), or there is no dimension; and
2. **be uncorrelated with rating** (L-025), or it is not style, it is **strength wearing a friendlier
   name** — and the swarm already measures strength to ±103 points (E13).

## Result

84 players, ratings 789–2129, depth 15.

| dimension | spread | corr with rating | verdict |
|---|---|---|---|
| **`queenless_share`** | **1.40** | **−0.069** | **style** |
| **`seconds_per_move`** | **1.74** | +0.226 | **style** |
| `check_share` | 1.32 | −0.536 | strength, not style |
| `game_length` | 1.17 | +0.541 | strength, not style |
| `capture_share` | 1.10 | −0.563 | strength, not style |
| `material_at_20` | 1.15 | +0.473 | strength, not style |

**Every "aggression" measure is a strength marker.** Weaker players capture more, check more, and
play shorter games. A style profiler with only the first bar would have told a 1200 *"you are an
aggressive attacking player"* while measuring *"you are weaker"* — which is exactly the personality
label § 6 warns against, arrived at by arithmetic rather than by vibes.

## The performance half does not survive

§ 6 asks for tendency **and** performance: where does the player actually score better? That is the
useful claim — *"you steer into these positions and they do not suit you"* is actionable in a way a
bare tendency is not.

    queenless_fit = error rate with queens off / error rate with queens on
    n = 84   median 0.80   p10 0.62   p90 1.01   spread 1.27

**Everyone errs about 20 % less with the queens off, and players barely differ in how much.** A
spread of 1.27 is the range that has failed every previous screen — S7's `quiet_penalty` was 1.27,
S5's suppressed claims 1.20–1.24. So the fit question has no answer in this data.

## What shipped

`chesscoach/style.py` and a `style` field on the profile (schema v8), carrying **one** tendency.

- **Never a Finding.** A tendency is not a weakness, and routing it through the findings machinery
  would put it in front of the arbiter competing for one of the player's two priorities. `S10` is
  registered in the swarm purely so its measurement reaches the peer reference, and it returns an
  empty report by construction.
- **The report states the tendency and refuses the verdict**: *"That is a preference, not a strength
  or a weakness. Nothing here says whether it suits you — players differ in what they steer towards
  and barely differ in how much it helps them, so any answer would be invented."*
- **`seconds_per_move` is not built**, despite passing both bars. It is a mean rather than a rate, so
  the peer reference cannot hold it in its present shape, and its performance half is already S2's
  territory (`long_think_error`). Recorded as available rather than dropped.

## Honest limitations

- **One dimension is not a style profile.** § 6 lists early queen trades, castling side, sacrifice
  rate, pawn storms, sharpness and structure; this measures one of them.
- **Queenless share is a proxy for a preference, not the preference itself.** A player may reach
  queenless positions because opponents trade into them, not because they steer there.
- **The two bars are thresholds, not tests.** 1.35 spread and 0.35 correlation are conventions chosen
  to sit between the ranges this project has already measured as working and not working.
- **The fit result may be a measurement artefact.** Error rates fall with queens off partly because
  simpler positions are easier to evaluate, which compresses win-probability loss (L-009). A
  result-based fit measure might separate players where an error-based one cannot.
