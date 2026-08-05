---
id: cas-domain-sections
title: Section Catalogue
desc: 'The coaching knowledge chunked into agent-sized sections, ordered by priority for the 1400–1800 band.'
updated: 1785255600000
created: 1785255600000
---

# Section Catalogue

The deliverable of **M2**. Each section is a candidate agent in the swarm ([[mission]] M4 builds one
agent per section, in this order).

## Design rules

Four rules, each earned by something that went wrong or was learned earlier:

1. **A section is defined by what goes *wrong*, not by what exists** (L-007). "Pawn structure" is a
   topic; "concedes fixable pawn weaknesses and does not exploit the opponent's" is a diagnosis.
   Topics produce descriptions; failures produce coaching.
2. **A section must be diagnosable from evidence we can actually obtain** — otherwise its agent can
   only recite generic advice, which is the known anti-pattern ([[domain.coaching]] § 4, R-12).
3. **Boundaries follow how coaches diagnose, not how books are chaptered** (L-001). Where our two
   source vocabularies disagree — Lichess calls the pin tactical, Nimzowitsch calls it an Element —
   we do not split on that seam ([[domain.positional-vocabulary]]).
4. **Ordered for the 1400–1800 band** ([[decisions.0005-scope-band-source-online-only]]). What binds
   at 1100 or 2100 is different and is future work.

## Scoring

Each section carries three ratings, used to set priority:

- **Signal** — how strongly it can be diagnosed from a player's games (high/medium/low)
- **Support** — free data and tooling available (strong/partial/none)
- **Band value** — how much it decides results at 1400–1800

## Tier 1 — build first

Strong signal, strong free support, high band value. These prove the pipeline end to end.

### S1 · Tactical pattern gaps — **designed** ([[capacity.agents.s1-tactical-gaps]])
**Owns:** which tactical motifs the player misses, allows, or executes — by motif, phase and frequency.
**Diagnosed from:** engine-detected critical moves + motif detection (deterministic, proven in prior
art, L-004) + the player's puzzle history.
**Prescribes:** puzzles filtered by theme, phase and difficulty from the CC0 database.
**Signal** high · **Support** strong ([[domain.puzzle-themes]]: 75 labelled themes) · **Band value** high
**Why first:** the only section where diagnosis and prescription share one free, labelled vocabulary.
Everything else has to invent its own.

### S2 · Decision process & clock behaviour — **built** ([[capacity.agents.s2-decision-process]])
**Owns:** the habits that produce errors regardless of knowledge — moving instantly in critical
positions, time-trouble collapse, long-think-then-bad-move (the Kotov-syndrome signature), failure to
check opponent threats.
**Diagnosed from:** `%clk` timestamps against error positions. **No engine needed for most of it.**
**Prescribes:** process changes, not content.
**Signal** high · **Support** strong (clock data verified present, E1) · **Band value** high
**Why early:** it is the cheapest section to build, it targets the process/habit gap type that
content-based coaching never reaches ([[domain.coaching]] § 2), and it is the one an LLM-only coach
cannot do at all — it needs the data.

### S3 · Endgame technique & conversion — **built** ([[capacity.agents.s3-endgame-technique]])
**Owns:** endgame errors by material type, conversion of winning positions, resilience in worse ones.

> **Scope corrected on building.** *Conversion of winning positions is not measurable* under the
> shared eligibility rule, and the rule is right: `diagnosable()` excludes anything beyond
> `DECIDED_CP` because win probability compresses at the extremes (L-009), so errors in won positions
> are both cheap to make and nearly invisible. S3 measures **advantage retention** instead — going
> wrong while clearly better but not yet winning. Narrower, honestly named, and it answers the
> coaching question one step earlier.
**Diagnosed from:** phase-segmented error profile, win-probability trajectories, material
classification at the point of simplification.
**Prescribes:** endgame-tagged puzzles (`rookEndgame`, `pawnEndgame`, …) and the classical
techniques Capablanca orders first.
**Signal** high · **Support** strong (endgame theme tags; public-domain primary source) · **Band value** high

### S4 · Opening repertoire outcomes — **built** ([[capacity.agents.s4-opening-outcomes]])
**Owns:** not opening theory — opening *results*: where the player leaves book, which openings cost
them, how often they are punished before move 15, which named traps they fall into.

> **Scope corrected on building.** *Which openings cost them* is not answerable from 24-game
> corpora — a dozen ECO codes gives every per-opening claim two games behind it, which L-022 records
> as firing for nobody. S4 subdivides by **colour** instead, a real repertoire boundary with half the
> data in each half, and defers per-opening claims to ~100+ game histories. Named traps are not
> built: they need the CC0 trap dataset, and the claim would inherit the same denominator problem.
**Diagnosed from:** ECO/opening headers, the CC0 `chess-openings` trap data, score-by-opening.
**Signal** medium-high · **Support** strong · **Band value** medium
**Why it belongs early:** it settles the contested "openings don't matter below 1800" claim
*per player* with their own evidence, instead of asserting either side ([[domain.chess-concepts]] § E).

## Tier 2 — build once the pipeline is proven

Detection is proven; relevance-weighting (C6) is not. These sections are where that gets solved.

> **Re-scoped 2026-07-28 after E03.** Positional features showed almost no association with this
> band's errors, and the one striking effect failed replication
> ([[experiments.e03-relevance-weighting]]). Two consequences. First, this **confirms the Tier 1 /
> Tier 2 ordering** — at 1400–1800 games really do appear to be decided by tactics and process
> rather than structure, exactly as M1's sources claimed. Second, Tier 2 sections must now justify
> themselves on **peer-deviation** grounds ("you concede this more than your rating peers") rather
> than error-prediction grounds, because error prediction was tested and did not work.

### S5 · Pawn-structure weaknesses — **built** ([[capacity.agents.s5-pawn-structure]])
**Owns:** backward, isolated, doubled and hanging pawns; passed pawns; which side of the structure
the player is on and whether they handle it correctly.
**Support** strong — detectors proven in [[experiments.e02-positional-detectors]].
~~**Blocked on:** C6. Base rates are too high for presence to mean anything on its own.~~

> **Unblocked by counting creation instead of presence.** The base-rate objection was correct and is
> answered rather than ignored: having an isolated pawn is 96 % of games, so S5 counts weaknesses the
> player's own move **creates** in their own camp. Presence is inherited from the opening and the
> opponent; creation is a choice, and only choices are coachable.
>
> **The section carries a limitation none of the others do**, and it is E03's rather than a hedge:
> it can say a player is unusual, not that it costs them anything. Every other section's subject is
> itself a mistake; conceding a structure is not. Only three features are built (isolated, backward,
> doubled) — passed pawns, hanging pawns, islands and majorities are all still absent.

### S6 · Squares, files and piece placement — **built** ([[capacity.agents.s6-squares-and-files]])
**Owns:** outposts, holes, open and semi-open files, the seventh rank, good/bad bishop.
**Support** strong — same detectors. Outposts have the best base rate (7 %) of those tested.
~~**Blocked on:** C6, and the relevance problem is sharper here.~~

> **Three of these five topics were dropped on evidence** → [[experiments.e09-square-candidates]].
> Screened before the section was written: holes (spread 1.25), bad bishops (1.27) and unused open
> files (1.31) do not distinguish players at this band. Outposts (**2.15**) and the seventh rank
> (**1.82**) do.
>
> The warning in this entry was half right. A correct outpost detection is *not* a trivial edge
> knight — outposts turned out to be the strongest discriminator in the project. What is trivial is
> everything phrased as a property of the player's own position (L-024).

### S7 · Calculation quality — **screened and not built** ([[experiments.e10-calculation-candidates]])
**Owns:** the calculation skills distinct from pattern knowledge — finding quiet moves, finding
defensive moves, depth of forcing sequences, breadth of candidate consideration.

> **The warning in this entry was right, and is now measured.** The contrast that would isolate
> calculation — erring more when the best move is quiet than when it is forcing — has a median of
> **1.17** and players differ on it by a spread of **1.27**, the range of every failed candidate.
> The one rate that does spread, `missed_quiet` at 1.56, correlates **+0.737** with `missed_forcing`:
> the players who go wrong on quiet moves are the players who go wrong on forcing moves, so a claim
> built on it would restate the overall error rate.
>
> **S7 becomes a consumer of V9 rather than a section.** A probe gives a position untimed and asks
> for a move *and a reason*, which separates *did not see it* from *could not work it out*. No
> arrangement of game records does that. Blocked on **D10**.
**Support** partial — `quietMove` and `defensiveMove` themes give labelled material, but measuring a
player's calculation *from games alone* is weak: a missed quiet move may be a knowledge gap, a skill
gap, or a clock gap.
**Notably:** this section exists only because the Lichess vocabulary revealed it (D2) — our own
concept map had no slot for it. It is also the section most dependent on **V9 probes**, since
calculation is best measured by asking.

### S8 · Attack & defence
**Owns:** king attack and defence — attacking the castled king, pawn storms, sacrifice soundness,
defensive resources, king safety concessions.
**Support** partial — `kingsideAttack`, `queensideAttack`, `exposedKing`, `sacrifice` themes exist;
soundness needs the engine.

## Tier 3 — hard; needs proxies or the language layer

Concepts about *intention and relation*, not arrangement ([[domain.positional-vocabulary]]).
Scheduled last deliberately: they are where an LLM-based coach is most likely to produce fluent
nonsense, so they should be attempted only once the evidence pipeline can hold them to account.

### S9 · Planning & prophylaxis
Requires knowing what the opponent intended and whether it was prevented. Engine-assisted proxy:
did the move reduce the opponent's best available continuation? **Signal** low-medium · **Support** none

### S10 · Style & repertoire fit
Measured tendency versus measured performance, per [[domain.coaching]] § 6 — the falsifiable version
of "style". **Signal** medium · **Support** partial · Needs enough games per player.

### S11 · Practical & psychological
Tilt after losses, collapse in won positions, resilience. Partially visible in result sequences,
clock behaviour and conversion rates; the rest needs V9 dialogue. **Signal** low-medium ·
**Support** partial

## Not sections — orchestration roles

These are M3 architecture, not knowledge domains. Listing them here so they are not mistaken for
sections and accidentally built as topic agents:

| Role | Purpose |
|---|---|
| Profile custodian | owns the structured player profile all sections read and write (C1) |
| Prober | conducts active assessment (V9) — separates knowledge from skill gaps |
| Path planner | consumes all sections, produces the ordered learning path (V5, V6) |
| Explainer | turns the profile into language the player can act on (V8) |
| Evaluator | measures the swarm against [[evaluation]] |

## Priority order for M4

**S2 → S1 → S3 → S4 → S5 → S6 → S7 → S8 → S10 → S11 → S9**

S2 leads rather than S1, despite S1 being the richer section: it is the cheapest to build, needs no
engine for most of its signal, and therefore proves the whole pipeline — ingest, profile, diagnose,
explain — at the lowest cost. The first agent's job is to make the architecture real, not to be the
best agent.

## Open

- Sections are sized by *diagnostic coherence*, not by an estimate of agent complexity. S1 may prove
  large enough to split (motif detection vs. motif prescription).
- Tier 2 cannot start until C6 (relevance weighting) is answered, or its agents will emit true and
  useless statements (R-14).
- No section owns *concept prerequisites* — the ordering knowledge in [[domain.chess-concepts]] § C.
  That may belong to the path planner rather than to any section. Flagged for M3.
