---
id: cas-domain-concepts
title: Chess Concept Landscape
desc: 'The domains of chess knowledge, their concepts, prerequisite structure and relevance by strength band.'
updated: 1785254500000
created: 1785254500000
---

# Chess Concept Landscape

First-pass answer to questions 1–4 of [[mission.step-01-foundations]]. Sources and evidence quality
in [[domain.sources]]. Evidence classes per [[capacity.knowledge]].

> **Framing note (L-001):** this map is organised by *what a coach diagnoses*, not by how chess books
> are chaptered. Hence "calculation" and "practical process" are top-level domains even though few
> books are organised that way — they are where a large share of club-level losses actually come from.

## A. The ten knowledge domains

| ID | Domain | What it covers |
|---|---|---|
| K1 | **Fundamentals** | rules, notation, basic checkmates, relative piece values, what a hanging piece is |
| K2 | **Tactics** | motifs and mating patterns — the pattern vocabulary |
| K3 | **Calculation & visualisation** | producing candidate moves, forcing-move scans, depth, accuracy, stopping criteria |
| K4 | **Positional judgement** | imbalances, structure, square/piece quality — evaluating a position |
| K5 | **Planning** | turning an evaluation into a plan; typical plans per structure |
| K6 | **Openings** | principles, repertoire, structures reached, move-order, punishing deviations |
| K7 | **Endgames** | elementary mates, K+P theory, rook endings, technique, conversion |
| K8 | **Attack & defence** | king attack patterns, sacrifices, prophylaxis, defensive resources |
| K9 | **Practical process** | time management, blunder-checking habit, converting won positions, resilience |
| K10 | **Meta-learning** | how to train: puzzle practice, game review, study balance, spaced repetition |

K9 and K10 are not "chess knowledge" in the classical sense but they are among the strongest
determinants of club-level results, and they are *diagnosable from game data* (K9) — which makes
them first-class citizens for this swarm.

## B. Concepts within each domain

### K2 Tactics
- **Motifs:** fork / double attack · pin (absolute, relative) · skewer · discovered attack ·
  double check · deflection · decoy / attraction · removal of the defender · overloading ·
  interference · zwischenzug (in-between move) · x-ray · clearance · trapped piece ·
  desperado · pawn promotion tactics · underpromotion · windmill · perpetual check / stalemate tricks
- **Mating patterns:** back rank · smothered · Anastasia's · Arabian · Boden's · Greco's ·
  Damiano's · ladder/two-rook · queen+knight · h-file mate · Légal's
- Motif vocabulary maps almost 1:1 onto Lichess puzzle theme tags → see [[domain.signals]]. This is
  the single most useful alignment for automated diagnosis found so far.

### K3 Calculation
- Candidate moves (a shortlist rather than following the first impulse)
- Forcing-move scan: **checks, captures, threats** — for *both* sides
- Opponent-move scan ("what does their move threaten?") — the single most commonly skipped step
- Blunder-check before committing (is anything of mine hanging *after* this move?)
- Depth vs. breadth; when to stop calculating; evaluating the leaf position
- Visualisation accuracy (holding a position in the head without moving pieces)
- **Contested:** Kotov's discipline of building a full analysis tree and never revisiting a branch.
  De Groot's earlier empirical work found strong players *do* revisit lines and consider few
  candidates, so the tree method is better treated as a *training exercise* than a description of
  expert cognition. Mark any advice derived from it as `single-expert`, not `measured`.

### K4 Positional judgement
- **Imbalances** (Silman's framing): material · pawn structure · minor-piece quality ·
  space · initiative/development lead · king safety
- **Pawn structure:** isolated (IQP) · doubled · backward · hanging pawns · passed pawn ·
  pawn majority / minority · pawn chain · holes · pawn breaks
- **Squares & files:** weak squares · outposts · open and semi-open files · the seventh rank ·
  colour complexes
- **Piece quality:** good vs. bad bishop · bishop pair · knight vs. bishop by structure ·
  rook activity · the worst-placed-piece principle · piece harmony/coordination
- **Dynamics:** initiative · tempo · space vs. activity trade-off · restriction

### K5 Planning
- Deriving a plan from the imbalances rather than from general aspiration
- Typical plans attached to typical structures (e.g. minority attack, IQP play for both sides,
  Carlsbad structure, closed-centre wing play)
- Transformation of advantages (converting one advantage type into another)
- Prophylactic thinking: what does the *opponent* want, and can it be prevented first

### K6 Openings
- Principles: fight for the centre · develop pieces · king safety · don't move the same piece
  twice without reason · don't bring the queen out early · connect rooks
- Repertoire construction: coherence, structure-based selection, effort budget
- Move-order and transposition; punishing common deviations
- Openings as *structure generators* — the correct level of abstraction for coaching is
  "what middlegame does this give you", not "memorise 14 moves"

### K7 Endgames
- Elementary mates: K+Q, K+R, K+2B, (K+B+N as an outlier)
- K+P: opposition · key squares · rule of the square · triangulation · breakthrough · zugzwang
- Rook endings (the most frequent piece ending): **Lucena** (winning bridge) ·
  **Philidor** (third-rank defence) · Vancura · rook behind the passed pawn · rook activity over material
- Minor-piece endings; opposite-coloured bishops (drawish tendency); Q vs. P
- Technique: king activation · principle of two weaknesses · when to trade into an ending ·
  conversion of extra material

### K8 Attack & defence
- Attacking the castled king: same-side (piece attack, sacrifices on h7/h2, f7/f2, g7/g2) vs.
  opposite-side (pawn storms, race counting)
- Sacrifice types: positional, clearance, destruction of the king's shelter, exchange sac
- Defence: prophylaxis, counterattack, active defence, simplification, fortress, accepting a worse
  but holdable position

### K9 Practical process
- Time management; clock discipline; distribution of thinking time
- **Kotov syndrome** — long think, nothing found, panic, plays an unanalysed move
- The blunder-check habit; playing "safe good" over "unclear brilliant"
- Converting winning positions; not relaxing after winning material
- Resilience after a mistake (tilt); playing on in worse positions
- Post-game review as a habit

### K10 Meta-learning
- Puzzle practice: little and often; **solving to be right rather than solving to be fast**
- Game review of one's *own losses*, focusing on the turning point
- Study-time allocation by level (see D below)
- Repetition of the same material until patterns are automatic, rather than novelty-chasing

## C. Prerequisite structure (partial order)

```
K1 fundamentals
 ├─> K2 tactics (motifs)
 │     └─> K3 calculation (needs a pattern vocabulary to generate candidates)
 │            ├─> K8 attack & defence (needs calculation + motifs)
 │            └─> K5 planning
 ├─> K7a elementary endings (independent of K2 — teachable immediately)
 │     └─> K7b K+P theory ──> K7c rook endings ──> K7d technique
 ├─> K6a opening principles (independent) ──> K6b repertoire (needs K4/K5 to be meaningful)
 └─> K4 positional judgement ──> K5 planning ──> K6b

K9 practical process: cross-cutting, teachable at any level, and the earlier the better
K10 meta-learning:   cross-cutting, precondition for everything else being efficient
```

Two structural claims worth stating explicitly because they shape the swarm:

1. **Calculation depends on the tactical pattern vocabulary.** You cannot generate good candidate
   moves for patterns you do not know. So K2 gates K3, which gates most of the rest.
2. **K9/K10 are cross-cutting and cheap to fix.** They are usually the highest-ROI intervention at
   club level, and they are the domains most amenable to automatic diagnosis from game data
   (time stamps, blunder distribution) — a strong argument for building those agents early.

## D. What binds at each strength band

Evidence class: `expert-consensus` unless stated. Bands are approximate and Elo-pool dependent.

| Band | Binding constraint | What a coach works on | Study balance (consensus, approximate) |
|---|---|---|---|
| **< 1000** | rules fluency, one-move blunders, hanging pieces | basic mates, piece safety, opening principles, simple tactics | tactics-dominant |
| **1000–1400** | *blunders* — games are decided by who drops material last | tactical motif vocabulary, blunder-check habit, turning-point review of every loss, basic K+P endings | tactics + process; openings ≈ principles only |
| **1400–1800** | *recurring personal weaknesses* — errors become individual rather than generic | personalised diagnosis; middlegame plans; more endgames; a first real repertoire if openings are being punished | ≤ 20% openings; rest middlegame/tactics/endgames |
| **1800–2000** | calculation depth, positional judgement, opening preparation quality | serious repertoire, endgame theory, annotated master games, prophylaxis | structured across all domains |
| **2000+** | preparation depth, specific structures, practical/psychological edge | deep prep, own-game deep analysis, specialised endgames | individual |

**This band table is the most decision-relevant output of M1** — it says a coaching swarm should
behave very differently at 1100 than at 1900, and it argues (see [[state]] P3) for picking one band
for the first end-to-end slice. The 1400–1800 band is where *personalised* diagnosis adds most over
generic advice, which is precisely the thing this system is supposed to do.

## E. Contested claims (do not present as fact)

| Claim | Status | Why it matters |
|---|---|---|
| "Openings don't matter below 1800" | `expert-consensus`, contested by opening-course sellers and by players punished in the first 10 moves | Determines a large share of study-time advice; the swarm should *check it per player* (are they actually losing in the opening?) rather than assert it |
| "Study endgames first" (Capablanca) vs "tactics first" | contested `single-expert` traditions | Sequencing decision; testable per player via phase-wise error data |
| Kotov's analysis-tree method | `single-expert`, contradicted by de Groot's observations | Affects how calculation is taught |
| "10,000 hours / deliberate practice determines skill" | `measured` but **partial** — Hambrick, Oswald, Altmann, Meinz, Gobet & Campitelli (2014), *Intelligence* 45, 34–45, report deliberate practice accounting for **about one third of the reliable variance** in chess performance. A broader meta-analysis (Macnamara, Hambrick & Oswald, 2014, *Psychological Science*) puts games at a similar order. Practice matters enormously and explains a minority of the differences between players. | Directly bounds what the swarm may honestly promise a player about progress. Verified 2026-07-28 (D1) |
| Starting age matters (early practice worth more) | `measured` (Gobet) | Affects realistic expectation-setting for adult improvers |
| "Playing style" as a stable trait | weak — mostly `folklore`; strong players are described as switching modes by position | V3 (style profiling) must be defined operationally from game data, not from a personality quiz |

## Open items for the next research pass

- Exact figures and citations for the deliberate-practice variance claim (currently cited from
  memory of a meta-analysis — must be verified before it appears in the thesis).
- A concrete mapping from Lichess puzzle themes → the K2 motif list above (mechanical, do in M2).
- Typical-plan catalogues per pawn structure (needed for K5 agents, not yet collected).
- Whether a usable public taxonomy of *positional* motifs exists comparable to puzzle themes for
  tactics — this is the main asymmetry: tactics are machine-labelled, strategy is not.
