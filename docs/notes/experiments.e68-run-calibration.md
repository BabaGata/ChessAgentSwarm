---
id: cas-exp-e68
title: 'E68 — The window was letting chance in, and the author''s literal words were right'
desc: 'A permutation test on the endgame run threshold: same moves, same error counts, shuffled which moves erred. Three-in-three beats chance 1.96 to 1 with no shuffle in 200 reaching it; three-in-four, the setting E67 shipped, was matched by one shuffle in eight. Every move of slack lets the error rate masquerade as clustering.'
updated: 1789171200000
created: 1789171200000
---

# E68 — How long a run has to be

**Answers:** [[design.detectors-name-consequences]] § 6's open calibration ·
**Code:** `experiments/e68-run-calibration/`, `chesscoach/sections/s3_endgame_technique.py` ·
**Date:** 2026-08-31 · **Status:** settled — **3 in 3, and the design note's proposal was wrong**

## The question, asked properly

The design note left `RUN_LENGTH` and `RUN_WINDOW` to be settled by *"how often runs of each length
occur in the corpus"*, and [[experiments.e67-persistence-and-endgame-runs]] shipped its first
proposal, 3 drops within 4 moves.

**Frequency is the wrong question.** A player who errs often produces runs by chance, so a setting
that finds many runs may be finding nothing but the error rate — which S3 already reports, and which
E10 closed a section slot for.

So the baseline is a **permutation test**: keep each player's endgame moves and their number of
errors, shuffle *which* moves erred, count runs again. That holds the error rate fixed by
construction and destroys only the clustering, **so the gap between observed and shuffled is the
clustering and nothing else.**

Twelve players, 200 shuffles, non-tactical drops only.

## The window was letting chance in

| run / window | observed | by chance | ratio | shuffles that matched it |
|---|--:|--:|--:|--:|
| 2 in 2 | 79 | 61.5 | 1.28 | 1 % |
| 2 in 3 | 105 | 96.7 | 1.09 | 14 % |
| **3 in 3** | **35** | **17.9** | **1.96** | **0 %** |
| 3 in 4 — *shipped by E67* | 50 | 39.9 | 1.25 | **12 %** |
| 3 in 5 | 67 | 58.6 | 1.14 | 20 % |
| 4 in 4 | 17 | 5.7 | **3.00** | 3 % |
| 4 in 5 | 28 | 15.3 | 1.83 | 2 % |
| 4 in 6 | 34 | 25.7 | 1.32 | 12 % |

**Every move of slack lets chance catch up**, and the pattern is monotone: 3-in-3 at 1.96, 3-in-4 at
1.25, 3-in-5 at 1.14. The same for four: 3.00, 1.83, 1.32.

**The setting E67 shipped was one of the weakest tested.** At 3-in-4 one shuffle in eight matched or
beat the real games, so the claim was barely distinguishing *imprecision one move after the other*
from *a player who errs a lot* — which is the exact failure the correction existed to fix.

## The author's literal words beat the design note's relaxation

> *"So that it can be seen that the player is imprecise **one move after the other**."*

Strictly consecutive. The window was the design note softening that into "three within four", and the
measurement says the softening was the error. **3 in 3 is adopted**: the strongest ratio of any
setting that fires often enough to be useful, and no shuffle in 200 reached it.

4-in-4 has a higher ratio still (3.00) and fires **17** times across twelve players — too rare to
carry a claim, and its 3 % is worse than 3-in-3's 0 %.

**Corpus effect:** endgame errors go 50 → **35**, from an original 211 under the old any-drop rule.

## Two tests had to be inverted

`test_the_window_allows_one_good_move_inside_a_run` asserted the opposite of what the calibration
found, and is now `test_one_accurate_move_breaks_the_run`. A second test built a run of three
non-tactical drops with a hung piece in the middle and expected the three to count; under the
calibrated rule they are not consecutive, and should not — the player did not err on three moves in
a row, they erred, missed a tactic, then erred twice.

**That is the fifth and sixth test to encode a behaviour later corrected**, across three experiments.
The pattern is now clear enough to state as a rule: **a test written against a threshold is evidence
about that threshold, and calibrating it should be expected to break the test.**

## Honest limitations

- **Twelve players and 200 shuffles.** The ratios are stable but the counts are small: 35 instances
  is two players' worth.
- **The permutation destroys within-game ordering only.** It holds each game's error count fixed,
  which is the right control for clustering, but it cannot tell clustering caused by a *deteriorating
  position* from clustering caused by not knowing the endgame — and those are different diagnoses.
- **Nothing has been read.** 1.96 says the runs are real; it does not say they are endgame ignorance.
