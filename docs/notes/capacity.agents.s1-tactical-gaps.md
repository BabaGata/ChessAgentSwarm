---
id: cas-agent-s1
title: 'Agent S1 — Tactical pattern gaps'
desc: 'The second agent: which tactical motifs a player misses or walks into.'
updated: 1785312000000
created: 1785312000000
---

# Agent S1 — Tactical pattern gaps

**Section:** [[domain.sections]] → S1 · **Status:** detectors built and measured; agent not yet built
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **Detectors done.** Eight motifs in `chesscoach/tactics.py`, 30 unit tests, and the §4 gate
> measured in [[experiments.e04-motif-precision]] — which caught two of them badly over-firing
> (`trappedPiece` by ~6.5×, `hangingPiece` by counting pawn grabs) exactly as this note predicted.
> Base rates on 51,422 real positions now range from 0.38 % to 6.51 %.

## Why this agent, now

The 38-player sweep in [[architecture.peer-reference]] measured the project's weakest point precisely:
S2 asserts **one claim kind**, for **16 %** of players. It nominally has three conditions and in
practice one working detector. A system whose only sentence is *"you err after long thinks"* is not a
coach, and no amount of refining S2 changes that — the missing thing is **breadth of diagnosis**.

S1 is also the first genuine test of [[decisions.0006-staged-blackboard-orchestration]]'s claim that
sections are additive and independently ablatable. One agent cannot demonstrate that; two can.

## 1 · Remit

**Which tactical patterns this player does not see** — by motif, in both directions:

- **missed** — a tactic was available and they played something else;
- **allowed** — their move handed the opponent a tactic.

**Explicitly not its business.** *Why* it happened is someone else's: if the misses cluster under
time pressure that is S2's finding, not S1's. Endgame technique is S3's. S1 answers only *which
patterns*, and the pairing of S1 with S2 is what turns "you miss forks" into "you miss forks when
short of time" — which is the first sentence in this project that would sound like a coach.

## 2 · Knowledge organisation

Unlike S2, S1 has a real vocabulary. The motif list is the knowledge, encoded as detector
definitions, and it maps onto the CC0 Lichess puzzle themes already catalogued in
[[domain.puzzle-themes]]. That mapping is what later makes prescription possible: the same names
identify the weakness and select the training material.

**First tranche of motifs**, chosen for crisp definitions and frequency at 1400–1800:
fork / double attack · pin · skewer · discovered attack · hanging piece · back-rank mate ·
removal of the defender · trapped piece.

Deliberately deferred: deflection, interference, zwischenzug, clearance, overloading, x-ray. They
are real and less crisply defined; adding them before the first eight are validated would multiply
the calibration work without adding coverage where it matters.

**Licence note.** Prior art ([[domain.prior-art]]) implements twelve such detectors, and is
**AGPL-3.0**. Its existence tells us the approach works and roughly what it costs. Nothing is copied;
every detector here is written from the definition.

## 3 · Agent type

**Deterministic detector plus statistics.** No model, no retrieval — as required in the diagnosis
stage by [[architecture.orchestration]], and appropriate because a motif is a geometric property of a
position and a move.

## 4 · Knowledge maintenance

The detector definitions are the only tunable state, and they are the risk. Prior art documented a
skewer detector over-firing **10–18×** before being constrained, and E02 found that plausible-looking
detector code fires far too often on real boards.

So each detector ships with two things before it may be used:

1. **unit tests on constructed positions**, including the negative cases that separate a real
   definition from a lazy one;
2. **a hand-checked precision estimate on real games**, from a stratified random sample — the same
   procedure as E02, whose 16/16 verification is the standard to match.

## 5 · Tools

`chesscoach.analysis` observations, `python-chess`, `chesscoach.confidence`,
`chesscoach.evaluation.splithalf`, `chesscoach.peers`.

**No additional engine calls.** This is worth stating because it is not obvious: detecting an
*allowed* motif needs the opponent's best reply *after* the player's move, and that is already
present — it is the `best_move` of the **next observation**. Consecutive observations therefore
contain everything both directions need, so S1 costs nothing on top of analysis that has already run.

## 6 · General instruction

The behavioural contract, to be enforced by tests:

1. **Rates are per opportunity, never per move.** The denominator for "misses forks" is *positions
   where a fork was there to be found*, not all positions. A per-move rate would mostly measure how
   tactical the player's games are.
2. **Conservative detectors.** Prefer missing a real motif to inventing one; for a coach a false
   positive sends the player to study something that was never wrong.
3. **Never name a motif the detector did not tag.** No inference beyond the tag.
4. **Peer-compare.** Everyone misses tactics; only deviation from the rating band is a diagnosis
   (L-011, L-012).
5. **Evidence is sampled uniformly**, not chosen for severity.
6. **Zero findings is a valid output**, and `insufficient_data` is distinct from "no problem".

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core — carries `best_move`, `loss_wp`, `fen_before`, `move_played` |
| corpus, provenance | | ingest / analysis |
| band, time_control, peers | | [[architecture.peer-reference]] |

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `missed_motif` | motif name | a tactic was available; the player did not take it |
| `allowed_motif` | motif name | the player's move gave the opponent this tactic |

**Gap type is `unknown`, `determined_by = inferred`** — and that is the honest answer, not a
placeholder. A missed fork cannot distinguish *doesn't know the pattern* from *knows it and didn't
see it here* (L-002). S2 can say `process` because a clock reading is exogenous; S1 cannot. This is
precisely the gap a V9 probe is designed to close, and S1's output is what will make probes worth
asking.

`executed_motif` is **measured but not asserted as a finding**: it belongs in a knowledge profile
(V2) and matters for not telling someone to study what they already do well, but it is not a
weakness and must not be reported as one.

## 9 · Efficacy measure

Four levels, strongest first:

1. **External validation against the CC0 puzzle database.** Lichess puzzles carry human-usable theme
   tags and a known solution move. Running our detectors on those solution moves and comparing labels
   is a measurement of accuracy against an **independent labelled corpus** — something this project
   has not had before, and free. *(Needs the puzzle dump for validation only, never at runtime.)*
2. **Hand-verified precision on real games**, stratified sample, E02's procedure.
3. **Planted-weakness score.** Requires a new `WeaknessSpec` kind — *motif blindness*: the flawed
   player plays an inferior move whenever the best move executes motif M. This is a small extension
   to [[evaluation]]'s generator and gives sensitivity and specificity against known ground truth.
4. **Split-half replication and peer comparison**, as the confidence policy already requires.

## 10 · Cost profile

Zero marginal cost. No engine calls of its own (§5), no model calls, pure board logic over
observations that already exist. Expected to run in seconds for a 40-game corpus.

## Known limitations, recorded before building

- **"Missed" is defined against the engine's best move.** If the best move happens to be a fork, not
  playing it counts as a missed fork — but sometimes the tactic is the *second*-best move, and
  sometimes the best move is positional and no tactic existed at all. So the claim is really "missed
  the best move, which executed motif M". Honest phrasing matters here.
- **Opportunity denominators are approximate.** Enumerating every motif available across all legal
  moves would be the rigorous denominator and is expensive. The first implementation counts
  opportunities as *critical positions whose best move carried the motif*, which is cheap and
  defensible — and understates opportunities, so it will bias rates upward. That must be stated
  wherever the rate is shown.
- **Depth-bound**, like every other signal (E01). Motif tags depend on which move the engine called
  best.
- **Tactical players meet more tactics.** Peer comparison handles part of this and not all of it.
- **Detector calibration is the main risk**, and history says the failure is over-firing, not
  under-firing.
