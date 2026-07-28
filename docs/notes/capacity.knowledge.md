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
| Chess concepts | [[domain.chess-concepts]] | empty — M1 |
| Coaching practice | [[domain.coaching]] | empty — M1 |
| Computable signals | [[domain.signals]] | empty — M1 |
| Sources | [[domain.sources]] | empty — M1 |
| Runtime knowledge store | — | does not exist; designed in M3 |

## Quality rules for domain knowledge

Chess improvement advice contains a lot of confident folklore. Every domain claim carries:

- **Source** — who says it, where.
- **Evidence class** — `measured` (data/study), `expert-consensus`, `single-expert`, `folklore`.
- **Applicability** — which strength band(s) it applies to.
- **Testability** — can the swarm verify this claim against a player's own games?

Claims that are `folklore` and untestable may still be recorded, but must never be presented to a
player as fact, and must not silently drive a coaching decision.
