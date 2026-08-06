---
id: cas-exp-e12
title: 'E12 — Corpus depth beats breadth of sections'
desc: 'Rebuilding on 150-game histories took coverage from 53% to 83%. Six sections had taken it from 24% to 53%.'
updated: 1786492800000
created: 1786492800000
---

# E12 — Corpus depth beats breadth of sections

**Answers:** [[state]]'s P0 after S8 · **Date:** 2026-08-06 · **Status:** done — **decisive**

## Question

Three consecutive section screens had returned two viable claims, none, and one that reached nobody
new, while coverage sat at 20 of 38 players. The hypothesis: the binding constraint is not the range
of things the swarm can diagnose but **`FOCUS_DISTINCT_GAMES = 5` on 24-game corpora** — a weakness
appearing in three of a player's games cannot clear a five-game floor however well the section
measures it.

## Method

Rebuild both halves on the E05 deep histories: **84 players × ~150 games** (11,890 games), against
the previous 38 × ~24.

The peer reference and the profiles both had to move. A deeper *reference* only sharpens the
population rates; `FOCUS_DISTINCT_GAMES` counts the **diagnosed player's own** games, so the gain
had to come from deeper player corpora.

Cost: **76,909 uncached positions**, about 45 minutes at 8 workers. Everything else was already in
the cache from E05 — the deep histories were fetched and largely analysed for the drift experiment,
so this rebuild was mostly paid for already.

## Result

| | 24 games, 38 players | 150 games, 84 players |
|---|---|---|
| **players advised** | 20 of 38 — **53 %** | 70 of 84 — **83 %** |
| **told nothing** | 47 % | **17 %** |
| distinct claim kinds | 16 | **27** |
| mean pairwise overlap | 0.06 | **0.05** |
| groundedness | 100 % | **113/113** |
| priorities per player | never > 2 | never > 2 |

**Sections S3–S8 together moved coverage from 24 % to 53 %. Corpus depth alone moved it to 83 %** —
and overlap *fell*, so the extra advice is more specific rather than more generic.

## What the deeper reference did, separately

Comparing the two references directly: **14× the evidence, and most rates barely moved.**

| | change from 38 → 84 players |
|---|---|
| the common claims (`long_think_error`, `early_error`, `concedes_weakness`, …) | under ±5 % |
| **the rare ones** | `allowed_motif.backRankMate` **−53 %**, `missed_motif.capturingDefender` **+40 %**, `endgame_error.minor` **+33 %**, `allowed_motif.skewer` **−21 %** |

L-013 recorded that population rates converge fast, measured on the frequent claims. **That was right
for frequent claims and wrong for infrequent ones** — and every section built since then leans on
infrequent claims. A `backRankMate` peer rate that halves is the difference between a finding and
silence for anyone near the boundary.

## The floor became load-bearing

[[open-questions]] D12 added a magnitude floor to `focus` two cycles ago, chosen so that it removed
none of the 40 findings then in existence — the smallest was 1.40 and the floor is 1.25. It was
explicitly built for a future large-denominator section rather than for the present.

That future arrived here:

| corpora | detected findings | min ratio | median | advised below 1.4 |
|---|---|---|---|---|
| 24 games | 46 | **1.40** | 1.94 | 1 |
| 150 games | **192** | **1.25** | 1.66 | **11** |

**The distribution is now truncated exactly at the floor.** On shallow corpora nothing came near it;
on deep ones claims are queuing beneath it. Without D12 those would be findings — real, reliable, and
too small to say.

The floor is **left at 1.25**. The arbiter's two-priority cap already filters the weakest: advised
findings have a median ratio of 1.75 against 1.66 detected, and three-quarters of what a player hears
is at least 1.56. But the value has changed status — it was a safety net and is now a live parameter
deciding what the weakest advice sounds like, and it should be revisited against real players rather
than against the finding distribution.

## Consequences

1. **The peer reference and the working corpus both move to the deep histories.** 24-game corpora
   remain the realistic case for a new user, and that is now a *stated operating limit* rather than
   the default everything is measured on.
2. **Stop treating section count as the coverage lever.** L-026.
3. **D12 reopens as a calibration question**, not a design one.

## Honest limitations

- **The 84 players are not a fresh sample.** They are the E05 deep histories, discovered from the
  same rating band and time control, and 38 of them are the original reference population.
- **83 % coverage is coverage, not correctness.** Nothing here says the extra findings are *right* —
  only that the swarm now has enough evidence to speak about far more players.
- **A real user brings 24 games, not 150.** The honest reading is that the swarm needs a deep history
  to work well, which is a constraint on who it can help rather than a solved problem.
- **Fourteen players are still told nothing**, and no attempt was made to find out what they have in
  common.
