---
id: cas-exp-e08
title: 'E08 — The anti-pattern metrics, finally runnable'
desc: 'D1–D4 from evaluation.md, blocked since design on there being a language layer. The swarm is not generic — it is mostly silent.'
updated: 1785974400000
created: 1785974400000
---

# E08 — The anti-pattern metrics, finally runnable

**Answers:** [[evaluation]] family D, and [[state]]'s long-standing P1 · **Code:** `experiments/e08-anti-patterns/`
**Date:** 2026-08-05 · **Status:** done — **the swarm is specific, and too quiet**

## Question

[[evaluation]] defines five anti-pattern metrics and records them as *"needs the language layer to
exist"*. It now exists, and D1 has been P1 in [[state]] for several cycles with the note that it
*"would have caught M5's base-rate finding automatically instead of by eye"*. This is that check,
run over 38 real players.

Profiles had to be regenerated first: the ones left from earlier cycles predate the planner, so they
carry findings and no plan — and every one of these metrics asks what a player is actually **told**,
which is the plan (`build_profiles.py`).

## Result

| Metric | Reading |
|---|---|
| **D1** inter-player divergence | mean pairwise overlap **0.24**; 3 of 36 pairs identical; 6 distinct claim kinds |
| **D2** base-rate specificity | `long_think_error` told to **56 %** of advised players |
| **D3** priority count | never above 2 — 29 players get 0, five get 1, four get 2 |
| **D4** groundedness | **13/13** reported findings cite a specific game |

## What it says

**The swarm is not the generic coach.** Mean overlap of 0.24 means two advised players are told
mostly different things, which is the direct test for R-12 and it passes. D3 confirms the arbiter's
limit holds on real data — the "list nine weaknesses" failure cannot occur by construction and does
not occur in practice. D4 is 100 %, so V8's mechanical half is satisfied.

**D2's flag turned out to be the wrong reading, and separating it was the useful part.** A claim made
to most players looks like a description of the rating band rather than a diagnosis. But there is a
duller explanation: a claim can dominate because its *denominator* is bigger, so it clears the
confidence gate more often. S2 measures against every long think; S1 measures against motif
opportunities, of which [[mission.step-07-second-iteration]] counted roughly three per player for
skewers.

So the metric now reports **detected against advised**:

| claim | detected | advised |
|---|---|---|
| `long_think_error.long_think` | 6 | 5 |
| `allowed_motif.pin` | 4 | 4 |
| `allowed_motif.trappedPiece` | 1 | 1 |
| `missed_motif.pin` | 1 | 1 |
| `missed_motif.discoveredAttack` | 1 | 1 |
| `allowed_motif.hangingPiece` | 1 | 1 |

They are equal everywhere. **The arbiter is not over-selecting long thinks — almost nothing else
clears the gate to compete with it.** Fourteen findings across thirty-eight players.

**So the real result is coverage, not genericness: 29 of 38 players are told nothing at all.** That
is not a false-positive problem and not an anti-pattern; it is a system that is honest and mostly
silent. Silence is the correct output when nothing reaches confidence, and a coach who has nothing
to say to three players in four is still not much of a coach.

## Consequences

1. **Breadth is now the binding constraint**, and this is the measurement that says so rather than
   an intuition. It supports building sections S3+ next, and it revises
   [[decisions.0009-prober-before-breadth]]'s deferral — that ADR's reason (a system diagnosing
   eleven things it cannot ask about) no longer holds now the prober exists.
2. **D2 must always be read with detection counts.** On its own it would have sent the next cycle
   chasing a base-rate problem that is not there. Recorded in the metric itself rather than in a
   footnote nobody reads.
3. **D5 coverage is now the metric that matters** and is not built — *what fraction of the player's
   actual errors can the swarm explain at all?* 29 silent players out of 38 is a proxy for it, and a
   poor one.

## Honest limitations

- **38 players, 14 findings.** Every percentage here rests on small counts, and D1's 0.24 overlap is
  computed over just 36 pairs.
- **One band, one time control, one site.**
- **D1 measures overlap of claim *kinds*, not of the text.** Two players told about `pin` receive
  different numbers and different games, so the true divergence is understated — which is the safe
  direction for a metric whose failure mode is missing genericness.
- **D5 (coverage) and the E-family human review remain unbuilt.**
