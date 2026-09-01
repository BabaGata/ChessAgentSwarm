---
id: cas-exp-e76
title: 'E76 — 1a is built: you are out of theory sooner than players at your level'
desc: 'The author ruled that telling a player they do not know the opening is coaching, which released 1a. A share beats a threshold on reliability by 0.83 to 0.65, the baseline needs no engine so it lives in its own file, and the claim now reaches 7 of 12 review players.'
updated: 1788217200000
created: 1788217200000
---

# E76 — Leaving theory, built

**Answers:** [[design.detectors-name-consequences]] § 1a, released by a chess ruling ·
**Code:** `chesscoach/book_depth.py`, `experiments/e76-leaving-theory/` ·
**Date:** 2026-08-31 · **Status:** **built, wired, reaching players**

## What released it

[[experiments.e75-book-depth]] left one question, and said it was a chess judgement rather than a
measurement: the median player leaves theory after 5.3 plies and the whole spread is about six, so is
*"a move and a half earlier than your peers"* coaching or trivia? The author:

> *"It is coaching to tell the player that they don't know the opening"*

## A share, not a threshold

Two formulations were measured before either was built:

| | best split-half reliability |
|---|--:|
| share of games where they left theory before ply N | **+0.65** |
| **share of early moves played outside theory** | **+0.83** |

Thresholding discards *how far* out of theory the game went and keeps only whether it was. The
window was swept from 8 to 30 plies: the gap between strong players and peers is widest at **10
plies** (−23 %) and reliability peaks there too, so `EARLY_PLIES = 10` — the first five moves each
side.

**The threshold sweep also inverted the obvious reading.** The strong-vs-peer gap peaks at ply 7–8,
which is where a threshold rule would have been set; reliability at ply 8 is **+0.47**. Picking the
setting that best separates strong players from weak ones would have picked the setting that least
agrees with itself.

## Attribution was tested, not assumed

`BookWalk.left_by_white` exists so a player is not charged for an *opponent's* sideline. Restricting
to games the player left first:

| | strong-vs-peer gap | split-half |
|---|--:|--:|
| every game | −23 % | **+0.83** |
| only games I left first | −24 % | +0.64 |

**The same gap at two-thirds the reliability**, because restricting halves the games per player. Every
game counts, and the chess argument for it — that a player prepared in an opening knows the answers
to sidelines too — is the author's to confirm. The measurement says the choice costs nothing either
way.

## The baseline needs no engine, so it does not live in the peer reference

`data/openings/book-depth-norms.json`, built in seconds by `build_norms.py`, keyed on **band and
speed**:

| speed | players | games | median share outside theory |
|---|--:|--:|--:|
| rapid | 72 | 2,019 | **43.5 %** |
| blitz | 65 | 1,817 | **50.0 %** |

Putting this in the peer reference would make a baseline that costs seconds depend on an engine pass
that costs an hour. `development-norms.json` set the same precedent for the same reason. A player's
baseline is standardised over their own speed mix, so an all-blitz player is compared against blitz.

## What it says

Wired into S4. Over the twelve review players, at 20 games each:

| | |
|---|--:|
| measured | **7 of 12** |
| reached a plan | 1 (cademan, **59 % against 46 %**) |

**Deliberately unpriced.** Leaving theory is a state, not a mistake — the reasoning that makes
`concedes_weakness` unpriceable — and charging it the win probability lost in those plies would
double-count what `early_error` already counts there. So it reaches a player by being unusual for
their level or not at all.

## Two defects worth recording

**The claim counted plies and could cite moves.** `Measurement` refuses a claim reporting more
instances than it can locate — *"instances_at has 19 moves but instances is 105"* — which is how the
measure came to be counted in the player's **own** moves rather than the game's plies. The invariant
was right and it changed the design for the better.

**Then it counted from zero in a codebase that counts from one.** `Observation.ply` is `index + 1`
and `_is_theory` reads `ply <= plies_in_book`; the new window used 0-based indices. **The only
symptom was silence**: 52 instances, none of them found in the by-ply lookup, and the claim correctly
refused for having no evidence. The guard fired, did the right thing, and hid the cause. The fix
calls `_is_theory` rather than re-deriving it, because two definitions of "still in theory" in one
codebase is one too many.

## Honest limitations

- **The 43.5 % baseline is a median over 72 players' own shares**, not a pooled total — pooling would
  let a player with many games set the population's number. But it is one number per band and speed,
  and openings differ: a Najdorf player and a London player do not face the same book.
- **cademan is below the band** ([[experiments.e70-band-mismatch]]), so their 59 % against 46 % is
  partly the band mismatch and not only their opening knowledge. The one player this claim reaches is
  the one player whose baseline is most suspect.
- **The book is 3,810 CC0 lines.** "Outside theory" means outside *that* book, and a line it does not
  name is not thereby unknown to the player.
- **Nobody has checked the claim against positions.** It fires; whether the moves it cites are
  genuinely a player leaving preparation is the detection sheet's question.
