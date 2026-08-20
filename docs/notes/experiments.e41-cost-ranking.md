---
id: cas-exp-e41
title: 'E41 — Cost ranking loses too, and that is what identifies the real cause'
desc: 'The reviewer proposed ranking by severity and count instead of by peer excess. Tested directly it also agrees 0 times in 6 — and two rules that disagree about everything giving the same answer means the ranking rule was never the cause. It is category width.'
updated: 1787961600000
created: 1787961600000
---

# E41 — Would ranking by cost beat ranking by peer-relative excess?

**Answers:** the reviewer's *"the mistakes that are not unusual to still be counted … for stronger
players every their mistake will be disregarded while the severity and the count can still make a
good rank"* · **Code:** `experiments/e41-cost-ranking/` · **Date:** 2026-08-20 ·
**Status:** done — **the proposal is refused, and refusing it located the actual defect**

## The two claims in the question, and what the code says before any measurement

**One: the cost pool was supposed to handle this.** It exists
([[decisions.0010-three-priorities-and-the-cost-pool]]) and it fires. But `arbiter.py` gives it only
the slots the peer comparison leaves empty — `_take_diverse(..., limit - len(chosen))` — and its
docstring is explicit that these *"can never displace an assertable finding."* It is a fallback, not
a ranker.

**Two: the reviewer's account of the gate is right, and blunter than the agent had remembered.**
`confidence.py:101`:

```python
if stats.rate <= stats.baseline_rate:
    return TierDecision(tier=ConfidenceTier.NONE, ...)
```

`baseline_rate` **is** the peer rate. Reaching `focus` additionally needs
`rate >= baseline_rate * FOCUS_MARGIN` (1.25). So being merely *average* at something is silence —
a player must be measurably worse than their band before the system will say anything at all.

## Result one — the pool is not a fallback, it is most of the report

| | |
|---|--:|
| mean slots filled from the cost pool | **2.1 of 3** |
| corr(rating, slots from the pool) | **+0.19** |

**The reviewer's mechanism is real; their rating hypothesis is not supported.** Pool dominance is
near-universal rather than concentrated at the top — the weakest player in the set
(Maximilian_Honigtopf, 1171) and a strong one (bjagus, 1855) both take **0 of 3** from the pool,
while 1340 and 1923 both take 3 of 3. Whatever drives it, it is not playing strength.

The finding that matters is the level, not the trend: **the peer comparison is filling less than one
slot in three.** The system is already mostly cost-ranked, without saying so.

## Result two — the proposal loses, on the reviewer's own notes

Against E40's derived rankings, on the same twenty games:

| ranking rule | top finding in reviewer's three | median overlap |
|---|--:|--:|
| shipping (peer excess, cost pool behind it) | **0 / 6** | 0.5 / 3 |
| **by cost alone (the proposal)** | **0 / 6** | **0.0 / 3** |

And on E17's objection — degeneracy — cost ranking is worse but not catastrophic: it names one claim
to 4 of 12 players against 3 of 12, with 5 distinct leading claims against 8. Nothing like E17's
70 %, because the reference is now full-size.

**So the proposal is refused.** It does not improve agreement, it reduces the spread of what players
are told, and it costs the diagnosis its specificity.

## And the refusal is what identifies the cause

Two ranking rules that disagree about almost every claim produced **the same answer**. A rule that
does not change the outcome is not the thing deciding the outcome. So `where_is_material.py` dumped
the entire candidate list for the six annotated players and asked where `hangingPawn` and
`hangingPiece` actually are:

| | |
|---|--:|
| asserted — ranked and lost | **1** |
| sub-threshold — measured, priced, outranked | **7** |
| **absent — never became a candidate** | **5** |

Three separate defects, none of them the arbiter:

**1. Five of twelve never reach the arbiter at all.** `bjagus` and `maikel5` have neither claim —
for the two players whose reviewer notes are dominated by hanging material. This is
[[experiments.e31-move-level-agreement]] and [[experiments.e32-hanging-pawn-screen]] again: the
notes sit below the label threshold, so no motif ever runs. **No ranking change could ever have
helped these.**

**2. The seven that are measured are above the peer rate on every single one**, costing **6.3–15.1**
points of win probability a game — and are still not assertable. Two gates do it:

- `FOCUS_GAMES_WITH_DATA = 20` against a **20-game window**, which yields 18–19 games with data.
  cademan (7/18) and goydorak (8/19) are blocked by the review window's own size.
- `FOCUS_MARGIN = 1.25` — Crossfire1983's `hangingPiece` is 1.14×, Hirsican's `hangingPawn` 1.21×.
  Above peers, expensive, and not above them *enough*.

**3. In the cost pool they lose to claims that structurally contain them.** `s4_opening_outcomes.py:141`
tallies `early_error` for **every** diagnosable error inside the opening window — including the hung
pieces. A phase bucket is wider than a motif, so it accumulates more cost by construction, and
`advantage_error` is wide in the same way.

**Cost ranking therefore ranks by category width, not by importance.** That is exactly the objection
the reviewer raised earlier about broad categories landing in every player's top three, and it is
now measured rather than predicted. `drop_redundant_aggregates` already exists to stop this — it
operates *within* a section and these claims are in different ones.

## Consequence

- **The proposal is refused as stated** and the arbiter is unchanged. Recorded so it is not
  re-litigated: cost ranking was measured against the reviewer's own notes and did not improve them.
- **The defect is relocated** off the arbiter and onto three things that can each be tested:
  cross-section aggregate suppression, the two focus gates against a 20-game window, and the
  detector threshold for the five absent claims.
- **`FOCUS_GAMES_WITH_DATA = 20` colliding with a 20-game review window is a new and separate
  finding**, and it contaminates the review: a claim can be blocked purely because the reviewer read
  twenty games rather than twenty-five.

## Honest limitations

- **Six players for the agreement half**, and they inherit every limitation of
  [[experiments.e40-derived-ranking]] — a quarter of notes unmapped, counting used as a proxy for
  ranking, and a vocabulary table written by the agent.
- **Twelve for the pool-share half**, which is too few to call a +0.19 correlation anything but
  absent. It rules out a strong trend; it does not establish there is none.
- **`by_cost` here ignores confidence tier entirely**, which is the purest reading of the proposal
  but not the only one. A version that kept the evidence gates and dropped only the peer comparison
  is untested and would land somewhere between the two rows.
- **Nothing here says the material claims *should* be top-three.** It says they are being excluded
  by width, window size and threshold rather than by a judgement about importance — which is a
  different and more fixable problem.
