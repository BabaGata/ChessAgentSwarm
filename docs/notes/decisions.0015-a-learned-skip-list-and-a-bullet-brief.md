---
id: cas-adr-0015
title: 'ADR-0015 — A learned skip list, an Assessor that reads text, and a brief made of bullets'
desc: 'The Assessor moves from judging titles to reading sentences; the cheap permanent judgement becomes a deterministic skip list it maintains, under four guards. The Compiler emits bullet points so one bad point is dropped instead of a paragraph.'
updated: 1788480000000
created: 1788480000000
---

# ADR-0015 — A learned skip list, and a brief made of bullets

**Status:** accepted · **Date:** 2026-08-28 · **Revises:**
[[decisions.0014-three-agents-for-the-opening-brief]]

## Context

Reading the swarm's first real trace, the author objected to three things at once:

> *"tiktok.com → video, reddit.com → forum or comment thread. this kind of resources should be on the
> skip list of the scout and the assessor should update the skip list for such resources … The main
> function of the assessor should be to investigate text and remove sentences that are not important
> for the plan … the compiler does not have to make proper paragraphs but bullet points should be
> better."*

All three are right, and together they say the Assessor was pointed at the wrong problem. It was
spending a model call per search result to conclude that TikTok hosts videos — a permanent fact about
a domain, re-derived every run — while nobody was reading the page text where only a reader helps.

## Decision

**1. A deterministic skip list, seeded and then learned.** Domains that cannot carry plan-level prose
are filtered *before* fetching. The Assessor adds to it when a page turns out not to be an article.

**This is the only persistent state in the project a language model may write to**, and a poisoned
skip list fails silently and forever — the swarm would stop finding a good source and nothing would
say why. Four guards:

| | |
|---|---|
| **domains only, never paths** | a model cannot exclude one article |
| **a reason from a fixed set** | `social video shop database forum no-text`; anything else is refused |
| **a site that has ever helped can never be skipped** | the load-bearing one |
| **plain JSON, with who added each entry and when** | the author reads the list in a minute |

And the model is only asked to classify a page that **already failed to yield readable prose**, so it
never gets the chance to condemn a site it merely disliked.

**2. The Assessor reads text, not titles.** Its job is now: keep the sentences a 1500 could use, drop
history, definitions, move lists, advertising and study advice. It answers with **indices**, so a
kept sentence is the page's own words by construction, and the non-plan filters from E51 stay as a
veto over its choice.

**3. The brief is bullet points.** Each point is grounded-checked on its own, so one bad point is
dropped instead of a whole paragraph. Joining points into sentences belongs to the agent that finally
speaks to the player, which knows the rest of that player's profile.

**4. The opponent half is wanted, not required.** `Brief.accepted` needs plan points only, and the
Compiler is told in as many words that writing no `WATCH` lines is correct when the notes do not
support them.

## Consequences

- `chesscoach/skiplist.py`; `Assessor.read` and `Assessor.classify`; `Brief` becomes points.
- **A bug the change exposed:** `ollama.indices` read bare digits, so a model answering *"Black should
  break with **c5**"* selected sentence five. Answering by index is meant to make prose harmless, and
  it did not. A list item must now stand alone as a token.
- **A second one, in the same family:** SearxNG reports `unresponsive_engines`, and the field was
  ignored — so a rate-limited run read as *"the web has nothing on this opening"*. It raises now.
  **This is L-046's fifth instance in this project**, which is itself worth a note.

## What this does not settle

**The binding constraint is note supply, and it has been all along.** Every failure measured today —
invented bullets, restated opponent halves, empty briefs — traces to the Compiler being handed one or
two weak sentences and filling the gap. The agents' logic is covered; what is not solved is getting
enough good sentences out of the pages the web actually returns.

**And this revision is not yet validated live.** Every search engine SearxNG queries was rate-limited
by the time it was finished, so the live run reports zero pages and says nothing either way. What is
verified is the logic, in tests, and the Assessor and Compiler against cached pages.
