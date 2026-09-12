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

**Option 2 is built** (2026-09-12). `detection_sheet.py` opens a short second engine session over the
~160 sampled rows and prints the engine's top three with scores under each. It is pointed at the
position the claim is about — after the player's move for `allowed_motif`, where the lines shown are
the *opponent's*, and before it otherwise. The counted move is starred, and a row whose move does not
appear at all says so. Verified on the two rows the author rejected by naming a better move:

    lichess.org/akIZ3faz#15   engine: Ne4 +1.67 | d5 +1.26 | Ne5 +0.99
    lichess.org/n3uQfuWO#30   engine: Rg3 +0.00 | f5 -0.51 | Bb5 -1.22

*"Ne8 is a bad move … **Ne4** is a good one"* and *"Rh3 is a bad move … **Rg3** is a good one"* — both
named moves are the engine's first line, now on the page where the marker can see them.

Option 2 is nearly free, needs no schema change, and improves the instrument that every other
decision on this list depends on. Option 1 is the real fix and is affordable, but it makes
`missed_motif` count opportunities it has never counted — **the peer reference and the separation
register both become stale for every `missed_motif` claim** (L-058), which is an hour of rebuild and
a re-marking round, not a patch.

Neither is built. This note exists so that the code has somewhere to come from (hard rule 4).

## The real fix, in full

**What changes is one line**, and everything after it is consequence.

```python
# chesscoach/sections/s1_tactical_gaps.py, _count_available
best = _legal(board, observation.best_move)      # <- one move
for motif in detect_motifs(board, best):
    missed = tallies[_key(MISSED, motif)]
    missed.opportunities += 1                    # the denominator
    if erred:
        missed.instances += 1                    # the numerator
```

becomes *"every move within `INACCURACY_WP` of the best"* — the rule
[[design.punishment-validity]] already wrote for the other side.

### Why it is not a one-line change

**It moves the denominator, not only the count.** `missed.opportunities` is *"how many times a pin was
on the board at all"*. Widening the rule adds positions where a pin was available-but-second-best, so
**both** numerator and denominator grow and the rate can move either way. A claim can come out
*quieter*. That is correct behaviour, and it is why this cannot be reasoned about without rebuilding:

    rate = instances / opportunities

Today, for `pin`, both are near zero in the sampled positions. Afterwards both are real numbers and
the rate is a real rate. Whether it lands above or below the peer rate is **not** predictable from the
+220 % instance figure, because the peer rate moves too.

### What goes stale, and why it is an hour rather than a patch

1. **The peer reference** (`data/raw/out/peers-e84.json`) holds `missed_motif.*` rates computed under
   the old rule, for 80 players across three bands and two speeds. Comparing a player measured the new
   way against peers measured the old way measures **the rule change**, not the player. That is L-059
   in the form where the norm does *not* move with the definition, and so reports a difference that is
   not real. `build.py`, about fifty minutes.
2. **The separation register** is generated from those rates and must be regenerated after it.
3. **Every marked `missed_motif` row** judges the old rule. `recheck.py` can re-ask the detector, but
   *"was this motif available"* now means something different — so `carry_marks.py` carrying a `[y]`
   forward would carry a verdict about a different question. Those marks need re-doing, not carrying.

### Where the engine call goes

Not into `detect_motifs` — that stays static and free, for the 469× reason already measured. The
MultiPV call belongs in the **analysis pass**, beside the one `punishment.candidates_in` already
makes, where the position is open and the result can ride on the `Observation`:

```python
# chesscoach/analysis/core.py, per errored position
punishments = _punishments(board, current, mover_is_white, analyser)   # exists
candidates  = _candidate_moves(board, analyser)                        # new
```

`s1_tactical_gaps` then reads `observation.candidates` the way it reads `observation.punishments`, and
**keeps its stated property of making no engine call of its own**. The cache needs a row shape holding
N lines instead of one, which is the only schema work.

### Cost, restated for the shape actually proposed

MultiPV 3, at error positions only: **+38 s per player**, against the 32 s `allowed_motif` already
spends and a 7.8-minute pass. The reference rebuild is the real bill, and it is paid once rather than
per player.

## Why a truncated list can still be a complete answer

MultiPV 3 returns three moves, and the worry is obvious: *if the pin is the engine's 7th choice,
MultiPV 3 never mentions it, so the claim silently misses it.*

**Sometimes that worry is answerable, and the engine's own output says when.**

The question a missed tactic asks is: **is there any move executing this motif that is within
`INACCURACY_WP` of the best?** Call that the *qualifying set*. MultiPV returns its lines in
**descending order of evaluation** — that is what MultiPV means. So line 1 is the best move, line N is
the worst of the N shown, and every move **not shown is no better than line N**.

That last clause is the whole argument. Take a real row from the sheet:

    line 1:  Ne4  +1.67       <- the best
    line 3:  Ne5  +0.99       <- the last one shown

and suppose the inaccuracy threshold is about 0.35 in these terms. Then

- line 3 is already **0.68 below** line 1, which is further than an inaccuracy;
- every move the engine did **not** show is **no better than line 3**;
- so every unshown move is also more than an inaccuracy below the best;
- so **no unshown move can qualify**, and the three shown lines contain the entire qualifying set.

The truncation hid nothing, and that is proved rather than hoped.

Now the other case:

    line 1:  Ne4  +1.67
    line 3:  Nc6  +1.55       <- still within an inaccuracy

Here line 3 qualifies, so line 4 might have qualified too and the list was cut mid-set. The claim is
then looking at a **lower bound**: every motif it found is real, and there may be more it cannot see.

**So the rule is a check, not a guess:**

```python
complete = (best_wp - worst_shown_wp) > INACCURACY_WP
```

When it holds the answer is exact. When it does not, the position is either re-asked at a larger N or
recorded as a lower bound — and the honest version says which, rather than reporting a lower bound as
though it were a count. How often it holds at N=3 is measurable on the existing corpus before anything
is built, which is open question 1.

**The same check does not apply to `allowed_motif`**, which does not truncate at all: it asks
`detect_motifs` about every legal reply and evaluates only those executing a motif, so its qualifying
set is complete by construction. Worth keeping in view — the two claims would reach the same rule by
different routes, and only one of them needs a completeness test.

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
3. ~~**Does the author agree a second-best tactic is a missed tactic?**~~ **Answered 2026-09-12:
   yes.** Asked whether *"doesn't have to be the very best move"* holds for the player's own side as
   well as the opponent's, the author said it does. The rule is symmetric by decision rather than by
   inference, and Option 1 has its warrant.
