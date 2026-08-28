---
id: cas-adr-0012
title: 'ADR-0012 — Quote the plans from the page, never write them'
desc: 'The sentences the author endorsed turned out to be the source page''s own words. So the system selects sentences and attributes them, bounded, instead of paraphrasing — which reverses opening_guides'' "never from body text" rule and gives the reason.'
updated: 1788480000000
created: 1788480000000
---

# ADR-0012 — Quote the plans from the page, never write them

**Status:** accepted · **Date:** 2026-08-28 · **Supersedes a rule in:**
`chesscoach/opening_guides.py`

## Context

The author approved one guide — FreeChessTrainer's Pirc page — and asked for the same shape
everywhere:

> *"The short written descriptions in agent assessment are good and I would like similar short
> descriptions to be in other opening resources created by the agent. So I want the main lines to be
> fetched with maybe a few variants. Short summary or description of the information about the plans
> and a link for further references."*

**The first thing checked was who wrote those descriptions**, because the answer decides everything
that follows. They are **verbatim page text**:

> *"Black allows White to occupy the center with pawns on e4 and d4, aiming to undermine it later
> with well timed pawn breaks and piece pressure."*

found at character 171 of the fetched page. So what was endorsed was **FreeChessTrainer's writing,
selected** — not the agent's writing.

That matters because [[decisions.0011-detection-correctness-over-expert-agreement]] and R-03 forbid
exactly the other reading. If the agent were being asked to *write* short plan summaries, the answer
would have to be no: LLM-generated chess advice presented as knowledge is the folklore this project
refuses to launder.

## Decision

**The system selects sentences from the linked page and quotes them, attributed and bounded. It
never writes one.**

Choosing which of a page's sentences answer *"what should I aim for?"* is a text-processing
question, and this project may answer those. Deciding what the plans **are** is a chess question, and
it may not.

Three parts assembled from three places, deliberately kept apart:

| part | source | needs endorsement? |
|---|---|---|
| the moves | `lichess-org/chess-openings`, CC0 | no — reference data |
| the plans | sentences quoted from the linked page | **yes** — quoting is endorsing |
| the link | the guide itself | yes, as before |

**This reverses a rule stated in `opening_guides.py`**, which held that a summary is taken *"from
`meta description` only, never from body text, because extracting prose is how a link turns back
into a copy."* That concern is real and is answered by bounds rather than by abstinence:
**`MAX_QUOTES = 3` and `MAX_TOTAL_WORDS = 90`, always beside a prominent link and its publisher.**
Three attributed sentences next to a citation is quotation; a page's worth of extracted prose is a
copy. The line is drawn in constants so it can be argued with.

**Which few variants to show is decided from the player's own games.** The Sicilian has 391 named
lines; choosing four by editorial judgement would be this project inventing chess opinion. Choosing
the four the player actually reached is a measurement, and it is the evidence rule every other claim
already obeys (V8). With no games the fallback is the shallowest lines, **labelled as a fallback**
(`Line.games is None`) rather than presented as a choice.

## Consequences

- `chesscoach/opening_plans.py` — the selector. Rules are the author's own three objections
  inverted, plus five learned from reading real output (see [[experiments.e49-opening-resources]]).
- `chesscoach/opening_resource.py` — assembles moves + quotes + link for one family.
- `Opening` gains `pgn`; `Guide` gains `plans`. The book is regenerable, so the schema change costs
  one download.
- **An unreviewed page contributes no sentences.** Quoting is a stronger endorsement than linking,
  so it obeys the same `reviewed` gate — tested, because it is the property most likely to break
  silently.
- **Empty is a valid answer.** A page with no plan sentence yields nothing and the link still
  stands. Inventing a sentence to fill the gap is the one thing this design exists to prevent.

## What this does not settle

**Whether the chess in the quoted sentences is correct.** The selector can tell that a sentence is
forward-looking, jargon-free and about the board; it cannot tell whether the plan is the right plan.
That is still the author's `reviewed=true`, and it is now load-bearing in a stronger way than
before — approving a link used to mean *"this page is worth reading"* and now also means *"these
sentences may be repeated in my name."*
