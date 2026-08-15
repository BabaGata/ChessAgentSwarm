---
id: cas-adr-0010
title: 'ADR-0010 — Three priorities, and a cost pool for what unusualness misses'
desc: 'The first expert review found the most expensive pattern in a player’s games measured, gated and discarded. Cost now fills the slots the peer comparison leaves empty, labelled as ordinary.'
updated: 1786924800000
created: 1786924800000
---

# ADR-0010 — Three priorities, and a cost pool for what unusualness misses

**Date:** 2026-08-15 · **Status:** accepted

## Context

The first expert review ([[evaluation.expert-review]]) produced its first disagreement, on player
`bernes`. The reviewer's Form A named **undefended pieces** as the main weakness. The report named
**missed forks**, which the reviewer ranked third.

Re-measured, the system's own numbers explain it exactly:

| | conceded hanging piece | missed fork *(reported)* |
|---|--:|--:|
| rate | 10.7 % of errors | 32.3 % of chances |
| distinct games | **10 of 53** | 9 of 53 |
| cost to the player | **7.3 wp/game** | 4.2 wp/game |
| peers lose | 8.7 | 3.9 |
| ratio to peers | 1.29× | 1.89× |
| excess over peers | **−1.3** | +0.3 |
| tier | **`watch` — never shown** | `focus` — shown |

Two independent mechanisms hid it, and **neither was a bug**:

1. **The confidence gate.** On 112 trials, 10.7 % against 8.3 % is not a significant difference. The
   Wilson lower bound does not clear the peer rate, so `assign_tier` returns `watch`, and only
   `focus`/`priority` reach a player. Calling this player *unusual* would have been a claim the data
   does not support.
2. **The ranking.** [[experiments.e15-expected-gain]] ranks by cost **above** what peers pay. Here
   that excess is negative, so even a passing claim would have sorted below forks.

The system was right on its own terms and still failed the reader. **Being unusual was the only
route into the report**, and the most expensive pattern in the player's games — the one a human led
with — was measured, priced, and thrown away.

This is [[experiments.e25-shared-weaknesses]]'s objection arriving from a new direction. E25 answered
it with a band-level section, on the condition that only claims passing the divided-gradient screen
appear — five of twenty-seven. `allowed_motif.hangingPiece` is **not** one of the five: within
1400–1800, stronger players do not concede hanging pieces less once general skill is divided out. So
the band section could not carry it either, and by design should not.

The second half of the reviewer's reading was a **factual disagreement**, not a gating one:
`missed_motif.hangingPiece` measured 3 misses in 77 chances — **3.9 % against 6.9 % for peers**. The
player takes free pieces slightly *better* than their level. That is recorded in
[[evaluation.expert-review]] as a criterion-2 result and is not addressed here.

## Decision

Two changes, and the second is the one that matters.

1. **`MAX_PRIORITIES` 2 → 3**, at the thesis author's direction. `context.priorities_for` gains a
   middle band (`STEADY_EFFORT_HOURS = 6.0`) so study time still sizes the plan: under 3 h one thing,
   under 6 h two, otherwise three.
2. **A second selection pool.** Sections keep their sub-threshold (`watch`) findings instead of
   discarding them (`SectionReport.sub_threshold`). The arbiter fills slots the peer comparison left
   empty from that pool, ranked by **what the pattern costs the player outright**.

Four constraints hold it in place:

- **Cost never displaces unusualness.** The assertable pool is filled first, always. Being unusual is
  what makes the first slots a *diagnosis* rather than a description (R-14, anti-pattern D2).
- **Only what the first pool left empty.** [[experiments.e17-ranking-stability]] measured raw cost
  ranking the whole list: one claim named to 70 % of players. Cost here is a filler, not a ranking.
- **Labelled, in both sections.** *"Ordinary for your level, and still what these mistakes cost you
  most."* E25 condition 2 — a population fact must not be dressed as a personal accusation.
- **The evidence rule is unchanged.** `Finding` refuses to exist without a cited position, so a
  cost-ranked step is falsifiable on exactly the same terms (CLAUDE.md hard rule 6).

The excess-cost sentence is also rewritten for this case. With peers losing more, the old wording
printed *"roughly −1.4 a game is what fixing this could get back"*. It now reads: *"Players at your
level lose about 8.7 to the same thing, so this is not costing you your rating — it is costing you
the next one."*

## Alternatives considered

| Alternative | Why it lost |
|---|---|
| **Relax the confidence gate** | The gate is correct. 10.7 % against 8.3 % on 112 trials is not significance, and loosening it to admit one claim would admit noise for every player. |
| **Rank everything by raw cost** | Measured and rejected in E17: `instant_move_error` would be named to nearly everyone. The author's own reading matches it for `bernes`, and would be degenerate across the band. |
| **Add `allowed_motif.hangingPiece` to the band notes** | It fails E25's divided-gradient screen. Adding it would contradict measured evidence to satisfy one reviewer. |
| **Show `watch` claims as a plain "also seen" list** | No training step, no progress check — it would name the weakness and prescribe nothing, which is the failure the arbiter exists to avoid. |

## What running all twelve found

One player is an anecdote, so the change was re-run across the whole review sample before shipping.
Two defects surfaced that `bernes` alone could not show.

**A pattern the player does *better* than peers was being offered as a priority.** `Sheriwoyama` was
handed *"your play falls off when the clock is short"* at **13 % against 15 % for players at your
level** — better than average — under a heading saying it stood out, with a training step attached.
Cost could not filter it: the claim costs 8.6 a game against the population's 7.1, because the
condition arises more often for this player, so the *excess* is positive while the *rate* is below
the population. Fixed: a cost-ranked filler must also be at or above the peer rate. A missing peer
rate still passes, since absence of a reference is not evidence of being better than average.

**"WHAT STANDS OUT" was asserting a diagnosis that had not been made.** Two of the twelve had no
assertable finding at all and still got that heading over three ordinary patterns. When every
reported item arrived on cost the heading is now **WHAT COSTS YOU MOST**, followed by *"Nothing in
your games is unusual for your rating band — measured against players at your level, you are where
you should be."*

**The degeneracy check passes.** E17's failure mode was raw cost naming one claim to 70 % of players.
Across the twelve: **18 distinct claims, most-named 4/12 (33 %)**. The peer-rate filter improved it
— `time_pressure_error.clock` fell from 5/12 to 3/12.

**Plan length is now near-constant, and that is the real cost of this decision.** Eleven of twelve
players get three priorities; before, the spread was 0–3 and the length itself carried information
about how much the system had found. **Silence went 2/12 → 0/12.** The stratified sample's "silent"
stratum ([[evaluation.expert-review]]) no longer describes anything, which changes what that stratum
was built to test. Accepted rather than hidden: a report that says *"nothing about you is unusual,
and here is what costs you most"* is more useful than one that says nothing, and E08's objection to
silence was that it reads as *"you are fine"* — which the new wording states explicitly instead of
implying.

## Consequences

**Easier.** The report can now name a pattern that is expensive and ordinary, which is the only
honest way to answer *"a mistake everyone at your level makes is still a mistake"*. Sub-threshold
findings are retained rather than destroyed, so any later question about what was nearly said is
answerable.

**Harder.** `profile.findings` may now contain `watch`-tier entries — only those the arbiter chose.
Anything counting findings as "what the swarm asserts" must filter by tier. `explainer.is_shared`
reads the tier rather than storing a separate flag, so the marker cannot drift from the decision.

**Foreclosed.** Nothing structural. The cap is now a number rather than a principle, and the
principle it replaced — one or two things, not nine — is carried by the *ordering* and the "do this
one first" marker instead.

**Not resolved.** The reviewer ranked undefended pieces **first**; the system ranks it second, behind
a peer-relative finding. That disagreement stands and is a criterion-2 result, not a bug to tune
away.

## Vision link

V5 (prioritisation), V8 (explainability), and success criterion 2 — the weaknesses named should match
what a strong independent reviewer would name.

## Revisit when

- the expert review completes and criterion 2 has more than one player's evidence;
- a cross-band corpus exists, which would let E25's learnability screen be re-run with real rating
  spread and might admit `allowed_motif.hangingPiece` to the band notes on its own merits;
- the cost pool is measured to name the same claim to most players, which is the E17 failure mode
  reappearing one level down.
