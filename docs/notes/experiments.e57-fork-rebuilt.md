---
id: cas-exp-e57
title: 'E57 — The fork detector now demands forced loss, and stops firing entirely'
desc: 'Rebuilt on the author''s definition: two NEWLY attacked pieces and definite material loss. Only 3 of 1,014 knight double-attacks on a rook and bishop survive it. On the review corpus the claim goes 146 firings to zero, which needs the author''s eye before it can be called correct.'
updated: 1788652800000
created: 1788652800000
---

# E57 — Rebuilding `fork` on newly-attacked targets and forced loss

**Answers:** [[design.detectors-name-consequences]] § 3 · **Code:** `chesscoach/tactics.py`,
`tests/test_fork.py` · **Date:** 2026-08-29 ·
**Status:** built, tested, one vacuous-truth defect found by reading output and fixed — **and it still never fires in S1, which is unresolved and 15 positions await marking**

## What changed

The author's definition:

> *"Forks are moves that occur when at least 2 pieces were newly (so they weren't attacked before)
> attacked by one single piece after moving that piece and the result is definite loss of material."*

The old detector asked only whether the moved piece attacked two things worth winning and survived.
It never asked whether the attacks were **new**, and never asked whether material was **lost**.

Four conditions now, and the fourth is the one that changes everything: **no defender reply saves
everything**, checked over one ply of legal replies, skipping replies that themselves lose material
(the commonest being capturing the forking piece, which `_lands_safely` has already priced).

The king is a target without being a prize — it cannot be captured, so `wins_material` says nothing
about it. Excluding it would have blinded the detector to the **family fork**, which is the
commonest fork there is.

## How much stricter, measured

Hand-built positives kept turning out not to be forks. Searched over random positions:

| | |
|---|--:|
| knight double-attacks on a rook and a bishop examined | **1,014** |
| of those, genuine forks under the new rule | **3** |

**The old detector would have counted all 1,014.** The reason is the one the author gave: a rook
attacked alongside a bishop usually steps to a square that *also defends the bishop*, and nothing is
won. In the position built to be their example, Black has `Rd3` and `Re6`; in a queen-and-rook
version, six replies save both.

That is the whole correction in one number, and it is why building the fixtures by hand failed three
times: **most double attacks are not forks.**

## And then it stopped firing altogether

| claim | before | after |
|---|--:|--:|
| `allowed_motif.fork` | 113 | **0** |
| `missed_motif.fork` | 33 | **0** |

Both now sit in the sheet's **NEVER FIRED IN THESE GAMES** section, whose own text says a detector
that never fires *"is as much a defect as one that fires wrongly."*

**This is consistent rather than broken**, and the check that establishes it: a direct scan of 3,908
engine best-moves finds **65 forks** — 1.7 %, a healthy rate. The detector works. The S1 populations
are far narrower than "all best moves": `allowed_motif` looks only at the opponent's punishing reply
after a diagnosable error, and `missed_motif` only at the player's own best move where they erred.
A rule roughly twenty times stricter, applied to a few hundred positions, reaching zero is
arithmetically unsurprising.

**Unsurprising is not the same as right.** Whether the rule is now *too* strict is a chess question
and the author's to answer.

## Then a scan of played moves found a sixth L-046

The zero could not be checked by waiting for an S1 population to produce a fork. Scanning **played
moves** costs no engine time and produces the same detector's own positives, so it was done first —
and it found a defect the nine fixtures could not:

**Every checkmate was a fork.** `_loses_material_whatever_the_defender_does` iterates the defender's
legal replies and returns *"nothing saved the targets"* when the loop ends. With **no** legal replies
the loop ends immediately and the answer is vacuously yes. **104 of 1,779 hits were mate or
stalemate** — 6 %, and among the first five positions read by eye.

This is [[learning.lessons]] **L-046 for the sixth time**, and the third in a week after E54's
confounded control arm and E56's empty baseline: *an empty case returning the same value as a real
one.* All three were found by reading output rather than by a test, because the empty case is exactly
what a hand-built fixture does not contain.

Guarded, tested against the real position (`2Q5/8/8/p7/P7/k7/2Q4K/8 w - - 5 60`, `Q8c3#`), and no
stalemate fixture written: a stalemating move leaves the king un-attacked, so it never reaches two
targets and would pass for the wrong reason.

## What it fires on now

Over 2,125 games, **1,675 forks on played moves** — 1.1 % of moves, matching the 1.7 % measured on
engine best moves:

| | | |
|---|--:|--:|
| a check that also wins a **pawn** | 656 | 39 % |
| a check that also wins a **piece** | 544 | 32 % |
| **two pieces, no king** | 475 | 28 % |

**Nearly three quarters involve a check**, which is the shape a fork actually has at 1600 level. The
pawn-winning third is real by the author's definition — *"definite loss of material"* — and is the
part most likely to be judged too small to name. That is a chess judgement and is left to the author
rather than decided here.

`experiments/e57-fork-rebuilt/results/fork-sample.txt` holds **15 of them as diagrams with a mark
box**, drawn at a fixed seed.

## An unexplained side effect

`allowed_motif.pin` went **32 → 43**. `detect_motifs` returns a set, so removing forks should not
create pins, and this is not yet accounted for. Recorded rather than waved through.

## Consequence

- **The rebuild ships**, because it implements the specification and every fixture is verified rather
  than assumed — including the negative cases, which are what carry the test file.
- **The fork claim is currently unmakeable.** No player can be told they miss forks or allow them.
  That is either the correction working (the old claim was wrong 113 times) or the new rule being
  unreachable in practice, and only a person reading positions can say which.
- **15 positions are waiting to be marked**, and marking them is what turns the zero from
  *arithmetically consistent* into *known correct or known wrong*. Nothing further should be built on
  this detector until they are.

## Honest limitations

- **The 3-in-1,014 figure is from random positions**, which are not game positions. It measures the
  rule's strictness, not its accuracy.
- **Nothing here is hand-verified on real games yet.** The eleven tests are constructed positions,
  and the corpus figures are counts rather than judgements. The sample exists to fix that and is
  unmarked.
- **The composition table classifies, it does not validate.** *"544 checks that win a piece"* is the
  detector describing itself.
- **The pin change is unexplained**, and an unexplained side effect in a neighbouring detector is
  exactly the kind of thing that turns out to matter.
