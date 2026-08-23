---
id: cas-exp-e45
title: 'E45 — The increment correction cuts the band note''s headline by 21 %, and the claim survives it'
desc: 'D16 fixed: seconds_spent now adds the increment back. instant_move_error falls 22.40 to 17.69 wp/game in rapid, still leads the band note. Re-screening caught something bigger — two band claims had been stale since the corpus rebuild and no longer clear E25''s bar.'
updated: 1787961600000
created: 1787961600000
---

# E45 — Fixing the increment, and re-measuring what depended on it

**Answers:** D16, and the author's *"fix D16 and re-measure the band note"* ·
**Code:** `chesscoach/analysis/observations.py`, `experiments/e45-increment-correction/` ·
**Date:** 2026-08-20 · **Status:** done — **fix applied, band note re-measured, and it found a second
staleness nobody was looking for**

## The defect

`Observation.seconds_spent` was `clock_before - clock_after`. `%clk` is written **after** the
increment is credited, so with an increment `i` the reading falls by `spent - i` and the stored value
understated thinking time by exactly `i`. A 3.5 s move on a 180+2 game recorded as **1.5 s** and
tripped `INSTANT_MOVE_SECONDS = 2.0`. Only `chesscoach/evaluation/planted.py` had ever subtracted an
increment; the analysis path never did.

**14.7 % of the peer corpus carries an increment** (596 of 4,050 games), so this was a
population-level error rather than an edge case — and it inflated precisely the most expensive claim
this project has measured.

## The fix

`increment_seconds()` in `chesscoach/ingest/pgn.py` reads the tag; `Observation.increment` carries it;
`seconds_spent` adds it back. Zero for an unreadable tag rather than `None`, because a missing
correction must be the identity rather than a propagating unknown that disables the fix for the games
that need it. Eight tests, including the exact 180+2 case from
[[experiments.e44-clock-on-noted-moves]].

## Result — the correction, with a clean control

Same corpus, same engine, same depth; only the correction differs.

| cell | rate before | after | cost before | after |
|---|--:|--:|--:|--:|
| rapid `instant_move_error` | 18.56 % | **17.40 %** | 22.40 | **17.69** (−21 %) |
| blitz `instant_move_error` | 21.32 % | 21.02 % | 34.33 | **32.16** (−6 %) |
| rapid `long_think_error` | 35.36 % | **35.65 %** | 22.52 | 19.92 |
| blitz `long_think_error` | 38.25 % | **39.07 %** | 21.67 | 20.35 |
| `time_pressure_error` | — | *unmoved* | — | *unmoved* |

**Clock-free cells that moved: 0.** That is the control, and it is the reason the attribution below
can be made at all.

Three things worth reading off it. Rapid moves four times as much as blitz, because two seconds is a
far larger share of a considered move at 10+0 than at 3+0. `long_think_error`'s **rate rises** —
correcting a clock moves things in both directions, and moves formerly too short to qualify now cross
the threshold. `time_pressure_error` does not move at all, correctly: it reads the clock *remaining*,
not the time *spent*.

## The band note survives

| rapid, ranked as `band.py` ranks | before | after |
|---|--:|--:|
| **`instant_move_error`** | 22.40 | **17.69** |
| `early_error.white` | 15.59 | 15.59 |

`instant_move_error` still leads, in both strata and by a wide margin. **The number was wrong; the
claim was not.**

## And the re-screen found something larger

Re-running E25's screen on the full-size reference passes **3 of 32** claims against E25's cutoff of
divided-r < −0.2, where `band.py` carried **five**:

| claim | stored r | re-measured | verdict |
|---|--:|--:|---|
| `instant_move_error` | −0.41 | **−0.40** | stays |
| `missed_motif.hangingPiece` | −0.21 | **−0.31** | stays |
| `early_error.white` | −0.37 | **−0.24** | stays |
| `early_error.black` | −0.46 | **−0.13** | **removed** |
| `allowed_motif.backRankMate` | −0.22 | **−0.12** | **removed** |

**Neither removal is caused by the increment fix.** Neither claim reads the clock, and the control
above shows no clock-free cell moved. They had been stale since the **2026-08-19 full-size corpus
rebuild**, and E25 was never re-run against it — the band note has been naming two claims that its
own screen no longer supports, for a day, unnoticed. `band.py` now carries three, each with its
re-measured number.

## What changed in the reports

All twelve rebuilt. Mostly the band-note block, plus two substantive moves:

- **Sheriwoyama's leading finding changed** — `long_think_error` → `advantage_error`, because the
  population's long-think rate rose slightly and the player is correspondingly less unusual on it.
- **simonvj's recoverable gain on `long_think_error` more than doubled**, 2.0 → **4.6** wp/game, as
  the peer cost fell from 22.5 to 19.9 while their own rate held.

## Honest limitations

- **The band note's own cost figure has never been re-recorded since the corpus rebuild.** E25's note
  still says 16.1 wp/game; the pre-fix figure on the full-size reference was 22.40 and the post-fix
  one is 17.69. The 16.1 was already stale before this experiment touched anything.
- **`INSTANT_MOVE_SECONDS = 2.0` is still inherited, not examined.** The correction changes which
  moves fall either side of an arbitrary line; it does not defend the line.
- **A delay increment is not handled**, only a Fischer increment. No game in either corpus uses one,
  so this is untested rather than wrong.
- **E25's cutoff of −0.2 is unchanged and unexamined.** Two claims sit at −0.13 and −0.12, close
  enough that a slightly different cutoff would keep them; what the re-screen establishes is that they
  no longer clear *the bar the project already set*, not that they are worthless.
