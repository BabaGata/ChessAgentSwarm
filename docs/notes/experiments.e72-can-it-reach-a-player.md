---
id: cas-exp-e72
title: 'E72 — Thirteen claims fire and can never be told to anyone, and the whole endgame section is one of them'
desc: 'A reachability audit of the full 50-claim vocabulary. 14 reach players, 13 are mute, and every endgame_error variant is unreachable — the vocabulary-level cost of the run rule. The detection sheet, meanwhile, is well targeted: only 2 of its 29 claims are mute.'
updated: 1788199200000
created: 1788199200000
---

# E72 — Can this claim ever reach a player?

**Answers:** the P1 raised by [[experiments.e71-why-the-pool-was-empty]] ·
**Code:** `experiments/e72-can-it-reach-a-player/` · **Date:** 2026-08-31 ·
**Status:** done — **13 mute claims, and the endgame section is silent**

## The question

E71 found, incidentally, that `concedes_weakness` is measured, printed on the detection sheet, and
**structurally unable to fill a priority slot**. Defensible for one claim; a question about the
system if it is true of many.

It bears on what the author is being asked to do. The detection sheet is **145 boxes across 29
claims** and each mark is a careful judgement against a real position. A claim that can reach nobody
is still worth checking — a wrong detector is worth knowing about — but it is worth *less* than one
that reaches someone, and nothing said which was which.

There are exactly two routes to a player: **clear the confidence gate**, or **be priced into the
cost pool**. A claim that takes neither, for every player in the corpus, is **mute**.

## The vocabulary, 12 players, 20 games each

| route | claims |
|---|--:|
| **reaches players** | **14** |
| eligible, never chosen | 12 |
| silent by design | 10 |
| **MUTE — fires, priced, never becomes a finding** | **13** |
| never fires | 1 |
| **in the vocabulary** | **50** |

*Eligible, never chosen* is not a defect — those claims were rankable and lost to something dearer,
which is the arbiter doing its job with a cap of three.

## The endgame section cannot reach anyone

| claim | fires for | priced for | asserted | pooled | told |
|---|--:|--:|--:|--:|--:|
| `endgame_error.any` | 7 | 12 | 0 | 0 | **0** |
| `endgame_error.rook` | 4 | 10 | 0 | 0 | **0** |
| `endgame_error.minor` | 2 | 8 | 0 | 0 | **0** |
| `endgame_error.queen` | 2 | 12 | 0 | 0 | **0** |
| `endgame_error.rook_minor` | 1 | 10 | 0 | 0 | **0** |
| `endgame_error.pawn` | 0 | 4 | — | — | **0** |

**All six variants are unreachable.** This is the same change E71 priced at six priority slots, seen
one level up: E67 made an endgame error a **run of three consecutive imprecise moves** on the
author's own words, and at that threshold the claim fires too rarely and for too few games to clear
the confidence gate for anybody.

It is not a regression — the run rule is what the author asked for, and a claim that fires on a
single blunder was the thing being corrected. But **an entire section that can no longer speak to
any of twelve real players is a fact worth having in front of the person who set the threshold**,
and E68's calibration note did not report it because it was measuring clustering against chance, not
reach.

`fork` and `skewer` are the other cluster: `missed_motif.fork`, `missed_motif.skewer` and
`allowed_motif.skewer` are all mute, which is consistent with the known result that `fork` fires for
nobody after the rebuild.

## The detection sheet is well targeted

The reassuring half, and the reason this was worth running before the author spends an evening on
145 boxes:

| the sheet's 29 claims | count |
|---|--:|
| reaches players | **14** |
| eligible, never chosen | 11 |
| **mute** | **2** (`early_error.any`, `endgame_error.any`) |
| not measured in this run | 2 (the development claims) |

**25 of 29 reach or could reach a player.** Marking the sheet is not time spent on claims nobody
will ever be told about.

## What this cost to find, and what it nearly cost

The first run reported **23 mute claims**. Ten of those were the system working: `executed_motif` is
excluded by name in `s1_tactical_gaps.NOT_ASSERTED` — *"knowing what a player does well matters for
not prescribing it, but it is not a weakness and must not be reported as one"* — `plays_queenless` is
a style tendency deliberately kept out of the findings machinery (D3), and `concedes_weakness.any` is
a pooled claim that `s5_pawn_structure` records as discriminating nobody.

**A reachability audit that does not know intent manufactures defects.** Reporting 23 would have
sent the author to fix code that is right, which is worse than not running the audit. The by-design
set is now named in the script with the line of code that justifies each entry.

## A stale comment found on the way

`s5_pawn_structure` still says `doubled` and the pooled `any` *"reach this bar for nobody, and are
measured, kept in the peer reference, and never asserted"*. **`concedes_weakness.doubled` now asserts
for two players and reaches one** — the persistence correction changed it and the comment did not
move. Corrected.

## Consequence

- **The endgame threshold has a reach cost, now measured**, and it belongs with the author's other
  open judgements rather than being settled quietly.
- **`early_error.any` is mute while `early_error.white` and `early_error.black` both reach players** —
  the pooled claim is redundant against its own split, which is worth knowing before the
  `early_error` correction (the last of the six) is built.
- **The sheet is worth marking**, and now demonstrably so.

## Honest limitations

- **Mute here means mute for these twelve**, at 20 games each, in one band, against a peer reference
  with one stratum. A claim that reaches nobody in this corpus may reach someone in another — and
  six of these twelve are outside the band anyway ([[experiments.e70-band-mismatch]]), which suppresses
  the asserted route for four of them and inflates it for two.
- **Two development claims were not measured in this run** (`late_castling.book`, `pawn_error.any`),
  so their reachability is unknown rather than good or bad.
- **This says nothing about whether any claim is correct.** It says whether a correct one could ever
  be spoken. The detection sheet remains the instrument for the other question.
