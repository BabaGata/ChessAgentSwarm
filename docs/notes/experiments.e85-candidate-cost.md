---
id: cas-exp-e85
title: 'E85 — The candidate cost is about ten minutes, and half of it is pins'
desc: 'The blocking measurement for the punishment-validity design. detect_motifs already removes 93 per cent of replies for free, leaving 1.52 engine evaluations per error position — roughly 31,000 for the blitz and rapid reference and ten minutes of wall clock. Half the bill is one motif.'
updated: 1788660000000
created: 1788660000000
---

# E85 — What pricing the candidates would actually cost

**Answers:** the blocking measurement named in [[design.punishment-validity]] ·
**Code:** `experiments/e85-candidate-cost/` · **Date:** 2026-09-05 ·
**Status:** done — **the design is affordable, and the cost has a shape worth knowing**

## The question

[[design.punishment-validity]] proposes counting a punishment when *some* reply within a
win-probability window of the best executes the motif, rather than only the single best reply. That
needs an evaluation of each **candidate** reply, and the design could only bound the bill between
**8,000 and 80,000 evaluations** — a spread too wide to build on. It named the measurement as the
first task rather than the second.

## What the free filter removes

`detect_motifs` **is** the static filter. A move only becomes a candidate by passing the material
checks the detectors already apply — `_lands_safely`, `_is_worth_winning`,
`_loses_material_whatever_the_defender_does` — so nothing new had to be written to filter, only
counted.

Fifteen players, **3,324 error positions with a usable reply**:

| per error position | mean | median | p90 | max |
|---|--:|--:|--:|--:|
| legal replies | 31.7 | 33 | 44 | 57 |
| **executing a motif** (survive stage 1) | **2.1** | 1 | 5 | 46 |
| **still needing an engine call** | **1.5** | 1 | 4 | 44 |

**Stage one removes 93 % of replies and costs nothing.** Of the 2.1 that survive, a further 0.6 are
free because the *best* reply already executes them — and the best reply's evaluation is already
stored, so those motifs are priced by data that exists.

## The bill

| | |
|---|--:|
| candidate moves | 7,131 |
| free (the best reply's own motifs) | 2,056 |
| needing an evaluation | 5,075 |
| **distinct (position, move) pairs** | **5,047** |
| **distinct evaluations per error position** | **1.52** |

Stable across sample sizes: **1.48** on 3 players (667 positions), **1.52** on 15 (3,324). The
estimate is not delicate.

| rebuild | evaluations | at E01's depth-15 throughput |
|---|--:|--:|
| the blitz + rapid reference (~20,600 errors) | **31,300** | **≈ 10 minutes** |
| all three bands, overlapping (~2×) | **62,600** | **≈ 19 minutes** |

[[experiments.e01-engine-throughput]] measured 980 positions in 17.9 s at depth 15 with 18 worker
processes — about **55 positions per second**. Against a band rebuild that already takes about fifty
minutes, this is a **20–40 % addition**, not a new order of magnitude. **C1 holds comfortably.**

The measurement itself cost **nothing**: 33,767 of 33,767 cache lookups hit.

## Half the bill is one motif

| motif | priced | share |
|---|--:|--:|
| **`pin`** | **2,485** | **49 %** |
| `trappedPiece` | 1,257 | 25 % |
| `discoveredAttack` | 687 | 14 % |
| `hangingPawn` | 480 | 9 % |
| `capturingDefender` | 221 | 4 % |
| `hangingPiece` · `skewer` · `fork` | 171 | 3 % |

**Two motifs are 74 % of the engine budget.** Pins are very often available as a non-best move —
which is a fact about chess, not about the design, and it is the single biggest lever on the cost.

The distribution also inverts between free and priced. `hangingPawn` and `hangingPiece` are mostly
executed by the *best* reply, so they are nearly free: when a piece hangs, taking it usually **is**
best. Pins and trapped pieces are usually available but not best, so they carry the cost. That is the
same asymmetry E84 found under D2, seen from the other side.

## The obvious saving is circular, and should not be taken

Most of the priced budget goes to claims that **currently do not separate players** —
`allowed_motif.pin`, `.discoveredAttack`, `.capturingDefender`, `.skewer` and `.fork` are all in the
[[experiments.e84-band-references]] register. Skipping them would cut the bill by roughly two thirds.

**It would also guarantee never learning whether the new rule fixes them.** Those claims are flat
*under the current rule*, and the whole argument for the rule is that the current one mismeasures
them. Declining to price a claim because the measurement it is meant to repair says it is flat is
[[learning.lessons]] L-051 exactly: a test written against a threshold is evidence about that
threshold, and this would be a budget written against one.

**The cheap version of this experiment is the one that cannot answer the question.** At ten minutes,
there is no reason to take it.

## Honest limitations

- **Extrapolation, not a run.** 3,324 error positions were measured and ~20,600 projected, on the
  assumption that the sampled players are typical of the corpus. They are the first fifteen files
  alphabetically, not a random draw.
- **The throughput figure is borrowed.** E01 measured *game* positions in sequence with 18 workers.
  Candidate positions are one-off and share nothing, and mid-game tactical positions may search
  slower than the average position in a game. **Ten minutes is an estimate from a measured rate, not
  a measured wall clock**, and the first real run should report its own.
- **This prices Option 3 only.** Option 4's principal-variation window needs search beyond one reply
  and is not costed here — deliberately, since the design defers it.
- **`wp(stand)` is free** and was not counted, correctly: the position's own evaluation before the
  reply is already stored on the observation.
