---
id: cas-design-narrated-session
title: 'Design — a local model in the coaching session'
desc: 'The report gains a model-written summary checked against the measurements, the session takes follow-up questions, and the prober returns as an exercise from the player''s own games.'
updated: 1789862400000
created: 1789862400000
---

# Design — a local model in the coaching session

**Source:** the author, 2026-09-19 · **Status:** built and measured · **Serves:** V9, V8 ·
**Builds on:** [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]],
[[design.coaching-conversation]], [[capacity.agents.prober]]

## What the author asked for

> "Zašto se ne koristi jezični model … bilo bi dobro da se jezični model ipak koristi. … da rezultate
> ispiše jezični model i da se sesija nastavi na način da igrač može postaviti još koje pitanje
> modelu." — and — "provjeri može li se i prober na kraju iskoristiti na neki praktičan način."

Until now `coach` ran no model at all: the report is templates, the prober is off, the model-backed
modules (`opening_summary`, `answering`, `plan_selector`) sat outside the session.

## The rule this keeps

ADR-0013: **a local model may rephrase what it cannot assert.** Every model output in the session
is checked deterministically against the text it was given, and falls back to that text when it
fails. The session is never worse than the template report, and the report the player can audit
stays printed in full.

## Three parts

1. **Summary (`narrator.py`).** For each finding the plan acts on, the model gets a short fact sheet
   built from the measurement — nothing else — and writes one or two sentences in the second
   person. Each is checked by `grounding.check` (no move or square absent from the sheet, novelty
   ≤ 0.45) **plus a new number check**: every number must occur in the sheet. A rejected sentence
   leaves its finding out; none kept or no model → no summary, and one line saying why. Printed above
   the full report under a heading that says a local model wrote it from the measurements below.
   (First designed on the whole rendered report; E92 changed it — see *Built*.)
2. **Follow-up questions (`followup.py`).** After the report the player may ask questions. First
   the model answers from the report alone, or says the report does not cover it; the answer is
   checked the same way. If the report does not cover it and the book knowledge graph is reachable,
   `answering.answer` answers from the books with attribution (E79 rules unchanged). Otherwise a
   fixed refusal. The model never answers from its own chess knowledge.
3. **Exercise from the player's own games (`exercise.py`).** The prober's move check without its
   diagnosis: for each prioritised finding, one position from the player's games where the engine
   named a better move. The player types a move; the check is deterministic (`_same_move`); the
   feedback shows what they played in the game and the engine's move. **No classifier and no change
   to the gap type** — D10 is still open, so the answers are recorded on the profile (`apply=False`)
   and nothing else. Any claim kind with a better move qualifies, not only motifs, because this is
   practice, not diagnosis.

## Definition of done

- [x] three modules with tests that need no running model (injected transport / fakes)
- [x] `coach` runs summary → report → questions → exercise; each step can be switched off; EOF and a
      stopped Ollama end the session cleanly
- [x] the `--probe` path's `peers` bug fixed
- [x] measured on real profiles: summary acceptance rate, time per summary, and the rejection reasons
- [x] thesis updated to describe what the model does and what it measured at

## Alignment (phase 2)

1. **Serves** V9 (dialogue) and V8 (every model sentence is checked against the evidence-bearing
   report). C1 holds: `qwen2.5:3b`, 1.9 GB, local (E50).
2. **Moves** D9 dialogue; D8 only if the summaries are accepted at a useful rate.
3. **Cheaper way?** The model already rephrases opening plans (E50) and answers book questions
   (`ask`); this reuses both and adds only the number check and the session loop.
4. **Forecloses** nothing: every part is optional and falls back to the template path.
5. **Narrowed**: the model summarises and answers; it does not choose priorities, write the plan or
   judge the player's reasons.

## Built

`chesscoach/narrator.py` (summary + the number check), `chesscoach/followup.py` (questions),
`chesscoach/exercise.py` (practice), `chesscoach/after_report.py` (the session around the report,
testable without a terminal). `coach` gained `--no-summary`, `--no-questions-after`,
`--no-practice` and `--summary-model`; the `--probe` path's undefined `peers` is fixed. 41 tests, none
needing a running model.

**The first real run changed the design.** Asked *"What is a pin?"*, the model answered **from the
report** with a wrong definition, and it passed: novelty 0.42, while a good answer about the report
scored 0.43. Novelty cannot tell a definition invented from the report's vocabulary from a
paraphrase of the report. So the route decides instead: a question asking what something *is*
(English and Croatian patterns) never reaches the report path and goes to the books or is refused,
and the prompt forbids explaining chess ideas. A test asserts the report prompt is never sent for
such a question -- the first version of that test passed for the wrong reason (the fake answer failed
novelty anyway) and was rewritten to count calls.

**The summary's input changed twice on reading its output.** Whole report: findings mixed up (3 of 8
wrong). One finding's block of report text: "% of the time" read as "% of the games", labels copied.
Shipped: a **fact sheet** per planned finding, plain sentences built from the measurement, so the
model sees one finding and the share is said in words (1 of 8 wrong, a reversed relation). The
summary is therefore built from the profile, not from the rendered report.

**Practice needed the board.** Moves are stored as UCI; the first version compared text and would
have marked `Bg4` wrong against `c8g4`. Answers are read on the board, and the position is printed
as a board from the side to move.

43 tests; 2,220 in all. Measured in [[experiments.e92-narrated-session]]; decision
[[decisions.0021-a-local-model-in-the-session]].
