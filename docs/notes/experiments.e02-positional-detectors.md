---
id: cas-exp-e02
title: 'E02 — Positional feature detectors'
desc: 'Can the positional taxonomy be turned into board-feature detectors? Yes — and detection turns out not to be the hard part.'
updated: 1785255400000
created: 1785255400000
---

# E02 — Positional feature detectors

**Answers:** D4 in [[open-questions]] — the project's biggest technical risk
**Code:** `experiments/e02-positional-detectors/` · **Date:** 2026-07-28 · **Status:** done

## Question

Tactics have free machine labels ([[domain.puzzle-themes]]); strategy has none. D4 asked whether the
positional taxonomy that already exists in the literature can be turned into board-feature
detectors, the way prior art has already done for tactical motifs (L-004).

## Method

Four concepts, chosen because each has a definition precise enough to argue about:
**knight outpost**, **isolated pawn**, **backward pawn**, **rook on an open/semi-open file**.

Written as pure functions on a `chess.Board`, deliberately conservative (prefer a miss to a false
positive), with each definition stated in its docstring — these are contested terms, and an unstated
definition cannot be reviewed.

Validated in two stages:

1. **15 unit tests** on constructed positions where the answer is not in doubt, including the
   negative cases that separate a real definition from a lazy one (a knight that *looks* like an
   outpost but can still be hit by a pawn; a rearmost pawn whose advance square is *not* covered, so
   it is not backward).
2. **766 sampled positions across 50 real games** from the target band, sampling from move 12 and
   every 4th ply so near-identical consecutive positions do not dominate. Then a stratified random
   sample of **16 detections was checked by hand**, board by board.

## Results

### Detection works

**16 of 16 hand-checked detections were correct** against their stated definitions. 15/15 unit tests
pass. Examples verified include a genuine `Nf5` outpost protected by an e4 pawn with no black pawn
able to reach e6 or g6; a black `c7` pawn backward behind advanced `b6`/`d6` neighbours with a white
`d5` pawn covering `c6`; and correctly distinguishing open from semi-open files.

Total cost: a few hundred lines of `python-chess`, no engine, no dataset, no model.

### But detection is not the interesting part

| Feature | Detections | % of positions | % of games |
|---|---|---|---|
| knight outpost | 62 | **7.2 %** | 36 % |
| isolated pawn | 1132 | **74.7 %** | 96 % |
| backward pawn | 212 | **20.8 %** | 60 % |
| rook on open/semi-open file | 845 | **74.7 %** | 94 % |

**A feature present in three quarters of all positions carries almost no diagnostic information.**
Telling a player "you have an isolated pawn" is true in 96 % of their games and therefore useless —
it is the positional equivalent of telling them they have pieces.

Two of the four detectors have usable base rates (outpost 7 %, backward pawn 21 %); two do not.

### A second, subtler problem: correct but irrelevant

Several verified outposts were knights on `a5` in simplified endgames. They satisfy every clause of
the definition — advanced, pawn-protected, unattackable by pawns — and no coach would mention them,
because an edge knight in an endgame is not doing the work the concept is *about*. The definition is
correct; its **relevance** is not guaranteed.

This is distinct from a false positive and would not be caught by any test of the definition.

## Conclusion — D4 resolved, and reframed again

**Positional concepts are deterministically detectable with high precision, cheaply.** The risk that
strategy would be intractable because it lacks labelled data does not materialise: the labels can be
*computed*, because the concepts are geometric properties of the position, not statistical patterns.

**The real difficulty moves downstream.** A detector answers "is this feature present?"; coaching
needs "does this feature matter, for this player, right now?". Three candidate routes to a signal,
all of which need the machinery the project is already building:

1. **Co-occurrence with loss** — features present when this player's evaluation drops, versus their
   baseline. Requires the engine layer ([[experiments.e01-engine-throughput]]).
2. **Recurrence across games** — the same feature repeatedly on the wrong side of the player's
   losses. Requires the C2 minimum-sample rule, and matches the aggregate-not-per-move finding of
   E01 (L-006).
3. **Comparison against a reference population** — does this player concede backward pawns more than
   their rating peers? Requires a reference corpus, which the Lichess open database supplies free.

## Consequences

| Affected | Change |
|---|---|
| **D4** | resolved — detection is tractable; the risk relocates to relevance-weighting, not detection |
| [[domain.signals]] | positional features join the computable list, with the base-rate caveat attached |
| M2 | positional sections **are** buildable; they were the doubtful ones. But a section must be defined by *what goes wrong*, not by *what is present* |
| M3 / C1 profile schema | must carry base rate and relevance evidence per feature, not merely presence |
| [[evaluation]] | a new failure mode to test for: statements that are true, specific, and useless |
| Risk register | new risk — "correct but irrelevant output" is not caught by correctness tests |

## Honest limitations

- Precision was measured **against the stated definitions**, not against expert judgement. A titled
  player might disagree with a definition itself; that is a separate and unbudgeted question.
- 16 hand-checked detections is a small sample. It is enough to show the detectors are not broken;
  it is not enough to claim a precision figure to any accuracy.
- Four concepts out of dozens. They were chosen for definitional crispness, which likely makes them
  the *easiest* four. Prophylaxis, piece harmony and "the worst-placed piece" will not yield to the
  same treatment.
- All detections are of *presence*, not of *whether the player handled it correctly* — which is the
  thing coaching actually cares about.
