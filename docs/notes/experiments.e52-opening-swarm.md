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

## Revised the same day → [[decisions.0015-a-learned-skip-list-and-a-bullet-brief]]

The author read the trace above and redirected the design: sites like TikTok belong on a **skip
list** the Scout consults before fetching and the Assessor maintains; the Assessor's real job is
**reading text and keeping the sentences that matter**; and the Compiler should emit **bullet
points**, leaving prose to whichever agent finally speaks to the player.

Built and tested. **Not validated live**: by the time it was finished every engine SearxNG queries
was rate-limited — brave and google cse *"Suspended: too many requests"*, startpage *"CAPTCHA"* — so
the live run reports zero pages and says nothing about the design either way. `SearxSearcher` now
raises on that instead of returning empty, which is **L-046's fifth instance here**.

Run offline against cached pages, the Assessor keeps sentences and classifies a text-free page as
`no-text`, and **every Compiler bullet was dropped** — *"names moves not in the source: e5, d5"* —
because it had two weak notes to work from. The checker behaving correctly on bad input.

**The finding that survives every variation tried today: the binding constraint is note supply.**
Invented bullets, restated opponent halves and empty briefs all trace to the same place, and no
change to the agents' logic has moved it.

*(One flaw in the offline harness, stated rather than hidden: it matches cached pages to openings by
a word in the URL, and paired an alexcolovic Pirc page with the London System.)*

## The note supply, located and fixed

The author's correction: *"It keeps sentences a 1500 can use, this doesn't has to be disregarded,
compiler will be the one that writes something understandable, more information is better than just
disregarding it. Fix the note supply."*

**Both halves were right.** The Assessor was filtering for *readability*, which is the Compiler's
job, and the supply was three notes from seventeen pages.

The loss was located stage by stage before anything was changed, with no model involved:

| stage | count across 38 cached pages |
|---|--:|
| blocks | 5,653 |
| sentences | 11,161 |
| inside the length window | 4,223 |
| passing the veto | **1,061** |
| **reaching the Compiler** | **3** |

**So the filters were never the constraint.** Probing the Assessor directly found it: handed 50
numbered sentences, `qwen2.5:3b` answered **`NONE` on four pages of six**. At 25 it answered with
indices; at 12 it answered `NONE` on six of six. Batch size was not the variable — **the prompt was**.
It listed six DROP rules against three KEEP rules and offered an explicit `NONE`, so *filtering* was
the frame and refusal the attractor. One answer came back `'3, NONE'`.

Reframed as **ranking** — *"pick the {limit} most informative"* — pages yielding notes went
**1 of 6 → 4 of 6** with no other change.

Four fixes, each from something observed:

- **`is_usable_note`** replaces `is_admissible` at this stage: relevance and information, never
  readability. A sentence naming the Maroczy bind is now kept and translated later.
- **Chunking**, 25 sentences per question, so the whole article is read instead of its first 50.
- **`FIRST_PERSON` was case-sensitive**, so *"Oh me i also play it against d4 and c4"* reached the
  Compiler as a note.
- **`STATISTIC` and `NAVIGATION`**, after loosening the veto let through *"At 1200 Elo, the top reply
  is d4, played 33.4% of the time"*, *"Across 50.8 million Lichess games…"*, a breadcrumb trail and
  an emoji menu item. Loosening a filter is not free and the cost showed up immediately.

| | before | after |
|---|--:|--:|
| notes reaching the Compiler | 3 | **~30** |
| openings with a brief | 0 of 5 | **5 of 5** |
| plan points | 0 | **8** |
| **opponent points** | **0** | **8** |

**The opponent half now works**, having been 0 in every previous run.

## The novelty ceiling was swept and left alone

The Compiler is now told to translate hard terms, which introduces words the source never used — so
the ceiling was measured rather than assumed:

| ceiling | false claims passing |
|---|--:|
| 0.35 | 2 % |
| **0.45 (shipping)** | **4 %** |
| 0.55 | 10 % |
| 0.65 | 23 % |

Raising it to 0.55 would have recovered four dropped points at **2.5× the false-claim rate**. With
the supply fixed the system is no longer starved, so the trade is refused and 0.45 stands.

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
