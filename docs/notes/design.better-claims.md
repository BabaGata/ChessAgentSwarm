---
id: cas-design-better-claims
title: 'Design — Where the variance is: why tactical claims cannot separate players and knowledge claims can'
desc: 'Measured within band, 22 of 24 non-tactical claims separate players and only 10 of 30 tactical and positional ones do. A rating band is approximately a measure of tactical strength, so conditioning on it removes the variance tactical claims measure. The fix is to split claims along lines where players have gaps rather than along a taxonomy of what happened on the board.'
updated: 1788724800000
created: 1788724800000
---

# Design — Where the variance is

**Serves:** V4 (gap detection), V5 (prioritisation) · **Follows:**
[[experiments.e84-band-references]] · **Status:** finding + design direction, nothing built

## The measurement

Every screened claim, grouped by family, measured **within band** — the stratum a peer comparison is
actually keyed on:

| family | separates | screened | strongest |
|---|--:|--:|---|
| style | 1 | 1 | `plays_queenless` **36.9×** |
| opening habit | 4 | 4 | `repeat_move` **14.7×** |
| opening knowledge | 2 | 2 | `out_of_book` **8.3×** |
| endgame knowledge | 6 | 6 | `endgame_error.rook` **4.8×** |
| time use | 3 | 3 | `instant_move_error` **4.1×** |
| where errors fall | 3 | 3 | `early_error.any` **3.9×** |
| king safety | 1 | 1 | `allows_pressure.king` 2.4× |
| material care | 2 | 3 | `moved_into_attack` 2.3× |
| **tactics: spotting one** | **3** | **7** | `missed_motif.pin` 1.5× |
| **tactics: being punished** | **3** | **9** | `allowed_motif.hangingPawn` 2.1× |
| **tactics: executing one** | **2** | **7** | `executed_motif.capturingDefender` 1.9× |
| **squares conceded** | 1 | 3 | `allows_square.outpost` 1.4× |
| **pawn structure** | 1 | 4 | `concedes_weakness.doubled` 1.7× |

**Non-tactical: 22 of 24. Tactical and positional: 10 of 30.** And the magnitudes are not close — the
best tactical claim reaches 2.1×, while habits and knowledge reach 8×, 14× and 36×.

## Why, and it is structural rather than a defect

**A rating band is approximately a measure of tactical strength.** Conditioning on band therefore
removes exactly the variance tactical claims measure. Two 1600s see forks about equally well — that
is much of what makes them both 1600. What differs between them is *what they know* and *what they
habitually do*.

This is not a fault in the detectors and no amount of detector work repairs it.

## The design error underneath: splitting a skill instead of a knowledge

The two families that behave most differently are split the same way on the surface and not at all
underneath.

**`endgame_error` splits by the kind of position** — `queen`, `rook`, `rook_minor`, `minor`, `pawn`
(`s3_endgame_technique.material_class`). **All six splits separate players.** Each is a separate body
of knowledge: rook endings are a subject, pawn endings are a different subject, and a player can
own one and not the other.

**The motif claims split by the kind of tactic** — `fork`, `pin`, `skewer`, `discoveredAttack`,
`trappedPiece`. **Ten of thirty separate.** But spotting a fork and spotting a pin are *the same
underlying skill*: board vision. Splitting by motif does not create variance, it slices one skill
thinner.

> **Knowledge is patchy; skill is not.** You can know rook endings and not know pawn endings. You
> cannot really see forks and not see pins.

**Where the current design produces the problem.** The claim vocabulary was taken from the **Lichess
motif taxonomy**, deliberately and for a good reason — it lets detectors be validated against the CC0
puzzle database ([[experiments.e86-detector-audit]]). But that taxonomy classifies **what happened on
the board**, not **what the player is missing**. It is a taxonomy of positions, and it was used as a
taxonomy of gaps. Those are different things, and only the second one varies between players of equal
strength.

## The design direction

**Split along lines where players actually have gaps.**

| currently split by | which is | better split by |
|---|---|---|
| `endgame_error` → material class | **knowledge** ✓ already right | — |
| `out_of_book` → one number | knowledge, not split at all | **per opening** — "you leave book on move 6 in the French and move 14 in the Italian" |
| `concedes_weakness` → isolated / doubled / backward | a taxonomy of **what is on the board** | **per structure** — IQP, Carlsbad, hanging pawns: each is a subject with its own plans |
| `missed_motif` → fork / pin / skewer | slices of **one skill** | keep as *evidence*, not as a diagnosis |

Three further routes, in descending order of evidence:

1. **Measure exposure, not only conditional rate.** E84 found players meeting time pressure 5.4× a
   game against peers' 0.4 while handling it *better* once there. *"You are in time trouble
   constantly"* separates; *"you handle time trouble badly"* may not. Exposure is a choice; conditional
   skill tracks rating.
2. **Compare a player against their own past** (V7). *"You have got worse at this"* needs no
   between-player variance at all and sidesteps the whole problem. The regression-to-the-mean
   machinery already exists, held out at 15 % (R-15).
3. **Interaction claims, with the held-out rule enforced.** *"You miss forks when short of time"* may
   vary where the main effect does not — and this is the route most likely to manufacture false
   positives. E03's phase-stratified backward pawn had a 2.40 lift and a tidy mechanism, and
   **reversed to 0.76 on held-out players**.

**Deeper histories help only `skewer` and `backRankMate`**, which failed on power rather than
flatness ([[experiments.e83-spread-rescreen]]'s MDE analysis separates the two). More data cannot
create variance that is not there.

## Nothing built is wasted

The tactical detectors are accurate about individual positions — that is what the audit tests — they
simply cannot rank players. So they become the **evidence** under a separating claim rather than the
diagnosis itself:

> *"Your errors cluster in the opening (3.9×). Here are three of them, and two were forks you
> allowed."*

The separating claim carries the diagnosis; the tactical detector supplies the position a player can
check on a board (V8).

## Separation is necessary, not sufficient

`plays_queenless` separates at **36.9×** and **nobody should be coached about it**. It is a style
tendency: how much of a player's game is spent with the queens off. [[experiments.e14-style-dimensions]]
screened six candidate tendencies on 84 players against two bars — a dimension must vary between
players *and* be uncorrelated with rating, because a tendency that rises with strength is strength
wearing a friendlier name. **Four of six were strength in disguise** (captures, checks, game length,
material kept, all correlating 0.47–0.56). Queenless share survived at correlation **−0.069**.

It is measured, real, and independent of strength — and it is a **description**, not a gap. E14 also
tried to measure whether the preference *suits* the player and found every player errs about 20 % less
with queens off, so `style.py` deliberately refuses to say whether it is working for them.

**A claim worth making needs three things:** players differ on it, it costs something, and it is
learnable. This screen tests only the first.

## Honest limitations

- **One corpus, one depth, mostly one stratum.** `best_within_band` reports the largest stratum, which
  is `1400-1800|blitz` for most claims. A claim flat there could separate in another band.
- **The families are my grouping**, not a measured taxonomy. `material care` holding three claims and
  `style` holding one makes the percentages coarse.
- **This says nothing about coachability.** The strongest separator in the whole set is the one claim
  the project explicitly refuses to coach.
