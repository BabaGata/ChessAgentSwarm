---
id: cas-exp-e67
title: 'E67 — Persistence wired in for every weakness, and endgame_error becomes a run'
desc: 'The author extended their doubled-pawn rule to isolated pawns, so persistence is now a property of any pawn weakness rather than a special case. And endgame_error is rebuilt as consecutive drops the tactics do not explain: 211 firings become 50, with the run condition doing seven times the work of the residual one.'
updated: 1789171200000
created: 1789171200000
---

# E67 — Persistence everywhere, and endgame errors as runs

**Answers:** [[design.detectors-name-consequences]] §§ 5–6, plus the author's extension ·
**Code:** `chesscoach/structure.py`, `chesscoach/sections/s5_pawn_structure.py`,
`chesscoach/sections/s3_endgame_technique.py` · **Date:** 2026-08-31 ·
**Status:** steps 3 and 4 complete; **5 of 6 corrections built**

## Persistence is not about doubled pawns

> *"Isolated pawn should also have similar persistance check"*

The author extended their own rule, and they were right that it generalises: the argument was never
about doubling. **A weakness that repairs itself before the opponent can use it cost the player
nothing**, and a detector looking at one board cannot tell the difference.

So `persistent_doubled` became `persistent(boards, colour, feature)`, over any of the three pawn
weaknesses, and `count_backward` was split into `_backward_pawns` plus a counter so all three can
report *where* they are. Persistence is tracked **per file**, because a weakness that clears on one
file and appears on another is two episodes rather than one that lasted.

**And it is now wired into S5**, which was the structural change the design note flagged and E66 left
undone. A conceded weakness is kept only if it is still there after three more of the player's own
moves.

Two decisions the wiring forced, both from the author's wording rather than convenience:

- **the player's own moves, not plies** — they said *"moves"*, and a player who repairs the weakness
  at their next turn held it for one;
- **a game that ends first is not a repair.** Those moves were never played, so the weakness is
  kept. Dropping it would make short games look clean, which is the censoring [[experiments.e58-opening-development]]
  named and refused.

## `endgame_error` — a run, and only what the tactics do not explain

> *"Endgame error should be calculated just when there are big drops of the advantage in a few
> consecutive moves... Also, if the sudden loss of the advantage of the one move is detected by other
> motif tests this should not be taken in the account because those are tactical losses and this is
> lack of knowledge of the endgames."*

Both conditions built. A run is **3 losing moves within a window of 4** of the player's own endgame
moves, and tactical drops are removed **before** the run is looked for — a hung rook between two
inaccuracies does not join them into a run, because it is not the same failure.

`_is_tactical` asks whether the move the **engine** wanted executes a motif. Saying *"you do not
understand endgames"* to a player who missed a fork names the wrong weakness, and the report already
has a section for the right one.

### What each condition removes

Twelve review players, twenty games each:

| | | |
|---|--:|--:|
| endgame errors under the old rule (any drop) | **211** | |
| of those explained by a motif — the residual condition | 21 | **10 %** |
| surviving under the new rule | **50** | **24 % of old** |

**The run condition does about seven times the work of the residual one.** That is the same shape as
`doubled` in E66, where persistence removed 64 % and distance 17 %: **when the author gives two
conditions, one of them carries the correction and the other trims an edge** — and which is which has
not once been guessable in advance.

This also makes the claim **explicitly residual**, a new relationship between sections: `endgame_error`
now depends on the motif detectors being right. When `fork` was wrong, this claim was wrong with it.

## What the fixtures said about the old rule

Three S3 tests failed on the change and **the fixtures were wrong, not the code**: they built two
endgame moves with one error, which is exactly the single blunder the author says is not an endgame
error. They now build runs. Four S5 and S6 fixtures needed the same treatment in E66.

That is four separate occasions in two experiments where a test encoded the behaviour being
corrected. Worth noting as a pattern: **a test written against a detector is evidence about the
detector's rule, so correcting the rule should be expected to break it** — and a suite that stayed
green through these corrections would have been the thing to worry about.

## Honest limitations

- **Twelve players, and no position has been read.** 50 is a count, not a verdict, and whether those
  runs are really endgame ignorance is a chess judgement nobody has made.
- **`RUN_LENGTH = 3` and `RUN_WINDOW = 4` are the design note's first proposal**, unchanged. The note
  said they would be settled by how often runs of each length occur in the corpus; that measurement
  has not been made, so they are reasonable rather than calibrated.
- **`_is_tactical` uses the same motif detectors this project has repeatedly found wrong.** The
  residual is only as good as what it subtracts.
