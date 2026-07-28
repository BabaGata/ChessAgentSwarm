# E03 — Relevance weighting

Answers open question **C6**: how is a detected feature weighted for relevance?

E02 established that positional features are detectable, and that detection is not the hard part —
isolated pawns occur in 96 % of games, so *presence* is not a coaching signal (lesson L-007). This
experiment tests the first candidate route: **co-occurrence with the player's own errors**.

**Findings and consequences are in the vault:** `docs/notes/experiments.e03-relevance-weighting.md`.

## The measure

    lift(F) = P(error | F present) / P(error | F absent)

A feature that carries no information about this player's mistakes has lift near 1, however often it
is detected. Reported at two levels:

- **population** — pooled across players: is this feature associated with errors in this band at all?
- **per player** — is this feature unusually costly *for this player*? That is what personalised
  coaching requires, and it is the comparison a generic coach cannot make.

Every figure carries its sample size and a Wilson score interval. A lift computed from nine moves is
not a finding, and the code marks it `reliable: false` rather than letting it look like one.

## Running

```bash
python collect.py --games-dir <data-dir> \
    --engine "C:\stockfish\stockfish-windows-x86-64-avx2.exe" \
    --out records.jsonl --workers 18

python relevance.py --records records.jsonl --out results
```

`collect.py` analyses every position at depth 15 (E01's working setting), records which features are
present — split into the mover's **own** features and the **opponent's**, since advice differs
entirely between the two — and whether the move played was an error.

Detectors are imported from `../e02-positional-detectors` rather than copied, so a change to a
definition cannot silently diverge between experiments.

## Replication design

The measure is run on two disjoint sets of players:

- a **discovery** sample, where associations are looked for;
- a **held-out** sample of different players, where any association found must reproduce.

This is not optional rigour. With 8 feature keys across 3 phases there are 24 cells, so the largest
lift in the discovery sample is expected to look impressive whether or not anything is there. A
finding that does not reproduce on held-out players is a multiple-comparisons artefact, and the
project's own risk register (R-13) exists to stop exactly that being reported as a result.

## Outputs

| File | Contents |
|---|---|
| `results/relevance.json` | population and per-player lift per feature, with counts, intervals and reliability flags |

Records are not committed — they are large and regenerable.
