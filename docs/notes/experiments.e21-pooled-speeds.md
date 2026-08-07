---
id: cas-exp-e21
title: 'E21 — Pooling speeds takes a 24-game history from 50% advised to 79%'
desc: 'The first change in the sequence to move coverage the right way, and it moves it a long way: more players, more claim kinds, overlap unchanged.'
updated: 1786492800000
created: 1786492800000
---

# E21 — Pooling speeds

**Answers:** step 5 of [[design.short-history-prioritisation]] · **Date:** 2026-08-06 ·
**Status:** done — **built and shipped**

## Question

[[experiments.e16-shallow-corpus]] found the binding constraint is **events per corpus**, not the
policy. Three attempts to fix it at the policy end had failed by this point — D12's floor,
peer-relative cost, and shrinkage ([[experiments.e20-shrinkage]], which halved coverage). E19 showed
blitz is the same player, and the fetch was discarding a median **82 %** of every player's games.

## What was built

**Pool the evidence, stratify the baseline.**

- `chesscoach/speed.py` — Lichess's own classification, by *estimated duration* (initial + 40 ×
  increment), so 3+2 is blitz and 5+5 is rapid. Reimplemented because the swarm works from PGN,
  where only the `TimeControl` tag survives.
- `Corpus.speed_mix` — the share of a player's games at each speed.
- `SectionContext._mixed` — **direct standardisation**. A claim's baseline is the population rate at
  each speed, weighted by how much of that speed *this player* actually plays. A blitz-heavy player
  is compared against what peers do at a blitz-heavy mix, never against a rapid-only population.
- `build-peer-reference --merge-with`, because a reference has to span every speed a player might
  bring. Cells are keyed by time control, so merging adds strata rather than blending them.
- `DIAGNOSTIC_PERF_TYPES` now includes blitz.

E01's rule is **kept, not overruled**: rates are still never compared across speeds. What pools is
the evidence, which is not what E01 was about.

## Result

Same 84 players, truncated to 24 rapid games — the realistic shallow case — with and without their
blitz games pooled in:

| at 24 rapid games | rapid only | **+ blitz pooled** |
|---|--:|--:|
| **players advised** | 42 — **50 %** | **66 — 79 %** |
| distinct claim kinds | 20 | **25** |
| mean pairwise overlap | 0.08 | 0.09 |
| groundedness | 70/70 | **113/113** |
| priorities per player | never > 2 | never > 2 |
| silent players with nothing to say even with more games | — | **0 of 18** |

**Coverage rises by more than half, claim variety rises with it, and overlap is unchanged.** The
extra advice is not the same thing said to more people — there are *more distinct claims*, which is
the opposite of what buying coverage with generic output looks like.

This is the first change in the whole sequence to move coverage in the intended direction, and it is
the one E16 pointed at from the beginning.

## Why the policy attempts failed and this did not

Every earlier attempt tried to make the confidence policy more generous about the evidence it had.
The policy was not being stingy — the evidence genuinely was not there, which is why the *better*
estimator (E20) was *stricter*. Adding four games for every one changes the input rather than the
verdict, and the same policy then finds enough to speak about.

Recorded as a pattern rather than a one-off: **three failures at the policy end and one success at
the supply end** is the strongest evidence in the project for where the constraint really lives.

## Honest limitations

- **Overlap did rise, from 0.08 to 0.09.** Small, and against a rise in claim kinds, but it is not
  zero and the trend is worth watching if more speeds are ever admitted.
- **Bullet is untested and excluded.** Somewhere below blitz, "the same player, hurrying" becomes a
  different game. E19 located that boundary below rapid and no further, so the line sits where the
  evidence stops.
- **The mix is weighted by games, not by opportunities.** It assumes a game offers about as many
  chances to go wrong at either speed. Cheap to revisit if a section ever tracks opportunities per
  speed; unlikely to matter while the speed gap itself is 1.06×.
- **~5× the games is ~5× the engine time for a fresh player**, and that is still not measured
  end to end. D9's cost figure is now optimistic and should be re-timed.
- **Coverage is not correctness.** 79 % of players are now told something; whether it is the right
  something is what [[vision]]'s success criterion 2 exists for, and remains untested.
