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

The **skeleton**: ingest → deterministic analysis core → player profile. Section agents (the parts
that produce findings) arrive in mission step M4.

The **evaluation harness** also exists, built deliberately *before* the first agent — one written
afterwards is one shaped by the agents.

```
chesscoach/
  ingest/         PGN parsing, corpus identity
  analysis/       engine, evaluation cache, error labels, observations
  profile/        the player profile — models and persistence
  sections/       the diagnostic agents (S2 so far)
  evaluation/     split-half replication, planted weaknesses, ground-truth scoring
  confidence.py   when the swarm may assert a weakness
  orchestrator.py runs the agents, writes findings to the profile
  pipeline.py     engine/cache session and provenance
  cli.py          analyse · make-eval-set · check-eval-set · score-agent
experiments/      e01–e03: the measurements that shaped the design
tests/            166 tests
```

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
python -m pytest                              # 166 tests
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
     do    Drill `pin` puzzles, and solve to be right rather than fast.
     why   seen in 8 of 24 games, at 30.3% against 11.6% for peers at your level
     check pin missed when available below 21.0% over the next 30 games (currently 30.3%)
```

That last line is the point. It is a prediction the system can be **proven wrong about**, computed
from the same measurement that produced the finding rather than written by a language model. Check
points are derived from how often the chance actually arises — 30 games for pins, 20 for something
commoner. Time estimates in days are deliberately absent: how long an intervention takes to show is
an open question, and inventing "2–3 weeks" would be exactly the folklore this project refuses.

And then it goes back to find out. Run against a player's *later* games, the first prediction the
system ever checked came out like this:

```
progress  (0 met, 1 not met)
  [NOT MET] S2.long_think_error.long_think.own
       predicted  below 21.9% over the next 20 games (currently 26.4%)
       observed   24.4% (was 26.4%, target 21.9%)
```

Recorded, not hidden — a plan carries how it turned out. That run was a retrospective split with no
intervention, which makes it a **control**: it says untreated drift is about two points, against a
target asking for four and a half. A target that drift alone would satisfy is not a prediction.

The honest limitation: **nothing asks the player anything.** Probes, and phrasing fit for a person
to read, do not exist.

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
