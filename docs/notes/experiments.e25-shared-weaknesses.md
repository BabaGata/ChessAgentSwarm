---
id: cas-exp-e25
title: 'E25 — Five shared weaknesses are worth naming, and the swarm names none of them'
desc: 'Most claims stop falling with rating once general skill is divided out. Five do not — including the most expensive claim in the band, which is currently advised to nobody.'
updated: 1786579200000
created: 1786579200000
---

# E25 — Shared weaknesses that are still worth coaching

**Answers:** the author's objection to peer-relative severity · **Date:** 2026-08-07 ·
**Status:** done — **the objection is upheld, for 5 claims of 27**

## The objection

Step 3 ranks by what a claim costs **above** what it costs peers, which stops one
expensive-for-everybody claim being named to 70 % of players (E17). The author's objection:

> A mistake everyone at your level makes is still a mistake, and fixing it is exactly how you stop
> being at that level.

Half of this the report already handles — it prints the raw cost *and* the peer cost, so a shared
weakness is not hidden when it is reported. What the excess changes is **selection**: a claim where
the player loses 25 and peers lose 24 has an excess of 1, sinks below everything, and is therefore
never said at all.

## The question that separates the two readings

Both sides are right about different things — the objection about **cost**, the ranking about
**personalisation**. What decides whether a shared weakness is worth naming is:

> among claims expensive for everyone, which ones do players at the **top** of the band commit less
> often than players at the bottom?

Falling with rating means the band demonstrably learns to fix it. Flat means it is a property of
chess at this level, and "fix this" means "be better at chess".

**The confound is fatal if ignored.** Rating is largely *determined* by error rate — V1 estimates one
from the other at ±103 points — so every error-type claim correlates with rating by construction.
Both are therefore measured:

| | |
|---|---|
| **raw** | corr(claim rate, rating) |
| **divided** | corr(claim rate ÷ the player's overall error rate, rating) |

The second is L-025's screen: does it survive dividing out what is already measured?

## Result — the confound is almost the whole effect

84 players, rapid and blitz pooled.

| | |
|---|--:|
| median raw correlation with rating | **−0.42** |
| **median after dividing out general skill** | **+0.15** |

Nearly every claim falls with rating, and **nearly all of that is just better players making fewer
mistakes of every kind**. After division most claims flatten, and several *rise* — higher-rated
players in this band concede outposts (+0.64), king pressure (+0.59) and discovered attacks (+0.59)
*more* relative to their overall error rate, presumably because they play sharper positions.

So "report every shared weakness" would be wrong. Most of them carry no evidence that anyone learns
to fix them specifically.

## Result — but five survive, and one is glaring

| claim | cost/game | divided r |
|---|--:|--:|
| **`instant_move_error`** | **16.1** | **−0.41** |
| `early_error.black` | 10.6 | −0.46 |
| `early_error.white` | 9.5 | −0.37 |
| `missed_motif.hangingPiece` | 2.1 | −0.21 |
| `allowed_motif.backRankMate` | 0.8 | −0.22 |

**`instant_move_error` is the most expensive claim measured anywhere in this project — 16.1 points of
win probability a game — it is shared across the band, it is specifically learnable, and it is
currently advised to precisely nobody.** It appears in no player's plan in any profile build this
cycle, because everyone does it at a similar rate and it therefore never clears `FOCUS_MARGIN`
against peers.

> **Figures re-measured 2026-08-20.** The table above is what this experiment found *at the time*, on
> the five-player-per-stratum throwaway reference, and is kept as the record of that run. Re-run by
> the same method on the full-size reference with the increment corrected
> ([[experiments.e45-increment-correction]]):
>
> | claim | cost/game then | now | divided r then | now | |
> |---|--:|--:|--:|--:|---|
> | `instant_move_error` | 16.1 | **22.8** | −0.41 | **−0.40** | stays |
> | `missed_motif.hangingPiece` | 2.1 | **2.5** | −0.21 | **−0.31** | stays |
> | `early_error.white` | 9.5 | **15.5** | −0.37 | **−0.24** | stays |
> | `early_error.black` | 10.6 | 15.8 | −0.46 | **−0.13** | **fails the −0.2 bar** |
> | `allowed_motif.backRankMate` | 0.8 | 0.8 | −0.22 | **−0.12** | **fails the −0.2 bar** |
>
> **Five survivors became three**, and `band.py` was updated to match. The headline claim holds and
> its cost is *higher*, not lower, than recorded here — two changes pulled in opposite directions and
> the corpus rebuild outweighed the increment correction. **They cannot be cleanly decomposed**
> without reverting the code, so no split is claimed; what is measured is the endpoint.
>
> **Note which statistic this is.** 16.1 and 22.8 are the *median across players* of each player's own
> cost. The number a player actually reads in the band note is the population's pooled cost for their
> speed — **17.69 rapid, 32.16 blitz** — which is a different quantity and was never 16.1.

That is the author's objection made concrete: the peer comparison is systematically blind to the
band's biggest shared, learnable weakness, and blind *because* it is shared.

## What follows

Not "rank by raw cost" — E17 measured where that leads. The shape that fits the evidence is a
**separate, clearly-labelled band-level section**, on three conditions:

1. **It never consumes the one or two personal priorities.** Those stay peer-relative, which is what
   makes them a diagnosis rather than a description (R-14, anti-pattern D2).
2. **It is not phrased as a personal finding.** *"Players at your level lose about 16 points a game
   to moves played in under two seconds, and the stronger ones lose less"* is a true statement about
   a population; *"you play too fast"* is a claim about a player that this measurement does not
   support.
3. **Only claims passing the divided-gradient test appear** — five today, not twenty-seven.

## Built, 2026-08-07

`chesscoach/band.py` holds the five screened claims with the correlation that admitted each one;
`PlayerProfile.band_notes` stores them (schema v12); the explainer prints a separate section. The
cost is looked up **live** from the reference through `peer_cost_per_game`, so it inherits the
per-speed mix-matching — a blitz-heavy player's band is a blitz-heavy band.

Capped at three, for the same reason the arbiter caps priorities at two: a list long enough to be
comprehensive is short enough to be ignored.

On a real 24-game report:

```
WHAT YOUR WHOLE LEVEL LOSES MOST TO

 - Players at your level lose about 20.3 points of win probability a game to moves
   played in under two seconds.
 - Players at your level lose about 10.8 points ... to mistakes before move 15 with Black.
 - Players at your level lose about 10.2 points ... to mistakes before move 15 with White.

   These are not findings about you — they are what the whole rating band
   loses most to, and the stronger players in it lose less. Your own one or
   two priorities above are the ones that are unusual for you specifically.
```

**Nothing about the diagnosis moved**, which is the point. Re-running the anti-pattern family on the
same 84 profiles: 66 advised, 25 claim kinds, overlap 0.09, groundedness 113/113, never more than two
priorities — identical to the run without band notes. They are not findings, the arbiter never sees
them, and they cannot displace a personal priority.

## Honest limitations

- **One band.** The gradient is measured *within* 1400–1800, where the rating range is narrow and the
  divided correlation is doing a lot of work on a little spread. Cross-band data would be far
  stronger evidence and does not exist.
- **The rating is a blend.** It is the player's mean own Elo across pooled rapid and blitz games, and
  E19 measured blitz ratings running ~81 points lower. A player's speed mix therefore biases their
  "rating" here, and the mix varies a lot between players. This is the weakest part of the
  measurement.
- **Dividing by the overall error rate is a crude control.** It is a ratio of two noisy quantities,
  and it removes general skill only to first order.
- **Nothing here shows the five are *fixable by coaching*** — only that stronger players in the band
  do them less, after skill is divided out. Association, not instruction.
