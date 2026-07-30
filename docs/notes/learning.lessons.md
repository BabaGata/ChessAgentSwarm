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

### L-013 — Population rates converge fast; individual verdicts at the boundary do not
**Date:** 2026-07-31 · **Cycle / mission step:** M7 · **Class:** technique
**Context:** Widening the peer reference from 7 players to 38 ([[architecture.peer-reference]]).
**Observation:** The population rate for the long-think condition moved from 17.7 % to **17.8 %** —
a seven-player sample had already estimated it to within 0.1 points across 3,675 moves. Yet
`esik24`, asserted at `priority` against the small reference, went **silent** against the wide one.
A 0.4 percentage point change in the peer rate flipped the verdict, because that player's confidence
interval straddles the population rate.
**Lesson:** These are the same fact seen twice. A small reference is fine for *estimating a
population* and unsafe for *judging a borderline player*, precisely because the borderline is where
a small shift in the reference decides the answer. Two consequences were applied. First, tiering was
wrong: `priority` was reached on **distinct-game count alone**, so a claim whose interval merely
grazed the population rate printed at the strongest tier. It now additionally requires the interval
to clear the comparison **by a margin** (1.25×), which regraded four of six findings from `priority`
to `focus`. Second, the tier follows the interval's *lower bound* rather than the point estimate, so
a player at 1.89× can rank below one at 1.78× — apparent size and strength of evidence are different
things, and the tier should track the second.
**Applied to:** `chesscoach/confidence.py` (`PRIORITY_MARGIN`), [[architecture.confidence]],
[[architecture.peer-reference]].

---

### L-012 — Self-baselines overstate by however much the population shares the behaviour
**Date:** 2026-07-29 · **Cycle / mission step:** M7 (peer reference) · **Class:** technique
**Context:** Building the rating-peer reference and re-running S2 against it
([[architecture.peer-reference]]).
**Observation:** Four players had apparent long-think weaknesses at 2.10–2.85× their own baselines.
Measured against a population of their peers, two disappeared entirely — one sat inside the
population rate, one *below* it — and the two that survived fell to 1.65× and 1.52×. The population
rate for that condition is 17.7 %, against individual self-baselines of 9–11 %.
**Lesson:** A within-player comparison overstates every effect by roughly the amount the behaviour is
universal, and the overstatement is invisible from inside one player's data. Concretely here it was
a factor of about 1.7 and it turned two non-findings into confident ones. Any coaching system without
a peer reference will over-report, and will do so most confidently on exactly the conditions that are
most universal — because those have the largest gap between the population rate and any individual's
"other moves". The display must also state the comparison actually used: showing a self-baseline lift
for a claim promoted on a peer comparison would misrepresent the evidence.
**Applied to:** `chesscoach/peers.py`, S2's peer-aware assertion, `_comparison_line` in the CLI,
and the resolution of open question C6.

---

### L-011 — A weakness most players share is a base rate, not a diagnosis
**Date:** 2026-07-28 · **Cycle / mission step:** M5 · **Class:** domain
**Context:** Running S2 on 135 real games across seven players, the first non-synthetic data in the
project ([[mission.step-05-assess-s2]]).
**Observation:** Four of six eligible players showed `long_think_error` at 2.10×, 2.22×, 2.31× and
2.85× against their own baselines. The uniformity was the finding. The mechanism is plain once seen:
a long think happens *because* the position is hard, and hard positions produce errors — the
condition is **selected by the same thing that causes the outcome**. A self-baseline cannot separate
"you are bad after long thinks" from "long thinks happen in bad positions".
**Lesson:** Before asserting a measured effect, ask whether the condition is *selected* by something
correlated with the outcome. Where it is, a within-player baseline is structurally incapable of
answering, and only a peer population can. Two practical consequences: conditions of this shape are
marked and **withheld** rather than reported (S2's `selection_confounded`), and the check should be
automatic — comparing findings *across* players would have caught this immediately, which is
evaluation metric D1 and is now promoted. More generally, this is why the peer reference corpus is
no longer optional: three separate lines of work (C6, D2, and S2's assertability) now depend on it.
**Applied to:** `chesscoach/sections/s2_decision_process.py`, [[mission.step-05-assess-s2]],
risk R-14, and the reordered priorities in [[state]].

---

### L-010 — When an agent fails its evaluation, suspect the fixture first
**Date:** 2026-07-28 · **Cycle / mission step:** M4 (S2) · **Class:** process
**Context:** Scoring the first agent against the planted `time_pressure` weakness.
**Observation:** S2 reported a `long_think_error` at 2.92× and missed the planted weakness entirely.
The agent was right and the fixture was wrong: the generator's time model made the flawed player
think slowly for its first ten moves, so "long think" coincided exactly with "early game", where
errors still cost win probability, while the planted time-pressure errors happened late, where they
compress toward invisibility (L-009). S2 had correctly found the strongest real pattern in the data
it was given.
**Lesson:** A failed evaluation is a claim about the *pair* of agent and fixture, and the fixture is
the newer and less-examined half. Before changing an agent, check what the fixture actually contains
— here, that a synthetic condition had been made to coincide with a confound. Two fixes followed,
one on each side: the generator now uses uniform think times so a time-pressure plant cannot be
confounded with a long-think signal, and **S2 now excludes moves played in already-decided
positions**, which is a genuine improvement that only surfaced because something was measured. Within
competitive positions the planted signal reads 37.7 % against 6.8 %, where across all moves it read
8.9 % — the decided positions had been burying it.
**Applied to:** `chesscoach/sections/s2_decision_process.py` (`DECIDED_CP`), `cli.py` time-model
options, [[mission.step-04-first-agent]], and `ScoreCard`, which now distinguishes *declined for
insufficient data* from *missed* — scoring an honest refusal as a failure would penalise the
behaviour the whole design is trying to produce.

---

### L-009 — A planted weakness is not automatically a *measurable* weakness
**Date:** 2026-07-28 · **Cycle / mission step:** M3 (evaluation harness) · **Class:** technique
**Context:** Building the planted-weakness generator, family C of [[evaluation]].
**Observation:** Two problems appeared as soon as the fixture was checked against the analysis core.
First, the initial fixture gave planted moves a 16.9 % error rate against **0.0 %** for the flawed
player's other moves — because outside the planted condition it played the engine's own choice. That
is a far easier discrimination than any real player presents, and any agent measured against it
would have been flattered. Second, only a minority of deliberately bad moves registered as errors at
all: once a game is decided, further bad moves cost almost no win probability, so the *measured*
severity of a planted flaw is diluted by the damage already done. Adding a background mistake rate
fixed the first problem and made the second visible — planted error rate fell from 16.9 % to 7.7 %
against a 4.3 % baseline, a lift of 1.81×.
**Lesson:** An evaluation fixture needs its own verification step before anything is scored against
it. Two requirements follow: **background noise**, so the flawed player is not perfect outside the
planted condition; and awareness that **win-probability labels compress in decided positions**, so a
weakness planted late in a lost game is nearly invisible. A fixture that cannot be seen by the
deterministic layer is not a test of any agent — it is a broken fixture, and `check-eval-set` exists
to catch that before it wastes a measurement.
**Applied to:** `chesscoach/evaluation/planted.py` (`background_severity`, and `write_eval_set`
refusing a set where nothing was planted), the `check-eval-set` command, and [[evaluation]]'s
limitations.

---

### L-008 — Held-out replication is not optional; the first striking result was an artefact
**Date:** 2026-07-28 · **Cycle / mission step:** M2 (E03) · **Class:** process
**Context:** Testing whether positional features predict a player's errors
([[experiments.e03-relevance-weighting]]).
**Observation:** Pooled analysis showed nothing. Stratifying by game phase produced a striking
effect — backward pawns in endgames with error lift 2.40 and 2.12 — together with a tidy mechanistic
explanation for why pooling had hidden it. On a held-out sample of four different players the same
measurement gave 0.88 and 0.76: not merely absent, **reversed**. With 8 features across 3 phases
there were 24 cells; the largest was always going to look impressive.
**Lesson:** Any association discovered by searching a space of measurements must reproduce on a
held-out sample of *different players* before it is written down as a finding — and a plausible
mechanism is not evidence, it is the thing that makes an artefact convincing. Practically: every
diagnostic rule the swarm ever uses gets discovered on one player set and confirmed on another, and
the same discipline becomes the B1 split-half test in [[evaluation]]. The cost of this replication
was ten minutes of engine time.
**Applied to:** [[experiments.e03-relevance-weighting]], risk R-13, [[evaluation]] T0 tier,
open question C6.

---

### L-007 — Detecting a feature is easy; knowing it matters is the hard part
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (E02) · **Class:** domain
**Context:** Building positional feature detectors to resolve D4, the project's biggest technical risk.
**Observation:** Four positional concepts were detected with 16/16 hand-verified precision in a few
hundred lines of `python-chess` — no engine, dataset or model. But isolated pawns appear in 74.7 % of
sampled positions and 96 % of games, and rooks on open/semi-open files likewise. Worse, several
*correctly* detected outposts were edge knights in simplified endgames that no coach would ever
mention: the definition held, the relevance did not.
**Lesson:** The scarce resource in automated coaching is **relevance, not detection**. Any pipeline
step that outputs "feature X is present" must be paired with evidence that X *mattered* — through
co-occurrence with evaluation loss, recurrence across the player's games, or comparison against a
peer population. It also names a failure mode that no correctness test catches: **output that is
true, specific and useless.** That belongs in [[evaluation]] as something to test for explicitly.
**Applied to:** [[experiments.e02-positional-detectors]], [[domain.signals]], risk R-14, the M2 brief
(sections defined by what goes wrong, not by what is present).

---

### L-006 — A single move's error label is not a fact; a recurring pattern is
**Date:** 2026-07-28 · **Cycle / mission step:** M1 (E01) · **Class:** domain
**Context:** Measuring whether analysis depth changes the diagnosis
([[experiments.e01-engine-throughput]]).
**Observation:** Between depth 15 and depth 18, about a quarter of error labels disagree and one
blunder in six is seen by one setting and not the other. Depth 12 agrees with depth 18 on only 61 %
of labels. The disagreement concentrates at classification thresholds — moves landing just either
side of a boundary.
**Lesson:** Per-move claims are unreliable at any affordable depth; **aggregate, recurrence-based
claims are robust**, because threshold noise averages out over many instances while a genuine
weakness does not. Therefore: the swarm may say "you missed knight forks nine times across six
games"; it may not assert "move 23 was a blunder" as a bare fact. This turns the minimum-sample rule
(C2) from good practice into a correctness requirement, and it means analysis depth must be stored
with every derived signal — profiles built at different depths are not comparable.
**Applied to:** [[experiments.e01-engine-throughput]], [[domain.signals]], open question C2,
risk R-13.

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
