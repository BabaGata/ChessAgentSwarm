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

```
chesscoach/
  ingest/      PGN parsing, corpus identity
  analysis/    engine, evaluation cache, error labels, observations
  profile/     the player profile — models and persistence
  cli.py       the pipeline entry point
experiments/   e01–e03: the measurements that shaped the design
tests/         74 tests
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

```bash
python -m pytest                              # 74 tests
python -m pytest --cov=chesscoach             # 85% coverage
```

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
