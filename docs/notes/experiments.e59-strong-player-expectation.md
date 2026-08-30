---
id: cas-exp-e59
title: 'E59 — Two of the four development signals separate a 1600 from a 2600, and one is backwards'
desc: '5,917 games from the top-100 rapid players supply the expectation. Coverage is good (90 % of subject games), late castling and repeat moves discriminate at AUC 0.73 and 0.70 — and pawn share runs the wrong way: strong players push MORE pawns in the opening, not fewer.'
updated: 1788825600000
created: 1788825600000
---

# E59 — Building the expectation from players who know the openings

**Answers:** [[design.opening-development-signals]] · **Code:**
`experiments/e58-opening-development/{fetch_strong,expectations,separation}.py` · **Date:**
2026-08-30 · **Status:** three questions answered — **two signals survive, one is inverted, and one
of my own calibrations was mis-specified**

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

### Pawn share is backwards

**AUC 0.25 is not noise — it is a strong signal pointing the other way.** Strong players spend
**38 %** of their opening moves on pawns; the 1600s spend **34 %**. Only 17 % of subjects exceed the
strong players' 75th percentile, where 25 % would be expected by chance.

The hypothesis was:

> *"beginner players... move too many pawns unnecessarily"*

In this data they move **fewer**. A plausible reading — and it is a reading, not a finding — is that
strong players choose openings built on pawn play (Sicilian, French, Queen's Gambit) and execute
their breaks on time, while weaker players shuffle pieces instead. The per-opening table supports
this indirectly: strong and subject pawn shares are nearly identical *within* most families, so the
difference is largely which openings get played rather than how they are played.

**`pawn_moves_in_opening` cannot ship as designed.** Inverted, it would say *"you push too few
pawns"*, which may be true and is a strange thing to tell a 1600 without a chess reason. That is the
author's call.

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

## Consequence

- **Two claims proceed**: `late_castling` and `repeat_move_in_opening`, against a per-opening
  expectation from strong players, with the author's +1/+2 tolerance.
- **`pawn_moves_in_opening` is held**, pending the author's judgement on a signal that discriminates
  well in the direction opposite to the hypothesis.
- **`slow_development` is not yet separately tested** — it shares most of its content with late
  castling and must go through the same test before it is built.
- **The own-median fallback is confirmed necessary** and scoped: 4 families, 10 % of games.

## Honest limitations

- **100 players, not 200** — the leaderboard cap. Per-family counts are half what was planned.
- **2556–2932 is elite, not "knows the opening".** Some of the gap is strength rather than knowledge,
  and nothing here separates those. The peer step is what is supposed to, and it has not run yet.
- **AUC here compares strong against subjects, which is not the claim's job.** The claim compares a
  subject against *peers*. A signal separating 1600 from 2600 might still fail to separate 1600 from
  1600, and that test needs the peer reference rebuilt.
- **The subject corpus is rapid only**, and every figure here would move on blitz.
- **`_family` files a game by the deepest named position reached**, so transpositions land where they
  ended rather than where they began.
