---
id: cas-exp-e91
title: 'E91 — The same games give a different diagnosis, because a fixed depth is not a fixed answer'
desc: 'Analysing one player twice produced different findings. The input was byte-identical, the evidence sampling is seeded, and the cache is homogeneous. The cause is the engine: at a fixed depth Stockfish returns -5 cp on a cold search and -24 cp for the same position after searching others, because the transposition table carries state.'
updated: 1788739200000
created: 1788739200000
---

# E91 — A fixed depth is not a fixed answer

**Found while:** verifying the clone-and-run story · **Date:** 2026-09-06 · **Status:** explained,
not fixed — **and not fixable here**

## What happened

The same 30 games of one player, analysed twice, produced different findings:

| claim | warm cache | fresh cache |
|---|--:|--:|
| `allowed_motif.capturingDefender` | 17 | 19 |
| `allowed_motif.hangingPiece` | 20 | 19 |
| `long_think_error` | **absent** | 59 |
| `missed_motif.hangingPawn` | 11 | **absent** |

The strength estimate moved from **1737** to **1710**.

## What it was not

- **Not the input.** Both runs read the same file, `md5 c5ecc7d7…`.
- **Not the evidence sampler.** It is seeded from a digest — `random.Random(int.from_bytes(...))` —
  and deliberately deterministic.
- **Not a mixed cache.** All 353,420 rows are depth 15 and `Stockfish 18`; there is no second engine
  or depth in it.
- **Not a code difference.** Both runs are the same commit.

## What it is

**A fixed depth is not a fixed answer.** The same position, same engine, same depth:

```
cold engine                              -5 cp   best = d4c5
after searching three other positions   -24 cp   best = d4c5
```

Stockfish's transposition table carries state between positions, so a search at depth 15 depends on
what the process searched before it. The cached evaluations were computed during the band builds, in
band order; a fresh run computes them in game order. **Different history, different number.**

19 centipawns is small, and most of the time it changes nothing. It changes something when a claim
sits near a threshold — which is what `long_think_error` and `missed_motif.hangingPawn` did here,
crossing the confidence gate in one run and not the other.

## What it means, and what it does not

- **A fresh clone is self-consistent.** It builds its own cache in its own order, so a user's re-runs
  agree with each other. The shipped cache is not distributed, so nobody inherits this.
- **Re-analysis can move a borderline claim.** Stated as a limitation rather than engineered around.
- **The peer reference and the player are not analysed in the same order**, so the comparison carries
  this noise too. It is averaged over thousands of positions per claim, which is why rates are stable
  even where a single evaluation is not.
- **This is not a determinism bug to fix.** Making it reproducible would mean a fresh engine process
  per position, which E01 measured as the expensive path, or clearing the table between positions,
  which throws away the speed that makes the whole thing free.

## Honest limitation

**One position, one comparison.** The mechanism is well known and the demonstration is real, but the
*size* of the effect across a corpus is not measured here — only that it is large enough to move a
claim across a gate at least twice in thirty games.
