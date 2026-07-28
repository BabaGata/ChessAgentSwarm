---
id: cas-exp-e01
title: 'E01 — Engine throughput & diagnosis stability'
desc: 'How long analysis takes on the target machine, and whether analysis depth changes the diagnosis or only the evaluation.'
updated: 1785255100000
created: 1785255100000
---

# E01 — Engine throughput & diagnosis stability

**Answers:** A1, A2 in [[open-questions]] · **Code:** `experiments/e01-engine-throughput/`
**Date:** 2026-07-28 · **Status:** done

## Setup

| | |
|---|---|
| Engine | Stockfish 18, AVX2 build, `C:\stockfish` |
| Machine | 20 logical cores, Windows 11 |
| Sample | 59 rated rapid/classical games fetched from the Lichess API, from 3 players rated 1489–1788 (the [[open-questions]] B1 target band) |
| Method | one engine evaluation per position; the loss for a move is the drop in the mover's win probability between the position before and after it |
| Classification | win-probability points: inaccuracy ≥10, mistake ≥20, blunder ≥30; evals clamped at ±1000cp; a move matching the engine's own first choice scores zero loss (L-005) |
| Hash | 256 MB per engine process |

Games are **not** committed (see [[experiments]] conventions); `fetch_games.py` reproduces an
equivalent sample.

## A1 — Throughput

### Finding 1: more engine threads made analysis *slower*

Depth 15, five games (482 positions), one engine at a time:

| Threads | Seconds per position | Relative |
|---|---|---|
| **1** | **0.064** | 1.0× |
| 4 | 0.146 | 2.3× slower |
| 16 | 0.186 | 2.9× slower |

At a **fixed depth**, extra threads widen the search rather than reaching the target depth sooner,
and synchronisation overhead dominates on analyses this short. Threads help when the limit is *time*;
they hurt when the limit is *depth*.

**Consequence:** spend cores on more games at once, not more threads per game. One engine thread per
process, many processes.

### Finding 2: whole-game analysis is cheap

Ten games (980 positions), 18 worker processes, one thread each:

| Setting | s/position | Wall clock, 10 games | **Projected wall clock, 50 games** |
|---|---|---|---|
| depth 12 | 0.031 | 5.4 s | **27 s** |
| depth 15 | 0.134 | 17.9 s | **89 s** |
| depth 18 | 0.624 | 80.6 s | **403 s** (6.7 min) |
| depth 20 | — | *not completed* | see finding 3 |

A player's entire recent game history can be analysed in **under two minutes at depth 15**, or seven
minutes at depth 18, on an ordinary laptop, for **zero cash cost**.

### Finding 3: wall time is dominated by the longest game

The depth-20 run never finished. Nine of ten games completed quickly; the tenth — 182 positions —
ran alone for roughly 27 CPU-minutes. Because work was parallelised **per game**, all other cores sat
idle waiting for it.

**Consequence:** parallelise per *position*, not per game. Otherwise throughput is set by the single
longest game in the batch, and adding cores does not help.

## A2 — Does depth change the diagnosis?

30 games, all labels compared against depth 18 as reference (depth 20 was unaffordable per finding 3;
depth 18 is a *reference*, not ground truth).

| Cheap setting | Exact label agreement | Blunder-set agreement |
|---|---|---|
| depth 12 | 61.3 % | 69.2 % |
| **depth 15** | **73.6 %** | **83.7 %** |
| 100 ms/move | 64.4 % | 81.6 % |

About 250 labelled errors across 30 games (~8 per game).

### The result, honestly stated

**Depth materially changes the diagnosis — it is not merely a change of evaluation.** Even between
depth 15 and depth 18, roughly a quarter of error labels disagree, and one blunder in six is seen by
one setting and not the other. Depth 12 is clearly too coarse.

Most disagreement is at threshold boundaries (a move landing just either side of the
inaccuracy/mistake line) and in moves labelled by one setting only — but that is exactly the point:
**a single move's label is not a stable fact.**

### Consequence — this is the important one

**Per-move claims are unreliable; aggregate claims are not.** A coach that says *"your move 23 was a
blunder"* is making a statement that a modest change in analysis depth would contradict about 16 % of
the time. A coach that says *"you missed knight forks nine times across six games"* is on solid
ground, because threshold noise averages out over many instances while a genuine recurring weakness
does not.

This independently justifies the design direction already suggested by prior art
([[domain.prior-art]]): diagnosis must be **aggregate and recurrence-based**, with the
minimum-sample rule of open question C2 doing real work. It also means the swarm must **never**
present a single move's classification as a fact without hedging.

### Working setting

**Depth 15 for routine analysis, depth 18 when a specific position is being discussed.** Depth 15
gives the best stability-per-second (89 s for 50 games at 84 % blunder agreement with depth 18);
depth 12 saves little in absolute terms and costs a lot of agreement. A fixed 100 ms/move is roughly
as stable as depth 12 but with less predictable behaviour, so depth-based limits are preferred.

Whatever is chosen must be **recorded with every stored analysis** — labels are not comparable across
depths, so a profile built at depth 12 cannot be merged with one built at depth 18.

## Consequences summary

| Affected | Change |
|---|---|
| **A1** | resolved — cost is negligible; C1 is comfortably satisfied for the deterministic layer |
| **A2** | resolved — depth changes diagnosis; per-move labels are unstable, aggregates are robust |
| **C5** ([[decisions.0002-compute-first-speak-last]]) | supports acceptance: the deterministic layer is affordable enough to carry the diagnostic load |
| **C2** minimum-sample policy | promoted from "good practice" to **necessary** — it is what makes claims survive analysis-parameter changes |
| **C4** precompute vs per-player | per-player engine analysis is cheap enough that little needs precomputing; the expensive precomputation is the puzzle/opening corpora, not the player's games |
| [[domain.signals]] | analysis depth must be stored alongside every derived signal |
| Architecture | parallelise per position; store the engine settings with the results |
