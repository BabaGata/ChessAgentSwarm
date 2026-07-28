---
id: cas-glossary
title: Glossary
desc: 'Shared vocabulary for the project — adaptive-system terms and chess/coaching terms.'
updated: 1785254500000
created: 1785254500000
---

# Glossary

## Project / adaptive-system terms

| Term | Meaning here |
|---|---|
| **Vision** | The desired end state. Rarely changes. [[vision]] |
| **Mission** | The iterative steps toward the vision. Revised when it stops serving. [[mission]] |
| **Capacity** | Agents, tools, knowledge, infrastructure — the ability to act. [[capacity]] |
| **Learning** | The process that updates capacity to serve the vision better. [[learning]] |
| **Cycle** | One pass of the [[process]] loop; the project's unit of work. |
| **Scorecard** | The 0–5 distance-to-vision table in [[state]]. |
| **Section** | A cohesive chunk of coaching knowledge that one agent will own. [[domain.sections]] |
| **Swarm** | The orchestrated set of agents that together act as the coach. |
| **Alignment check** | Phase 2 of the cycle: testing a plan against the vision before executing it. |
| **Evidence class** | `measured` / `expert-consensus` / `single-expert` / `folklore`. [[capacity.knowledge]] |

## Chess & coaching terms

Filled during M1 as terms are actually used. Definitions must be precise enough for an agent to act
on — "positional understanding" is not yet a definition.

| Term | Meaning | Where used |
|---|---|---|
| **ACPL** | average centipawn loss — mean engine-evaluation cost of a player's moves. A centipawn is 1/100 of a pawn. Not comparable across time controls or position sharpness | [[domain.signals]] |
| **Motif** | a reusable tactical pattern (fork, pin, skewer, deflection…). Machine-labelled in the Lichess puzzle database | [[domain.chess-concepts]] K2 |
| **Imbalance** | a difference between the two sides (material, structure, minor-piece quality, space, initiative, king safety) from which a plan is derived | [[domain.chess-concepts]] K4 |
| **Prophylaxis** | preventing the opponent's best idea before executing your own plan | [[domain.chess-concepts]] K4/K8 |
| **Outpost** | an advanced square, protected by a pawn, that enemy pawns cannot attack | [[domain.chess-concepts]] K4 |
| **Candidate moves** | the shortlist of moves considered before calculating, rather than following the first impulse | [[domain.chess-concepts]] K3 |
| **Kotov syndrome** | long think, nothing found, panic as the clock falls, then playing an unanalysed move | [[domain.chess-concepts]] K9 |
| **Lucena / Philidor** | the standard winning and drawing techniques in rook + pawn endings | [[domain.chess-concepts]] K7 |
| **Opposition** | kings facing each other with an odd number of squares between; the side *not* to move holds it | [[domain.chess-concepts]] K7 |
| **Gap type** | why an error happened: knowledge / skill / process-habit / psychological. Different remedies | [[domain.coaching]] § 2 |
| **Probe position** | a position presented to the player to elicit a move *and its reason*, to test knowledge that games cannot reveal (V9) | [[domain.coaching]], [[domain.signals]] |
| **Band** | an approximate strength range (e.g. 1400–1800) with its own binding constraint and study balance | [[domain.chess-concepts]] § D |
| **Turning point** | the move in a game where the evaluation actually decided the result | [[domain.signals]] |
