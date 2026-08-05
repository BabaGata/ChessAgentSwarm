---
id: cas-agent-s6
title: 'Agent S6 — Squares, files and piece placement'
desc: 'Built on two claims out of five candidates, chosen by a population screen run before the section rather than after it.'
updated: 1786320000000
created: 1786320000000
---

# Agent S6 — Squares, files and piece placement

**Section:** [[domain.sections]] → S6 · **Status:** **built and assessed**
**Design precedes code**, per the guardrail in the `adaptive-cycle` skill.

> **Built.** `chesscoach/squares.py` + `chesscoach/sections/s6_squares_and_files.py`, 34 tests.
> Registration one line again — ADR-0006's fourth test.
>
> | | before S6 | after S6 |
> |---|---|---|
> | players advised (of 38) | 19 | **20** |
> | silent | 19 | **18** |
> | distinct claim kinds | 13 | **15** |
> | mean pairwise overlap | 0.08 | **0.06** |
>
> **Both features fire**, which is the § 9.1 promise kept: `outpost` twice and `rook_seventh` once,
> across three players, at ratios 1.93–2.34. Compare S3, whose five material classes fired for
> nobody, and S5, where `doubled` and the pooled claim fired for nobody. **This is the first section
> where no claim was dead weight** — because it is the first where the claims were chosen by
> measurement instead of by the catalogue.
>
> **And it is small**, exactly as § 10 predicted. Three findings. The events are rare — under 1 % of
> moves — so `FOCUS_DISTINCT_GAMES` (five separate games) is the binding constraint, not the peer
> comparison. A section can be correctly designed, correctly built, and still mostly quiet.

## The screen came first this time

L-023 was learned expensively on S5: a section's claims are worth building only if players differ on
them, and S5 was fully built before that was checked. [[state]] now says to screen first. E09 did,
engine-free, in about a minute:

| candidate | p90/median spread | |
|---|---|---|
| `concedes_outpost` | **2.15** | **highest in the project** |
| `allows_rook_seventh` | **1.82** | comparable to `early_error.black` (1.92) |
| `cedes_open_file` | 1.31 | fails |
| `bad_bishop` | 1.27 | fails |
| `concedes_hole` | 1.25 | fails — sits exactly on S5's suppressed `concedes_weakness.any` |

**S6 is built on the first two and nothing else.** The catalogue names five topics; three of them
turn out not to distinguish players at this band, and the section is smaller than the catalogue
entry as a result.

### The pattern the screen exposed, which is bigger than S6

The three that fail are all about **what the player's position looks like** — a hole in their camp,
a bishop hemmed by its own pawns, a rook not on the open file. The two that succeed are about
**what the opponent gets** — a knight settled where it cannot be evicted, a rook on the second rank.

The same split runs backwards through the project. S5's `concedes_weakness` — the player's own
structure — spreads 1.20–1.85, mostly at the bottom. S1's `allowed_motif` — what punishes the player
— fires readily. **Claims framed as *what your opponent achieves against you* discriminate; claims
framed as *what your position contains* do not.** That is a hypothesis worth carrying into S7 and S8,
and it is recorded as **L-024**.

## 1 · Remit

**What the player's play lets the opponent establish.** Two things, both permanent and both the
opponent's to enjoy:

- a **knight settled on an outpost** in the player's half, pawn-backed and unevictable;
- a **rook reaching the player's second rank**.

**Explicitly not its business.** Whether the player's own squares are weak — E09 says players do not
differ on that. And what to do instead, which is a recommendation problem.

## 2 · Knowledge organisation

Two detectors, both extending E02's outpost definition rather than inventing one:

| feature | definition |
|---|---|
| `outpost` | enemy knight on ranks 4–6 of the player's half, defended by an enemy pawn, on a square **no pawn of the player's can ever advance to cover** |
| `rook_seventh` | enemy rook on the rank where the player's pawns began |

The third condition on `outpost` is what makes it permanent rather than merely annoying, and is the
one casual definitions omit (E02, L-004).

## 3 · Agent type

**Deterministic, no engine calls of its own.** Both are pure board properties, and the position after
the opponent's reply is already the `fen_before` of the observation two plies on.

## 4 · Knowledge maintenance

The detectors are the tunable state. `outpost` inherits E02's hand-verified definition from the
opposite side; `rook_seventh` is exact and needs no calibration. Neither has been hand-checked
against real games *in this direction*, which is the weaker part and is stated rather than hidden.

## 5 · Tools

`chesscoach.squares` (the detectors), `chesscoach.analysis.observations`, `chesscoach.sections.base`,
`chesscoach.confidence`, `chesscoach.peers`.

## 6 · General instruction

1. **Judge across the opponent's reply, not the player's move.** What a player concedes is realised
   in the answer. Measuring across their own move alone finds almost nothing — E09's first pass did
   exactly that and reported two rates of zero, which was wrong rather than interesting.
2. **Count creation, never presence** (E02: presence is uninformative).
3. **Peer-compare or stay silent.**
4. **Zero findings is a valid output.**

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| observations | `tuple[Observation, ...]` | analysis core — `fen_before`, `mover_is_white`, `ply` |
| corpus, provenance, band, time_control, peers | | as every section |

## 8 · Outputs

| `claim.kind` | Subject | Meaning |
|---|---|---|
| `allows_square` | `any` | pooled — how often the player's move lets the opponent establish something permanent |
| `allows_square` | `outpost` / `rook_seventh` | the same, per feature |

Aggregate-first per L-022, with `drop_redundant_aggregates()` handling the pooled/specific overlap.

**`gap_type` is `unknown`, `determined_by = inferred`.**

## 9 · Efficacy measure

1. **Already answered, in advance:** the deviation exists — 2.15 and 1.82, the top of the range this
   project has measured. This is the first section to clear § 9.1 before being written.
2. **Does it move E08's coverage**, without raising overlap?
3. **Do both features fire**, or only one (S3's material classes; S5's `doubled`)?
4. **Split-half replication and peer comparison**, as the policy requires.

## 10 · Cost profile

Zero marginal cost. Two board scans per diagnosable move.

## Known limitations, recorded before building

- **Rare events.** Median rates are 0.8 % and 1.0 % of moves — roughly five to seven instances per
  player per 24 games. The denominator is large (≈660) but `FOCUS_DISTINCT_GAMES` needs five separate
  games, so many players will fall short and the section will be quiet for them.
- **Conceding an outpost is not necessarily an error**, exactly as in S5 — sometimes the square is
  worth giving for something concrete, and nothing here distinguishes that from not noticing. This is
  probe material (V9).
- **`rook_seventh` counts arrival, not damage.** A rook on the seventh in a dead-drawn endgame counts
  the same as one that ends the game.
- **Neither detector is hand-verified in this direction.** E02 verified outposts as an asset for the
  side that owns them; this section reads them as a concession by the other side, which is the same
  geometry but has not been eyeballed on real positions.
- **Three of the catalogue's five topics are dropped**, so S6 does not cover holes, bad bishops or
  open-file usage at all. E09 is the evidence; if a later, larger corpus shows they do discriminate,
  the screen is cheap to re-run.
