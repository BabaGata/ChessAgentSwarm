# E01 — Engine throughput & diagnosis stability

Answers open questions **A1** (how long does analysis take?) and **A2** (does depth change the
diagnosis?).

**Findings and their consequences are recorded in the vault:**
`docs/notes/experiments.e01-engine-throughput.md` — read that, not this file.

## Reproducing

```bash
# 1. Fetch a sample of real games (not committed - games are re-fetchable)
python fetch_games.py --out <data-dir> --band 1400 1800 --games 50

# 2. Measure
python benchmark.py \
    --games-dir <data-dir> \
    --engine "C:\stockfish\stockfish-windows-x86-64-avx2.exe" \
    --out results \
    --phase both --workers 18
```

Requires `python-chess` and a local Stockfish binary. The sample will differ between runs — player
selection walks recent Lichess arena standings for players inside the requested rating band — so
exact timings vary, but the relationships between settings hold.

## Results in `results/`

| File | Contents |
|---|---|
| `throughput.json` | first run — the thread comparison at fixed depth (1 vs 4 vs 16 threads, sequential) |
| `throughput_v2.json` | second run — depths 12/15/18, one thread per engine across 18 processes |
| `results.json` | the A2 label-stability comparison |
| `labels_sample.json` | per-game error labels from the first few games, for inspection |

Note that `throughput.json` and `throughput_v2.json` are not directly comparable: the first measures
one engine at a time, the second measures many engines competing for the same cores. The first
answers "do threads help?"; the second answers "how long does a batch take?".
