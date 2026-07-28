---
id: cas-learning-lessons
title: Lessons Learned
desc: 'Generalisable lessons extracted from executed work — what worked, what did not, and why.'
updated: 1785254500000
created: 1785254500000
---

# Lessons Learned

Append-only log. One entry per lesson, newest first. A lesson is only a lesson if it would change
what a future cycle does — otherwise it is a diary entry and does not belong here.

## Template

```
### L-NNN — <short title>
**Date:** YYYY-MM-DD · **Cycle / mission step:** Mx · **Class:** technique | process | domain | tooling
**Context:** what was being attempted
**Observation:** what actually happened (with evidence)
**Lesson:** the generalisable claim
**Applied to:** the note/rule/code changed because of it
```

---

### L-005 — Classify errors on win probability, not raw centipawns
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (F1) · **Class:** technique
**Context:** Writing the E01 benchmark's error classifier, then reading Arrakis Engine's analyzer.
**Observation:** Arrakis converts centipawns to win probability with the Lichess formula
`winPct = 50 + 50 × (2 / (1 + exp(−0.00368208 × cp)) − 1)` before classifying moves. Raw centipawn
thresholds misrank badly at the extremes: losing 100cp at equality can decide the game, while losing
100cp at +900 is irrelevant — yet a fixed threshold labels both identically. They also cap evals at
±1000cp **and** force loss to 0 when the played move equals the engine's best move, documenting the
bug this fixes: mate-delivering moves such as `Qxf7#` otherwise register as 2000cp *losses*, because
Stockfish encodes mate as ±30000 internally.
**Lesson:** Error classification must operate on win probability, with an explicit mate/best-move
guard. Our E01 benchmark used raw centipawn thresholds and lacks the played-best-zero rule — it
measures throughput correctly but its labels need revising before they mean anything.
**Applied to:** [[domain.prior-art]]; `experiments/e01-engine-throughput/benchmark.py` (to revise);
open question C2.

---

### L-004 — Tactical motifs are deterministically detectable; be conservative about it
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (F1) · **Class:** technique
**Context:** Reading Arrakis Engine's `motifs.py` while resolving F1.
**Observation:** Twelve tactical motifs (fork, pin, skewer, discovered check, mate threat, removing
the defender, hanging piece, trapped piece, back-rank mate, deflection, overloaded defender,
zugzwang) are detected by ~900 lines of pure Python over `python-chess` primitives plus a min-value
SEE heuristic — no LLM, no puzzle-database matching, and cheap enough to run only on critical moves.
The author states the detectors are deliberately conservative ("we'd rather miss a real motif than
tag a false positive") and documents a calibration failure where the skewer detector over-fired
10–18× before being constrained.
**Lesson:** Don't reach for a model where board logic suffices — the tactical half of diagnosis is a
solved, free, testable problem. Adopt **conservative-by-default** as a stated principle for every
detector: for a coach, a false positive is worse than a miss, because it sends the player to study
something that was never wrong. And calibrate each detector against real games; plausible-looking
detector code over-fires.
**Applied to:** [[domain.prior-art]], [[domain.signals]], risk R-13, the D4 framing in
[[open-questions]].

---

### L-003 — Diagnosis is computable; only explanation and dialogue need a language model
**Date:** 2026-07-28 · **Cycle / mission step:** M1 · **Class:** technique
**Context:** Answering M1 Q11–Q13 — which coaching diagnoses are computable from game data.
**Observation:** Nearly every diagnostic signal a coach uses (error rates by phase, missed tactics,
motif of the refutation, clock behaviour, conversion rates, repertoire performance) is derivable
from an engine plus parsing plus statistics, at zero marginal cash cost. The language model is
needed only for explaining, planning, and conducting dialogue. See [[domain.signals]] § 5.
**Lesson:** Architect the swarm to **compute first and speak last** — a deterministic analysis core
produces a structured player profile, and language models operate on that summary rather than on raw
games. Token volume then stays roughly constant per player instead of scaling with moves analysed,
which is what makes constraint C1 achievable at all.
**Applied to:** [[decisions.0002-compute-first-speak-last]] (proposed), [[domain.signals]],
[[capacity]] cost discipline.

---

### L-002 — Passive game analysis cannot tell a knowledge gap from a skill gap
**Date:** 2026-07-28 · **Cycle / mission step:** M1 · **Class:** domain
**Context:** Building the diagnosis taxonomy in [[domain.coaching]] § 2.
**Observation:** The same observable error — a hung knight — has at least four distinct causes
(missing knowledge, unexecutable knowledge, a broken checking habit, a psychological state), each
needing a different remedy. Absence of a correct move in a game is weak evidence of not knowing it,
and a correct move may have been played for the wrong reason. Games alone cannot separate these.
**Lesson:** The swarm needs an **active assessment** capability — probe positions where the player is
asked for a move *and its reason*, under controlled conditions — not only passive analysis. Player
interaction is therefore a core diagnostic capability, not a presentation layer added at the end.
**Applied to:** [[mission]] M3 brief, [[domain.signals]] § 3, [[state]] open questions.

---

### L-001 — The knowledge map determines the agent topology, so it must be revisable
**Date:** 2026-07-28 · **Cycle / mission step:** M1 setup · **Class:** process
**Context:** Framing M1 before doing the research.
**Observation:** M2 chunks the M1 knowledge overview into sections, and M4 builds one agent per
section. Any error or arbitrary boundary in the M1 map propagates directly into the swarm's
structure and is expensive to undo once agents exist.
**Lesson:** Treat the section catalogue as a versioned artefact with an explicit revision
procedure, and prefer boundaries that follow *how coaches diagnose* rather than how chess books are
organised — book structure is didactic convention, not diagnostic structure.
**Applied to:** [[mission.step-01-foundations]] (method + definition of done), and the M2 brief
in [[mission]].
