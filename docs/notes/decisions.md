---
id: cas-decisions
title: Decisions
desc: 'Decision log — every choice that constrains future work, with its context and consequences.'
updated: 1789430400000
created: 1785254500000
---

# Decisions

Architecture/direction decision records. A decision belongs here if reversing it later would cost
real work, or if a future reader would otherwise ask *"why on earth is it like this?"*.

## Log

| ID | Date | Decision | Status |
|---|---|---|---|
| [[decisions.0001-adaptive-documentation-driven-process]] | 2026-07-28 | Steer the project as an adaptive system through a Dendron vault + enforced cycle | accepted |
| [[decisions.0002-compute-first-speak-last]] | 2026-07-28 | Deterministic analysis core produces a structured player profile; LLMs operate only on the summary | **accepted** — prior-art convergence + E01 measurements |
| [[decisions.0003-add-v9-dialogue-and-active-assessment]] | 2026-07-28 | Add V9 (dialogue & active assessment) to the vision — passive analysis cannot separate knowledge gaps from skill gaps | accepted |
| [[decisions.0004-free-research-materials]] | 2026-07-28 | Add C7 — build the knowledge base from freely obtainable sources; paid material only to unblock | accepted |
| [[decisions.0005-scope-band-source-online-only]] | 2026-07-28 | Scope: target band 1400–1800, Lichess API as game source, online play only | accepted |
| [[decisions.0006-staged-blackboard-orchestration]] | 2026-07-28 | Staged blackboard: agents share the profile, run in isolation, never message each other | accepted |
| [[decisions.0007-storage-sqlite-cache-json-profile]] | 2026-07-28 | SQLite position cache keyed by (position, engine, depth); JSON player profiles | accepted |
| [[decisions.0008-deterministic-planner]] | 2026-07-31 | The planner is deterministic; only the prober and explainer use a model | accepted |
| [[decisions.0009-prober-before-breadth]] | 2026-08-03 | Build the prober before sections S3–S11 — four scorecard dimensions are at zero and all four need the player to be asked something | accepted |
| [[decisions.0010-three-priorities-and-the-cost-pool]] | 2026-08-15 | Three priorities, and a second pool ranked by cost for what the peer comparison leaves empty — after the first expert review found the most expensive pattern in a player's games measured and discarded | accepted |
| [[decisions.0011-detection-correctness-over-expert-agreement]] | 2026-08-23 | Detection correctness outranks expert agreement. Three Form B/C found the detectors systematically wrong — Black move numbers off by one, UCI not SAN, bare game ids, mis-detected motifs, incomprehensible examples. The review becomes a defect-finding instrument rather than a scoreboard |
| [[decisions.0012-quote-the-plans-rather-than-write-them]] | 2026-08-28 | The plan summaries the author endorsed were the source page's own words, checked before designing. So the system selects and quotes sentences - bounded at 3 and 90 words, always attributed, always behind reviewed=true - and never writes one. Reverses opening_guides' "never from body text" rule and gives the bounds that answer it |
| [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]] | 2026-08-28 | Ollama is admitted for language work on supplied text and refused as a source of chess. Rephrasing is checkable against the source; asserting is not. Every output passes a deterministic grounding check or falls back to the quotes, and carries evidence class `composed` vs `quoted`. qwen2.5:3b adopted on measurement over qwen3:8b |
| [[decisions.0014-three-agents-for-the-opening-brief]] | 2026-08-28 | Scout, Assessor and Compiler, each with a stated role and a forbidden failure mode. Answers the author's objection that the swarm was mostly deterministic Python: the models now decide which pages, which sentences and which words, while the grounding check still decides whether the words survive. Each role fails toward doing nothing |
| [[decisions.0015-a-learned-skip-list-and-a-bullet-brief]] | 2026-08-28 | The Assessor stops judging titles and starts reading sentences; the cheap permanent judgement becomes a deterministic skip list it maintains, under four guards — the load-bearing one being that a site which has ever helped can never be skipped. The brief becomes bullet points, so one bad point is dropped instead of a paragraph |
| [[decisions.0016-a-run-store-for-the-swarm]] | 2026-08-28 | SQLite (stdlib, no dependency) for what the agents did, written as the run proceeds so a rate limit leaves what it had; JSON stays for the opening book, measured at 0.04 s to load and 1.2 ms per game walked, because it is a load format rather than a query format |
| [[decisions.0017-constrain-the-answer-with-a-schema]] | 2026-08-29 | Ollama's `format` field makes a malformed answer unrepresentable rather than unlikely, at no dependency cost. The prose parsers stay as the fallback and are tested on both paths. Adopted on construction rather than measurement: the parse rate was already 100 % |\n
| [[decisions.0018-the-thesis-is-a-mission-step]] | 2026-09-08 | The thesis becomes **M8** and runs alongside M7, not after it. It may never claim more than [[state]] does, which makes it a measurement step: its first pass forced three claims in this vault to be weakened against the code | superseded by 0020 |
| [[decisions.0019-fork-and-skewer-by-geometry]] | 2026-09-08 | A slider attacking two pieces on one line through it is a **skewer**, not a fork — the author's rule over the endorsed Lichess definition, knowing the motif key is also the puzzle filter | accepted |
| [[decisions.0020-the-thesis-leaves-the-mission]] | 2026-09-15 | Writing the thesis is **no longer a mission step**: M8 is removed from [[mission]] at the author's request; its alignment row (C5, success criterion 6) passes to M6, and the thesis tasks leave [[state]] | accepted |

## Template

```
### ADR-NNNN — <title>
**Date:** · **Status:** proposed | accepted | superseded by ADR-MMMM | rejected
**Context:** the forces at play, what we knew at the time
**Decision:** what we chose
**Alternatives considered:** and why they lost
**Consequences:** what this makes easy, what it makes hard, what it forecloses
**Vision link:** which V/C item this serves
**Revisit when:** the condition that should reopen this
```
