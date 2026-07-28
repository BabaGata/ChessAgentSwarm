# E02 — Positional feature detectors

Answers open question **D4**: can the positional taxonomy that exists in the literature be turned
into board-feature detectors, given that — unlike tactics — it has no labelled corpus?

**Findings and consequences are in the vault:** `docs/notes/experiments.e02-positional-detectors.md`.

Short version: yes, cheaply and precisely. But detection is not the hard part — isolated pawns occur
in 96 % of games, so *presence* is not a coaching signal. Relevance-weighting is the real problem.

## Running

```bash
python -m pytest test_detectors.py -v          # 15 definition tests
python run.py --games-dir <data-dir> --out results --sample 16
```

`run.py` samples positions from move 12 onward, every 4th ply, and writes:

| File | Contents |
|---|---|
| `results/counts.json` | detection counts and base rates per feature |
| `results/review_sample.md` | stratified random sample with boards drawn, for manual checking |

The review sample uses a fixed seed, so re-running on the same games reproduces the same sample.

## Files

- `detectors.py` — four pure detectors over `python-chess`; each states its definition in its
  docstring, because these are contested terms and an unstated definition cannot be reviewed
- `test_detectors.py` — constructed positions including the negative cases that separate a real
  definition from a lazy one
- `run.py` — validation over real games

## Status

Experiment code. A detector that survives validation is reimplemented for production in M4 with its
own design note — see the guardrail in the `adaptive-cycle` skill.
