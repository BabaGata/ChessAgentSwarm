---
id: cas-exp-e04
title: 'E04 — Motif detector precision'
desc: 'Do the tactical detectors fire sensibly on real games? Two were badly over-firing, and base rates found them.'
updated: 1785312400000
created: 1785312400000
---

# E04 — Motif detector precision

**Gate for:** [[capacity.agents.s1-tactical-gaps]] — detectors may not be used until measured
**Code:** `experiments/e04-motif-precision/` · **Date:** 2026-07-31 · **Status:** done

## Question

Unit tests prove each detector matches its stated definition. That is not the same as being *right*
on real boards. The design note named the expected failure mode — **over-firing** — on the strength
of prior art's skewer detector firing 10–18× too often and E02's finding that plausible-looking
detector code fires far too readily.

## Method

Eight detectors run over the **engine's best move** at every position after the opening, across
**807 games / 51,422 positions** from 38 players, reading best-moves straight from the depth-15
cache so no engine was needed. Then base rates per motif, and a stratified hand-checked sample.

Base rates are the cheap screen: a motif that fires implausibly often is over-firing, and you do not
need to inspect anything to suspect it.

## Result — two detectors were badly wrong

| Motif | Before | **After** | |
|---|---|---|---|
| hangingPiece | 11.25 % | **6.51 %** | pawns excluded |
| trappedPiece | 8.67 % | **1.34 %** | ~6.5× reduction |
| pin | 6.41 % | 6.41 % | unchanged |
| fork | 3.62 % | 3.62 % | unchanged |
| capturingDefender | 2.68 % | 2.68 % | unchanged |
| discoveredAttack | 2.43 % | 2.43 % | unchanged |
| skewer | 0.95 % | 0.95 % | unchanged |
| backRankMate | 0.38 % | 0.38 % | unchanged |

### `trappedPiece` — "every escape is covered" is vacuously true when there are none

It fired on an **undeveloped a1 rook**, boxed in by its own knight and pawn. `all(...)` over an empty
list is `True`, so any attacked piece that had never moved counted as trapped. That single mistake
accounted for most of an 8.67 % base rate.

Trapped means *it had somewhere to go and we took it away*. Two constraints added: the piece must
**have** escape squares, and must be **winnable** — undefended, or attacked by something cheaper.

**The bug was also in my own positive test.** The original case was a bishop on a8 walled in by its
own b7 pawn — an instance of exactly the thing being ruled out. It was replaced with a real trap: a
knight on h8 whose only squares, f7 and g6, are covered by pawns.

### `hangingPiece` — most firings were free pawns

Two of three sampled firings were pawn grabs (`Qxb4`, `Bxb3`). Technically correct, and not what the
motif means: *"you hang pieces"* is not a claim about pawns. Dropping pawns is a real weakness and a
different one. Captures below minor-piece value are now excluded.

## Hand-verification after the fixes

| Motif | Checked | Correct |
|---|---|---|
| pin | 3 | **3** — including two absolute pins of a pawn against the king |
| skewer | 3 | **3** — e.g. `Qh4` hitting the queen on g3 with the rook on e1 behind it |

**Not individually hand-verified this pass:** fork, discoveredAttack, capturingDefender,
backRankMate. Their base rates are plausible and their unit tests pass, which is weaker evidence
than the six above. Stated rather than glossed.

## Consequences

| Affected | Change |
|---|---|
| `chesscoach/tactics.py` | two definitions tightened; three new tests, one replacing a wrong one |
| [[capacity.agents.s1-tactical-gaps]] | the §4 gate is met for pin and skewer; partially met elsewhere |
| S1 | may proceed — but base rates are now known, and any claim built on `pin` or `hangingPiece` starts from a 6 % population rate, which is precisely why peer comparison exists |

## Honest limitations

- Precision was measured **against my own definitions**, not against expert judgement. A titled
  player might disagree with the definitions themselves.
- Six hand-checked detections is enough to show two detectors are not broken; it is not a precision
  figure to any accuracy.
- Only the **engine's best move** was classified. Motifs available on second-best moves are invisible
  to this measurement, which is the known limitation already recorded in the S1 design note.
- The external check against the CC0 puzzle themes — the strongest available evidence, because the
  labels are independent — is **not yet done**.
