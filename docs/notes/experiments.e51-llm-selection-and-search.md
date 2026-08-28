---
id: cas-exp-e51
title: 'E51 — The model has the recall and the regexes have the precision; the search judge has neither'
desc: 'Selection: composing a model with the non-PLAN filters recovers 12 real plan sentences the regexes were losing, after the veto removes the marketing and analysis lines the model admits. Search: the judge is safe, conservative and currently useless — it changed nothing on four openings.'
updated: 1788480000000
created: 1788480000000
---

# E51 — Can a model replace the plan-sentence regexes, and judge search results?

**Answers:** the author's *"[selection] could be skipped and let llm summarize. Would searching be ok
task for llm to check the result and see if it is ok and if new word combination could be used to get
better results"* · **Code:** `chesscoach/plan_selector.py`, `chesscoach/opening_search.py`,
`experiments/e51-llm-selection-and-search/` · **Date:** 2026-08-28 ·
**Status:** done — **selection adopted as a composition; search built, measured, and not yet earning
its place**

## The constraint discovered first, which shaped both answers

The obvious version of the request — hand the model the whole page — was refused on measurement
before anything was built. `grounding.py` compares a rewrite against its source, and **that check's
power is a function of the source's size**:

| source the check compares against | false claims that pass |
|---|--:|
| the extracted quotes (ships today) | **3 %** |
| the whole page | **76 %** |

Probes were real sentences from *other* openings' pages — true there, false here. Against the English
Opening's 14,955-word essay the check accepts **98 %**: a big page already contains most chess
vocabulary and dozens of squares, so a false claim finds its parts scattered across it.

**Selection is not only a filter on what the model reads. It is what makes the check on what the
model writes mean anything.** So selection could become a model's job only if its output stayed small
and stayed the page's own words — which is why `LlmSelector` answers with **indices**, never text.

## Part 1 — selection: the model has recall, the regexes have precision

Run head to head on the same pages, the model's exclusive picks split cleanly.

**Real plan sentences the `PLAN` pattern was losing:**

> *"This gives white flexibility to later choose between two main plans: strike in the center or
> start an attack on the kingside."*

**And junk the filters correctly refuse:**

> *"One of the players who has been using it for many years … is Gata Kamsky."* — trivia
> *"White's main idea in the Alapin **Highlighted course The High Pressure Alapin Sicilian
> Discover** White is hoping…"* — marketing spliced in
> *"Nxe5 6.d4 with a fork and Black can only get a balanced game…"* — an annotated variation

So the answer is not *replace* but **compose**, and the split is not arbitrary — it follows which
rule was doing which job:

| half of the rules | who does it now |
|---|---|
| `PLAN` — is it forward-looking? | **the model** (this was the recall bottleneck) |
| jargon, marketing, meta, analysis-line, length, board-terms | **the regexes, as a veto** |

`is_plan_sentence` is split into `is_admissible` plus `PLAN` to make that possible.

| | before the veto | after |
|---|--:|--:|
| chosen by both | 4 | 4 |
| regex only | 32 | 33 |
| **model only** | **32** | **12** |

**The veto removes 20 of the model's 32 exclusive picks and keeps the ones worth having.** 3.1 s per
page.

One filter was loosened by the same evidence: `MAX_MOVE_TOKENS` **3 → 5**, because *"White develops
the dark-squared bishop to f4 before blocking it with e3, then builds a solid pawn chain with c3 and
e3"* names four squares and is plain prose. The numbered-move check is the strong signal for an
annotated variation; this one is a backstop.

## Part 2 — search: safe, conservative, and currently doing nothing

`GuidedSearcher` lets the model reject results and reword the query. On the four uncovered openings:

| | |
|---|--:|
| openings where the judge kept anything | **0 of 4** |
| wordings tried | 12 |
| **candidates the author gained** | **0** |

Every attempt ended with the safety fallback returning the plain results. **It never made anything
worse and never made anything better**, at a cost of three searches and six model calls per opening.

### Is the judge broken, or were the results really that bad?

Two explanations fit an all-zero run equally well, so they were separated before either was written
down (L-046). A hand-built case mixes one real guide with the exact junk the run returned:

| model | agreement with a person |
|---|--:|
| `qwen2.5:3b` | **10 of 12** |
| `qwen3:8b` | 9 of 12 |

**The judge works and is conservative.** It never accepted junk — every error is a *false negative*
on a genuine guide, twice answering `NONE` with *"The London System: complete guide for club
players"* in front of it. On the Pirc it was perfect: kept the guide, rejected all three.

Conservative is the right failure direction here, since the fallback guarantees nothing is lost. It
is also why the feature currently achieves nothing.

### Two harness bugs found on the way, both mine

- **The probe asked about the Pirc while offering London and English guides**, then scored the judge
  wrong for rejecting pages about a different opening — which the prompt explicitly tells it to do.
- **The probe scored the safety fallback as a verdict.** When the judge keeps nothing, `search`
  returns the plain results; reading that as *"the judge approved these"* reported 6 of 12 for a
  judge that had said `NONE`. Corrected, the same run is 10 of 12.

Both are the shape this session keeps producing: a fact about the harness one edit away from being
recorded as a fact about the model.

## Consequence

- **Ship the composition.** `LlmSelector(veto=True)` is the selector to use where a model is
  available; `RegexSelector` remains the offline floor and the default.
- **Keep `GuidedSearcher`, do not rely on it.** It is safe by construction — never returns fewer
  candidates than the plain searcher — and on this evidence it earns nothing. Recorded so it is not
  re-proposed as an obvious win.
- **`unparseable` is counted on the searcher**, because *"the judge did not answer"* and *"the judge
  approved everything"* were the same value and must not be.
- **The query log is written out.** Acquisition is now non-deterministic, which criterion 6 cares
  about; it cannot be replayed exactly, so it is made readable instead.

## Honest limitations

- **The judge sees titles and domains, not page text.** The observed failures are legible from those
  — *"33 Chess Openings You Should Know"* on `blog.duolingo.com` — but a guide with a dull title is
  invisible to it, which is a plausible cause of the false negatives.
- **Twelve pages, four openings, one machine.** The selection disagreement is read, not scored: no
  one has labelled which of the 12 model-only sentences a 1500 would actually want.
- **Nothing is endorsed.** Every page involved is still `reviewed=false`.
