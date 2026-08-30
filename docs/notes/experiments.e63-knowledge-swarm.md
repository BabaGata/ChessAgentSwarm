---
id: cas-exp-e63
title: 'E63 — The drafting swarm, and three attempts to make it tell a definition from an example'
desc: 'Scout → Assessor → Compiler pointed at a detected claim. The pipeline works end to end and the definition is verbatim from a page by construction. But the first run produced a "definition" of castling about pawn moves — choosing by index guarantees provenance, not relevance — so the Compiler gained the ability to answer "none of these". It now refuses 2 of 3, correctly, and the bottleneck is retrieval reach.'
updated: 1788998400000
created: 1788998400000
---

# E63 — Drafting the knowledge base

**Answers:** [[design.knowledge-base]] Option C · **Code:** `chesscoach/knowledge_swarm.py`,
`experiments/e63-knowledge-swarm/` · **Date:** 2026-08-30 ·
**Status:** working end to end — **one good entry, and the fix was the model, not the prompt**

## What was built

The author chose Option C and asked that LLM agents be used as far as they go. This reuses the three
agents rather than growing a fourth — **the `Assessor` is used completely unchanged**, since its
prompt takes a topic string and a claim name is as good a topic as an opening name. Only the queries
and the final assembly are new.

**The definition is not written by a model.** It is a sentence from the retrieved page chosen **by
index**, the same trick that keeps the Assessor's kept notes verbatim. The model chooses *which*
sentence defines the thing; it never composes one. Four ways that can go wrong are refused rather
than repaired: an index outside the list, prose in an integer field, an ungrounded `why`, and
unsupported `practice`.

`not_this` is never written here, and nothing drafted is ever `reviewed`.

## The first run produced confident nonsense

Three claims, and all three "succeeded":

| claim | the chosen "definition" |
|---|---|
| `fork` | *"In each board white can win material by force, if he chooses his moves wisely…"* |
| `hangingPiece` | *"To avoid confusion with hanging pawns, which refer a duo of…"* |
| `late_castling` | *"There are two possible moves that place a pawn in the centre of the board: 1."* |

Every one is a **real sentence, verbatim, from a real page** — and none of them defines the thing.
The castling entry is about pawn moves.

**Choosing by index guarantees provenance. It cannot guarantee relevance.** With no way to say *"none
of these"*, the model must return the least-bad sentence, and the least-bad sentence from a page
about something else is a plausible wrong answer where *"nothing found"* was the truth. That is
L-046 with the failure moved out of the pipeline and into the content — and it would have been
invisible in any count, because the run reported 3 of 3 drafted.

## The fix: let it refuse

`definition: -1` means no sentence here defines the topic, and the prompt says so plainly —
*"most pages are about something else, so -1 is the right answer more often than not. Do not pick the
closest sentence."*

Re-run:

| claim | before | after |
|---|---|---|
| `fork` | wrong sentence | *"The Knight forks the King and Rook, forcing the King to move…"* |
| `hangingPiece` | wrong sentence | **nothing usable found** |
| `late_castling` | wrong sentence | **nothing usable found** |

**1 drafted, 2 correctly refused**, and an incomplete entry cannot be endorsed, so nothing wrong can
reach a player through it.

## What is still wrong

**The one entry that survived is an example, not a definition.** *"The Knight forks the King and
Rook"* shows a fork; it does not say what one is. It would still be useful to a player and it is
useless for the detector review, which is the half the author cares about most.

**The bottleneck is retrieval reach, not the pipeline.** The four-engine SearxNG set — mojeek, mwmbl,
wikipedia, wikibooks — does not reach a chess tactics glossary. Wikibooks' chess material is about
openings and strategy; it has no motif dictionary. So the Assessor is choosing from pages that were
never going to contain a definition.

**A smaller thing worth recording:** the surviving sentence contains mojibake (`Black<?>s`), so the
fetched body's encoding is not always what the decoder assumes.

## Consequence

- **The pipeline is correct and the refusal path is the valuable part of it.** A swarm that produces
  nothing is recoverable; a swarm that produces confident nonsense that reads well is not.
- **Retrieval has to reach better sources before another drafting run is worth doing.** Options, in
  the order the design note already ranks them: more engines in the SearxNG set, or the keyed
  provider the quota guard now makes safe.
- **The detector-review use is not yet served at all**, because no retrieved sentence has been a
  definition precise enough to compare a detector against. That was the half worth most.

## Widening the engine set, and what it did not fix

The four-engine SearxNG set reached no chess glossary, so it was widened to seven after checking
which names the image actually knows (`curlie` was silently ignored, the same behaviour that hid the
original 84-engine bug):

| | before | after |
|---|--:|--:|
| results for *"what is a fork tactic in chess"* | 6 | **92** |
| results for *"hanging piece chess"* | 21 | 38 |
| unresponsive engines | — | **none** |

`encyclosearch` earns its place; `mwmbl` does most of the work and is the only engine that reached
*"Hanging Piece — Chess Terms — Chess.com"*. **`yep` and `fireball` were removed after
measurement**: unresponsive on every query tried, so they cost a request and a timeout wait and
returned nothing.

**And the drafts got worse, not better: 0 of 3, down from 1.** Better retrieval, fewer entries.

## The real problem was telling a definition from an example

Inspecting the kept notes for `fork` showed a genuine definition sitting among them:

> *"An absolute fork is when a piece attacks two or more enemy pieces simultaneously, one of them
> being the King."*

The model had refused it. **I had over-corrected the prompt** — having told it to pick the best
sentence and got nonsense, I told it that refusing was *usually* right, and it refused everything.

**A refusal option needs a criterion, not a bias.** Rewritten to say what a definition *is* — a
sentence that would still make sense to someone who had never heard the term, and an example of the
thing happening is not one. That did not work either: the model picked *"the Knight forks the King
and Rook"*, the example named almost verbatim in the instruction as a counter-example.

**So it was measured rather than argued about.** Same eight notes, three models:

| model | picked |
|---|---|
| `qwen2.5:3b` | *"The Knight forks the King and Rook..."* — the **example** |
| `qwen3:8b` | *"An absolute fork is when a piece attacks..."* — the **definition** |
| `phi4-mini:3.8b` | the **definition** |

**The distinction is a capability, not a wording.** The roles are now split: the Assessor keeps
`qwen2.5:3b`, where picking sentences by the hundred is measured to be adequate, and the Compiler —
which makes the one judgement that decides the entry — gets `qwen3:8b`.

## The entry it produces

```
DEF   An absolute fork is when a piece attacks two or more enemy pieces
      simultaneously, one of them being the King.
WHY   A player who gets this wrong may lose their king and other valuable
      pieces in one move.
SRC   chessjournal.com, chessmood.com, en.wikipedia.org
```

Usable, sourced, and **still not right for the detector review** — which is the point the design
note made in advance. *Absolute* fork is a **subtype**: a fork involving the king. The detector's
fork is not restricted to king forks, so adopting this sentence as the specification would narrow it
wrongly. And *"may lose their king"* is loose in a way a chess reader will notice.

**This is the strongest evidence yet for the rule that `not_this` and the precise rule stay with the
author.** The swarm found a real definition from a real source, and it is still the wrong definition
for the job the author wanted it for.

## Honest limitations

- **Three claims, and one good entry.** Everything here rests on a handful of drafting attempts.
- **The model comparison is one prompt on one set of notes.** `phi4-mini:3.8b` did as well as
  `qwen3:8b` and is smaller; nothing here establishes which is better in general.
- **"Correctly refused" is my judgement, not a marked result.** Nobody has read the kept notes to
  confirm a definition really was absent rather than missed.
- **The grounding gate has not been stress-tested here.** `why` and `practice` were mostly empty, so
  the checks that drop ungrounded prose have barely fired on real output.
