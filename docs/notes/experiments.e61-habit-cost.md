---
id: cas-exp-e61
title: 'E61 — Pricing a habit by what its own moves lost clears the arbiter'
desc: 'The author rejected an end-of-opening cost because two weak players'' errors cancel. Summing loss_wp over the moves each habit names instead: 20.4 wp/game for repeat moves, and correlations with the general error rate of 0.44–0.64, well under E10''s 0.917. Development claims reach a plan for the first time — 1 of 12, and the bottleneck moves to the assertion rate.'
updated: 1788912000000
created: 1788912000000
---

# E61 — What the habit's own moves cost

**Answers:** [[experiments.e60-peer-reference-rebuild]]'s open decision ·
**Code:** `chesscoach/development.py`, `chesscoach/opening_development.py`,
`experiments/e58-opening-development/habit_cost.py` · **Date:** 2026-08-30 ·
**Status:** the arbiter block is cleared; **the assertion rate is now the limit**

## The author's method, and why the alternative was wrong

E60 offered three ways out and I recommended pricing the claims by where the opening *ended*. The
author rejected that and gave a better method:

> *"Maybe calculating the cumulative cost that happened during the opening would be good option. In
> the games of weaker players they don't have to eventually end opening worse because their opponent
> also plays badly. Maybe combining cost of the moves when the same piece was moved repeatedly
> instead of developing the other piece, combining the cost of every pawn move when the piece should
> be developed instead and combining the cost for every move when the player should castle the king
> but he did something else."*

**The objection kills the alternative outright.** Two weak players' errors cancel, so an opening that
ends level says nothing about how it was played. Per-move attribution never touches the opponent.

It also dissolves E60's framing. I had called the missing cost a *category mismatch* — the habit's
moves are not the moves that lose. That was wrong: **the habit's moves do lose, measurably**, and
summing what they lost is the arbiter's own cost model rather than a second currency.

**The "instead of" condition is load-bearing** and is in the author's wording three times: *instead of
developing the other piece*, *when the piece should be developed instead*, *when the player should
castle but did something else*. Without it the labels degenerate into *"this was a pawn move"* and
the sum re-measures the general error rate under a habit's name. So a repeat move counts only while a
minor is still at home, and a declined castle only when castling was legal.

## What each habit costs

40 players, 20 games each, summed `loss_wp` over the moves each habit names:

| habit | median wp/game | p90 | share of opening loss |
|---|--:|--:|--:|
| repeat instead of developing | **20.4** | 43.0 | 36 % |
| pawn instead of developing | **12.8** | 26.7 | 22 % |
| declined an available castle | **9.7** | 32.2 | 17 % |

**These are large.** The whole opening loses a median 55.7 wp/game, and each habit is a real fraction
of it.

**They overlap and must not be summed.** A pawn move while a minor is at home *and* castling is
available is an instance of two habits at once. The headline claim therefore takes the **union** of
the flags, which counts each lost move once; adding them would inflate exactly the claim that
competes for a plan slot.

## Is it the general error rate wearing a habit's name?

The screen that matters, because a player who errs more errs more on pawn moves too:

| habit | r with the player's overall opening error rate |
|---|--:|
| repeat | 0.64 |
| pawn | 0.64 |
| **declined castle** | **0.44** |
| all three | 0.74 |

**All well under E10's 0.917**, which closed a section slot, and under the 0.85 ceiling this design
states. The declined castle is the most independent signal in the set. These carry information the
error rate does not.

## The result

| | before | after |
|---|--:|--:|
| development claims in a plan | **0 / 12** | **1 / 12** |
| development claims asserted | 1 / 12 | 1 / 12 |

**The arbiter block is gone.** An asserted development claim now wins a slot on the same terms as
every other claim — no special case, no reserved slot, no reordering. The author's method was the
right one of the three and it was not among the three I offered.

**The bottleneck has moved to the assertion rate.** Only 1 of 12 review players asserts a development
claim at all, against a band-level figure of ~25 % that predicts about 3. With n = 12 that gap is
inside noise, but it is unexplained and it is now the thing standing between these claims and
players.

## A silent failure, for the third time this week

The cost had to reach **three** places, and it reached two: the tally, `measure()`'s
`ConditionMeasurement` — which is what the peer reference pools — and `_assess()`'s `Measurement`,
which is what the **arbiter ranks**. I patched the first two, rebuilt the reference, re-ran, and got
`0/12` again with `cost/g 0.00` on a claim I had just priced.

Nothing errored. The reference was correct. The claim was asserted. It simply sorted last, exactly as
before, for want of a field in a third constructor.

Same shape as E60's missing `examples` and E56's empty baseline: **a value that must flow through
several layers fails silently at the layer nobody checks**, and only instrumenting the end of the
chain finds it. Reading the number I expected to change, rather than the log, is what caught all
three.

## Consequence

- **`slow_development`, `late_castling` and `repeat_move` are priced** and compete normally.
- **The pawn claim may return.** E59 dropped it because the *rate* does not discriminate — but its
  *cost* is 22 % of opening loss at r = 0.64. Same number of pawn moves as peers, worse ones. That is
  a different claim from the one that was dropped and it has not been tested.
- **Next is the assertion rate**, not the arbiter.

## Honest limitations

- **1 of 12 is one player.** Everything about delivery here rests on a single case.
- **`loss_wp` is engine loss against the best move**, so a habit move that was bad for an unrelated
  reason still counts toward the habit. The "instead of" condition narrows this but does not remove
  it, and the correlations above are the evidence that it has not swallowed the measure.
- **The overlap is handled by union, not by attribution.** When one move is two habits at once,
  nothing here decides which habit deserves the blame.
- **No cost figure has been read by a person** against the games it came from.
