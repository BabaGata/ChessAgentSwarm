---
id: cas-exp-e22
title: 'E22 — The corpus was sliding, not accumulating, and no store was needed to fix it'
desc: 'A returning player was diagnosed on no more evidence than the first time. The fix is the size of the fetch, not a local game store: Lichess is the archive.'
updated: 1786492800000
created: 1786492800000
---

# E22 — Accumulating the corpus

**Answers:** step 6 of [[design.short-history-prioritisation]] · **Date:** 2026-08-06 ·
**Status:** done — **smaller than the plan implied, and measured**

## What the plan said, and what was actually wrong

> **Diagnosis** runs on the accumulated corpus, so a returning player has *more* evidence than at
> first contact, not less.
>
> — with the cost noted as *"needs corpus identity and storage the CLI does not currently have"*.

**Two things in that were wrong.**

**The storage was never needed.** Lichess keeps a player's whole archive, free and complete. The
swarm does not have to remember a player's games; it has to *ask for enough of them*. What the plan
called a storage problem was a **request-size** problem.

**And half of the layer was already built.** `check-progress` has always measured over the games
played *since* the plan, using `CorpusRef.game_ids` — the docstring says *"a rate over the whole
corpus would be diluted by the very games that produced the diagnosis"*. Layer 5's harder half was
done before the plan proposed it.

## The real defect

`coach --games 60` fetches the **60 most recent** games. So a player who returns after twenty more
games is diagnosed on twenty new and forty old — the window **slides**. They played more chess and
the swarm knows no more than before, which makes coming back pointless in exactly the loop V7 exists
to run.

## What was built

`games_to_fetch(window, previous)`: with a previous profile, ask for that corpus **plus** the window,
capped at `MAX_ACCUMULATED_GAMES = 300`. `coach --previous PROFILE.json` supplies it.

The cap exists because C1 is a constraint rather than an aspiration: without it a player with four
thousand games would trigger a four-thousand-game analysis on their second visit. 300 is deep enough
that the corpus stops being what limits the diagnosis — E12 measured 150-game histories advising
83 % of players.

## What it costs — measured, warm cache

| | games | moves | time |
|---|--:|--:|--:|
| first session, 24 rapid | 24 | 1,051 | **0.8 s** |
| second session, blitz pooled in | 69 | 3,730 | **1.2 s** |
| a long history, 150 rapid + blitz | 197 | 9,625 | **2.2 s** |

**A 197-game pooled diagnosis takes 2.2 seconds.** 2.9× the games costs 1.6× the time, and findings
rise with the corpus — 5 → 6 → 10.

This is the measurement that makes accumulation affordable, and it is a property of the **cache**: a
returning player's old games are precisely the ones already in it, so the only engine cost is the
games they have played since. Growing the corpus is close to free; the cost lives entirely in first
contact.

## D9 needs re-timing, and this is not it

The session figure in [[state]] predates blitz. On a warm cache a deep pooled session is ~2 s, but a
**fresh** player now brings up to 5× the games, and E01's throughput (89 s per 50 games at depth 15,
before parallelism and opening dedup) puts a 300-game cold start in the minutes rather than the
~2 minutes D9 currently claims. That figure has not been measured end to end since blitz was
admitted and should not be quoted until it is.

## Honest limitations

- **No two-session run against the live API was performed.** It needs real elapsed time and a player
  who actually plays in between; what is tested is the arithmetic of the window and the cost of the
  analysis, not a month of someone's life.
- **The cap is a guess with a rationale, not a measurement.** 300 is justified by E12's 150-game
  result, not by anything measuring where returns actually flatten.
- **Recency is not yet applied** (step 7). A 300-game corpus may reach back years, and the swarm
  currently weights a game from 2019 exactly like one from last week. E19 found a quarter of players
  have windows spanning 90+ days; accumulation makes that worse before step 7 makes it better.
