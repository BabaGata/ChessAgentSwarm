---
id: cas-domain-puzzle-themes
title: Puzzle Theme Vocabulary
desc: 'The 75 Lichess puzzle themes mapped onto our concept landscape — the free labelled vocabulary the swarm can diagnose and prescribe against.'
updated: 1785254900000
created: 1785254900000
---

# Puzzle Theme Vocabulary

Resolves **D2** in [[open-questions]]. The authoritative theme list comes from Lichess's own source
(`translation/source/puzzleTheme.xml` in `lichess-org/lila`) rather than from the puzzle dump, which
avoids a ~250 MB download to answer a vocabulary question. **75 themes**, each with an official
description.

Why this matters: these tags are attached to every puzzle in the CC0 puzzle database. Any concept
that appears here is one the swarm can both **diagnose** (does this player miss it?) and
**prescribe** (here are 50 puzzles that drill it), for free. Any concept that does *not* appear here
has no free labelled training material and needs a different mechanism.

## 1. Tactical motifs → [[domain.chess-concepts]] K2

| Lichess theme | Our concept | Note |
|---|---|---|
| `fork` | fork / double attack | |
| `pin` | pin | not split into absolute/relative |
| `skewer` | skewer | |
| `discoveredAttack` | discovered attack | |
| `discoveredCheck` | discovered check | |
| `doubleCheck` | double check | |
| `deflection` | deflection | |
| `attraction` | decoy / attraction | Lichess's name for what coaches call a decoy |
| `capturingDefender` | removal of the defender | |
| `interference` | interference | |
| `intermezzo` | zwischenzug | same idea, different tradition |
| `clearance` | clearance | |
| `xRayAttack` | x-ray | |
| `hangingPiece` | hanging piece | the single most common club-level error type |
| `trappedPiece` | trapped piece | |
| `zugzwang` | zugzwang | also an endgame concept (K7) |
| `promotion`, `underPromotion`, `advancedPawn` | promotion tactics | `advancedPawn` is a positional precursor rather than a motif |
| `sacrifice` | sacrifice | broad; overlaps K8 |
| `quietMove` | — **no K2 equivalent** | "does not check, capture or threaten" — a *calculation* skill (K3), not a pattern. Valuable: missing quiet moves is a distinctive diagnostic signature |
| `defensiveMove` | — **no K2 equivalent** | belongs to K8 defence. Also diagnostically distinctive |
| `collinearMove` | — none | a geometric curiosity, not a coaching concept |
| `attackingF2F7` | f2/f7 weakness | K8 attack, and an opening-phase pattern |
| `kingsideAttack`, `queensideAttack` | attacking the castled king | K8 |
| `exposedKing` | king safety | K4/K8 |
| `castling` | king safety / development | K6 principle |

## 2. Mating patterns → K2 mating patterns

`backRankMate`, `smotheredMate`, `anastasiaMate`, `arabianMate`, `bodenMate`, `operaMate`,
`morphysMate`, `pillsburysMate`, `dovetailMate`, `epauletteMate`, `hookMate`, `killBoxMate`,
`cornerMate`, `doubleBishopMate`, `balestraMate`, `blindSwineMate`, `swallowstailMate`,
`triangleMate`, `vukovicMate`, plus the generic `mate` and `mateIn1` … `mateIn5`.

Lichess's list is **richer than ours** — we listed 10 named patterns, they tag 19. The `mateInN`
tags are a free difficulty axis: mate-in-1 failures and mate-in-4 failures mean completely different
things (pattern recognition vs. calculation depth).

## 3. Phase tags → phase-wise diagnosis

`opening`, `middlegame`, `endgame`.

Directly useful: they let us prescribe *"tactics that occur in endgames"* rather than tactics in
general, and they line up with the phase-wise error profile in [[domain.signals]]. A player whose
errors cluster in the endgame can be given endgame-tagged tactical puzzles.

## 4. Endgame type tags → K7

`pawnEndgame`, `rookEndgame`, `knightEndgame`, `bishopEndgame`, `queenEndgame`, `queenRookEndgame`.

This is the free labelled material for the endgame domain. Rook endings — the ones sources say
matter most — are directly addressable.

## 5. Evaluation-goal tags

`advantage` (200–600cp), `crushing` (≥600cp), `equality` (≤200cp, i.e. save a draw).

An underrated axis: `equality` puzzles train *defence and resilience*, which maps to the
psychological/practical domain (K9) that most training material ignores.

## 6. Meta tags

`oneMove`, `short` (2 moves), `long` (3), `veryLong` (4+) — a calculation-depth axis.
`master`, `masterVsMaster`, `superGM` — source-quality filters.
`mix`, `playerGames` — UI conveniences.

`playerGames` is notable: **Lichess generates puzzles from a specific player's own games.** That is
exactly the "missed tactic in your own game" mechanism described in [[domain.signals]], and it means
the reference implementation of that idea is public.

## 7. Gap analysis

### In our K2 list but *not* in Lichess's vocabulary
- **overloading / overloaded defender** — Arrakis implements a detector for it ([[domain.prior-art]]),
  so it is computable even though there is no puzzle tag.
- **desperado**, **windmill** — no tag, no detector. Rare enough to defer.
- **Greco's, Damiano's, Légal's mates, ladder mate** — no tags. Minor.

### In Lichess's vocabulary but missing from our K2 list
- `quietMove` and `defensiveMove` — **the two most interesting omissions.** Neither is a tactical
  pattern; both are *calculation and mindset* skills. A player who solves forcing puzzles well but
  fails quiet-move puzzles has a specific, nameable weakness (only sees checks and captures) that
  our concept map did not have a slot for. Add to K3.
- 9 extra named mating patterns.
- The phase, endgame-type, difficulty and evaluation-goal axes, which our list treated as properties
  rather than as tags.

### The asymmetry, confirmed again
Every theme here is **tactical, mating, phase or material-type**. There is not a single positional
tag: no outpost, no weak square, no bad bishop, no pawn-structure type, no prophylaxis. This is the
same asymmetry recorded in [[domain.signals]] and [[domain.prior-art]] — and it is now confirmed
from three independent directions (our concept map, prior-art motif detectors, Lichess's own
vocabulary). **Open question D4 is the central technical risk of this project**, and M2 must not
assume positional sections are as tractable as tactical ones.

## Consequences for M2

1. The tactical section of the catalogue can be defined **directly from this vocabulary** — it is
   pre-labelled, free, and consistent between diagnosis and prescription.
2. `quietMove` / `defensiveMove` justify a **calculation-quality** section distinct from a
   tactical-pattern section.
3. Endgame sections can be scoped by material type, matching the free tags.
4. Positional sections have no such support and will need their own design — likely deterministic
   board-feature detectors (the D4 experiment), not a labelled corpus.
