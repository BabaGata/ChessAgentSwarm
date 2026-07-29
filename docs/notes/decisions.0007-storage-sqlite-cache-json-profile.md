---
id: cas-adr-0007
title: 'ADR-0007 — SQLite analysis cache, JSON player profiles'
desc: 'Bulk position analysis in a keyed SQLite cache; the player profile as a versioned JSON document.'
updated: 1785256600000
created: 1785256600000
---

# ADR-0007 — SQLite analysis cache, JSON player profiles

**Date:** 2026-07-28 · **Status:** accepted

## Context

Two very different kinds of data. Position analysis is **bulk, uniform and machine-facing** — tens of
thousands of rows per player, write-once, read by aggregation. The player profile is **small,
structured and human-facing** — the thing a developer, a reviewer, and eventually a thesis examiner
needs to read and check by hand.

Storing both the same way makes one of them awkward.

## Decision

- **SQLite**, one file, for position analysis. Keyed by `(position, engine build, depth)`.
- **JSON documents**, one per player, versioned, for the profile.
- **Vendored CC0 corpora** (puzzle themes, openings/traps) as files, downloaded once, no runtime
  network dependency.

## Rationale

**Why a keyed position cache.** Positions recur — across a player's games, and heavily across
players in the opening. Cost falls with every player analysed. It also makes re-analysis at a fixed
depth reproducible, which [[evaluation]]'s B4 determinism test requires. The engine build and depth
belong in the key rather than in a column, because E01 showed results are **not comparable across
depths** — mixing them is the bug this key prevents structurally rather than by discipline.

**Why JSON for the profile.** It can be read, diffed and hand-checked. Test fixtures are files. A
reviewer can look at exactly what the system believed about a player on a given date, and a bad
finding is visible rather than buried in a join. The profile is small — findings, not positions — so
none of the reasons to reach for a database apply.

**Why not Postgres or a vector store.** No server, no service, nothing to pay for or keep running
(C1, C2). Nothing here needs similarity search; every lookup is exact.

## Consequences

- **Easier:** zero-setup local operation; reproducibility; inspectable profiles; cheap incremental
  sessions.
- **Harder:** two stores to keep consistent. Mitigated by making the profile **regenerable** from
  corpus + cache — it is a derived artefact, and if the two disagree, the profile is rebuilt.
- **Forecloses:** concurrent multi-user access, which is a stated non-goal.
- **Watch:** the cache grows without bound. It is a cache, so it can be pruned by last-use; noted
  rather than solved, since a laptop-scale corpus will not hit it soon.

## Vision link

C1–C3 (free, single machine, self-hostable), C5 (auditable), and B4 determinism in [[evaluation]].

## Revisit when

The cache stops fitting comfortably on disk, or profiles grow large enough that reading them by hand
stops being the point.
