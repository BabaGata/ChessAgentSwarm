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
Eight of the eleven planned section agents are built (S1–S8), each screened
against real players before it was written. Of the other three, S10 exists as a
**refusal** rather than a gap: a player's style tendency is measured, but *"this
style suits you"* is not supported by the evidence, so it asserts nothing (E14).
S9 (planning and prophylaxis) and S11 (practical and psychological play) are not
built — scheduled last on purpose, because they are where a coach is most likely
to produce fluent nonsense.

The **evaluation harness** also exists, built deliberately *before* the first agent — one written
afterwards is one shaped by the agents.

```
chesscoach/
  ingest/         Lichess fetching, player discovery, PGN parsing, corpus identity
  analysis/       engine, evaluation cache, error labels, observations, parallel prefetch
  profile/        the player profile — models and persistence
  sections/       the diagnostic agents — tactical gaps, decision process,
                  endgame technique, opening outcomes, pawn structure,
                  squares and files, material safety, attack and defence
  evaluation/     split-half replication, planted weaknesses, ground-truth scoring
  tactics.py      nine motif detectors, named after the Lichess puzzle themes
  material.py     why material was lost, as distinct from what won it
  punishment.py   which replies count as punishing a mistake
  precision.py    how often a detector is right, from marks a person made
  separation.py   which claims may compare a player with peers, and which may not
  development.py  opening development, against a strong-player expectation
  strength.py     how strong the play looks — ±103 points from rapid, ±129 from
                  blitz, measured on strangers; rating never shown to it
  style.py        how they play, as distinct from how well — and no verdict on it
  context.py      the four questions games cannot answer; study time sizes the plan
  humaninput.py   cleaning what a person typed, before anything reads it
  confidence.py   when the swarm may assert a weakness
  peers.py        the rating-band reference population, leave-one-out
  orchestrator.py runs the agents, writes findings to the profile
  arbiter.py      picks the one or two things worth working on
  planner.py      turns those into steps with falsifiable targets
  progress.py     goes back and checks whether the targets were met
  prober.py       asks the player, and tells a knowledge gap from a skill gap
  classifiers.py  the one place a language model acts — local, and ablated
  explainer.py    the report a person reads. Templates, not generation
  narrator.py     a local model's summary above the report, checked against its facts
  followup.py     questions after the report: from the report, else the books, else no
  exercise.py     practice positions from the player's own games (the prober's move check)
  after_report.py the session around the report, testable without a terminal
  session.py      one session end to end, and the probe gate
  pipeline.py     engine/cache session and provenance
  opening_*.py    the opening brief — plans quoted from sources, a three-agent
                  local-model swarm (Scout, Assessor, Compiler), and a run store
  knowledge*.py   what the swarm knows about each thing it detects: what it is,
                  why it matters, how to practise it
  conversation.py the conversation behind `talk`: ask, analyse, coach one thing
  cli.py          coach · talk · analyse · probe · report · check-progress ·
                  fetch-corpus · build-peer-reference · build-graph · ask ·
                  make-eval-set · check-eval-set · score-agent
experiments/      e01–e92: the measurements that shaped the design, including
                  the negative ones
tests/            2,220 tests
```

The loop runs end to end in **one command**: fetch → analyse → diagnose → prioritise → ask → plan
→ report, with `check-progress` returning to it later. Until recently every stage existed and none of
them were joined up, which made this a toolkit rather than a system.

The one thing it may not do is let a probe *change* a diagnosis. The classifier agrees with its
labels at kappa 0.74, but those labels were written and applied by the author, so the gate stays
shut until answers exist from someone else.

## Running it

### What you need

| | |
|---|---|
| **Python 3.12** | `pip install -e ".[dev]"` |
| **Stockfish** | any recent build, on `PATH` or passed with `--engine` |
| *(optional)* **Ollama** | only for `--probe`, `ask` and the knowledge swarm. **The report itself needs no model.** |
| *(optional)* **Docker** | only for `ask`, which reads a Neo4j graph |

Everything else is in the repository: the peer reference, the opening book and its
norms, the shelf and the knowledge base — about 7 MB, all public-domain or
generated here. **There is nothing to download and nothing to build first.**

### One player, one report

```bash
pip install -e ".[dev]"

python -m chesscoach.cli coach \
    --player <lichess-username> \
    --engine stockfish \
    --peers data/raw/out/peers-e84.json \
    --band 1400-1800 --time-control blitz \
    --cache eval-cache.db \
    --out profile.json
```

That is the whole thing. It fetches the player's rated games, analyses them,
diagnoses, picks one or two priorities, plans, and prints a report. Above the
report a local model (`qwen2.5:3b` through Ollama) writes a short summary, checked
against the measurements; after it you can ask questions, and at the end try the
positions from your own games where the engine found a better move. Each part is
optional: `--no-summary`, `--no-questions-after`, `--no-practice`. Without Ollama
the session runs as before and says why there is no summary.

**Already have the games?** Pass `--pgn games.pgn` and it will not fetch.
**Do not want the four questions?** Add `--no-questions`.

`--band` should be the player's actual rating band — `1200-1600`, `1400-1800` or
`1600-2000`, the three the shipped reference covers. Comparing someone against a
band they are not in is refused rather than silently allowed, because *"more often
than players at your level"* would then name the wrong level.

### Reading a report again

Analysis is the slow part and it is cached. To re-render without re-analysing:

```bash
python -m chesscoach.cli report --profile profile.json
```

`docs/samples/` holds a finished profile, so the report can be read before
anything is analysed at all.

### How long it takes

**About 90 seconds for 50 games** the engine has never seen, at depth 15 on an
ordinary laptop; **1.5 seconds for 60 games** on a warm cache. Zero cash.

Add `--probe --model llama3.1:8b-instruct-q6_K` to be asked about your own
positions first, which is what turns *"you miss pins"* into *"you know what a pin
is and did not see this one"*.

Unless `--no-questions` is passed, it first asks four questions games cannot
answer. Say you have an hour a week and the plan comes back with one thing in it,
not two. `talk` does the same as a conversation, and coaches one thing.

Needs a local Stockfish binary and a peer reference. Everything else is free and
offline.

### Building the peer reference from nothing

`--peers` is not optional in any meaningful sense: without a population, nothing
can be called unusual and the swarm stays silent. Building one takes two
commands, run once per speed.

```bash
# 1. Discover players in the band and fetch their games, one speed at a time.
python -m chesscoach.cli fetch-corpus --out corpus/rapid --speed rapid --players 80
python -m chesscoach.cli fetch-corpus --out corpus/blitz --speed blitz --players 80

# 2. Turn each directory into a stratum, merging the second into the first.
python -m chesscoach.cli build-peer-reference \
    --pgn-dir corpus/rapid --time-control rapid \
    --engine /path/to/stockfish --out peers.json --cache eval-cache.db

python -m chesscoach.cli build-peer-reference \
    --pgn-dir corpus/blitz --time-control blitz --merge-with peers.json \
    --engine /path/to/stockfish --out peers.json --cache eval-cache.db
```

**One speed per directory, always.** `--time-control` labels a whole directory
rather than reading each game's own control, and the failure when that label is
wrong is silent: a blitz-heavy player meets a reference with no blitz stratum,
every lookup returns nothing, and the peer comparison and band notes simply drop
out of a report that still renders and still looks complete. `build-peer-reference`
now refuses a directory that is less than 90% the speed it is being filed under —
a guard that exists because this chain was run for real and produced exactly that
report before anyone noticed.

**What reproduces is the procedure, not the sample.** Discovery reads arena
standings, and today's arenas are not the ones this project's reference was built
from. A reader gets a different 80-odd players from the same band; the population
*rates* should agree, the usernames will not. Run at 4 players the long-think rate
came out at 18.8% against the 17.8% measured over 38 — which is the level of
agreement to expect, and the reason rates rather than players are what anything
here is compared against.

Then generating an evaluation set whose weakness is known by construction:

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
python -m pytest                              # 2,177 tests
python -m pytest --cov=chesscoach             # 86% coverage
```

## What it currently says about real players

On a 24-game history the swarm advises **79%** of players, up from 50% before the
evidence from a player's other speeds was pooled into the diagnosis while the
baseline stayed per-speed (E19, E21). Every claim is peer-compared and traceable
to sampled positions from the player's own games.

The figure that matters more is the one measured on **thirty players the system
was never built on**: 86% of them received a diagnosis, against 84% for the
players it was built from — a difference of nothing (p = 0.46). The same test
found the blitz *rating* estimate failing on strangers, which is recorded with
equal prominence a few sections down.

The route there is the project in miniature. Players initially showed elevated error rates after long
thinks at 2.10–2.85× their *own* baseline — all correct measurements, none of them diagnoses, because
a long think happens *where the position is hard* and hard positions produce errors. Measured against
a population of peers instead, most of that evaporates: the population itself errs 17.8% of the time
in exactly those positions.

Two further things fell out of widening that population from 7 players to 38 (it
now stands at 84):

- **Population rates converge fast.** Seven players estimated 17.7% against 3,675 moves' worth of 38.
- **Borderline verdicts do not.** One player flipped from a top-tier finding to silence on a 0.4
  percentage point change in the reference. Tiering now requires a claim to clear the population by a
  *margin*, not merely to touch it.

The arbiter then picks **one or two** of those to work on — because a coach who lists nine weaknesses
has given you none. It picks them by **what they cost**: every claim whose instances are mistakes
carries the win probability given away on exactly those moves, so the ranking is *"this is costing
you four points a game"* rather than *"you do this 1.8× more than your peers"*. Claims whose
instances are choices rather than mistakes — conceding a structure, letting a rook reach the seventh
— have no cost to state and say so instead of guessing one.

The planner then turns each into a step with a check attached:

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
