---
id: cas-design-castling-drift
title: 'Castling late is only a fault if the player was drifting while they did it'
desc: 'late_castling fires on when the king reached safety and not on why. The author rejected a firing where White castled late because they were busy being better. This conditions the claim on unexplained errors between leaving book and castling, and gives the retired early_error machinery its use.'
updated: 1788746400000
created: 1788746400000
---

# Castling late is only a fault if the player was drifting

**Status:** design · **Date:** 2026-09-06 · **Mission step:** M6

## The problem

`late_castling` compares the ply the king reached safety against a per-opening norm. It says nothing
about *why* it was late, and the author rejected a firing on exactly that:

> *"In this example white took opportunities in the opening and now is better of even though he
> castled late. This should be taken in the account only when there are repeated bad moves before
> having the opportunity to castle."*

Castling on move 13 having seized the initiative and castling on move 13 having drifted are the same
number and opposite diagnoses. Only the second is a weakness a player can work on, and telling the
first player to castle earlier is advice that would have made their game worse — the same fault the
six corrections in [[design.detectors-name-consequences]] share.

## The design, in the author's words

> *"For late castling there could be use of the early_error any detector that has been retired. It
> could use it to get a count and a severity of the errors that were made by the players before
> casteling. It takes in the account only errors that have not been detected by some motif detector,
> which would mean that the player just didn't saw some motif. So this could be used to count
> together all the imprecise moves before castling and after out of the book move, so that it can be
> used as a measure if the player just played badly before casteling or he just played good and took
> opportunities and that is why he castled late."*

**Drift** = the player's errors in the window **after leaving book and before castling**, counting
only those **no motif detector explains**.

Three parts, each with a reason:

1. **After the book move.** Moves inside named theory are not the player's own choices and are never
   charged to them — `GameDevelopment.plies_in_book` already draws this line for the other
   development claims.
2. **Before castling.** The question is what the player was doing *instead* of castling. Errors after
   the king is safe say nothing about why it took so long.
3. **Unexplained by a motif.** An error the motif vocabulary already names is charged to that motif
   — `allowed_motif.*` or `missed_motif.*` — and charging it here too would count one mistake twice,
   which `chesscoach/overlap.py` exists to prevent. What is left is the residue: moves that lost win
   probability with no tactic to point at, which is precisely *"just played badly"*.

## What this reuses

**The retired `early_error` machinery gets its use, and it is the one the author named when retiring
it** — `s3_endgame_technique.ADVANTAGE_ERROR_RETIRED` and `s4_opening_outcomes.EARLY_ERROR_RETIRED`
were both kept on the argument that the tally is a cheap way to ask later whether errors in a window
are explained elsewhere. This is that question, asked for real:

> **an error inside the opening window that no motif explains** — which is what `early_error` counted,
> minus the part other detectors already own.

`early_error` failed as a *claim* because "you go wrong early" names a circumstance. As an **input to
another claim** it is exactly right: it is a measurement, and it was never wrong about what it
counted.

## Definition of done

- [ ] `drift_before_castling(game)` returns a count and a win-probability cost, computed from
      observations already in hand — **zero engine calls**
- [ ] `late_castling` records only when the count reaches the "repeated" bar the author set
- [ ] the author's `[n]` (`0tP1Rbmj#25`, White castled move 13 and was better) stops firing
- [ ] all three `[y]` marks keep firing
- [ ] the drift count and cost are carried as evidence, so a report can say *why* it fired
- [ ] measured across the reviewed games: how many `late_castling` instances survive

## Alignment (phase 2)

- **Serves V8** — every claim cites the player's own games, and this adds *why* to a claim that had
  only *when*. Serves **C1**: no engine call, the observations are already analysed.
- **Scorecard** — moves D4 (gap detection) by making an existing claim honest rather than by adding a
  claim. Nothing here widens the vocabulary.
- **Cheaper alternative considered:** conditioning on the win probability lost in the window, with no
  motif filter. Rejected: it double-charges errors the motif claims already own, and the author's
  sentence is specific about excluding them.
- **Forecloses** nothing — the gate is one predicate and reverting it restores the old behaviour.

## Open question — where the bar sits

The author said *"repeated bad moves"*. **Repeated is at least two**, which is the reading taken, and
the constant is named so it is visible. Whether two is right is a calibration question and the
reviewed corpus is the only evidence available; what it does to the five marked instances and to the
overall firing count is reported in [[experiments.e86-detector-audit]] rather than assumed.
