---
id: cas-vision
title: Vision
desc: 'The desired end state of the project: a free/near-free agent swarm that coaches chess players effectively.'
updated: 1785254500000
created: 1785254500000
---

# Vision

> An agent swarm that is **free or very cheap to run** and is **effective at coaching a chess player**:
> it works out how strong the player is, what they already know, which style of play suits them,
> which chess concepts they hold / lack / are ready to learn, what information would most improve
> them, and it turns that into a **learning path** with steps, priorities, time estimates and
> expected signs of progress.

The vision is the fixed point of the project. [[mission]] steps, [[capacity]] and every design
decision are judged by whether they move [[state]] closer to it.

## Desired capabilities

The finished system must be able to do all of the following for an individual player:

| # | Capability | What "done" looks like |
|---|---|---|
| V1 | **Skill assessment** | Estimate playing strength and its variance from games/puzzles/interaction, not just a self-reported rating. |
| V2 | **Knowledge assessment** | Determine which chess concepts the player demonstrably knows, in which contexts they apply them, and where the knowledge is shallow. |
| V3 | **Style profiling** | Characterise the player's tendencies and recommend a repertoire/style that fits their strengths, temperament and available study time. |
| V4 | **Gap detection** | Identify concepts the player does not know, mis-applies, or knows in theory but fails under pressure. |
| V5 | **Readiness / prioritisation** | Of all gaps, decide which ones are learnable *now* and would most improve results per unit of study time. |
| V6 | **Path planning** | Produce a coaching path: ordered steps, priorities, time estimates, and the observable signs that a step has been absorbed. |
| V7 | **Progress tracking** | Re-assess over time, detect whether predicted progress signs appeared, and re-plan when they did not. |
| V8 | **Explainability** | Every recommendation traceable to evidence (specific games, positions, patterns) — a coach who can say *why*. |

## Constraints (non-negotiable qualities)

| # | Constraint | Rationale |
|---|---|---|
| C1 | **Free or near-free to operate** | Thesis project, no funded infrastructure. Prefer local/open models, free API tiers, cached and precomputed knowledge over per-query LLM spend. |
| C2 | **Runs on a single ordinary machine** | No cluster, no paid GPU fleet. |
| C3 | **Open / self-hostable components** | Engine (Stockfish), data (Lichess), storage — all free and offline-capable where possible. |
| C4 | **Cost per coaching session must be measured, not assumed** | See [[evaluation]]; cost is a first-class metric alongside quality. |
| C5 | **Auditable reasoning** | No black-box "trust me" coaching. Ties to V8. |
| C6 | **Incrementally useful** | Each mission step must leave a system that is usable on its own, not only at the very end. |

## Success criteria

The vision is reached when, for a set of held-out real players:

1. The swarm's strength estimate correlates strongly with the player's actual established rating.
2. The swarm's identified weaknesses match those independently identified by a strong human
   reviewer / engine analysis on the same games (agreement measured, see [[evaluation]]).
3. The produced learning path is judged by a strong player as *reasonable, ordered and specific*.
4. Following a path produces the predicted progress signs more often than a control path
   (generic study advice).
5. A full assessment + plan for one player costs approximately nothing in cash terms and completes
   in minutes on a laptop.
6. The system is documented well enough that a third party can reproduce it from this vault.

## Non-goals

- Not a chess engine. We use existing engines; we do not try to out-calculate them.
- Not a playing bot. Playing strength of the system itself is irrelevant.
- Not a general-purpose tutoring platform. Chess only.
- Not a commercial product: no accounts, billing, scaling, or multi-tenant concerns.
- Not a replacement for a titled human coach — the target is *useful, honest, personalised guidance*.

## Review triggers

Review this note (and, if it changes, cascade to [[mission]] and [[state]]) when:

- A constraint turns out to be impossible or already violated (e.g. cost blows up).
- Research reveals a capability that is essential to coaching but missing from V1–V8.
- A success criterion proves unmeasurable and needs to be replaced by something observable.
- The user (thesis author) restates or refines the goal.

Every change here must be logged in [[decisions]].
