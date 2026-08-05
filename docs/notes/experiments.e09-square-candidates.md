---
id: cas-exp-e09
title: 'E09 — Screening S6 before building it'
desc: 'Five candidate claims, two survive. The first section screened before it was written — and the first pass was wrong in a way worth keeping.'
updated: 1786320000000
created: 1786320000000
---

# E09 — Screening S6 before building it

**Answers:** § 9.1 of [[capacity.agents.s6-squares-and-files]], in advance
**Code:** `experiments/e09-square-candidates/` · **Date:** 2026-08-05 · **Status:** done

## Question

L-023 was learned expensively: S5 was fully built before anyone checked whether players actually
differ on its claims, and most of it had to be suppressed. [[state]] now says to screen first. Which
of S6's candidate claims — if any — distinguish players at 1400–1800?

## Method

Engine-free, and that is the point: every candidate is a pure board property, so the screen needs
games and nothing else. 38 players, ~660 diagnosable moves each, about a minute. `diagnosable()` is
approximated by skipping the opening grace plies, which is enough to compare players with each other.

Five candidates, all framed as **what goes wrong** rather than what exists
([[domain.sections]] design rule 1):

| candidate | shape |
|---|---|
| `concedes_hole` | event — a move creates a square in the player's own half no pawn of theirs can ever cover |
| `concedes_outpost` | event — the opponent gets a knight settled where it cannot be evicted |
| `allows_rook_seventh` | event — an enemy rook reaches the rank the player's pawns started on |
| `cedes_open_file` | state — an open file exists, the player has a rook, and it is elsewhere |
| `bad_bishop` | state — a bishop hemmed by four or more of the player's own pawns on its colour |

## The first pass was wrong, and the error is the useful part

It reported `concedes_outpost` and `allows_rook_seventh` at a **median rate of exactly zero**, which
would have killed both. The cause: it compared the position before the player's move with the
position after it — and **a knight settles and a rook arrives on the opponent's turn**. Measuring a
concession across the conceder's own move finds almost nothing by construction.

Corrected to compare across the opponent's reply — the same framing S1 uses for `allowed_motif` —
both candidates came alive. Two of five were nearly discarded on a measurement error, in a screen
whose entire purpose was to decide what to build.

## Result

| candidate | median rate | p90/median spread | verdict |
|---|---|---|---|
| **`concedes_outpost`** | 0.0077 | **2.15** | **highest spread in the project** |
| **`allows_rook_seventh`** | 0.0102 | **1.82** | comparable to `early_error.black` (1.92) |
| `cedes_open_file` | 0.2866 | 1.31 | fails |
| `bad_bishop` | 0.3966 | 1.27 | fails |
| `concedes_hole` | 0.1963 | 1.25 | fails — sits on S5's suppressed `concedes_weakness.any` (1.24) |

For scale: claims already known to discriminate run 1.60–1.92; S5's suppressed ones run 1.20–1.24.

## What it says, beyond S6

**Three of the catalogue's five topics do not distinguish players at this band**, so S6 is built on
two claims and is smaller than its catalogue entry. The catalogue's own warning — *"a correct outpost
detection may still be a trivial edge knight"* — is now measured rather than anticipated, and it
turns out to be right about holes and bishops and wrong about outposts.

**The split is not random.** The three failures are all about *what the player's position looks
like*: a hole in their camp, a bishop behind its own pawns, a rook off the open file. The two
survivors are about *what the opponent gets*: a knight that cannot be chased, a rook on the second
rank.

The same line runs backwards through the project. S5's `concedes_weakness` — the player's own
structure — spreads 1.20–1.85, mostly at the bottom. S1's `allowed_motif` — what punishes the player
— fires readily. **Claims framed as what your opponent achieves against you discriminate; claims
framed as what your position contains do not.** Recorded as **L-024** and carried into S7 and S8 as
a design prior rather than a conclusion.

## Honest limitations

- **Approximate eligibility.** No engine, so decided positions are not excluded. That inflates all
  five rates equally and should not change their *relative* spread, which is what the screen uses.
- **Spread is a crude statistic.** p90/median on 38 players is noisy, and nothing here is a
  significance test — it is a triage tool for deciding what to build.
- **A failed candidate is not disproved**, only shown not to discriminate *in 24-game corpora at this
  band*. The screen is a minute's work and can be re-run on deeper histories.
- **The two survivors are rare** — under 1 % of moves — so many players will not have enough distinct
  games for them to clear the confidence gate.
