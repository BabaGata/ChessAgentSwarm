---
id: cas-exp-e83
title: 'E83 — The screen that decided what to build was ranking claims by how rare they are'
desc: 'The P1 was raised against a threshold that does not ship and closes as a non-finding. Underneath it, p90/median is bounded by 1/median, so it scored rarity as discrimination — E09 accept/reject is perfectly rank-ordered by base rate. Replaced with overdispersion: ten shipped claims do not separate players at all.'
updated: 1788573600000
created: 1788573600000
---

# E83 — Re-screening discrimination, and finding the screen was the defect

**Answers:** the P1 *"the L-024 spreads are near the rejection band"* ·
**Code:** `experiments/e83-spread-rescreen/` · **Date:** 2026-09-04 ·
**Status:** done — **the P1 closes as a non-finding and a larger one replaces it**

## The P1 was raised against a threshold that does not run

[[experiments.e82-move-number-rerun]] reported `allowed_motif` falling to **1.13×** and I opened a
P1 saying a live claim sat inside the band [[experiments.e09-square-candidates]] used to reject
detectors. **That 1.13× is the 10 wp row, and `analysis/labels.INACCURACY_WP` is 5.0.** At the
threshold that actually ships the fall was 1.59× to 1.34× — above the line, not inside it.

Re-measured on the peer reference's **83 players** rather than E33's 12, `allowed_motif` split by
motif runs **1.32× to 2.88×**, and its weakest arm straddles the line rather than failing it.
**The P1 is closed as a non-finding.** It was my own misreading of which row shipped.

## What the re-screen found instead

Four claims had bootstrap intervals **entirely below** E09's line. Three were `executed_motif`,
which `s1_tactical_gaps.NOT_ASSERTED` never reports — *"it is not a weakness and must not be
reported as one"*. Screening a competence measure against a weakness calibration is a category
error, and a player who captures every hanging piece **should** look like every other player.

That left `long_think_error` at **1.19× (1.13–1.27)** — asserted, and recorded across the vault at
**1.60**, where it serves as the project's floor: [[experiments.e11-attack-candidates]] shipped
`allows_king_pressure` at 1.59 because it *"sits just under `long_think_error` (1.60), which does
produce findings"*, and S5 and S8 both cite it the same way.

## p90/median cannot exceed 1/median

A rate cannot exceed 1.0, so **the statistic is bounded above by the reciprocal of the median**. A
claim firing on 81 % of its opportunities cannot score above 1.24 however cleanly it separates
players. Across 54 shipped claims, base rate correlates with spread at **r = −0.53**, and the
fraction of arithmetically available headroom each claim used inverts the ranking completely:

| claim | median | ceiling | spread | % of ceiling used |
|---|--:|--:|--:|--:|
| `executed_motif.hangingPiece` | 0.809 | 1.24× | 1.09× | **88 %** |
| `executed_motif.capturingDefender` | 0.646 | 1.55× | 1.24× | **80 %** |
| `long_think_error` | 0.389 | 2.57× | 1.19× | 46 % |
| `allows_square.outpost` | 0.010 | 97.7× | 1.58× | **2 %** |
| `allows_square.rook_seventh` | 0.006 | 167× | 1.81× | **1 %** |

## E09's verdict column is perfectly rank-ordered by base rate

E09's own table carries the confound, and nothing in this experiment was needed to see it:

| candidate | median rate | spread | verdict |
|---|--:|--:|---|
| `concedes_outpost` | 0.0077 | 2.15 | **accepted** |
| `allows_rook_seventh` | 0.0102 | 1.82 | **accepted** |
| `cedes_open_file` | 0.2866 | 1.31 | rejected |
| `bad_bishop` | 0.3966 | 1.27 | rejected |
| `concedes_hole` | 0.1963 | 1.25 | rejected |

**Accepted at 0.008 and 0.010; rejected at 0.196, 0.287 and 0.397, with no exception.** The two
built candidates are the two rarest by a factor of twenty to fifty. E09 called the statistic *"a
triage tool for deciding what to build"* and warned it was noisy on 38 players; it was not warned
that it was not scale-free, and **S6 was built on its two lowest-headroom candidates**.

## The replacement: do players differ by more than sampling noise?

Under a null where every player shares one rate, each player's count is binomial. Pearson dispersion
— observed variance over binomial variance — is **1.0 when players are interchangeable** and rises
with real separation **at any base rate**. Base rate now correlates at **+0.12**, against −0.53.

The ranking inverts for exactly the claims the old screen favoured:

| claim | old spread | dispersion | p |
|---|--:|--:|--:|
| `allowed_motif.backRankMate` | **2.88×** *(best in project)* | **0.60×** | 0.93 |
| `allowed_motif.skewer` | 1.93× | **0.83×** | 0.84 |
| `allows_square.rook_seventh` | 1.82× *(E09 accepted)* | **1.25×** | 0.061 |
| `allowed_motif.fork` | 1.57× | **1.15×** | 0.17 |
| `long_think_error` | 1.19× *(my alarm)* | **2.69×** | 2e-14 |
| `executed_motif.hangingPawn` | 1.23× | **2.53×** | 1e-12 |

**`long_think_error` separates players fine.** My alarm was wrong in the opposite direction from the
one I raised it in.

## Bracketing what clustering can do

Moves inside one game are not independent trials, so dispersion is **inflated** and "separates" is
the optimistic verdict. The inflation is bounded: if outcomes within a game were perfectly
correlated a game would carry one trial, so dividing by mean opportunities-per-game gives a floor.

| | claims |
|---|--:|
| separate under **any** clustering | **22** |
| depend on how correlated moves within a game are | 23 |
| **do not separate even assuming independence** | **10** |

**The last group is the robust finding** — it fails against the *optimistic* null, so no correction
can rescue it. Nine of the ten are asserted (`executed_motif.discoveredAttack` is not):

`allowed_motif.backRankMate` · `allowed_motif.fork` · `allowed_motif.skewer` ·
`allows_square.rook_seventh` · `concedes_weakness.isolated` · `missed_motif.discoveredAttack` ·
`missed_motif.fork` · `missed_motif.trappedPiece` · `slow_development.own`

`allows_square.rook_seventh` is **E09's second accepted candidate** and the claim
`squares.rook_seventh_preventable` was built for. `allows_square.outpost`, E09's flagship, lands in
the undecided group at 1.94× — not vindicated, only not refuted.

## Two defects in this experiment's own code, both found by reading output

- **The design-effect floor divided by a value below one.** Claims offering fewer than one
  opportunity per game — forks are not available every game — had their bound *inflated* by the
  correction meant to lower it, and `missed_motif.fork` (dispersion 0.94, p = 0.59) was reported as
  separating under any clustering. Clustering can only shrink effective sample size; the design
  effect floors at 1.
- **The guard order hid four more.** `floor > 1` was asked before the p-value, so claims with
  dispersion 1.04–1.37 at p of 0.09–0.38 were reported as certain. A point estimate above 1 is not
  significance. **This is [[learning.lessons]] L-055 a second time, in code written the same day the
  lesson was recorded.**

## Honest limitations

- **Dispersion says players differ, not that the claim measures a skill.** `plays_queenless` scores
  **50.4×** and is a style variable, not a weakness. A high score licenses nothing on its own; this
  screen only replaces the one that answered the same question badly.
- **E09's rejected candidates were never built**, so they cannot be re-screened. The inversion is
  inferred from the medians E09 recorded, not measured on those detectors.
- **23 claims stay undecided** and settling them needs per-game counts, which the peer reference does
  not store — it aggregates to player and stratum.
- **One corpus at one depth.** The reference is `peers-3af3206`, and nothing here re-runs detection.
- **Nothing is retired by this note.** Ten claims failing a screen is a finding to act on, not an
  action; what to do about nine asserted claims that do not separate players is the author's call.
