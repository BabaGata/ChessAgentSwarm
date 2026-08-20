---
id: cas-exp-e39
title: 'E39 — A 20-game read and a 50-game report disagree three times in four'
desc: 'The swarm changes its own leading finding 75% of the time between a 20-game window and the full corpus. The reviewer reads 20; the report is built from ~50. Most of the disagreement the review would measure is sampling.'
updated: 1787788800000
created: 1787788800000
---

# E39 — Is a 20-game read enough to judge a player?

**Answers:** the reviewer's question six players in · **Code:** `experiments/e39-review-window/` ·
**Date:** 2026-08-19 · **Status:** done — **not as the review is currently set up, and the fix is cheap**

## The question

> "I reviewed 20 games per player up to maikel5, is this going to be enough."

Two power questions hide in that, and they have opposite answers.

**The move-level comparison is fine.** Six players have produced **270 checkable annotated moves**
(bjagus 20, cademan 66, Crossfire1983 72, goydorak 37, Hirsican 55, maikel5 20), and
[[experiments.e31-move-level-agreement]] already runs the swarm over **the same 20 games** the
reviewer read. That comparison is matched and well powered.

**The ranked agreement test is not.** It asks whether the swarm's top finding appears in the
reviewer's ranked slots for ≥ 7 of 12 players — but the reviewer ranks from **20 games** while the
report in `b-the-system/` is built from the player's **whole corpus, ~50 games**. If those two
windows do not agree about what a player's main weakness is, the test measures the mismatch rather
than the diagnosis.

## Result — the swarm disagrees with itself

Twelve players, same reference, same depth. Leading priority from the first 20 games against the
leading priority from the whole corpus:

| | |
|---|--:|
| **top finding identical** | **3 / 12 — 25 %** |
| full-corpus top appears anywhere in the window's three | 5 / 12 — 42 % |
| window says nothing at all | 0 / 12 |
| median claims shared, out of three | **1.0** |

| player | 20-game top | full-corpus top | |
|---|---|---|---|
| bernes | `allowed_motif.hangingPiece` | `allowed_motif.hangingPiece` | ✓ |
| bjagus | `allows_square.outpost` | `allows_square.outpost` | ✓ |
| Sheriwoyama | `long_think_error` | `long_think_error` | ✓ |
| cademan | `advantage_error.clear` | `allowed_motif.fork` | ✗ |
| Crossfire1983 | `allows_pressure.king` | `allows_square.rook_seventh` | ✗ |
| goydorak | `early_error.white` | `allows_pressure.king` | ✗ |
| Hirsican | `allowed_motif.fork` | `concedes_weakness.isolated` | ✗ |
| maikel5 | `endgame_error.rook_minor` | `time_pressure_error.clock` | ✗ |
| maxhayastan | `advantage_error.clear` | `allows_pressure.king` | ✗ |
| Maximilian_Honigtopf | `early_error.black` | `allowed_motif.fork` | ✗ |
| Odin5306 | `moved_into_attack` | `allows_pressure.king` | ✗ |
| simonvj | `long_think_error` | `moved_into_attack` | ✗ |

**Three quarters of the time the swarm changes its own mind between the two windows**, and the
median overlap between the two top-threes is a single claim. So a reviewer who reads 20 games and
disagrees with a 50-game report is, most of the time, disagreeing with a *different sample* rather
than with the swarm's judgement.

This is [[experiments.e17-ranking-stability]] confirmed and sharpened. E17 found severity rankings
agreeing 65 % at 20 games; measured again after the threshold moved to 5.0, with S7 added and against
the full-size reference, the leading claim survives only 25 % of the time. The claim set is wider now
and the competition for the top slot correspondingly fiercer, so instability at the top has got
worse rather than better.

## Consequence — match the windows

**The report for each reviewed player should be generated from the same 20 games the reviewer read.**
That makes the comparison apples-to-apples, and any remaining disagreement is genuine.

It is cheap: the games are already fetched and analysed, and no reviewer work is invalidated —
Form A answers are about the games, not about the report.

**What it costs, stated plainly.** Twenty games is close to the swarm's floor: `FOCUS_GAMES_WITH_DATA`
is 20, so `focus` is only just reachable and more of the three slots will be filled from the cost
pool rather than from peer-relative findings. The review would therefore be judging the swarm **at
its weakest operating point** rather than at the ~50 games a real session fetches, and the thesis has
to say so. That is a smaller distortion than comparing two different samples, which is what the
current design does.

**The alternative was considered and rejected.** Asking the reviewer to read all ~50 games per player
would cost roughly 6 hours each — about 72 hours for twelve — against the 2 h 30 per twenty games
they have measured. Not available.

## Honest limitations

- **"First 20 games" is not necessarily the 20 the reviewer read.** They are taken in file order,
  which is the order the reviewer opened them, but that is an assumption rather than a record. Form A
  now asks how many games were read; it does not ask *which*.
- **Twelve players.** 3/12 has a wide interval; the honest reading is "the leading finding is
  unstable at this window", not "exactly 25 %".
- **This measures the swarm's stability, not the reviewer's.** A human reading 20 games may well form
  a more stable impression than the swarm does — chunking across games is what expertise is for —
  and nothing here tests that.
