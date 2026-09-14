---
id: cas-exp-e06
title: 'E06 — Does the progress check have any power?'
desc: 'The other half of E05. The target is reachable and improvers meet it 3x more often — but p = 0.12, so it is suggestive, not established.'
updated: 1785542400000
created: 1785542400000
---

# E06 — Does the progress check have any power?

**Answers:** [[open-questions]] **D8** · **Code:** `experiments/e06-progress-power/power.py`
**Date:** 2026-08-03 · **Status:** done — **suggestive, underpowered, not established**

## Question

E05 measured the **false-positive** rate: 15–23 % of untreated players meet their target by drift
alone. That is only half a test. A target that is well calibrated against drift but **unreachable by
real improvement** would look exactly like the current state, every "not met" would be uninformative,
and V7 would be machinery producing a constant answer.

## Method, and why the proxy is the honest one available

No coached cohort exists and none can be bought under C1. The nearest free proxy is **players whose
rating climbed across the split** — not coached, but demonstrably improving at something.

Rating change is the mean rating in the later period minus the earlier one, from the Elo in the PGN
headers, over the same date split E05 used. Players are cut at the top third.

**No re-analysis was needed.** `results.json` stores each prediction's `before`, `after` and
`expected`, and none of those depend on the target rule, so verdicts are arithmetic. They are
**recomputed at the current constant** rather than read from `status` — the stored verdicts were
decided at `NO_CHANGE_RATIO = 0.34`, which is no longer the rule, and reading them would have
answered a question about a constant the system does not use. That distinction changed the headline
from 0 % to 25 %.

### The confound, stated before the result

Rating and error rate **both regress**. A player whose earlier half was a bad patch has a depressed
rating *and* an inflated error rate, and both recover together with nobody improving. So the two
outcomes were not symmetric, and this was written down before looking:

- **improvers meet no more often than the rest** → strong evidence of no power; regression works
  *for* the alternative, so a null survives it.
- **improvers meet more often** → weak evidence, because regression predicts exactly that.

## Result

| | n players | mean rating change | met |
|---|---|---|---|
| **improvers** (top third) | 12 | **+141.3** | **4/16 (25 %)** |
| the rest | 26 | −16.2 | 3/36 (8 %) |

Fisher exact, one-sided: **p = 0.120**.

| Correlation (per prediction, n = 52) | r |
|---|---|
| rating change vs rate improvement | **+0.207** |
| rating change vs **early extremity** — *the confound's fingerprint* | **+0.059** |

## Reading it

**The target is reachable.** This is the result that mattered most and it is unambiguous: 4 of 16
improver predictions met their target. The catastrophic possibility — a target nothing can reach,
which would have made the whole V7 apparatus a constant "no" — **is ruled out**.

**The separation is threefold and in the right direction**, 25 % against 8 %.

**The confound is measurably absent.** If rating gain were regression wearing a disguise, gainers
would be the players whose earlier rate was most inflated relative to its own no-change estimate.
That correlation is **+0.059** — essentially nothing. Meanwhile rating gain does track rate
improvement at +0.207. So the pre-registered "weak evidence" reading is upgraded: the mechanism that
would have explained the separation away is not present.

**But it is not established.** p = 0.120 on 7 met events across 52 predictions. Neither the
contingency table nor the correlation clears conventional significance, and R-13 is explicit that a
convincing direction with a tidy mechanism is precisely how this project has fooled itself before
(E03's backward-pawn effect reversed on held-out players).

**So D8's answer is: probably yes, not demonstrably.** The progress check is not a dead test, and it
plausibly has real power — but saying "the swarm's targets detect improvement" is not yet supportable
and must not appear in the thesis as though it were.

## What this changes

- **The prober is worth building.** Its primary efficacy measure
  ([[capacity.agents.prober]] § 9) is *does probing improve the progress check's power*, which is
  only a meaningful question if the check has some. It does.
- **That measure will be underpowered too**, and that is now known in advance rather than discovered
  after building. Splitting 52 predictions by `gap_type` leaves cells too small to test. The prober's
  assessment needs either more players or a within-finding design.
- **D8 is downgraded, not closed.** Resolving it properly needs a treated cohort, which is outside
  C1, or considerably more data.

## Honest limitations

- **Rating gain is a weak proxy for coaching.** It captures improvement from any source, including
  playing more, playing weaker opponents, or time-control drift. It is not the treatment the thesis
  ultimately wants to claim about.
- **7 met events.** Everything above rests on them.
- **Rating change is measured over the same split as the finding**, so the earlier period contributes
  to both. A cleaner design would take rating from *before* the measurement window entirely.
- **The top-third cut is arbitrary.** The correlation is reported precisely because it does not
  depend on where the line falls; both point the same way.
- **Improvers had more findings per player** (16 predictions from 12 players vs 36 from 26), which is
  itself worth noticing — more active players generate more data and clear the confidence gate more
  often.

## Addendum 2026-09-14 — the 92 % cohort itself, re-fetched

The author asked whether the 92 % could be real improvement. E06 above answers
it for the deep 84-player rerun, not for the 32 players the 92 % was measured
on, and their histories were gone. They were re-fetched by name
(`e05-natural-drift/refetch_controls.py`): until 2026-08-01, 60 games, rapid and
classical as `e01 fetch_games.py` did. 19 histories match E05's game count
exactly, 12 differ by the 1–8 games E05 dropped during analysis, one account no
longer exists.

The 92 % results predate the `expected` field, so `power.py` cannot re-decide
them; `rating_vs_92.py` uses the stored verdict instead, which is the one that
produced 92 %.

| | predictions met | mean rating change |
|---|---|---|
| rating fell (7 players) | **7/7** | −41.8 |
| rating rose (5 players) | 4/5 | +32.2 |
| whole cohort (31 with history) | — | **−2.0**, median +0.8 |

**The cohort did not improve over the window, and the players who got worse met
every target.** Improvement cannot be what met them. Small n, unambiguous
direction.

Two fetch lessons, both cost an attempt each:
- **curl showed Lichess's 429 as a 404 HTML page**; urllib reported the real
  code. The endpoint was rate-limited, not blocked.
- **Without `until` the API returns the newest games**, which is a later period
  than the experiment measured; **rapid alone** dropped one player from 60
  games to 18. Replicating a fetch means replicating its query.
