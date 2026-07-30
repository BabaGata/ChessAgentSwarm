---
id: cas-mission-m5
title: 'M5 — Assess S2 inside the swarm'
desc: 'Does information flow through? Does the result serve the goal? What must change course?'
updated: 1785257600000
created: 1785257400000
---

# M5 — Assess S2 inside the swarm

**Status:** done · **Parent:** [[mission]] · **Assesses:** [[capacity.agents.s2-decision-process]]

M5 asks whether the agent built in M4 earns its place and whether the project is still pointed at
[[vision]]. It is separate from M4 so that *"it works"* and *"it helps"* are answered by different
questions — and this cycle they got different answers.

## 1 · Does information flow through properly?

**It did not.** S2 existed, was tested, and was scored — and was **not connected to the pipeline**.
The `analyse` command still wrote profiles with zero findings. The agent and the artefact it was
designed to write had never met. Every unit test passed; nothing was joined up.

Built in response, per [[architecture.orchestration]]: `chesscoach/orchestrator.py`, with two
behaviours the architecture specified and nothing had implemented —

- **failure isolation:** an agent that raises is recorded as failed and the run continues; its
  silence is never reported as "found nothing", because a crash reading as a clean bill of health is
  the worst available outcome;
- **section-scoped replacement:** re-running updates only sections that actually reported, so a
  crashed agent cannot quietly delete a previous diagnosis and tell the player a weakness has gone.

Verified end to end: `analyse` now produces a profile containing the finding, with a 100 % cache hit
rate on re-run.

### A second flow problem, found by using it

The production analyser is **sequential**. E01 measured that per-position parallelism is what makes
whole-corpus analysis fast, and the seam exists, but the shipped path analyses one position at a
time — roughly an order of magnitude off the measured optimum. Invisible against warm caches and
small planted sets; obvious the moment seven real players were queued at depth 15. Recorded, not
urgent at this scale.

## 2 · Does the end result serve the goal?

S2 was run on **135 real games across seven players** in the target band — the first time anything in
this project met data that was not synthetic. Two defects surfaced, both real.

### Defect 1 — the data gate was implemented per condition, not per section

[[architecture.confidence]] says a section reports nothing below 10 *games with data for the
section*. S2 had implemented that per **condition**: a condition occurring in only 12 of 30 games
counted as having 12 games of data and could therefore never reach `focus`, however badly the player
handled it. A rare but severe weakness was permanently unsayable.

Fixed: the gate counts games in which the player made any timed, competitive move after the opening.
How often a condition *arises* is already carried by `distinct_games` and the rate.

### Defect 2 — the finding that appeared for almost everybody

With the gate corrected, **four of six eligible players** showed `long_think_error`, at 2.10×, 2.22×,
2.31× and 2.85×. That uniformity is the finding. A weakness four players out of six share, at
similar magnitude, is not a weakness — it is **a property of chess**.

The mechanism is plain once seen: a long think happens *because* the position is hard, and hard
positions produce errors. The condition is selected by the very thing that causes the outcome.
Comparing against the player's own baseline cannot separate "you are bad after long thinks" from
"long thinks happen in bad positions"; only a rating-peer population can.

This is risk **R-14** — true, specific, evidence-backed and useless — materialising on real data, and
it is exactly what evaluation metric **D1 (inter-player divergence)** exists to catch. It was caught
by eye here because D1 is not built yet.

Fixed: conditions are now marked `selection_confounded`, measured but **withheld** with an
explanatory note until a peer baseline exists.

### What S2 says now

| | |
|---|---|
| 7 real players | **nothing to report** (6), **insufficient data** (1, at 8 games) |
| planted control | **found the planted weakness**, 37.7 % vs 6.8 %, 5.54×, 0 spurious |

The agent keeps full sensitivity to a constructed weakness while declining to speak about real
players. That is uncomfortable and it is correct: on this evidence there is nothing it can honestly
say. Every prior-art project in [[domain.prior-art]] would have produced a confident paragraph here.

## 3 · Did this move us toward the vision?

Yes at M4 — the scorecard moved 4 → 9 of 60, the first movement, because something was measured.
M5 adds no scorecard movement and instead establishes the **ceiling**: without a peer population, S2
can only assert conditions exogenous enough for a self-baseline to mean something. That is a small
subset of what it measures.

## 4 · Is a section missing?

Not a section — a **shared capability**. The rating-peer reference population is not coaching
knowledge and does not belong to any section; it belongs beside the profile and the confidence
policy, and every section will need it.

## 5 · What changes course?

**The peer reference corpus moves from "nice to have" to blocking.** Three independent needs now
converge on it:

1. **C6** — its only remaining route to relevance weighting, after E03 ruled out error co-occurrence;
2. **[[evaluation]] D2** — base-rate specificity, the metric that catches true-but-useless output;
3. **S2 itself** — `selection_confounded` conditions cannot be asserted without it.

When three separate lines of work require the same artefact, that artefact is the next thing to
build. [[state]] priorities reordered accordingly.

Also promoted: **implement D1 (inter-player divergence)**. It would have caught defect 2
automatically rather than by eye, and it is cheap — compare the findings produced across players and
flag anything nearly universal.

## Definition of done

- [x] Information flow verified end to end, with the gap it exposed fixed.
- [x] S2 run on real players, not only synthetic ones.
- [x] Defects found by that run fixed, with tests.
- [x] Planted control re-run to confirm sensitivity was not lost while suppressing noise.
- [x] Course correction recorded and [[state]] reprioritised.

## Working log

| Date | Activity | Alignment check | Outcome |
|---|---|---|---|
| 2026-07-28 | Wired S2 into the pipeline; ran it on 135 real games; fixed two defects it exposed | Serves V4/V8 by making the agent's output reach the profile at all, and serves C5 by refusing claims it cannot support. The uncomfortable result — silence on every real player — was accepted rather than tuned away, because tuning to produce output is precisely the anti-pattern R-12 describes | Orchestrator built; 2 defects fixed; peer corpus promoted to blocking; 158 tests |
