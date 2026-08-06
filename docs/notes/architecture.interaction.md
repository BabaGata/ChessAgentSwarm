---
id: cas-arch-interaction
title: Interaction & Probes
desc: 'The player-facing protocol: session flow, the probe mechanism for active assessment, and what is asked rather than inferred.'
updated: 1785256400000
created: 1785256400000
---

# Interaction & Probes

Resolves **V9** ([[decisions.0003-add-v9-dialogue-and-active-assessment]]) and narrows **B4**.

M1 established the reason this exists: the same observable error — a hung knight — has at least four
causes, and **games alone cannot distinguish them** (L-002). Interaction is a diagnostic instrument,
not a presentation layer.

## Session flow

```
1  CONNECT      username or PGN upload
2  CONTEXT      3–4 questions games cannot answer
3  ANALYSE      deterministic, ~90 s for 50 games — nothing is asked meanwhile
4  SHORTLIST    arbiter picks 1–2 candidate priorities
5  PROBE        2–6 positions, targeted at the shortlist
6  PLAN         ordered steps, each with a progress sign
7  REPORT       written artefact the player keeps
8  RETURN       later sessions re-analyse and check the predicted signs
```

**Both report and conversation** (B4), with the split settled: the *report* is the durable artefact,
the *conversation* is how assessment happens. The report is what the player returns to; the dialogue
is what makes the report about them.

> **Built as `cli coach`** (2026-08-06). Steps 1 and 3–7 run from one command — a username in, a
> report out, 7.6 s for 60 games on a warm cache. Step 5 runs with `--probe`, and **its results now
> reach the diagnosis**: the standalone `probe` command still records without applying (D10's gate),
> but a coaching session applies them and the report states the provenance instead, so V9 is part of
> the system rather than a demonstration beside it.
>
> **Step 2, the context questions, is still unbuilt** — nothing asks what the player wants or how
> much time they have, so the plan cannot yet be sized to them.

## Step 2 — Context questions

Four questions, not a form. They cover what no amount of analysis can reveal
([[domain.signals]] § 3): what the player wants, how much time they actually have per week, what
they have already tried, and whether they play anywhere the games are not visible.

The weekly-time answer is load-bearing: a plan that assumes six hours for a player with two is a
plan that fails and teaches the player the system does not know them.

> **Built** as `chesscoach/context.py`, asked by `cli coach` **before** the engine runs — analysis
> takes minutes, and someone who has just answered four questions waits more willingly than someone
> watching a progress bar. Every question is skippable.
>
> **Only the time answer changes a decision**, and that is deliberate. Under
> `FOCUSED_EFFORT_HOURS` the plan carries **one** priority instead of two. The threshold is a stated
> convention rather than a measurement — nothing in this project links study hours to outcomes — and
> it errs toward fewer, which is the direction § 4 of [[domain.coaching]] argues for anyway.
>
> **The other three change what the report can honestly say**, which is a smaller job and still worth
> doing. Goals and what-was-already-tried are quoted back verbatim, never interpreted: reading them
> would need a model, and a model that misread a goal would quietly plan for the wrong person.
> **`plays_elsewhere` is the one that earns its place** — it turns a blind spot the report had
> silently inherited into one it states: *"You said you also play over the board at your club. None
> of those games are in this."*

## Step 5 — Probes

The core mechanism. A probe presents a position and asks for a **move and the reason for it**.

| Probe kind | Asks | Separates |
|---|---|---|
| `move_and_reason` | best move + why | knowledge from luck — a right move for the wrong reason is not knowledge |
| `plan` | "what would you play for here?" — no single best move | whether a structure is understood, not whether a tactic is spotted |
| `recall` | "what is the drawing method here?" | knowledge of a named technique (Philidor, opposition) |

### The inference that justifies the cost

Probes are run **untimed**, on positions drawn from the player's own shortlisted weakness:

| In games | Untimed probe | Conclusion | Remedy |
|---|---|---|---|
| missed | fails | **knowledge gap** | teach the pattern |
| missed | solves it | **skill or process gap** | drill under time; fix the checking routine |
| missed | solves it, wrong reason | **fragile knowledge** | rebuild the concept |
| found | fails on probe | small sample, or luck | lower confidence, do not coach |

That table is the whole argument for V9. Without it, every one of those rows gets the same generic
"study forks" advice — which is the coaching anti-pattern the swarm exists to beat.

### Rules

- **Bounded:** 2–6 probes per session. Probing is the player's time and attention, the scarcest
  resource in the system.
- **Drawn from their own games** where possible — a position they actually reached is more
  convincing and more relevant than a textbook one.
- **Never leading.** "Is there a fork here?" tests nothing. "What would you play, and why?" does.
- **Answers are recorded verbatim** in the probe record. The player's own words are evidence; the
  language layer's paraphrase is not.
- **A probe may overturn a finding.** If the player demonstrates the knowledge, the finding's
  `gap_type` changes and it may drop out of the shortlist entirely. Probes that can only confirm are
  theatre.

## Step 7 — Report constraints

The explainer may state only what the profile contains, with its evidence
([[architecture.orchestration]]). Concretely, checked mechanically by [[evaluation]]'s D-family:

- one or two priorities, never a list of nine (D3);
- every claim cites specific games (D4);
- `insufficient_data` is reported, not hidden — "we could not assess your endgames, only four of
  your games reached one" is honest and useful; silence implies competence;
- no claim whose peer lift is ≈ 1 (D2) — true of everyone is not a diagnosis;
- plan steps state their progress sign in the player's terms, not as a statistic.

## Step 8 — Return sessions

What makes this a coach rather than a report generator, and what no prior-art project does:

1. re-analyse only the new games (position cache makes this cheap);
2. **check the predicted progress signs** — did the thing we said would happen, happen?
3. if a sign appeared, the step is marked addressed and the finding's history records it;
4. **if it did not, that is information about the plan, not about the player.** Re-plan, and record
   that the prediction failed — a system that quietly drops its failed predictions is unfalsifiable.

Point 4 is the honesty mechanism for V6/V7. It is also the only evidence the project will ever
generate about whether its coaching actually works.

**Built** as `chesscoach/progress.py` and the `check-progress` command. It re-measures the same
quantity over the games played **since** the plan — a rate over the whole corpus would be diluted by
the very games that produced the diagnosis — and records the verdict in the plan itself, so a plan
carries how it turned out.

Two verdicts exist for *we cannot say*, kept apart from *no*: `too_early` (fewer games than the plan
asked for, so judging now would claim a success it has not earned) and `not_measurable` (the chance
never arose). Collapsing either into a failure would make the system look more decisive and be less
honest.

Making it work required a schema change worth recording: `progress_sign` was written for a person to
read, and a machine cannot test prose. The falsifiability the plan claimed was only half real until
`PlanStep` carried `target_rate` — the number the sentence describes.

## Tone

Not a design flourish — a diagnosis a player rejects is a diagnosis that does nothing. Findings are
stated with their evidence and their limits, the player is told what was measured and what was not,
and nothing is claimed about their potential, talent, or ceiling. The system reports what their
games show and what they said.
