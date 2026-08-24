---
id: cas-adr-0011
title: 'ADR-0011 — Detection correctness outranks expert agreement'
desc: 'The author filled three Form B/C and found the detectors systematically wrong. The expert review is paused as a priority and becomes an instrument for finding defects; being right outranks being agreed with.'
updated: 1788220800000
created: 1788220800000
---

### ADR-0011 — Detection correctness outranks expert agreement

**Date:** 2026-08-23 · **Status:** accepted

**Context.** The thesis author completed the first three Form B/C of the expert review — the first
time anyone had read the system's *reports* against the games with the intent to judge them — and
found defects that no internal measurement had caught:

- **Every Black move was cited one number too high.** Confirmed and fixed the same day
  (`phrasing.move_number`, ply is 1-based and the formula assumed 0-based). The existing test
  asserted *"ply 40 is move 21"*, which is the bug written down as the expectation, so it could never
  have failed on it. → **L-044**
- **Moves are printed in UCI** (`g8f6`) where a chess player reads SAN (`Nf6`).
- **Games are cited by bare id**, with no colours, opponent or date, so a player cannot find them.
- **The motifs are wrong often enough that the author calls the design faulty** — forks
  mis-detected, `moved_into_attack` firing on ordinary exchanges, king-attack claims raised deep in
  endgames.
- **Cited examples are frequently incomprehensible** — engine-preferred moves with no material or
  clear positional consequence the player can see.
- **Advice is not actionable enough**, and the "edge of your repertoire" wording around move 15 is
  wrong for this level, where players leave book by move 8 or around castling.

The author's instruction: *"The motif detection design should be fixed and tested as a priority.
Expert review is not important anymore but the weakness detection correctness is."*

**Decision.** **Detection correctness becomes the project's first priority, ahead of expert
agreement.** The pre-registered agreement criterion is not abandoned — it is recorded, with its 0/6
result, as a measurement taken on a system now known to be defective, and it is no longer the thing
being optimised. The expert review changes role from *scoreboard* to *defect-finding instrument*, and
the remaining Form A collection is dropped as a requirement.

This is a **restatement of the goal by the thesis author**, which
[[process]]'s phase 8 names explicitly as a trigger for revising the mission rather than deferring.

**Alternatives considered.**

- *Finish the review first, then fix.* Rejected: five criteria would be measured against output whose
  examples the author has already shown to be wrong, spending the reviewer's remaining time
  generating data about a system that is being replaced.
- *Fix only the presentation defects and keep the agreement target.* Rejected: SAN and richer
  citations make the reports **easier to check**, which is exactly why they are worth doing, but they
  change nothing about whether a fork is a fork.
- *Treat it as tuning.* Rejected on evidence. `tactics.py:280` `_lands_safely` asks
  "attacked → is it defended?" with no piece values and no exchange evaluation, while `material.py`
  already contains a static exchange evaluator the motifs never call. **Two different notions of
  "safe" exist in one codebase and the motifs use the naive one.** That is a design fault.

**Consequences.**

- **Makes easy:** every downstream claim gets more trustworthy at once, because sections consume the
  same detectors. Verification also gets cheaper — SAN and real game citations mean the author can
  check an example in seconds rather than reconstructing a position.
- **Makes hard:** the agreement figure cannot be quoted as a headline result, and the thesis must
  present it as what it is — a measurement of a system whose detectors were subsequently found wrong.
- **Forecloses:** nothing architecturally. The detectors sit behind a stable interface and the
  sections do not change shape.
- **Costs:** re-screening every motif needs hand-verified samples, which is author time, and it is
  the same method [[experiments.e04-motif-precision]] used when it caught two over-firing detectors.
- **Invalidates:** [[experiments.e31-move-level-agreement]] and
  [[experiments.e44-clock-on-noted-moves]] joined the author's noted move numbers with the broken
  formula, so roughly half of each — every Black note — matched the wrong move. Both must be re-run
  before their figures are quoted.
- **Scorecard:** D4 (V4 gap detection) has been the project's joint-highest score at 5. It is not
  defensible at 5 while the detectors are known faulty, and it moves down until re-screened.

**Vision link.** V4 (gap detection) directly; V8 (explainability) via citations a player can act on;
and the hard rule that **no coaching output may be unfalsifiable** — an example the player cannot
understand is not evidence, however correct the engine is about it.

**Revisit when:** the motif re-screen reports precision per detector on hand-verified samples. If
precision is high and the author's reading still disagrees, the fault is in the *naming* rather than
the detection, and that is a different repair.
