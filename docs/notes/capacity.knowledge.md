---
id: cas-capacity-knowledge
title: Knowledge
desc: 'What the project and the swarm currently know, and how that knowledge is stored.'
updated: 1785254500000
created: 1785254500000
---

# Knowledge

Two distinct bodies of knowledge, often confused:

1. **Project knowledge** — what *we* know about building this system. Lives in this vault.
2. **Domain knowledge** — what the *swarm* knows about chess and coaching. Lives under [[domain]]
   during research, and later in whatever runtime knowledge store M3 specifies.

The transition between the two is deliberate: research notes are the human-readable source, the
runtime store is derived from them. Keep the derivation reproducible rather than hand-maintaining
two copies.

## Current holdings

| Body | Where | Coverage |
|---|---|---|
| Project steering | this vault | vision, mission, process, decisions — complete for the current stage |
| Chess concepts | [[domain.chess-concepts]] | **first pass** — 10 domains, concept inventory, prerequisite order, band table, contested claims marked. Missing: typical-plan catalogues per structure, positional-motif taxonomy |
| Coaching practice | [[domain.coaching]] | **first pass** — assessment method, four-way gap taxonomy, sequencing, anti-patterns, progress indicators, operational style definition. Missing: a detailed published curriculum, adult-vs-junior differences, intervention timescales |
| Computable signals | [[domain.signals]] | **first pass, strongest area** — signal inventory, free tooling, what is *not* computable, methodological warnings |
| Sources | [[domain.sources]] | **first pass** — every source evidence-classed; commercial bias flagged (R-11); one claim marked unverified |
| Prior art | [[domain.sources]] § prior art | five comparable open-source projects identified, **none read yet** |
| Runtime knowledge store | — | does not exist; designed in M3 |

## Quality rules for domain knowledge

Chess improvement advice contains a lot of confident folklore. Every domain claim carries:

- **Source** — who says it, where.
- **Evidence class** — `measured` (data/study), `expert-consensus`, `single-expert`, `folklore`.
- **Applicability** — which strength band(s) it applies to.
- **Testability** — can the swarm verify this claim against a player's own games?

Claims that are `folklore` and untestable may still be recorded, but must never be presented to a
player as fact, and must not silently drive a coaching decision.
