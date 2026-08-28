---
id: cas-adr-0014
title: 'ADR-0014 — Three agents write the opening brief, and none of them may do two jobs'
desc: 'Scout, Assessor and Compiler, each with a stated role and a forbidden failure mode. The models decide which text and which words; the grounding check decides whether the words survive. Answers the thesis objection that the swarm was mostly deterministic Python.'
updated: 1788480000000
created: 1788480000000
---

# ADR-0014 — Three agents write the opening brief

**Status:** accepted · **Date:** 2026-08-28 · **Builds on:**
[[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]]

## Context

The author raised an objection about the *thesis*, not the code:

> *"this thesis is for study for AI and if I just have mainly pure python segments and not many
> working llm segments it is not good enough, it doesn't have to work the best but it should be
> functioning ok, with llms."*

That is fair and it was true. ADR-0013 admitted a model for one narrow rephrasing step bolted onto a
deterministic pipeline. A project called *ChessAgentSwarm* with one language-model call and no agent
roles is thin as an AI artefact, whatever its measurement discipline.

The author also specified the shape: multiple results, an *assessment* agent that discards what is
not good, and a *compiler* agent that writes **the plan for the player and what to be careful of as
the opponent's response**.

## Decision

**Three agents, each with one job, one prompt stating its role, and a failure mode it must not
have.**

| agent | does | must never |
|---|---|---|
| **Scout** | writes queries, casts a wide net | judge what it found |
| **Assessor** | discards the unusable, with reasons | write prose |
| **Compiler** | writes the brief from what survived | search, or add knowledge |

**The separation is load-bearing, not decoration.** An agent that both searched and judged has no
reason to discard its own results. One that both judged and wrote could quietly replace a weak source
with its own knowledge and nothing downstream would know.

**Every chess claim still traces to a fetched page.** The Compiler works only from sentences the
Assessor kept — verbatim, index-selected — and both halves of its output are checked by
`grounding.check` before anyone sees them. So the models decide **which text** and **which words**,
never **what is true about chess**. That is the same line ADR-0013 drew, extended across three roles
rather than abandoned because there are now more of them.

**The brief has two halves and they are checked separately**, so a good `PLAN` is not lost because
the `WATCH` half wandered.

**Each role fails toward doing nothing rather than doing harm.** The Scout's own default queries run
even when the model is unreachable, so a bad model cannot make the search worse than not asking one.
The Assessor's silence about a page is *"not judged"*, never rejection. The Compiler is not called at
all when nothing was approved, and may answer `WATCH: none`.

## Consequences

- `chesscoach/opening_swarm.py`, `chesscoach/ollama.py`; `SearxSearcher.search_detailed` now keeps
  snippets, which the Assessor needs and the old judge never had.
- **A new deterministic check the grounding gate cannot supply:** `_restates` rejects a `WATCH` that
  is the `PLAN` said again. Found in production output — the Pirc brief's `WATCH` was its `PLAN` with
  the colour flipped, and it passed grounding because every word was the source's.
- **The trace is kept**: every page found, every discard and its reason. Explainability (V8) applies
  to the swarm's own reasoning, not only to the player-facing claims.
- **It works on well-covered openings and not on obscure ones**
  ([[experiments.e52-opening-swarm]]), which is a property of the web rather than of the design.

## What this does not settle

**The `WATCH` half does not work.** Zero survived across every run: each was either a restatement or
invented and caught. The cause is structural rather than a prompt defect — the pages being retrieved
describe the player's plans, so no retrieved sentence says what the opponent does, and the Compiler
fills the gap from its own knowledge exactly as it should not.

Giving the Scout a second, opponent-facing query was tried and did not fix it. **The swarm is
non-deterministic** (the Scout runs at temperature 0.7), so a single before-and-after run cannot
separate a change from noise, and that comparison is reported as inconclusive rather than as a
result.

**The Assessor's verdicts are more reliable than its reasons.** It discards sensibly and then names a
category from the prompt's own list — calling a Duolingo blog *"a forum thread"* and a TikTok link
*"a move database"*. The reasons are shown to the author, so they are stated as unreliable rather
than trusted.
