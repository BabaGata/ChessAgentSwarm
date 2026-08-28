---
id: cas-exp-e52
title: 'E52 — The swarm writes a plan and cannot write the opponent half'
desc: 'Scout, Assessor and Compiler run end to end from an opening name. Roles execute, the Assessor discards 12 of 17 pages with reasons, and a PLAN survives for well-covered openings. Every WATCH half fails, and the cause is that nothing retrieved describes the opponent.'
updated: 1788480000000
created: 1788480000000
---

# E52 — Can three agents turn an opening name into a brief?

**Answers:** the author's *"multiple results … an assessment agent that will review the results and
discard what are not good at all … a compiler agent [that] will compile a short description of the
plan for the player and what should be careful as a response of the opponent"* · **Code:**
`chesscoach/opening_swarm.py`, `experiments/e52-opening-swarm/` · **Date:** 2026-08-28 ·
**Status:** done — **half the brief works; the other half fails for a reason worth naming**

## The design under test

    SCOUT      writes queries, casts a wide net       judges nothing
    ASSESSOR   discards the unusable, with reasons    writes nothing
    COMPILER   writes the brief from what survived    searches nothing

→ [[decisions.0014-three-agents-for-the-opening-brief]]

## The test set was split on purpose

An all-zero run on obscure openings cannot distinguish *"the swarm does not work"* from *"these
openings have no good pages"* — the L-046 shape again — so three uncovered openings run beside three
the author has already seen good material for.

| | Bird, Grob, Owen | Pirc, London, French |
|---|--:|--:|
| a usable brief | **0 of 3** | **1–2 of 3** |

**The split is the result.** The swarm's failure on the Bird is a fact about the web, not about the
design. Its success on the Pirc is what shows the roles execute end to end.

## What each role actually did

**Scout.** 6 distinct pages for the Bird, **17 for the London** — against 3 from the single fixed
query the previous design used.

**Assessor.** For the London it kept 5 and discarded 12, naming each:

    uscfsales.com         a list of many different openings
    tiktok.com            video
    chesscheatsheets.com  move database or statistics table
    reddit.com            forum or comment thread

**The verdicts are better than the reasons.** It discards sensibly and then picks a category from the
prompt's own list — it called a Duolingo blog *"a forum thread"* and a TikTok link *"a move
database"*. Recorded as unreliable rather than trusted, since the reasons are shown to the author.

**Compiler.** For the Pirc:

> **PLAN** — *"Control the center with pawns on d6 and c6, and develop pieces harmoniously to prepare
> for counterplay."*
> source: `thechessworld.com/articles/openings/czech-pirc-complete-guide-for-black/`

## The finding: every WATCH half fails

| | |
|---|--:|
| PLAN halves that passed | **1–2 of 6** |
| **WATCH halves that passed** | **0 of 6, every run** |

Each was one of two things:

**A restatement.** The Pirc's `WATCH` was its `PLAN` with the colour flipped — *"Black will aim to
control the center with pawns on d6 and c6, and will develop pieces harmoniously"* — and it **passed
the grounding check**, because every word came from the source. This is
[[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]'s stated hole, occurring in
production. `_restates` now catches it, and the first threshold did not: dividing shared words by the
`WATCH`'s own length lets a model escape by padding, so the denominator is the **shorter** of the
two — the six shared words were 50 % of the `WATCH` and **75 % of the entire PLAN**.

**Or an invention.** *"novelty 82 %: white, likely, try, gain, control, ready, challenge"* — the
Compiler filling a gap from its own training, which is exactly what the check exists for.

**The cause is structural, not a prompt defect.** Every page the Scout retrieves is about the
player's plans, so no retrieved sentence says what the opponent does. The Compiler is asked for
something its notes cannot support and does the only thing it can.

Giving the Scout a second, opponent-facing query (*"how to play against the X main responses"*) was
tried. Briefs went 2 → 1. **That comparison is inconclusive**: the Scout runs at temperature 0.7, so
one run against one run cannot separate a change from noise. The query is kept because it is
principled and cheap; the claim that it helps is not made.

## Consequence

- **The swarm ships as the acquisition path for openings with no curated guide**, behind
  `reviewed=true` like everything else.
- **`WATCH` stays unsolved and is named as such.** The fix it points at is retrieval, not prompting:
  the Assessor and selector would need to look for sentences about the *other* side, which is a
  different screen from the one built.
- **`_restates` is a check the grounding gate cannot supply.** Worth generalising: the gate answers
  *"did this come from the source"* and says nothing about *"is this the same claim twice"*.

## Honest limitations

- **Six openings, one machine, and a non-deterministic Scout.** No number here should be read as
  repeatable to better than ±1.
- **Nothing is endorsed.** No source is `reviewed=true`, so no brief reaches a player.
- **Grounded is still not correct.** A brief that passes both checks can be wrong about chess; that
  is what the author's review is for and it has not happened.
