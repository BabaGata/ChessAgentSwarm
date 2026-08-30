---
id: cas-exp-e59
title: 'E59 — Late castling survives the composition check; repeat moves halves; pawn moves are nothing'
desc: '5,917 games from the top-100 rapid players supply the expectation. The first separation test pooled openings and was confounded by which openings each population plays — the author caught it. Standardised: late castling holds at +9.8 pp, repeat moves halves to +2.0 pp, and pawn moves collapse to a coin.'
updated: 1788825600000
created: 1788825600000
---

# E59 — Building the expectation from players who know the openings

**Answers:** [[design.opening-development-signals]] · **Code:**
`experiments/e58-opening-development/{fetch_strong,expectations,separation,composition}.py` ·
**Date:** 2026-08-30 · **Status:** **one signal survives at full strength, one at half, one is
dropped** — read the composition section below before the separation table above it, which is
confounded and kept only to show what the confound did

## The corpus

> *"I don't want this to be built by peer reference but by better players who usually know the
> opening."*

**5,917 rated rapid games from 100 players rated 2556–2932**, taken from the public Lichess rapid
leaderboard. A public list rather than a band this project chose, so the selection cannot be tuned
toward a wanted answer; public usernames and public rated games only (R-10).

**The leaderboard endpoint caps at 100**, not the 200 requested. Noted because the reference is
half the intended size and the per-family counts below are what that bought.

## 1. Coverage — good, and the fallback was correctly predicted

| | |
|---|--:|
| subject families with 20+ games | **26** |
| of those, covered by 20+ strong games | **22** |
| share of subject games covered | **90 %** |

**The four that fall through are exactly the openings strong players do not play**: King's Pawn Game
(unclassified 1.e4 e5 sidelines, 9 strong games), Horwitz Defense (13), Van't Kruijs Opening (4),
Englund Gambit (10).

The author required the own-median fallback for *"openings that no other players from the corpus
play"* before any of this was measured. It is needed, it is needed for precisely the openings
predicted, and it carries **10 %** of subject games rather than the majority — so the main path is
the strong-player expectation and the fallback is genuinely a fallback.

## 2. The tolerance — and a calibration of mine that was wrong

The design proposed choosing between **+1** and **+2** by requiring that the threshold flag **≤ 25 %**
of the strong players' own games, on the reasoning that they are a known-good population.

**Nothing cleared it:**

| tolerance | +0 | +1 | +2 |
|---|--:|--:|--:|
| strong games called late (castling) | 43 % | 35 % | **29 %** |
| strong games called late (development) | 45 % | 39 % | **34 %** |

**The ceiling was the wrong test, and it was mine, not the author's.** It treats the threshold as a
per-game verdict whose false positives must be rare. The claim is nothing of the sort: it is a
**per-player rate compared with peers**. Strong players late 29 % of the time and a weak player late
70 % of the time is a perfectly good signal — a high base rate costs nothing as long as the two
populations differ. What kills a signal is firing *equally* on both, which is what E10 closed a
section slot for.

So the ceiling is withdrawn and replaced with a separation test. **The author's +1/+2 stands**; it is
not chosen by false-positive rate but it remains necessary for the reason they gave, since a
threshold at the bare median flags half the population it came from by construction.

## 3. Separation — the test that decides it

Each player's own rate, strong and subject scored against the **same** strong-player expectation.
AUC is the chance a random subject scores worse than a random strong player: 0.50 is a coin.

| signal | strong | subject | above strong p75 | AUC |
|---|--:|--:|--:|--:|
| **late castling** | 29 % | 42 % | 68 % | **0.73** |
| **repeat share** | 31 % | 36 % | 58 % | **0.70** |
| pawn share | 38 % | 34 % | 17 % | **0.25** |

**Late castling and repeat moves survive.** Both discriminate at a level that can carry a claim, and
`repeat share` is the direct measurement of the author's own description — *"beginner players tend to
not develop pieces but move already developed pieces"*.

### Pawn share looked backwards — and this reading was wrong

> **Superseded by the composition section below.** Kept because the mistake is the useful part.

The reading at the time was that AUC 0.25 is a strong signal pointing the other way: strong players
spend 38 % of opening moves on pawns against the subjects' 34 %, so beginners push *fewer* pawns, and
the claim would have to be inverted before it could ship.

**Two things were wrong with that.** The table pools every game a player played, so it cannot tell a
difference in *which openings* from a difference in *how one is played* — which the author asked
about immediately. And *share* is not the quantity the hypothesis is about: it divides by the window,
and the window differs between the populations.

Corrected, the pawn signal is not inverted. It is **absent**.

## The per-opening gap is small in the middle and large at the edges

Median gap across 44 (family, colour) cells: **+1.0 move**, with subjects later in 29 of 44 — so in
**15 cells the subjects castle earlier than the elite do**.

But the spread is what matters, and it is where the per-opening design earns its keep:

| | gap |
|---|--:|
| Philidor Defense, Black | **+8** |
| Zukertort Opening, White | **+7** |
| Queen's Gambit Accepted, White | **+5** |
| Nimzo-Larsen Attack, Black | **+5** |
| Vienna Game, White | **−3** |

A single global threshold would average these to nothing. This is the strongest evidence yet for the
author's instruction that norms be per opening.

## The author caught a confound, and it changes two of the three results

> *"Is pawn share checked averaged among all tested openings or opening by opening? My concern is that
> weaker players maybe play more commonly openings with not many pawn moves while stronger players
> more commonly play openings with more pawn moves, but when they play the same opening stronger
> players might have less pawn moves before castling."*

**The separation test above pooled every game a player played**, so a difference in the *mix* of
openings was indistinguishable from a difference in *play*. Two tests separate them: direct
standardisation, which scores both populations under the same opening mix, and paired within-family
differences, which never let one mix touch the other.

**They also exposed a second flaw.** E59 measured pawn *share*, but the hypothesis is about how many
pawn moves happen before the pieces come out. Share divides by the window, and the window differs
between the populations — so share can fall while the count rises. Both are now reported, plus a
censoring-free variant counted over a fixed first ten moves, since the completed-games filter
excludes exactly the games where development goes worst.

Over 36 (family × colour) cells, 6,602 strong and 2,070 subject games:

| | crude | standardised | within-opening median | subjects higher in |
|---|--:|--:|--:|--:|
| **late castling** | +11.3 pp | **+9.8 pp** | +10.8 pp | **30 / 36** |
| **repeat-move share** | +4.0 pp | **+2.0 pp** | +1.7 pp | 26 / 36 |
| pawn share | −2.8 pp | −1.2 pp | −0.9 pp | 7 / 36 |
| **pawn count before ready** | −0.35 | **−0.13** | −0.05 | **17 / 36** |
| pawn count, first 10 moves (uncensored) | −0.34 | −0.13 | −0.17 | 10 / 36 |
| opening window, moves | +0.17 | +0.18 | +0.29 | 22 / 36 |

**The author was right, and it matters:**

- **Late castling survives almost intact** — 11.3 → 9.8 pp, and subjects are later in **30 of 36**
  openings. This is a within-opening effect, not a repertoire artefact. It is the real signal.
- **Repeat moves halves.** Half of its crude gap was composition, and what remains is **+2.0 pp**.
  Still consistent (26 of 36) but far weaker than E59 reported, and it must be presented as such.
- **Pawn moves are not inverted. They are nothing.** On *count*, once the opening is held fixed, the
  populations are indistinguishable — **17 of 36** is a coin, and the median difference is 0.05 pawn
  moves. The censoring-free check agrees, so the completed-games filter was not hiding it.

**Why "share" looked inverted, mechanically:** subjects push the *same number* of pawns but take
**+0.29 moves longer** to finish developing. Same numerator, larger denominator, smaller share.

**So pawn share is not a measure of pawn behaviour** — it is partly a measure of window length, and
it should not be used at all. That is a defect in the metric rather than a finding about players, and
it was invisible until the count was reported beside it.

## Consequence

- **`late_castling` proceeds.** +9.8 pp standardised, 30 of 36 openings — the one signal that is
  clearly about how an opening is played rather than which one is chosen.
- **`repeat_move_in_opening` proceeds at half strength**, +2.0 pp standardised. Worth building, worth
  stating honestly, and a candidate to fail the peer step where late castling probably will not.
- **`pawn_moves_in_opening` is dropped, not held.** No within-opening effect on the measure that
  matches the hypothesis, and the measure that appeared to show one was contaminated by window
  length. Nothing here is worth telling a player.
- **`slow_development` is not yet separately tested** — it shares most of its content with late
  castling and must go through the same test before it is built.
- **The own-median fallback is confirmed necessary** and scoped: 4 families, 10 % of games.

## Honest limitations

- **100 players, not 200** — the leaderboard cap. Per-family counts are half what was planned.
- **2556–2932 is elite, not "knows the opening".** Some of the gap is strength rather than knowledge,
  and nothing here separates those. The peer step is what is supposed to, and it has not run yet.
- **AUC here compares strong against subjects, which is not the claim's job.** The claim compares a
  subject against *peers*. A signal separating 1600 from 2600 might still fail to separate 1600 from
  1600, and that test needs the peer reference rebuilt. **The AUCs in the table above are also
  pre-standardisation** and are therefore upper bounds — the standardised columns are the honest ones.
- **Standardisation controls for the opening family, not for the position.** Two Sicilians can be
  different games, and a family is a coarse stratum.
- **The subject corpus is rapid only**, and every figure here would move on blitz.
- **`_family` files a game by the deepest named position reached**, so transpositions land where they
  ended rather than where they began.
