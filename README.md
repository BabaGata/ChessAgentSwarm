# Chess Agent Swarm

An adaptive agent swarm that coaches chess players — diploma thesis project.

The system analyses a player's own games, works out what is actually costing them points, and turns
that into a learning path with steps, priorities and **predicted signs of progress** that it later
checks. It runs on one laptop for approximately no money.

## The vault is the authority

`docs/notes/` is a Dendron vault and it is the project's control room, not documentation written
afterwards. Start there:

| Note | Contents |
|---|---|
| `vision` | the goal — capabilities V1–V9, constraints C1–C7, success criteria |
| `mission` | the seven iterative steps and which one is active |
| `state` | what exists, the distance-to-vision scorecard, what is next |
| `architecture` | the system design and its children |
| `open-questions` | every unresolved question, its owner, and how it gets resolved |
| `experiments` | measured evidence, including the results that came out negative |
| `learning.lessons` | what was learned, and what changed because of it |

## What exists today

The full loop: ingest → deterministic analysis → findings → priorities → plan → progress check.
Two of the eleven planned section agents are built.

The **evaluation harness** also exists, built deliberately *before* the first agent — one written
afterwards is one shaped by the agents.

```
chesscoach/
  ingest/         PGN parsing, corpus identity
  analysis/       engine, evaluation cache, error labels, observations, parallel prefetch
  profile/        the player profile — models and persistence
  sections/       the diagnostic agents — S1 tactical gaps, S2 decision process
  evaluation/     split-half replication, planted weaknesses, ground-truth scoring
  tactics.py      eight motif detectors, precision-gated by E04
  confidence.py   when the swarm may assert a weakness
  peers.py        the rating-band reference population, leave-one-out
  orchestrator.py runs the agents, writes findings to the profile
  arbiter.py      picks the one or two things worth working on
  planner.py      turns those into steps with falsifiable targets
  progress.py     goes back and checks whether the targets were met
  prober.py       asks the player, and tells a knowledge gap from a skill gap
  classifiers.py  the one place a language model acts — local, and ablated
  explainer.py    the report a person reads. Templates, not generation
  session.py      one session end to end, and the probe gate
  pipeline.py     engine/cache session and provenance
  cli.py          analyse · make-eval-set · check-eval-set · score-agent ·
                  build-peer-reference · check-progress · probe · report
experiments/      e01–e07: the measurements that shaped the design, including
                  the negative ones
tests/            440 tests
```

The loop now runs end to end: **analyse → diagnose → prioritise → ask → plan → report → check.**

The one thing it may not do is let a probe *change* a diagnosis. The classifier agrees with its
labels at kappa 0.74, but those labels were written and applied by the author, so the gate stays
shut until answers exist from someone else.

## Running it

```bash
pip install -e ".[dev]"

python -m chesscoach.cli analyse \
    --pgn games/ --player alice \
    --engine /path/to/stockfish \
    --out alice-profile.json \
    --cache eval-cache.db
```

Needs a local Stockfish binary. Everything else is free and offline.

Generating an evaluation set whose weakness is known by construction:

```bash
python -m chesscoach.cli make-eval-set \
    --engine /path/to/stockfish --out evalset/ \
    --kind time_pressure --severity 0.8 --background 0.15 --games 12

python -m chesscoach.cli check-eval-set \
    --eval-set evalset/ --engine /path/to/stockfish
```

The second command verifies the planted flaw is actually visible to the analysis core before
anything is scored against it. A fixture nobody has checked is not a test.

```bash
python -m pytest                              # 440 tests
python -m pytest --cov=chesscoach             # 82% coverage
```

## What it currently says about real players

Across **38 real players** in the target band, the two existing agents assert findings for **9** of
them across **6 distinct kinds of weakness**, stay silent for 25, and decline on 4 for want of data.
One player carries a three-part profile — misses pins, concedes trapped pieces, errs after long
thinks — each claim peer-compared and traceable to sampled positions from their own games.

The route there is the project in miniature. Players initially showed elevated error rates after long
thinks at 2.10–2.85× their *own* baseline — all correct measurements, none of them diagnoses, because
a long think happens *where the position is hard* and hard positions produce errors. Measured against
a population of peers instead, most of that evaporates: the population itself errs 17.8% of the time
in exactly those positions.

Two further things fell out of widening that population from 7 players to 38:

- **Population rates converge fast.** Seven players estimated 17.7% against 3,675 moves' worth of 38.
- **Borderline verdicts do not.** One player flipped from a top-tier finding to silence on a 0.4
  percentage point change in the reference. Tiering now requires a claim to clear the population by a
  *margin*, not merely to touch it.

The arbiter then picks **one or two** of those to work on — because a coach who lists nine weaknesses
has given you none — and the planner turns each into a step with a check attached:

```
1. missed_motif (pin)
     do    Drill `pin` puzzles, and solve to be right rather than fast — review every one you get wrong.
     why   seen in 8 of 24 games, at 30.3% against 11.6% for peers at your level
     check pin missed when available below 14.6% over the next 20 games (measured 30.3%,
           ~25.2% if nothing changes; 15%–23% of players reach this target without
           changing anything)
```

That last line is the point, and every number in it is load-bearing. It is a prediction the system
can be **proven wrong about**, computed from the same measurement that produced the finding rather
than written by a language model. The target (14.6%) is set below the **no-change estimate** (25.2%),
not below the measured rate (30.3%) — because the gap between those two is regression to the mean,
and a target above it would be met by arithmetic. The 15% is the measured rate at which untreated
players clear the bar anyway.

Check points are derived from how often the chance actually arises, so a rarer motif gets more games.
Time estimates in days are deliberately absent: how long an intervention takes to show is an open
question, and inventing "2–3 weeks" would be exactly the folklore this project refuses.

And then it goes back to find out. Run against a player's *later* games, the first prediction the
system ever checked came out like this:

```
progress  (0 met, 1 not met)
  [NOT MET] S2.long_think_error.long_think.own
       predicted  below 21.9% over the next 20 games (currently 26.4%)
       observed   24.4% (was 26.4%, target 21.9%)
```

Recorded, not hidden — a plan carries how it turned out.

## The most important result so far is a negative one

Running that same check across **32 players who were never told anything**, **92% of the targets
were met anyway**. Mean improvement with no coaching at all: **+11.2 points**, against targets asking
for +5.5.

That is regression to the mean, and it is guaranteed by the selection: a weakness becomes a finding
*because* its rate was extreme, and re-measuring an extreme value returns a lower one whether or not
anything was done. **Any** system that measures a weakness, prescribes for it and re-measures will
appear to work — which is very likely what a coaching tool reporting "your weakness improved" is
reporting, since none of the comparable projects checks against a control.

Fixing that took three attempts, and the two failures are the interesting part:

| Target rule | Met by doing nothing |
|---|---|
| halve the gap from the measured rate | **92%** |
| halve the gap from a shrunk estimate *(the principled fix)* | 83% |
| calibrated against the measured no-change distribution | 8% *(in-sample)* |
| the same rule, **cross-validated** | **38%** |
| refitted on 6× the data, cross-validated at 2 and 5 folds | **15–23%** *(depends on sample depth)* |

Empirical-Bayes shrinkage barely helped, because it corrects for sampling noise and the regression is
much larger than noise. Calibrating against the measured control fixed that. Then cross-validation
showed the calibration was itself optimistic by about five times, with the two folds disagreeing 0/6
against 5/7 — so the number was withdrawn entirely, because 13 predictions cannot support one.

**Then the sample got bigger, and the finding partly dissolved.** Re-run across **84 players with
~150 games each** — 57 predictions instead of 13 — drift with no coaching fell from +11.2 points to
**+4.8**, and rates no longer halve on their own (median 0.52 → **0.87**).

The regression was mostly an artefact of thin samples. A rate measured over 30 games is far likelier
to be extreme by luck than one measured over 78, so **the +11.2 was never a fact about chess players;
it was a fact about measuring them briefly.** The constant fitted to it was not conservative but
unmeetable — 1 of 52 untreated predictions met it, and a target nothing reaches cannot detect
coaching either.

Refitted, the folds now agree (spread 0.011, and 2-fold and 5-fold match), so a false-positive rate
is stated again — as a **range**, because a controlled follow-up showed it depends on how much data
the finding rests on. Capping the measurement period at 30/45/60/78 games while holding the outcome
period whole gives **23 / 22 / 18 / 15%** met by drift alone. The output says 15–23% rather than
picking the flattering end.

That follow-up also corrected the previous paragraph's own story. The 0.34 → 0.58 move was *mostly
replacing a guess with a fit*, not a depth effect: 0.34 was never fitted at any depth, and the
properly fitted value on 30-game measurements is 0.488. Depth is real but modest. The first version
compared two runs differing in both sample depth and player set, and credited the difference entirely
to depth — the mechanism was persuasive enough to stop the confound being looked for.

What is still *not* claimed is the other half — whether a genuinely coached player can meet the
target. No coached cohort exists, so the test's power is unknown. See
`docs/notes/experiments.e05-natural-drift.md`.

**Something now asks the player.** A probe puts one of their own positions back in front of them,
untimed, and asks what they would play and why — which is the only way to tell *doesn't know the
pattern* from *knew it and didn't see it*. The move is checked deterministically; a local 8B model
does one job, deciding whether the player's sentence names the reason the detectors already found.
It never suggests a move and is never asked to evaluate a position.

Running it for real immediately found two defects a green test suite had not: a byte-order mark on
pasted input turned a correct move into a knowledge gap, and a stopped model recorded as *the player
was unclear* rather than *nobody asked*. Both lived exactly where real input arrives.

See `docs/notes/architecture.peer-reference.md` and `docs/notes/learning.lessons.md`.

## Design in one paragraph

**Compute first, speak last.** Diagnosis is deterministic — engine analysis, error labelling, motif
and feature detection, clock behaviour, all measured, all traceable to specific positions. Language
models are used only to conduct the assessment dialogue, plan and explain, and they read a
structured profile rather than raw games. This is what keeps the cost at roughly zero and every
claim attributable. Agents never talk to each other; they read and write a shared player profile, so
each can be evaluated, ablated and improved on its own.

## Some things measured along the way

- 50 games analyse in **89 seconds** at depth 15 on an ordinary laptop, for nothing.
- More engine threads made fixed-depth analysis **slower** — one thread per engine, many engines.
- Analysis depth changes the **diagnosis**, not just the evaluation, so single-move claims are not
  stable facts and only aggregates survive.
- Isolated pawns appear in **96 %** of games, which is why detecting a feature is not the same as
  having something to say about it.
- A striking result (backward pawns doubling endgame error rates) **reversed on held-out players**.
  It is written up as an artefact, in `experiments.e03-relevance-weighting`.

## Licence and data

Public games only, public usernames only. Stockfish is GPL-3.0 and is used as an external binary;
the Lichess puzzle and opening datasets are CC0.
