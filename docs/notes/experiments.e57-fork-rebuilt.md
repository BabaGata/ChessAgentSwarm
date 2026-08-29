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
**Status:** built and tested — **and it now never fires, which is a finding, not a result**

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

## An unexplained side effect

`allowed_motif.pin` went **32 → 43**. `detect_motifs` returns a set, so removing forks should not
create pins, and this is not yet accounted for. Recorded rather than waved through.

## Consequence

- **The rebuild ships**, because it implements the specification and every fixture is verified rather
  than assumed — including the negative cases, which are what carry the test file.
- **The fork claim is currently unmakeable.** No player can be told they miss forks or allow them.
  That is either the correction working (the old claim was wrong 113 times) or the new rule being
  unreachable in practice, and only a person reading positions can say which.
- **The cheapest next check:** the 65 best-move forks from the direct scan are real positions the
  detector fires on. A handful of those, read by the author, settles whether the rule is right — and
  they cost nothing to produce, unlike waiting for one to appear in an S1 population.

## Honest limitations

- **The 3-in-1,014 figure is from random positions**, which are not game positions. It measures the
  rule's strictness, not its accuracy.
- **Nothing here is hand-verified on real games yet.** The nine tests are constructed positions, and
  the corpus effect is a count rather than a judgement.
- **The pin change is unexplained**, and an unexplained side effect in a neighbouring detector is
  exactly the kind of thing that turns out to matter.
