---
id: cas-mission-m6
title: 'M6 — Maintenance log'
desc: 'The recurring maintain-and-commit step: refactoring assessments, and what was deliberately left alone.'
updated: 1785257800000
created: 1785257800000
---

# M6 — Maintenance log

**Status:** recurring · **Parent:** [[mission]]

M6 runs at the end of every cycle. [[process]] requires the refactoring question to be answered in
three parts — **need**, **usefulness**, **possibility** — and "no refactor needed" is a valid answer
that must be *stated*, not assumed. This note accumulates those answers so the codebase's shape has
a history rather than just a present.

---

## 2026-07-28 · after M5

### Done — extract the engine/cache session

| | |
|---|---|
| **Need** | Real. Three CLI commands each opened a cache, opened an engine, analysed, and closed both — the same sequence written three times. It was also the least-tested code in the project (`cli.py` at 41 %), and for a related reason: logic living inside command handlers is awkward to test. |
| **Usefulness** | High. The next agents add more commands, so the duplication was about to become fourfold. Extracting it also moved provenance construction next to the analyser that determines it, which matters because the engine and depth recorded on a finding must be the ones actually used. |
| **Possibility** | Safe. 158 tests covered the modules underneath; the extraction was mechanical and verified behaviour-preserving by re-running the planted set to identical numbers (37.7 % vs 6.8 %, 5.54×, 0 spurious). |

**Result:** `chesscoach/pipeline.py` — `engine_session`, `EngineSession.provenance`, `CacheStats`,
`load_games`. Coverage 80 % → **82 %**, tests 158 → **166**.

One thing the extraction forced into the open: cache statistics have to be **snapshotted before the
session closes**, because the row count needs a live connection and every caller naturally reports
those numbers after the work is done. That was a latent bug waiting for the first caller to read
stats slightly later than the others.

### Deliberately not done

| Candidate | Assessment |
|---|---|
| **Split `cli.py` into a package** | Need: mild — it is the largest module at ~190 statements across five commands. Usefulness: low today; it is still readable top to bottom and the commands share little beyond what was just extracted. **Revisit at ~8 commands or 300 statements.** |
| **Move E02's positional detectors into the package** | Deliberate. `experiments/` holds historical records of what was measured; reproducing an experiment must not depend on later refactors. The detectors get reimplemented against the section contract when a positional section is built — already the stated intent in [[experiments.e02-positional-detectors]]. |
| **Cover `evaluation/choosers.py`** (0 %) | Accepted. It exists only to drive a live engine subprocess; a unit test would test a mock. It is exercised whenever an evaluation set is generated. |
| **Parallelise the analysis core** | Deferred, not refused. A performance issue, not a correctness one ([[mission.step-05-assess-s2]] § 1), and the seam already exists because the analyser is injected. Stays P4 in [[state]] until analysis time is actually in the way. **Un-deferred 2026-07-29** — see below. |

---

## 2026-07-29 · parallel analysis, un-deferred on its own stated condition

The M5 assessment deferred this with an explicit trigger: *"until analysis time is actually in the
way"*. Widening the peer reference to a real population means analysing several hundred games, and
at the sequential rate that is roughly an hour per rebuild. The trigger fired, so the work was done
rather than deferred again — which is the point of writing the condition down instead of a vague
"later".

| | |
|---|---|
| **Need** | Real, and newly so. The same code was fine at seven players and is not fine at forty. |
| **Usefulness** | High: the peer reference has to be rebuilt whenever a section adds a condition, so this cost recurs. |
| **Possibility** | Safe. E01 already established the shape — one engine thread each, parallelise per *position* rather than per game — and the design needed no change to the analyser, only a prefetch pass that fills the cache the sequential path then reads. |

**Result:** `chesscoach/analysis/parallel.py`. Positions are collected across the whole corpus,
deduplicated, evaluated across many single-threaded engines, and written to the cache in one pass.
Deduplication earns its place beyond the parallelism: openings repeat heavily both within and across
players, so a multi-player corpus costs much less than the sum of its parts.

**Measured, and an earlier claim corrected.** One player's 24 games at depth 15 on a cold cache:
~119 s implied by E01's sequential rate → **40.9 s**. That is about **3×**, where
[[mission.step-05-assess-s2]] had said "roughly an order of magnitude". The original figure was
extrapolated from per-position numbers without checking end to end; the note now carries the
correction rather than the estimate.

### Documentation health

Vault checked against reality: [[mission]] progress table, [[state]] scorecard and priorities,
[[capacity.agents]] roster, [[domain.sections]] and [[architecture]] implementation status all now
match the code. Three lessons (L-009, L-010, L-011) and one materialised risk (R-14) were filed
during M4/M5 rather than at the end, which is the intent.
