---
id: cas-exp-e69
title: 'E69 — Four development claims, four signals, and one pair close to the line'
desc: 'The screen the design note promised before the claims shipped. No pair exceeds the 0.85 ceiling, so all four may ship — but slow_development and repeat_move sit at 0.81, and the pair E59 measured at 0.68 has since risen to 0.75 because the detectors changed underneath it.'
updated: 1788210000000
created: 1789171200000
---

# E69 — Are the development claims one signal or several?

**Answers:** [[design.opening-development-signals]]'s promised correlation screen ·
**Code:** `experiments/e69-development-correlations/` · **Date:** 2026-08-31 ·
**Status:** done — **all four ship, and one pair is worth watching**

## The commitment being honoured

The design note said this before any of the claims shipped:

> *"Whether all four survive is not an argument to win — it is a number to measure... If two exceed
> |r| > 0.85 across the review corpus, they are one signal with two names and only the more
> actionable one ships."*

E59 checked one pair and left the rest. Five detector corrections have landed since, so even that
number was stale.

**No engine pass was needed.** The peer reference stores per-player instances and opportunities for
every claim, which is exactly a per-player rate — so the screen reads the artefact that already
exists, and it is current by construction because the reference was rebuilt at HEAD.

## The development claims against each other

80–83 players, at least 10 opportunities each.

| pair | r | verdict |
|---|--:|---|
| `slow_development` / `repeat_move` | **0.81** | distinct, **narrowly** |
| `slow_development` / `late_castling` | 0.75 | distinct |
| `late_castling` / `repeat_move` | 0.75 | distinct |
| `slow_development` / `pawn_error` | 0.20 | distinct |
| `late_castling` / `pawn_error` | 0.29 | distinct |
| `repeat_move` / `pawn_error` | 0.16 | distinct |

**No pair exceeds the ceiling, so all four ship.** But two things deserve saying rather than being
buried under a pass:

**0.81 is not comfortably under 0.85.** `slow_development` and `repeat_move` share most of their
variance, which is unsurprising — a player who keeps moving the same piece is a player who takes
long to develop — and the ceiling was set in advance precisely so this decision would not be made by
eye. It passes. It would not take much for it not to.

**The pair E59 measured at 0.68 is now 0.75.** Nothing about the claims changed; the detectors
underneath them did, five times. A correlation measured before a correction is a fact about code
that no longer exists — the same lesson as the detection sheet's stamp, in a different artefact.

**`pawn_error` is the outlier, and it earns its place**: 0.16–0.29 against the other three, and a
median rate of 6 % against their 41–46 %. It is rare and independent, which is exactly what a fourth
claim should be if it is to be worth a slot.

## And against the claims they might be restating

A development claim that tracks the general opening error rate teaches nobody anything — E10 closed a
section slot at +0.917.

| | vs `early_error` | vs `endgame_error` |
|---|--:|--:|
| `slow_development` | 0.55 | 0.10 |
| `late_castling` | 0.46 | 0.01 |
| `repeat_move` | 0.54 | 0.14 |
| `pawn_error` | 0.35 | 0.22 |

**All well clear.** The development claims share about a quarter to a third of their variance with
the general opening error rate, which is what you would expect of two measures of the same phase, and
nothing like restatement. Near-zero against `endgame_error`, which is the sanity check: a claim about
the opening should not track one about the endgame, and none does.

## Consequence

- **All four development claims ship.** The screen the design note promised has been run and it
  passed.
- **`slow_development` / `repeat_move` at 0.81 should be re-run** whenever either detector changes.
  It is the pair most likely to cross.
- ~~**One item of the screen is still not done**~~ **— run 2026-08-31**
  → [[experiments.e75-book-depth]]. Book depth needed its own per-player measure because it is not a
  claim in the reference; computed over 84 players it correlates **−0.47** with `slow_development`,
  well under the ceiling, and is **reliable at split-half +0.81**. Every pair this note named has now
  been screened.

## Honest limitations

- **Correlation over 80 players with ~20 games each.** An r of 0.81 from this sample has a real
  interval around it and the ceiling is treated as a bright line, which it is not.
- **The claims are correlated because players are.** A weak player is late, repetitive and slow at
  once, so some shared variance is the band rather than the claims — and this screen cannot separate
  those.
- **Passing the screen is not evidence any of them is right.** It says they are four different
  things, not four true things.
