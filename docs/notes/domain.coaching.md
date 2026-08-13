---
id: cas-domain-coaching
title: Coaching Practice
desc: 'How chess coaches assess, diagnose, sequence and track players — the pedagogy the swarm must imitate.'
updated: 1785254500000
created: 1785254500000
---

# Coaching Practice

First-pass answer to questions 5–10 of [[mission.step-01-foundations]]. Sources in
[[domain.sources]]. This note is about *method*, not chess content ([[domain.chess-concepts]]).

> **Read [[domain.expertise-research]] alongside this note.** What follows was assembled from
> coach-authored websites and is honest about it (R-11). The **decisions the code actually rests
> on** — pattern recognition rather than calculation depth, pooling speeds, concrete claims rather
> than principles, refusing to promise rating gains — have since been traced to peer-reviewed
> sources, which support them. Two things there do *not* support this note: whether coaching helps at
> all is **contested in the literature**, and the field has little to say about training methods.
> Where the two notes disagree, the peer-reviewed one wins.

## 1. How a coach assesses a new student

The consistent shape of a first session across sources:

1. **Goals and context** — what does the player want, how much time do they have, what have they
   tried, what is their rating history and time control?
2. **Look at their own games**, especially recent losses. Generic lessons miss the mistakes that
   only appear in this player's games.
3. **Look for repetition, not spectacle.** Repeated errors across several games matter more than one
   dramatic blunder, because repeated errors expose the *habits* that control results.
4. **Produce one clear diagnosis**, named in plain language (missed tactics, poor opening recall,
   weak endgame habits, rushed decisions).
5. **Teach one idea** that addresses it, and give **one clear next step**.

Notable: *"the first month is spent diagnosing what the player doesn't know they don't know."*
Assessment is treated as an ongoing process, not a one-off test. This has a direct architectural
consequence — the swarm needs a **persistent player model** that is refined over sessions, not a
stateless analysis endpoint (V7, and an input to M3).

**Design consequence:** the coach's first move is *not* to teach. It is to gather evidence, find
repetition, and name one thing. A swarm that answers "here are the 9 areas you should work on" is
imitating a textbook, not a coach.

## 2. Diagnosis taxonomy — why a player actually loses

The most useful distinction found, because different causes need completely different remedies:

| Gap type | Looks like | Remedy | Detectable from games? |
|---|---|---|---|
| **Knowledge gap** | doesn't know the pattern/theory exists (never plays the Philidor defence in R+P) | teach the concept | partly — absence of correct play is weak evidence; needs a probe |
| **Skill gap** | knows it, can't execute under time/complexity | drilled practice, repetition | yes — errors cluster in complex or long-calculation positions |
| **Process/habit gap** | doesn't check opponent threats; moves fast; no candidate comparison | change the routine, not the knowledge | **yes, strongly** — time-per-move and blunder-type data |
| **Psychological gap** | tilt after a loss, panic in time trouble, risk aversion in won positions | practical/psychological work | partly — result sequences, clock behaviour, conversion rates |

This four-way split is the sharpest coaching idea found in M1 and should probably become a
first-class structure in the swarm: the same observable error ("hung a knight") has four different
explanations, and the coaching action differs entirely. **Distinguishing them likely requires
interaction with the player, not just game analysis** — see [[domain.signals]] § probes.

## 3. Sequencing

- **One or two priorities at a time**, not a list of nine. Isolate, build the session around them,
  reinforce.
- Give a **training plan for the period** plus a **regular checkpoint** — a loop, not a lecture.
- Sequence by prerequisite (see [[domain.chess-concepts]] § C) *and* by what is currently costing
  the player points, which is not always the same thing. When they conflict, coaches follow the cost.
- Study-time allocation shifts with band (see the band table in [[domain.chess-concepts]] § D).

## 4. Recognised anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Memorising opening theory at low ratings | games are decided by blunders long before the theory runs out |
| Novelty-chasing — new material constantly | patterns become automatic through repetition, not exposure |
| Solving puzzles for speed | trains guessing; the skill wanted is *being right* |
| Studying only what is enjoyable (usually attack) | leaves endgame/technique gaps that cost the most points |
| Fixing everything at once | no measurable change, no reinforcement |
| Coaching from generic material without looking at the student's games | misses the individual habits that decide results |
| Rating-obsession over process metrics | rating is slow and noisy; process metrics move first |

The swarm must be checked against this list — several of these are exactly the failure modes an
LLM-based coach falls into by default (especially "list nine weaknesses" and "recite generic advice").

## 5. Measuring progress other than rating

Rating is a lagging, noisy indicator confounded by everything the player does elsewhere. Leading
indicators used by coaches, all computable (see [[domain.signals]]):

- Blunder rate per game, and blunder rate **in the specific pattern being trained**
- Whether the trained motif is now spotted when it appears
- Time distribution — fewer instant moves in critical positions, less time trouble
- Conversion rate of winning positions
- Phase-wise error profile shifting
- Puzzle rating in the trained theme specifically
- Qualitative: can the player *explain* the plan in a typical structure (needs interaction)

**Design consequence (V6/V7):** a coaching plan step must ship with its own predicted progress sign
— "you should start noticing pins on the e-file within ~2 weeks; measured as: fewer than X missed
pin-motifs per 10 games." Without that, progress tracking is unfalsifiable (R-02).

## 6. Style, operationally

Sources describe four broad types — attacking, positional, defensive/counterattacking, endgame
specialist — while also saying strong players switch between them by position, and that this is
"a practical grouping rather than an official rule". Style is shaped by calculation strength,
opening choices, structural understanding and emotional comfort under pressure.

Treat "style" with suspicion (see contested claims in [[domain.chess-concepts]] § E). For V3 the
operational definition should be **measured tendencies + measured performance**, not a personality
label:

- *Tendency* — what the player actually does: early queen trades, castling side, sacrifice rate,
  pawn storms, average position sharpness, game length, closed vs. open structures reached.
- *Performance* — where they actually score better: their results and error rates split by
  position type.

A recommendation then becomes falsifiable: *"you score 12% better in closed positions but your
repertoire steers into open ones"* — evidence-backed, and directly actionable as repertoire advice.
That is the version of V3 worth building; the personality-quiz version is not.

## Open items for the next research pass

**Done 2026-08-14** → [[domain.expertise-research]]: the load-bearing claims now have peer-reviewed
sources, and E19's speed-pooling decision turned out to have a published precedent (Chabris & Hearst
2003, blunders per 1,000 moves 5.02 → 6.85 for a **sixfold** cut in thinking time).

Still open:

- **The four-way gap taxonomy above (§ 2) has no traced source.** It is the sharpest idea in this
  note, it drives `GapTypeHypothesis` in the profile schema, and its provenance is *"found in M1"*.
  It resembles the declarative/procedural distinction in skill-acquisition research, but that link is
  currently an assertion. Either source it or mark it as this project's own construct and defend it
  as such.
- Actual coach-authored curricula/lesson plans at a concrete level of detail (the Steps Method).
- How coaches handle adult improvers vs. juniors.
- Evidence on *how long* interventions take to show up in results — D5, still unanswered, and
  [[domain.expertise-research]] found the literature thin on training methods generally, so this may
  be a gap in the field rather than in the reading.
- How to elicit knowledge in dialogue (the probe-position idea) — is there published methodology?
