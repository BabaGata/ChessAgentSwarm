---
id: cas-exp-e10
title: 'E10 — Calculation cannot be measured from game records'
desc: 'S7 screened and not built. The contrast that would isolate calculation does not vary between players, and the rate that does is the error rate under another name.'
updated: 1786406400000
created: 1786406400000
---

# E10 — Calculation cannot be measured from game records

**Answers:** § 9.1 for S7, in advance · **Code:** `experiments/e10-calculation-candidates/`
**Date:** 2026-08-05 · **Status:** done — **negative, and the section is not built**

## Question

S7 owns *calculation quality*: finding quiet moves, finding defensive moves, depth of forcing
sequences. [[domain.sections]] flags it as the weakest-supported Tier 2 section and says so plainly —
*"measuring a player's calculation from games alone is weak… it is the section most dependent on V9
probes, since calculation is best measured by asking."*

E09 established the discipline: screen before building. This screens S7.

## Method

38 players, depth 15, warm cache. Unlike E09 this cannot be engine-free — every candidate needs the
engine's preferred move and an error label.

The premise is a **contrast**, not a rate. Everyone errs; the question is whether a player errs *more
when the answer is quiet than when it is forcing*. A check or a capture announces itself; a quiet
move has to be found. That gap is as close to "calculation" as a game record gets.

A move counts as forcing if it is a capture, a check, or a promotion — deliberately the improving
player's own crude categories ("checks, captures, threats") rather than a better theory.

## Result

| candidate | median | p90/median spread |
|---|---|---|
| `missed_quiet` | 0.1155 | 1.56 |
| `missed_forcing` | 0.1025 | 1.46 |
| `forcing_reflex` — played a forcing move where a quiet one was best | 0.1121 | 1.31 |
| **`quiet_penalty`** — `missed_quiet / missed_forcing`, per player | **1.17** | **1.27** |

**`corr(missed_quiet, missed_forcing) = +0.737` across 36 players.**

## Why this closes the section rather than shaping it

**The contrast does not vary.** A typical player errs 17 % more often when the best move is quiet
than when it is forcing, and players differ in that penalty by a spread of 1.27 — the same range as
[[experiments.e09-square-candidates]]'s failures and S5's suppressed claims. Whatever calculation
ability is, it does not show up as a differing quiet-versus-forcing gap in these games.

**The one rate that does spread is not about calculation.** `missed_quiet` at 1.56 looks borderline
until the correlation is read: **r = +0.737** with `missed_forcing`. The players who go wrong on
quiet moves are the players who go wrong on forcing moves. A claim built on it would restate the
overall error rate under a more flattering name — the L-014 failure in a new guise, where
`allowed_motif` divided by all moves and simply tracked how often the player erred at all.

**The tendency framing fails too.** `forcing_reflex` — reaching for a check or a capture when the
position wanted a quiet move — is the classic amateur description, and at 1.31 players barely differ
on it either.

Three independent framings, all negative. The catalogue's own warning was right, and is now measured.

## Consequences

1. **S7 is not built.** It stays in [[domain.sections]] with this note attached, rather than shipping
   a section that measures the error rate twice.
2. **The route to calculation is the prober**, exactly as the catalogue guessed. A probe gives a
   position untimed and asks for a move *and a reason* — which separates *did not see it* from
   *could not work it out*, and no arrangement of game records will. That makes S7 a **downstream
   consumer of V9** rather than a section, and it is blocked on D10.
3. **The screening method gains a second test.** E09 asked *does this vary between players?* E10
   shows that is not sufficient: a claim can vary and still be a proxy for something already
   measured. The second question is *does it survive dividing out what we already know?* Recorded as
   **L-025**.

## Honest limitations

- **"Forcing" is crude.** Captures, checks and promotions miss quiet threats, zwischenzugs and
  prophylaxis — a better definition might find a signal this one cannot.
- **24-game corpora.** `missed_forcing` has a median of only 148 opportunities per player, so its
  rate is noisy and the ratio inherits that noise. Deeper histories would sharpen the contrast,
  though a median penalty of 1.17 leaves little room for one.
- **Depth of calculation is untested.** Only *what kind of move was missed* was measured, not how
  long the forcing sequence was. That is the one framing left, and it needs multi-ply search per
  position rather than the single evaluation the cache holds.
- **A negative screen is not a proof of absence** — it says these three framings do not discriminate
  in 24-game corpora at this band.
