---
id: cas-design-multipv-candidate-moves
title: 'Design — Asking Stockfish for several good moves instead of one'
desc: 'MultiPV costs roughly N times a single search, so it is not a saving. It is worth paying for anyway in one place: missed_motif still reads only the engine best move, and measured over 187 positions that rule finds 10 tactics where "not best, good enough" finds 32 — and zero pins where the wider rule finds eight.'
updated: 2026-09-12
created: 2026-09-12
---

# Design — Asking Stockfish for several good moves instead of one

**Serves:** V4 (gap detection), V8 (falsifiable coaching), C1 (free) ·
**Follows:** [[design.punishment-validity]] · **Status:** **proposed** — measured, not built

## The author's question

> *"When I use it while checking the games it usually offers a few proposed moves that have a good
> score and their score. If you only get the evaluation of the current move and you get the
> evaluation of the move that can be played after you play it then implementing if possible this
> evaluation to get few good moves by stockfish and their scores could be used to check what next
> moves are worthwhile and which are not and if one of those good moves is the one that is for the
> motif that is detected."*

That is **MultiPV**, the mode the Lichess analysis board is running when it shows several lines at
once. The question is whether the system should use it.

## How the engine is used today

`StockfishAnalyser.analyse` asks for **one** line, at a fixed depth, and keeps two things from it:

```python
self._limit = chess.engine.Limit(depth=depth)
...
def _analyse_uncached(self, board):
    return to_position_eval(self._engine.analyse(board, self._limit))
```

`PositionEval` carries `score_cp` and `best_move` — the evaluation, and the first move of the
principal variation. Everything else the engine computed is discarded. Depth is fixed for the
analyser's lifetime because it is part of the cache key and of every finding's provenance.

Two callers ask the engine anything beyond that:

- **`punishment.candidates_in`** evaluates the position *after* each reply that executes a motif, and
  compares it against the position's own evaluation. That is [[design.punishment-validity]]'s
  *"not best, good enough"* rule, and it costs a measured **1.52 evaluations per error position**.
- **`evaluation/choosers.py`** already passes `multipv=` — for the synthetic-player harness, not for
  diagnosis.

So the machinery exists and is not wired into the claims.

## Measurement 1 — MultiPV is not a saving

Depth 15, one thread, 12 real middlegame positions on this machine:

| | ms/position | relative |
|---|--:|--:|
| single PV (today) | **96** | 1.00× |
| MultiPV 3 | 272 | **2.83×** |
| MultiPV 5 | 507 | **5.28×** |
| MultiPV 8 | 764 | **7.96×** |

**Roughly linear in N.** At a fixed depth the extra lines do not ride along on one search — asking
for the second-best move means not pruning the branches that prove it is second best.

This kills the obvious version of the idea. Replacing the per-candidate evaluations with one MultiPV
call would cost **5.28×** where the present design spends **1.52×** — three and a half times more, for
the same answer. [[design.punishment-validity]] guessed this (*"the naive reading is a MultiPV
analysis at every error position, which would be expensive"*) and guessed right, though it never
measured; the figure above is the measurement it was missing.

**Where MultiPV would still be wrong:** at every position. 4,900 positions for a fifty-game history
goes from 7.8 minutes to **41 minutes** at MultiPV 5. The two-minute analysis the whole cost argument
rests on would be gone.

## Measurement 2 — but there is one claim that needs it

`allowed_motif` was rebuilt on *"not best, good enough"*. **`missed_motif` never was.**

```python
def _count_available(tallies, board, observation):
    """Motifs the engine's move would have executed: an opportunity either way."""
    best = _legal(board, observation.best_move)
    if best is None:
        return
    for motif in detect_motifs(board, best):
```

One move. The engine's single best. A fork the player could have played, that was second best by a
hair, **is not a missed fork** — it is not an opportunity at all, so it is not even in the
denominator.

This is exactly the failure [[design.punishment-validity]] opens with, quoted from the author:

> *"The fork doesn't have to be the very best move by the engine."*

It was fixed for what the opponent does to the player, and left in place for what the player does.
The asymmetry is not deliberate and is not recorded anywhere.

**Measured**, 187 real positions, MultiPV 5, depth 15 — motifs found by the engine's best move alone
against motifs found by any move within `INACCURACY_WP` of it:

| motif | best move only | within an inaccuracy | |
|---|--:|--:|---|
| `pin` | **0** | **8** | finds nothing today |
| `discoveredAttack` | 4 | 16 | +300 % |
| `hangingPawn` | 3 | 5 | +67 % |
| `fork` | 1 | 1 | — |
| `hangingPiece` | 1 | 1 | — |
| `skewer` | 1 | 1 | — |
| **total** | **10** | **32** | **+220 %** |

**`missed_motif.pin` finds zero in this sample and would find eight.** That is not a tuning
difference; the claim is structurally blind. And it is the same fact [[design.punishment-validity]]
already recorded from the other side — *"`pin` alone is 49 % of the whole engine budget, because
those motifs are usually available but not best"*. A pin is a quiet move. The engine rarely ranks it
first. So a rule keyed on *first* cannot see pins, and a player who misses pins is told nothing.

The sample is small and two of the six motifs move on one instance each. What carries the finding is
the pin row and the discovered-attack row, both of which are large and both of which have a mechanism
behind them rather than only a count.

## The options

### Option 1 — MultiPV at error positions only

Ask for N lines **only where the player actually erred**, which is where `missed_motif` counts
anything. Measured: ~218 error positions per player.

| | extra per player |
|---|--:|
| MultiPV 3 | **+38 s** |
| MultiPV 5 | +90 s |
| MultiPV 8 | +146 s |

On top of a pass that already takes 7.8 minutes. `allowed_motif` spends 32 s today for comparison, so
**MultiPV 3 at error positions is the same order of cost as a feature the project already pays for**.

- ✅ Fixes the asymmetry with the rule the project already owns — one threshold, one owner.
- ✅ Cheap, and cheap for a reason that is stated rather than hoped: errors are 4 % of positions.
- ❌ **Incomplete by construction.** If the motif move ranks 6th, MultiPV 5 never mentions it. This is
  answerable rather than fatal: when the Nth line is already more than `INACCURACY_WP` below the
  first, the qualifying set is **complete** and the truncation cannot have hidden anything. Where it
  is not, the claim knows it is looking at a lower bound and can say so.
- ❌ The cache stores one `PositionEval` per `(fen, engine, depth)`. MultiPV results need either a
  second table or a widened row, and the cache is 283,576 positions that must keep working.

### Option 2 — MultiPV in the review tools only

Put the engine's top three moves and their scores **on the detection sheet**, next to the cited move.
No production cost at all: 163 rows × 0.5 s is **80 seconds** for a whole sheet.

This is worth doing whatever else is decided, and it is close to free. The author is currently opening
every link in Lichess and reading the top moves there by hand — the sheet can carry them. It also
directly serves the marking problem this whole line of work keeps hitting: *"Nxf7 would be a bad move
for white … Nc6 is much better"* is a judgement that needs the ranking visible.

### Option 3 — replace `candidates_in` with MultiPV

Measured above: **3.5× more expensive for the same answer**. No.

### Option 4 — MultiPV everywhere

41 minutes per player at MultiPV 5. No.

## Recommendation

**Option 2 now, Option 1 with MultiPV 3 next**, and Option 1 wants its own cycle because it changes a
claim's denominator and therefore every rate built on it.

Option 2 is nearly free, needs no schema change, and improves the instrument that every other
decision on this list depends on. Option 1 is the real fix and is affordable, but it makes
`missed_motif` count opportunities it has never counted — **the peer reference and the separation
register both become stale for every `missed_motif` claim** (L-058), which is an hour of rebuild and
a re-marking round, not a patch.

Neither is built. This note exists so that the code has somewhere to come from (hard rule 4).

## What this forecloses

- **A widened `missed_motif` cannot be compared against the old peer rates.** Both arms have to be
  rebuilt or the comparison measures the rule change (L-059 is exactly this, from the other end).
- **The cache schema** — once MultiPV rows are stored, the format is load-bearing for 283,576
  existing entries plus whatever a rebuild adds.
- **Depth stays fixed.** Nothing here argues for varying it, and varying it would break the cache key
  and the provenance at once.

## Open questions

1. **Is N=3 enough?** The measurement used 5. The right N is whatever makes the truncation check above
   pass most of the time, and that is measurable on the existing corpus without building anything.
2. **Does a wider `missed_motif` separate players?** +220 % instances is a correctness claim, not a
   discrimination one. [[design.punishment-validity]] made the same improvement on the allowed side
   and the register came out **net zero** — one claim recovered, one lost. The same could happen here
   and would still be worth having.
3. **Does the author agree a second-best tactic is a missed tactic?** It is their own words that
   argue for it, but they said them about the opponent's move. The player's side may deserve a
   different answer, and it is their call rather than an inference from a quote.
