---
id: cas-exp-e56
title: 'E56 — Retiring advantage_error silenced nobody, and freed two headlines'
desc: 'The second-commonest claim in the system stops being counted. Nobody loses a priority and nobody is left with nothing; two players were being told about it FIRST and now get something else. One of them swaps it for another claim already on the correction list.'
updated: 1788652800000
created: 1788652800000
---

# E56 — What moved when `advantage_error` was retired

**Answers:** [[design.detectors-name-consequences]] § 2's commitment that *"the arbiter's ranking will
move and must be inspected, not assumed harmless"* · **Code:**
`experiments/e56-retire-advantage-error/` · **Date:** 2026-08-29 · **Status:** done — **safe**

## Why it was retired

The author, having marked all five sampled instances *"cannot tell"*:

> *"Advantage error should be totally removed, or kept for future but not used nor calculated. It is
> completely uninformative."*

It fired **182 times across six players** — the second-commonest claim in the system — and named a
circumstance, *"you go wrong more often than most when you are already better"*, that no player can
act on. Every error it counted was already counted by whichever detector explains it.

**Retired, not deleted.** The author named a future use: checking whether the *origin* of such errors
is detected elsewhere, which is a question about the swarm's coverage rather than a claim about a
player. `ADVANTAGE_ERROR_RETIRED` gates the tally; `_is_clearly_better` and its tests stay.

## Result

| | |
|---|--:|
| players where it fired | **6 of 12** |
| headline finding changed | **2** |
| plans that got shorter | **0** |
| **players left with nothing to work on** | **0** |

**Nobody was silenced**, which was the risk worth checking: silence went 2/12 → 0/12 when the cost
pool was built ([[decisions.0010-three-priorities-and-the-cost-pool]]) and bringing it back unnoticed
would have undone that. Every player keeps the same number of priorities — the cost pool fills the
freed slot, which is what it is for.

**Two players were being told about it first:**

| player | was | now |
|---|---|---|
| `bjagus` | `advantage_error.clear` | `early_error.white` |
| `Sheriwoyama` | `advantage_error.clear` | `long_think_error.long_think` |

So for two of twelve, the single most prominent thing the report said was a claim the author judges
uninformative. That is a stronger argument for the retirement than the instance count was.

## The uncomfortable half of that result

**`bjagus` swapped one uninformative claim for another.** `early_error.white` is on the same
correction list, marked **0/4** — *"fires on real errors, explains them wrongly"*. One player's
headline moved from a claim that names nothing to a claim that explains wrongly.

That is not an argument against retiring `advantage_error`; it is evidence that the corrections are a
set rather than a list, and that `early_error` should not wait long. It also predicts that redoing
the opening claims will change `bjagus`'s headline a second time.

## A harness bug worth recording

The first run reported **0 of 12** and no change anywhere — because it filtered the retired claim out
of a diagnosis that had *already* retired it. The "before" arm was empty, and an empty arm compared
against a real one reports perfect safety.

The fix flips `ADVANTAGE_ERROR_RETIRED` back on for the baseline and runs the sections twice against
one cached analysis. **This is the same shape as E54's confounded two-arm test**, four days apart: a
comparison whose control arm was not the thing it claimed to control for.

## Consequence

- **The retirement ships.** No player loses a priority, none is silenced, and two stop leading with
  a claim that names nothing.
- **`early_error` moves up.** It is now `bjagus`'s headline and it is already known to be wrong,
  which is worse than it was when it merely fired often.
- **The cost pool absorbed the change invisibly**, which is worth noting as the mechanism working:
  the freed slots refilled without anyone dropping to a shorter plan.

## Honest limitations

- **Twelve players, twenty games each.** The same corpus every ranking result in this project rests
  on, with the same limits.
- **"Nobody silenced" is measured on players who all had something to say.** A player with almost
  nothing assertable could still be pushed under, and none of the twelve is that player.
- **This measures displacement, not improvement.** Whether `early_error.white` is a *better* headline
  than `advantage_error.clear` for `bjagus` is exactly the question the corrections exist to answer,
  and it is not answered here.
