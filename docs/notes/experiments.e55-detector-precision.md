---
id: cas-exp-e55
title: 'E55 — The precision screen exists, and it has nothing valid to measure yet'
desc: 'Five samples can condemn a detector and cannot exonerate one, so the screen runs in two stages. The 23 existing marks cannot be dated against the code they judged, which makes them unusable rather than merely old — and the sheet now stamps its own commit so that cannot happen again.'
updated: 2026-09-08
created: 1788652800000
---

# E55 — Precision per detector, on hand-verified samples

**Answers:** `state.md`'s week-old P0, *"the deliverable is precision per detector on hand-verified
samples — not a pass/fail"* · **Code:** `chesscoach/precision.py`,
`experiments/e55-detector-precision/` · **Date:** 2026-08-29 ·
**Status:** apparatus done, **measurement not started** — and the note says why

## The asymmetry the whole design rests on

At n = 5 a score of **0/5 puts the Wilson upper bound near 43 %**, which settles it. **5/5 puts the
lower bound near 57 %**, which settles nothing.

**Five samples can condemn a detector and cannot exonerate one.** So the screen runs in two stages:
everything at n = 5 to find what is broken, and only survivors that reach a player at n = 20. That is
the project's usual screen-then-measure shape, and here it also buys the scarcest resource in the
thesis — the author's time reading positions.

The consequence is stated in the code: *"a screen that reported 5/5 as confirmed would clear a
detector on an interval spanning 57–100 %, which is how a measurement becomes a testimonial."*

## The floor is the author's own threshold, not a round number

`PRECISION_FLOOR = 0.70`, anchored on their two recorded verdicts: `allowed_motif.hangingPawn` at
4/5 — *"works, leave alone"* — and `moved_into_attack` at 0/5 — *"broken"*. It sits below the
accepted point estimate and far above the rejected one.

Two marks is a weak basis for a constant. It is a better basis than a number chosen because it looked
reasonable, and it is labelled provisional.

**Note what this implies:** at 4/5 the interval is 38–96 %, so the screen **does not confirm** the
detector the author accepted by eye. It says "15 more marks would settle it" rather than agreeing —
which is the instrument working.

## The finding: the existing 23 marks cannot be used

The marks were recovered from `design.informative-claims.md` into a machine-readable file so they
would not be re-done. Then the question that decides whether they count: **what code were they made
against?**

- `chesscoach/tactics.py` — all motifs rebuilt **2026-08-24**
- `chesscoach/material.py` — `moved_into_attack` fixed **2026-08-27**
- the sheet they were marked on was **regenerated inside that same 08-27 commit**

**And the marking date is recorded nowhere.** The design note's frontmatter says 2026-08-23, but the
sheet it refers to was created on the 24th, so the note's date cannot be the marking date. Under
`marked_on = 2026-08-23` every mark is stale; under `2026-08-27` none is. **The evidence does not
distinguish them.**

So the honest position is that the project has **no valid precision data**, not because the marks
were bad but because they cannot be attached to a version of the code. That is worse than having
none, since it looks like having some.

*(A regeneration today produced a sheet identical to the committed one — same 33 claims, same
instance counts, same examples — confirming the sheet is current, and saying nothing about when it
was marked.)*

## The fix, so this cannot recur

The sheet now stamps its own provenance when generated:

    GENERATED 2026-08-29 from commit 2bf055f.
    Marks on this sheet judge THAT code. If a detector changes afterwards its
    marks stop being evidence about it -- record this line with them.

And `Dated` marks compare their date against the module that implements the claim, asked of git
rather than kept by hand — because a hand-kept date is exactly the thing that goes stale silently.
An unknown date **never** invalidates a mark: git being unavailable must not delete evidence (L-046).

## What exists now

| | |
|---|---|
| `chesscoach/precision.py` | Wilson intervals, three verdicts, the two-stage sizing, `Dated` staleness |
| `experiments/e55-detector-precision/score.py` | reads a marked sheet, reports precision per detector |
| the sheet | **33 claims, 165 boxes**, regenerated at `2bf055f`, stamped, unmarked |
| `marks-recovered.txt` | the 23 earlier marks, preserved and currently undatable |

**Marking happens in the sheet itself** — `[ ]` becomes `[y]`, `[n]` or `[?]` — because the marking
is the expensive part and a second file to keep in step would cost more than it saves.

## Consequence

- **The measurement is one marking session away**, and that session is the author's. 165 boxes at
  stage one; realistically the top ten detectors by firing count are where it matters, since
  `early_error.white.own` alone fires 200 times.
- **Nothing downstream should be trusted until the top few are marked.** A wrong detector poisons the
  arbiter, the plan and the report, and D4 cannot move off 3 until this produces numbers.

## Honest limitations

- **No precision has been measured.** This cycle built the instrument and found that the existing
  evidence could not be dated. Reporting anything else would be the testimonial the design exists to
  prevent.
- **The floor rests on two marks** and should be refitted once ten detectors are scored.
- **Precision says nothing about what a detector MISSES.** D15 defect (a) — five claims that never
  become candidates — needs a different screen and is untouched.

## The first scored round (2026-09-08)

The author marked **60 boxes across the twelve most-firing detectors** on `detection-sheet-2026-09-07`.
`score.py` reads them:

| detector | fired | marks | precision | verdict |
|---|--:|--:|--:|---|
| `out_of_book.any.own` | 45 | 3 | **0 %** | **condemned** |
| `missed_motif.fork.own` | 59 | 8 | **25 %** | **condemned** |
| `allowed_motif.fork.own` | 181 | 5 | 60 % | unsettled |
| `allowed_motif.hangingPawn.own` | 231 | 9 | 78 % | (marks stale, re-mark) |
| `moved_into_attack.own_move.own` | 120 | 9 | 44 % | (marks stale, re-mark) |
| `allowed_motif.pin` · `missed_motif.pin` · `hangingPiece` · `discoveredAttack` · `long_think` · `time_pressure` | | 4-5 each | 100 % | unsettled |

At n=5 the screen can condemn and cannot confirm, which is the property it was built to have.

### What the marks were actually about

Four distinct causes, and only two of them are bugs in the detector that was marked.

**1. An exchange read as a dropped pawn** — one row, and the largest measured effect. See L-060.
`_is_hanging_pawn` never called `_is_recapture`. Removing them takes `hangingPawn` from **884 to 719**
firings over 60 games, **-18.7 %**.

**2. A pin that was already there** — one row. `_lined_up_pairs` refuses to attribute a pin to a piece
that was *standing still*; it did not refuse the same piece **sliding along its own line**, which is
the same defect wearing a move. The author: *"those pieces were pinned already by the same bishop,
even before that move."* `_newly_lined_up` now filters the pairs for both `pin` and `skewer`.

Two fixtures in `test_motif_correctness.py` moved the rook **along** the d-file, so after this change
the control failed and the negative passed for the wrong reason. Both now bring the rook onto the
file. A fixture that reaches the state by the wrong route tests nothing once the route matters.

**3. Fork vs skewer — a vocabulary question, not a code one.** Six of the ten marked fork rows were
rejected with one reason: *"This is a skewer, fork is only when one of the involved pieces is not
aligned on the same line/diagonal."* Every one has the same geometry — a **slider** attacking two
pieces that lie on **one line through it, in opposite directions** (`Rd1+` hitting `Bb1` and `Kg1`).
Measured: **43 of 237 fork firings (18 %)** have that shape, against 61 firings of `skewer` itself.

This contradicts the project's own endorsed source. The motif vocabulary is the Lichess puzzle theme
list, and `data/knowledge.json` carries both definitions verbatim:

- **fork** — *"A move where a piece attacks two or more opposing pieces simultaneously."* No geometry.
- **skewer** — *"a high value piece being attacked, moving out the way, and allowing a lower value
  piece **behind it** to be captured."* Behind, and high-then-low.

The author's six cases are forks under both. **The decision is not free**, because the motif key is
also the exercise: `missed_motif.fork` becomes *"drill `fork` puzzles"* against the Lichess theme
filter. Relabelling sends a player to puzzles with the other geometry. Put to the author rather than
chosen.

**4. Detectors whose finding the author cannot act on** — `long_think_error`, `time_pressure_error`,
`out_of_book.any`: *"those are just informative but I don't know what kind of practices could be
done."* All three scored 100 %, 100 % and 0 % on correctness, so this is a separate axis from
precision. The advice **exists** — `planner._action` writes one per claim — and the sheet never showed
it, so a detector could only be judged on whether it fired and never on whether what it leads to is
worth a week. `detection_sheet.py` now prints a `tells you:` line under each claim. The sheet asks
both questions from the next generation on.

### Still open after this round

- `out_of_book.any` is condemned at 0/3 and the author asks for *"concrete opening detected"* instead.
  Two causes are entangled in its marks: book coverage (*"a variant of the accelerated london
  system"*) and attribution (*"out of book was white in the move 3"*) — the latter despite
  `left_book_themselves` existing, because the book contains the offbeat move and not the natural
  reply, so the deviation is recorded one ply late and changes hands.
- `moved_into_attack` at 44 % is stale (marked before `material.py` changed) and its one new rejection
  needs search, not SEE: *"taking the knight would result in a forced checkmate for white."* That is
  [[design.punishment-validity]] Option 1 pointed at a capture rather than at a punishment.
