---
id: cas-exp-e03
title: 'E03 — Relevance weighting'
desc: 'Can a detected feature be weighted for relevance by its association with errors? Largely no — and the replication caught an artefact.'
updated: 1785255900000
created: 1785255900000
---

# E03 — Relevance weighting

**Answers:** C6 in [[open-questions]] — partially, and mostly in the negative
**Code:** `experiments/e03-relevance-weighting/` · **Date:** 2026-07-28 · **Status:** done

## Question

E02 proved positional features are detectable and simultaneously showed detection is not a coaching
signal — isolated pawns occur in 96 % of games (L-007). C6 asks how a detected feature is weighted
for **relevance**. This experiment tests the first candidate route: **association with the player's
own errors**.

## Method

    lift(F) = P(error | F present) / P(error | F absent)

A feature carrying no information about this player's mistakes has lift ≈ 1 however often it is
detected. Measured at depth 15 (E01's working setting), on every position from ply 16 onward, with
features split into the mover's **own** and the **opponent's** — advice differs entirely between them.

Three refinements were added after the first pass returned nothing:

- **Drift** — cumulative loss over the mover's next 3 own moves, since a positional weakness is more
  plausibly associated with slow decay than with an immediate blunder.
- **Phase stratification** — because game phase turned out to predict errors better than any feature.
- **Replication on held-out players** — 8 features × 3 phases is 24 cells, so the largest lift is
  expected to look impressive whether or not anything is real.

| Sample | Players | Games | Moves | Baseline error rate |
|---|---|---|---|---|
| Discovery | 3 | 50 | 3,382 | 9.7 % |
| Held-out | 4 (different) | 76 | 4,382 | 10.3 % |

## Results

### 1. Move-level error association: no signal

Pooled lift, discovery sample — every feature between **0.87 and 1.26**. The drift measure was no
better (0.82–1.16). Having an isolated pawn or a rook on an open file says nothing about whether the
player is about to go wrong.

### 2. Game phase beats the entire positional vocabulary

| Phase | Discovery error rate | Held-out error rate |
|---|---|---|
| full-material middlegame | 13.4 % | 10.7 % |
| late middlegame | 9.9 % | 12.3 % |
| endgame | 6.1 % | 6.9 % |

A ~2× spread by phase, larger than any feature's association — and the phase *ranking* itself was not
stable between samples. Any relevance measure must control for phase, and phase alone is a weak
diagnostic too.

### 3. The finding that wasn't

Stratifying by phase appeared to rescue the whole approach. In the discovery sample's endgames,
backward pawns showed error lift **2.40** (opponent's, n=126) and **2.12** (own, n=121) — against
pooled lifts of only 1.25 and 1.17. The explanation was tidy: backward pawns are commoner in
endgames, where the baseline error rate is *lowest*, so pooling dragged the association toward 1 and
hid a real effect.

**It did not replicate.** On held-out players the same features gave pooled lifts of **0.88** (own)
and **0.76** (opponent) — not merely absent but *reversed* — and backward pawns did not appear among
the top endgame associations at all.

The tidy explanation was a multiple-comparisons artefact with a plausible story attached. Without the
held-out sample it would have been reported as a result, and it is exactly the failure R-13 exists to
prevent.

### 4. The one survivor

`own_outpost` — the player *has* a knight outpost — was the only feature to hold up:

| Measure | Discovery | Held-out |
|---|---|---|
| pooled error lift | 1.26 (n=124) | **1.55** (n=172) |
| drift ratio | 1.11 | **1.20** |
| within-phase | positive | positive in **all three** phases |

Consistent in direction across two disjoint player samples and two different measures. The effect is
modest and the sample small, so it is a **lead, not a result**.

Its direction is counterintuitive: the player errs *more* when they hold an outpost. Plausible
readings — outposts arise in closed manoeuvring positions where amateurs drift without a plan; or
comfortable positions invite relaxation, which is a recognised practical failure and, pleasingly,
the title of a chapter in Capablanca's *Chess Fundamentals* ("The danger of a safe position"). We
have no evidence to choose between them; that would need its own experiment.

## Conclusion — C6 partially answered

**Error co-occurrence is a weak relevance signal at best.** One feature out of eight showed a
consistent, modest association; the rest showed none, and the most promising-looking effect
evaporated on replication. This route does not deliver relevance weighting on its own.

Remaining routes, both untested and both now more attractive:

- **Peer-population comparison** — does this player concede backward pawns *more than rating peers*?
  This asks whether the player is **unusual**, not whether the feature predicts errors, so E03's
  negative result does not touch it. The free Lichess database supplies the reference corpus, and the
  same corpus doubles as evaluation metric D2 in [[evaluation]].
- **Recurrence across games** — the C2 rule. Note it measures *consistency*, not *importance*: it can
  establish that something is reliably true of a player without establishing that it costs them
  anything.

A fourth route this experiment suggests: **outcome-level association** — does the player *score*
worse in games where the feature appears? — which is closer to what a coach actually means than
move-level error correlation.

## The larger implication

There is a reading of these results that goes beyond method: **positional features may simply not
matter much at 1400–1800.** That is consistent with everything M1 found — this is the band where
sources agree games are decided by tactical oversights and process failures, not by structural
understanding.

If so, the negative result is not a setback but a **confirmation of the M2 build order**: Tier 1
(process, tactics, endgame technique, openings) before Tier 2 (positional). It also suggests Tier 2
should be re-scoped rather than merely deferred — and that its sections may need to justify
themselves on peer-deviation grounds rather than error-prediction grounds.

## Honest limitations

- 7 players total. Enough to catch an artefact, not enough to establish a small effect.
- Error labels come from the same engine at a single depth; E01 showed labels shift with depth, so
  a small association could be depth-dependent.
- Correlation only. A backward pawn in a lost endgame may be a *symptom* of a bad position rather
  than a cause of errors.
- Only four features were tested — the ones E02 happened to build.
- Phase is a crude three-way split by remaining material.
