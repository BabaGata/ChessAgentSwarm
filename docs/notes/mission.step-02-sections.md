---
id: cas-mission-m2
title: 'M2 — Section catalogue'
desc: 'Chunk the coaching knowledge into agent-sized sections, ordered by priority.'
updated: 1785255600000
created: 1785255600000
---

# M2 — Section catalogue

**Status:** first pass done
**Parent:** [[mission]] · **Delivers:** [[domain.sections]]

## Goal

Break the coaching knowledge into small, cohesive sections and order them by priority — where
priority means *how much this section decides results in the target band*, tempered by whether it can
be diagnosed from evidence we can actually obtain.

The catalogue is the swarm's topology: M4 builds one agent per section, in this order. Getting it
wrong propagates into every later step (L-001), so it is versioned and explicitly revisable.

## Alignment check

- **Serves:** V4 (gap detection) and V5 (prioritisation) most directly; V1/V2 depend on the sections
  covering the right ground. C6 (incrementally useful) — the tiering means the first agents ship
  something usable rather than a fragment of everything.
- **Moves:** capacity, not the vision scorecard. Expected for a design step.
- **Cheaper alternative considered:** skip the catalogue and build the obvious tactical agent first.
  Rejected — it would fix the architecture around the section that happens to have the best free
  dataset, rather than around what actually decides games. Tier 1 deliberately leads with S2
  (decision process), which no dataset supports and which matters more.
- **Forecloses:** little. Sections can be split, merged or reordered; the ordering is a plan, not a
  contract.
- **Made more aligned by:** rating every section for *signal* and *support* separately, so a section
  that matters but is hard to diagnose is visible as such instead of quietly dropping out.

## Method

Built by intersecting four things this project already established rather than by topic-listing:

1. the ten knowledge domains K1–K10 ([[domain.chess-concepts]]);
2. the four gap types — knowledge, skill, process, psychological ([[domain.coaching]] § 2);
3. what is actually computable, and at what base rate ([[domain.signals]],
   [[experiments.e02-positional-detectors]]);
4. what free labelled material exists to *prescribe* against ([[domain.puzzle-themes]],
   [[domain.positional-vocabulary]]).

## Result

Eleven sections in three tiers, plus five orchestration roles held out as M3 architecture rather than
knowledge domains. Build order: **S2 → S1 → S3 → S4 → S5 → S6 → S7 → S8 → S10 → S11 → S9**.

The one non-obvious call: **S2 (decision process and clock behaviour) is built first**, ahead of the
richer tactical section. It is the cheapest to build, needs no engine for most of its signal, targets
a gap type that content-based coaching never reaches, and is something an LLM-only coach cannot do at
all. The first agent's job is to make the architecture real, not to be the best agent.

## Definition of done

- [x] Sections are defined by diagnosable failures, not topics.
- [x] Each carries signal, support and band-value ratings.
- [x] Priority order stated with the reasoning for the non-obvious placements.
- [x] Orchestration roles separated from knowledge sections.
- [x] Dependencies recorded — Tier 2 is blocked on C6 (relevance weighting).
- [ ] Reviewed after the first agent exists (M5), when section sizing meets reality.

## Working log

| Date | Activity | Alignment check | Outcome |
|---|---|---|---|
| 2026-07-28 | Built the catalogue from the K1–K10 map, gap types, computability evidence and free prescribable material | see above | 11 sections, 3 tiers, 5 orchestration roles, build order set |
