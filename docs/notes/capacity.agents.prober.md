---
id: cas-agent-prober
title: 'Agent P — The prober'
desc: 'The first agent with a language model in it: asks the player for a move and a reason, and tells a knowledge gap from a skill gap.'
updated: 1785456000000
created: 1785456000000
---

# Agent P — The prober

**Capability:** [[vision]] V9, and the only route to V2 · **Protocol:** [[architecture.interaction]] § 5
**Status:** **deterministic core built and tested; not yet usable on a real player.**

> The protocol was designed in M3 and has not changed. This note is the *agent*: what it is allowed
> to do, what it may not, and how it will be judged.
>
> **Built** (`chesscoach/prober.py`, 28 tests): probe selection, the move check, the inference table,
> and writing `gap_type` back to findings. The model sits behind a `ReasonClassifier` Protocol, so
> the boundary in § 3 is enforced by the type rather than by discipline.
>
> **Not built, and it does not ship without them:** a model-backed classifier — the provider choice
> is open, see § 10 — and the hand-labelled answer set with its inter-rater agreement (§ 4), which
> this note requires *before* any probe result may change a finding. Until that exists the agent can
> be exercised but not believed.

## Why this agent, now

Four scorecard dimensions sit at **zero** — D1 skill, D2 knowledge, D3 style, D12 dialogue — and they
are not four gaps but one: **nothing in the system asks the player anything.** Every finding the
swarm produces today carries `gap_type: unknown`, and S1's design note says plainly that it cannot do
better, because a missed fork cannot distinguish *doesn't know the pattern* from *knew it and didn't
see it here* (L-002).

That distinction is not a refinement. It is the difference between two opposite prescriptions —
*teach the pattern* versus *fix the checking routine* — and getting it wrong sends the player to
study something that was never wrong.

It is also, for the thesis, the point at which the swarm contains an actual **agent** rather than a
deterministic detector. Everything built so far is a pipeline; this is the first component that
takes an open-ended input it cannot enumerate in advance.

## 1 · Remit

Given the arbiter's one or two shortlisted findings, **establish what kind of gap each one is**, by
asking the player to play a move and say why.

**Explicitly not its business:**

- *Choosing* what to probe about — that is the arbiter's, already done.
- *Deciding whether the player is right* — that is the engine's and the detectors', already done
  before the probe is shown.
- *Teaching, explaining, or commenting on the answer* — that is the explainer's, and doing it here
  would contaminate the assessment with the thing being assessed.

## 2 · Knowledge organisation

The prober holds almost no chess knowledge of its own, and this is deliberate.

| What it needs | Where it comes from |
|---|---|
| the position to show | the finding's own `Evidence` — positions from the player's games |
| the correct move | the analysis core's `best_move`, already cached |
| the correct *reason* | the detector's motif tag — the reason **is** `pin`, `fork`, `trappedPiece` |
| the vocabulary to match answers against | [[domain.puzzle-themes]], CC0 |

**The reason is machine-derived, never model-derived.** This is what keeps the agent inside ADR-0002
and clear of R-03. The model is not asked *"is this a good reason?"* — it is asked *"does what the
player wrote correspond to `pin`?"*, with the answer already known.

## 3 · Agent type

**Hybrid, and the split is the whole design.**

| Stage | Mechanism | Why |
|---|---|---|
| select positions | deterministic | evidence already sampled; no judgement needed |
| present, collect answer | plain I/O | |
| check the *move* | deterministic — string compare against `best_move` | a move is exact; a model would only add error |
| classify the *reason* | **language model** | free text cannot be pattern-matched without becoming a keyword hack |
| decide the `gap_type` | deterministic — the inference table | the conclusion must be reproducible from (move ✓/✗, reason ✓/✗) |

The model touches exactly one step, and its output is a **label from a closed set**, not prose. Both
the input to the diagnosis and the diagnosis itself remain deterministic; only the natural-language
understanding is delegated, because that is the one thing arithmetic genuinely cannot do.

This also means the agent degrades honestly: with no model available, the move check still runs, and
`gap_type` falls back to `unknown` rather than guessing.

## 4 · Knowledge maintenance

The tunable state is the **classification rubric** — what counts as the player having named the
reason. It is the direct analogue of S1's detector definitions, and history says it will be the
failure point.

Two guards before it may be used, mirroring S1 § 4:

1. a **fixed set of hand-labelled answers** — real phrasings, including near-misses ("his knight and
   rook are on the same line" *is* a pin named without the word) and false friends ("it forks the
   king" written under a position with no fork);
2. **inter-rater agreement** measured between the model and a human on that set, reported as a
   number, before any probe result is allowed to change a finding.

## 5 · Tools

`chesscoach.profile` (findings and their evidence), the evaluation cache (for `best_move` — no new
engine calls), `python-chess` for move parsing and legality, and **one free-tier LLM call per probe**.

## 6 · General instruction

The behavioural contract, to be enforced by tests:

1. **Never leading.** "Is there a fork here?" tests nothing and teaches the answer. The prompt is
   always "what would you play, and why?"
2. **Never reveal the answer during the probe.** Feedback belongs to the report, after assessment.
3. **The model classifies, it does not adjudicate.** It receives the player's text and the known
   reason, and returns a label. It is never asked what the best move is, never asked to evaluate a
   position, and never asked to generate chess advice.
4. **Answers are stored verbatim.** The player's words are the evidence; the classification is an
   interpretation of it and is stored separately, so a wrong classification is auditable and
   reversible.
5. **A probe may overturn a finding**, including removing it from the plan. Probes that can only
   confirm are theatre ([[architecture.interaction]] § 5).
6. **Bounded at 2–6 probes.** The player's attention is the scarcest resource in the system.
7. **Refusal is data.** "I don't know" is a valid, informative answer and must not be retried,
   coaxed, or treated as a failure to respond.

## 7 · Inputs

| Field | Type | From |
|---|---|---|
| shortlisted findings | `tuple[Priority, ...]` | `chesscoach.arbiter` |
| evidence positions | `tuple[Evidence, ...]` | each finding, already sampled |
| best move + motif tag | | evaluation cache + `chesscoach.tactics` |
| player answers | free text + a move | the session |

## 8 · Outputs

A `ProbeRecord` per probe — position, prompt, the player's move, their verbatim reason, the
classification, and the model and prompt version that produced it — plus a **revised `gap_type`** on
the finding it probed.

| Move | Reason | `gap_type` | Consequence |
|---|---|---|---|
| ✗ | — | `knowledge` | teach the pattern |
| ✓ | ✓ | `skill` or `process` | drill under time; the knowledge is there |
| ✓ | ✗ | `fragile` | rebuild the concept — a right move for the wrong reason is not knowledge |
| ✓ | refused | `unknown` | recorded, not guessed |

`determined_by` becomes `probed` rather than `inferred` — the first time anything in this system will
be able to say that.

**Schema consequence — smaller than this note first claimed.** `ProbeRecord`, `DeterminedBy.PROBED`
and `PlayerProfile.probes` **already existed**, designed in M3 against exactly this eventuality. The
prediction that they would need adding was wrong, and pleasantly so: it is the clearest evidence so
far that [[architecture.player-profile]] was designed for the whole vision rather than for what was
being built at the time.

What v3 → v4 actually needed: the `fragile` member, and four fields on `ProbeRecord`
(`expected_reason`, `move_correct`, `reason_matched`, `classifier`) so a verdict is auditable and a
model version is recorded.

Because every one of those is additive, **v3 profiles remain readable** and are upgraded on load —
`READABLE_SCHEMA_VERSIONS` in `profile/io.py`, which admits a version only when the step up from it
cannot change the meaning of existing data.

## 9 · Efficacy measure

Harder than for any previous agent, because there is no ground truth for "does this player know
pins". Four levels, strongest first:

1. **Does probing improve the progress check's power?** This is the real test and it links directly
   to **D8**. If `gap_type` is meaningful, then findings probed as `knowledge` should respond to
   study differently from those probed as `skill` — and the progress check already measures response.
   A prober that changes nothing downstream has not earned its cost, however plausible its labels.
2. **Inter-rater agreement** on the hand-labelled answer set (§ 4), model against human. Reported as
   a number, and below an agreed floor the agent does not ship.
3. **Overturn rate.** A prober that never contradicts the finding it probes is not measuring
   anything; one that contradicts most of them means the detectors are wrong, not the players. Both
   extremes are alarms, and the rate is worth watching from the first session.
4. **Self-consistency.** The same answer classified twice should get the same label. Free to measure,
   and a cheap early warning that the rubric is underspecified.

## 10 · Cost profile

The first component in the project with a **non-zero marginal cost**, so C1 and C4 apply directly.

- 2–6 model calls per session, one per probe, at the **outer** loop — never inside analysis.
- Input is a position description, a known reason, and a short player answer: small prompts.
- Free-tier or local model. A local small model is preferred and is plausibly sufficient, because
  the task is short-text classification against a supplied label, not chess reasoning.
- **Must be measured, not assumed** — this is the first time D9's cost dimension has anything real to
  measure, and the session total is currently unknown rather than zero.

## Known limitations, recorded before building

- **The probe is not the game.** A player solving a position untimed, knowing they are being tested,
  on a board presented to them, is in a different situation from the one where they erred. That is
  the point — it is what separates knowledge from execution — but it means a `skill` verdict is
  really "the knowledge is present under favourable conditions".
- **Two to six probes is a tiny sample.** One probe per finding cannot establish that a pattern is
  known in general, only that it was known here. The `gap_type` is a hypothesis with evidence, not a
  fact, and must be labelled as such wherever it is shown.
- **Self-report is fallible.** Players reconstruct reasons after choosing moves. The verbatim record
  is what protects against over-reading this; the classification does not.
- **The rubric is culturally and linguistically narrow** as first written — English, and the
  vocabulary of someone who has read chess material. A player who understands pins perfectly and has
  never heard the word must not be scored as ignorant, which is exactly what a keyword matcher would
  do and the main reason a model is used at all.
- **A model in the loop is a reproducibility cost.** Prompt and model version are recorded per probe
  so a profile can be re-derived, but an updated model can change a stored diagnosis. No previous
  component had this problem.
