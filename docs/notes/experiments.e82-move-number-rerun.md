---
id: cas-exp-e82
title: 'E82 — The off-by-one had spread to six places, and correcting it moved results both ways'
desc: 'E31 and E44 joined the reviewer notes with a move-number formula fixed in phrasing.py and never fixed in the experiments. Three experiments were stale, not two. E44 loses its one counterexample and gets stronger; E31 barely moves in aggregate while changing which notes matched.'
updated: 1788357600000
created: 1788336000000
---

# E82 — Re-running what the wrong move number touched

**Answers:** the P1 *"re-run E31 and E44 on the corrected move numbers"* ·
**Code:** `experiments/e31-move-level-agreement/`, `experiments/e28-expert-review/clock_annotate.py`,
`experiments/e33-error-threshold/` · **Date:** 2026-09-02 ·
**Status:** done — **and it found a third stale experiment**

## The defect

`phrasing.move_number` carries the warning in its own docstring:

> *"The obvious-looking `ply // 2 + 1` gets White right and reports **every Black move one too
> high**, which is what the reviewer caught reading their own games against the reports."*

It was fixed there (L-044, D17). **It was never fixed anywhere else, and it had been copied into five
other files**: E31's comparison, E28's clock annotation (which is E44's code), E33 twice, plus E01
and E02 for display labels.

**Three experiments joined the reviewer's own noted move numbers with the wrong formula**, not the
two the open item named. E33 was found only by grepping for other copies after fixing the first two.

Every site now calls `move_number`, except E01 and E02 — those predate the package and import nothing
from it, so the arithmetic is inlined with a comment naming the function it must match. That is the
weaker fix and it is the one that let this spread, so it is said out loud rather than left tidy.

## E44 — the correction makes it stronger

| | before | after |
|---|--:|--:|
| noted mistakes played in ≤ 2 s | 89 of 262 (**34 %**) | 76 of 262 (**29 %**) |

The note's argument was that 34 % *"means less than it looks"*, because these are mostly 3+0 games
where instant moves are ordinary. The corrected numbers strengthen that and **remove its one
exception**:

| player | ratio before | ratio after |
|---|--:|--:|
| bjagus | 0.52× | 0.43× |
| **cademan** | **1.25×** | **0.77×** |
| Crossfire1983 | 0.70× | 0.76× |
| goydorak | — | 0.79× |
| Hirsican | — | 0.73× |
| maikel5 | — | 0.58× |

A ratio below 1 means a player's *noted* mistakes were **less** often instant than their moves in
general. Before, cademan at 1.25× was the sole counterexample. **Every player is now below 1**, so
the reviewer's noticed mistakes were consistently not the rushed ones — a cleaner conclusion than
the note could state, arrived at by fixing an error rather than by finding new evidence.

## E31 — barely moves in aggregate, and moves a lot underneath

The note's headline was **bjagus alone**: 16/20 detection (80 %), 2/20 naming (10 %). That figure was
already stale before this — the results on disk read 18/20 and 6/20.

| player | notes | detection before → after | naming before → after |
|---|--:|---|---|
| Crossfire1983 | 54 | 70 % → **76 %** | 17 % → **26 %** |
| Hirsican | 40 | 90 % → 88 % | 55 % → **45 %** |
| bjagus | 20 | 90 % → **100 %** | 30 % → **60 %** |
| cademan | 60 | 75 % → 72 % | 48 % → **43 %** |
| goydorak | 16 | 44 % → **31 %** | 6 % → 6 % |
| maikel5 | 10 | 80 % → 80 % | 30 % → 30 % |
| **total** | **200** | **76 % → 76 %** | **35 % → 37 %** |

**The aggregate hardly changes and the per-player numbers change a great deal, in both directions.**

That is the finding, and it is not the one I expected. Reading `bjagus` alone — detection 90 → 100 %,
naming 30 → 60 % — looked like a clean improvement, and five more players said otherwise. The
off-by-one did not systematically inflate or deflate agreement; it **shuffled which notes matched**.
A Black-move note previously landed on the neighbouring ply, and sometimes there was an observation
sitting there.

So **some of the old detections were coincidences of the off-by-one**, and Hirsican's naming falling
from 55 % to 45 % is the correction removing false matches rather than losing true ones. A lower
number is the more truthful one here.

## Consequence

- **E31's and E44's headline figures were wrong** and are corrected in both notes.
- **The formula exists in one place now.** It spread by copying, so the fix is to have one owner and
  to say so where it cannot be imported.
- **E33 is re-run, and the first attempt did not happen.** This note and its commit both said it had
  been, and that was written while the run was in fact being killed by a 1,800-second ceiling I had
  put on it — the background task then reported *"exit code 0"* on truncated output, and the result
  file still carried its August date. Corrected here rather than quietly, because a note claiming a
  run that did not occur is precisely the stale evidence this whole task existed to fix.

  Re-run properly, **the checkable notes go from 106 to 134** — a quarter more of the reviewer's own
  notes now join at all, which is the largest single effect the off-by-one had anywhere. The rates
  barely move with them:

  | threshold | checkable | detected | named |
  |---|--:|--:|--:|
  | 10 wp | 106 → **134** | 58 % → 58 % | 28 % → **29 %** |
  | 7 wp | 106 → **134** | 70 % → **72 %** | 33 % → **36 %** |
  | 5 wp | 106 → **134** | 78 % → 78 % | 38 % → **39 %** |
  | 3 wp | 106 → **134** | 89 % → **90 %** | 42 % → **45 %** |

  **That the percentages held while the denominator grew 26 % is the reassuring part**: the 28
  recovered notes behave like the ones that were already joining, so E33's conclusion — that lowering
  the threshold buys agreement without collapsing discrimination — survives and is slightly stronger.

  **The discrimination table did move**, and against the threshold E33 was defending: at 10 wp,
  `missed_motif` falls from 1.53× to **1.28×** and `allowed_motif` from 1.38× to **1.13×**. Those are
  the L-024 spreads, and 1.13× is close to the 1.25–1.31× band E09 used to *reject* candidate
  detectors. It does not change E33's recommendation, which was to lower the threshold, but it makes
  the case at 10 wp weaker than the note recorded.

## Honest limitations

- **This does not validate the detectors.** It corrects the join between the reviewer's notes and the
  swarm's observations. Whether a matched claim is *right* is still the detection sheet's question.
- **The reviewer's move numbers are as written**, and a note saying "move 31" was checked against
  move 31 as they counted it. If any note counted differently the join is still wrong there, and
  nothing here could detect that.
- **`goydorak` at 31 % detection is now the outlier** and nothing here explains it. It was 44 % and
  is now lower; that player has 16 notes, so the interval is wide.
