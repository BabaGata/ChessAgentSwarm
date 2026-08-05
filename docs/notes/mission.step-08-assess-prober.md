---
id: cas-mission-m5-prober
title: 'M5 — assessing the prober and the explainer in the swarm'
desc: 'Does the language layer serve the goal? The reproducibility claim holds, the swarm is specific but silent, and one score was self-flattering.'
updated: 1785974400000
created: 1785974400000
---

# M5 — assessing the prober and the explainer in the swarm

**Status:** done · **Parent:** [[mission]] · **Agents:** [[capacity.agents.prober]], the explainer

The M4→M5 loop, third time round, and the first time the thing being assessed contains a language
model.

## Does information flow through correctly?

**Yes, and running it once for real proved it in the way that mattered.** The chain
analyse → diagnose → prioritise → probe → plan → report carries a finding from an engine evaluation
to a sentence a person reads, with the evidence surviving each hop: the report cites the same games
the detector sampled, at 13/13 groundedness (E08 D4).

Two defects were found by running it rather than by testing it, both at the boundary where real
input arrives, and both already recorded as [[learning.risks]] I-01/I-02. That is the honest headline
of this assessment: **429 passing tests did not catch either.**

## Did the reproducibility claim survive being measured?

[[capacity.agents.prober]] § 10 asserted that temperature 0 and a fixed seed make a verdict
repeatable, and `ProbeRecord.classifier` is recorded on the strength of it — the whole audit story
depends on a stored `gap_type` being re-derivable. It had never been measured.

**46/46 answers stable across three runs** for the shipping model, and for both baselines
(`run.py --repeat 3`). The claim holds. It is worth noting it was one experiment away from being an
assumption in a thesis.

## Does the end result serve the goal?

E08 ran the anti-pattern family from [[evaluation]] over 38 real players — metrics designed cycles
ago and blocked ever since on there being a language layer to point at.

| | |
|---|---|
| **not generic** | mean pairwise overlap **0.24**; R-12's failure mode is absent |
| **not overloaded** | never more than two priorities, on real data |
| **grounded** | 13/13 claims cite a specific game |
| **but silent** | **29 of 38 players are told nothing at all** |

The one metric that looked alarming — `long_think_error` reaching 56 % of advised players — is not
what it appeared to be. Detected counts equal advised counts for every claim kind, so the arbiter is
not over-selecting it; **almost nothing else clears the confidence gate to compete.** Fourteen
findings across thirty-eight players.

## Did this step move us closer to the vision, or further away?

Closer, and the scorecard needed correcting anyway.

**D8 explainability was scored 3 and that was self-flattering.** Reading a real report found an
internal identifier in player-facing prose — *"it is often a `trappedPiece` that punishes you"* — a
CC0 Lichess theme key, which a player has no way to read. D4 groundedness scored **100 % on that same
output**, because it only checks whether a claim cites a game. A metric passing is not the same as
the output being good, and this is the cleanest example of that the project has produced.

Fixed (`phrasing.subject_name`, translated on the way out and nowhere else — the key stays the key
where the player can *use* it, in "drill `pin` puzzles", because that is what a puzzle filter takes).
**D8 is corrected to 2 for the cycle in which it was scored 3, and returns to 3 now the defect is
fixed** — the number is the same, but it was not earned when it was claimed.

## Is a section missing?

**Yes, and this is the cycle's main output.** 29 silent players is a coverage failure, and it is
measured now rather than felt. [[decisions.0009-prober-before-breadth]] deferred sections S3–S11 on
the grounds that *"a system that diagnoses eleven things and cannot ask the player about any of them
is further from the vision than one that diagnoses two and can"*. **That reason has expired** — the
prober exists, so every new claim kind is now probeable.

Breadth is the binding constraint. The next M4 iteration is a section.

## Do we need new external information?

Not for the code. **F2 remains the outstanding debt** — primary coaching sources are still unread and
the concept decomposition rests on secondary web content (R-11). It is thesis-defensibility work, the
sources are free, and it is the one item on the board that does not compete with anything.

## Has anything surfaced that should change the project's course?

One thing, recorded as a lesson rather than a course change: **the metrics were right and the reading
of them was nearly wrong.** D2 flags a claim made to most players as a description of the band, which
would have sent the next cycle chasing a base-rate problem that does not exist. Distinguishing
*common* from *easy to detect* took one extra column, and the metric now carries it.

## Working log

| Date | Activity | Outcome |
|---|---|---|
| 2026-08-05 | Measured classifier self-consistency (§ 9 level 4) | 46/46 stable over 3 runs; the reproducibility claim holds |
| 2026-08-05 | Implemented D1–D4 and ran them over 38 players → [[experiments.e08-anti-patterns]] | not generic, not overloaded, grounded — but silent for 29 of 38 |
| 2026-08-05 | Read a real report | internal theme keys reaching the player; D8 was over-scored; fixed |
| 2026-08-05 | Re-read ADR-0009 against the evidence | its deferral reason has expired; breadth is next |
