---
id: cas-exp-e55
title: 'E55 — The precision screen exists, and it has nothing valid to measure yet'
desc: 'Five samples can condemn a detector and cannot exonerate one, so the screen runs in two stages. The 23 existing marks cannot be dated against the code they judged, which makes them unusable rather than merely old — and the sheet now stamps its own commit so that cannot happen again.'
updated: 2026-09-09
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
list, and `data/knowledge.json` carried both definitions verbatim:

- **fork** — *"A move where a piece attacks two or more opposing pieces simultaneously."* No geometry.
- **skewer** — *"a high value piece being attacked, moving out the way, and allowing a lower value
  piece **behind it** to be captured."* Behind, and high-then-low.

The author's six cases are forks under both. **The decision was not free**, because the motif key is
also the exercise: `missed_motif.fork` becomes *"drill `fork` puzzles"* against the Lichess theme
filter, so relabelling sends a player to puzzles with the other geometry.

**Decided by the author: their rule wins** ([[decisions.0019-fork-and-skewer-by-geometry]]). A slider
attacking two pieces that all lie on one line through it is now `skewer`. `_all_on_one_line` decides
the name and `_fork_on_one_line` is **one predicate used from both sides**, so the two detectors
cannot drift into claiming the same move or neither — L-060's lesson applied before it could recur.
The material test is untouched; only the name moves.

The reasoning that makes it more than deference: the two shapes are different **recognition skills**.
A knight fork is pattern recognition on the knight's move; *"my rook can drop onto that rank and hit
two things along it"* is line vision, the same skill as pins and skewers. Grouping by what a player
has to learn to see beats grouping by the puzzle database's tag.

**Measured over the same 60 games, and it accounts for itself exactly.**

| | before | after |
|---|--:|--:|
| `fork` | 237 | **185** (−52, −22 %) |
| `skewer` | 61 | **110** (+49, +80 %) |

52 out and 49 in is not a leak: **3** of the moved positions were already skewers by the
front-and-behind rule as well, so they lost `fork` and kept a `skewer` they already had. Chasing that
three-position gap produced a wrong diagnosis first — that the two detectors' different survival
tests (`_lands_safely` against `wins_material`) were dropping positions between them — and a change
made on it. Swept over the same games, **no position** passes every fork test, falls to the line
rule, and then fails the skewer guard, so the change was reverted and one guard still serves both.
The measurement is now in the code where the guess was.

`data/knowledge.json` moved with it. `fork` keeps the Lichess sentence — every move still called a
fork is a fork under it — with the narrowing in its note. `skewer` could not: the detector now fires
on a shape that sentence does not describe, so it carries an author-written definition covering both
geometries, sourced to the marked sheet, with the Lichess source retained beneath. The puzzle-filter
mismatch is **accepted and unfixed**, and recorded in that note so the next person meets it rather
than rediscovers it.

**4. Detectors whose finding the author cannot act on** — `long_think_error`, `time_pressure_error`,
`out_of_book.any`: *"those are just informative but I don't know what kind of practices could be
done."* All three scored 100 %, 100 % and 0 % on correctness, so this is a separate axis from
precision. The advice **exists** — `planner._action` writes one per claim — and the sheet never showed
it, so a detector could only be judged on whether it fired and never on whether what it leads to is
worth a week. `detection_sheet.py` now prints a `tells you:` line under each claim. The sheet asks
both questions from the next generation on.

### Still open after this round

- `out_of_book.any` is **retired** — condemned at 0/3, and the author chose replacement over repair:
  *"there should be concrete opening detected."* `OUT_OF_BOOK_ANY_RETIRED` silences the pooled claim
  and the per-opening ones stand alone. A thin repertoire now yields no claim at all, which is the
  honest answer: the pooled version was a safety net that fired *because* it pooled.

  **Neither cause underneath is fixed**, and both are still live: book coverage (*"a variant of the
  accelerated london system"*) and attribution (*"out of book was white in the move 3"*) — the latter
  despite `left_book_themselves` existing, because the book holds the offbeat move and not the
  natural reply, so the deviation is recorded one ply late and changes hands.
- `moved_into_attack` at 44 % is stale (marked before `material.py` changed) and its one new rejection
  needs search, not SEE: *"taking the knight would result in a forced checkmate for white."* That is
  [[design.punishment-validity]] Option 1 pointed at a capture rather than at a punishment.
- **The peer reference and the separation register are stale for `fork` and `skewer`** (L-058), and
  the marks on those two rows now judge code that no longer exists. Nothing quoting either rate is
  trustworthy until `e84-band-references/build.py` is re-run — about fifty minutes.

## The second half of the marking, and an instrument defect (2026-09-09)

The author kept marking while the first round was being fixed: **95 marks**, not 60, across
**19 detectors**. `score.py` now refuses the sheet outright — two detector commits landed after it
was generated — which is the staleness guard doing its job, so the rest of this reads the marks
directly.

### The sheet was showing evidence the system never used

`motif_line` built the *"punished by X"* line by taking the **first legal move in `legal_moves`
order** that executed the motif. It never looked at `observation.punishments`, so it could illustrate
a finding with a reply that `punishment.qualifying` had already thrown out as not worth playing.

**`allowed_motif.discoveredAttack` scored 0 of 5, and four of the five rejections are this:**

> *"Nxf7 would be a bad move for white with significant loss in wp, another move that leads to
> discovered attack Nc6 is much better."*

> *"Rh3 is a bad move for white with significant loss in wp, Rg3 is a good one."*

> *"Ne8 is a bad move for black with significant loss in wp, Ne4 is a good one."*

> *"Nxg5 is a really bad move for white with significant wp loss, Ne5 would be better."*

Every one of those is a correct judgement **about the move on the page**, and in each the author names
a *different* move that also delivers the motif. That is the shape of a display bug, not a detector
bug: the finding may rest on the good move and the sheet printed the bad one. The claim cannot be
scored either way until it is re-marked on a corrected sheet.

`motif_line` now shows `primary(observation.punishments)` — the reply the report would name — then
the other counted ones, and only then falls back to a search. **This affects every `allowed_motif`
row ever marked**, including the rounds already scored.

### The one rejection that is about the detector

> *"nc6 is not a good target, the black knight is defended and queen would never take that one. There
> was actually a fork by Nc7 … The check should be done to see if the detected attacked piece was
> actually good to be taken a move after."*

`_is_discovered_attack` does not require its **target** to be winnable, where `_is_fork` requires
exactly that of every one of its targets. Not fixed.

### The cross-cutting one: evidence that cost nothing

**37 of 163 cited rows are `lost 0.0 wp`**, and the author rejects them wherever they appear, in four
different detectors:

> *"if it is suspected to be an out of book move then it should have at least significant loss in wp"*

> *"this exact move did not had any significant wp loss and should not be counted"* (`late_castling`)

> *"White played good moves, completing the development"* (`slow_development`)

> *"The move didn't had any significant wp loss after all"* (`miscounted_exchange`)

| detector | 0.0 wp rows | rejected |
|---|--:|--:|
| `late_castling.book` | 4 / 5 | 2 |
| `slow_development.book` | 4 / 5 | 2 |
| `out_of_book.Hungarian Opening` | 2 / 5 | 2 |
| `out_of_book.Queen's Pawn Game` | 2 / 5 | 2 |
| `miscounted_exchange` | 1 / 5 | 1 |

**This is one question, not five**, and it is not obviously a bug: `late_castling` and
`slow_development` are *habit* claims measured over opportunities rather than over errors, so a
costless move can legitimately be an instance of the habit. What is wrong is citing a costless move
as the **evidence** — the author reads it as *"the system says this move was a mistake"* and it is
not saying that. The choice is between filtering instances by cost and choosing costly instances to
cite; they are different claims and the second is nearly free.

Two smaller ones: `concedes_weakness.doubled` is rejected once for doubling mid-exchange
(*"a beginning of the exchange that white did not continue immediately"*), and `endgame_error.any`
carries the same complaint that retired `out_of_book.any` — *"Endgames should be separated by the
types of the endgames, any is not informative."*

## Regenerated, marks carried, and re-asked position by position (2026-09-09)

`detection-sheet-2026-09-09.txt`, built at `726b476`. Two new tools, because the marking is the
expensive part and every regeneration until now has thrown it away:

- **`carry_marks.py`** moves a mark from an old sheet to a new one when the same claim still cites the
  same `(game, ply)`, and carries the author's comment with it. It reports **kept / gone / new**, and
  is explicit that a carried mark judges code that has since changed.
- **`recheck.py`** answers the question `carry_marks` cannot. The sheet samples **5 of N**, so a row
  leaves it either because the detector stopped firing or because the sample reshuffled — identical in
  a diff, and reading one as the other is how a fix gets claimed that never happened. It rebuilds each
  rejected position from the game and asks `detect_motifs` again. No engine.

### Carried

**62 of 95 marks carried**, 33 rows left the sheet, 102 rows are new and unjudged.

### Re-asked: 15 rejected motif rows, position by position

| | |
|---|--:|
| **no longer fire** | **8** |
| still fire | 7 |

| position | was | now |
|---|---|---|
| `mdpdLHYI#9` | `hangingPawn` — *"this was an exchange"* | **nothing** |
| `GV23qiD1#47`, `vmYdIpZ1#47` | `fork` — *"this is a skewer"* | **skewer** |
| `SuvK6tPc#72`, `z6Zw4EtZ#44`, `wW19J75A#82`, `JpiP6HBj#45` | `fork` — *"this is a skewer"* | **skewer** |
| `rBfHcNcI#29` | `pin` — *"pinned already by the same bishop"* | **nothing** |

Every fix lands on the exact position it was written for. Nothing was fixed by re-sampling.

### The five that still fire are the sheet's fault, not the detector's — proved by the author

All five `allowed_motif.discoveredAttack` rejections still fire **on the move the old sheet printed**,
which is consistent with the display bug rather than against it: that move was never the one the claim
rested on. The new sheet shows `primary(observation.punishments)`, and the author's own comments settle
it.

| position | old sheet showed | author said | new sheet shows |
|---|---|---|---|
| `akIZ3faz#15` | `punished by Ne8` | *"Ne8 is a bad move for black with significant loss in wp, **Ne4** is a good one"* | **`punished by Ne4`** |
| `NF4Pv6NH#26` | `punished by Qb5` (as `pin`) | *"Qb5 is not among good moves for white … **Qe4** would be better"* | **`punished by Qe4`** |

**Two independent rows where the move the author named as the good one is exactly the move the system
had counted.** The finding was right and the illustration was wrong, and the author could not have
known that from the sheet. `allowed_motif.discoveredAttack` and `allowed_motif.pin` are therefore
**unscored, not wrong**, and their marks are void rather than negative.

### The scoreboard after carrying

**No detector is condemned.** `missed_motif.fork` and `out_of_book.any` were the two, and both are
resolved — one by ADR-0019, one by retirement. Ten claims are *unsettled*: marked, above the floor,
and short of the ~20 marks that would confirm them.

| claim | instances before | after |
|---|--:|--:|
| `allowed_motif.hangingPawn` | 231 | **39** (−83 %) |
| `allowed_motif.pin` | 139 | **78** (−44 %) |
| `missed_motif.fork` | 59 | **35** (−41 %) |
| `allowed_motif.fork` | 181 | **153** (−15 %) |
| `missed_motif.skewer` | 4 | **26** (+550 %) |
| `out_of_book.any` | 45 | **retired** |

**`allowed_motif.hangingPawn` at −83 % is far past the −18.7 % measured over all legal moves**, and the
gap is the point: `allowed_motif` counts *punishments*, and a punishment is a reply to an error, where
a recapture is enormously more common than among legal moves at large. The rule bit hardest exactly
where the author said it hurt.

### Not explained, and flagged rather than glossed

**`allowed_motif.discoveredAttack` rose 29 → 49 (+69 %)** and nothing in this cycle touched
`_is_discovered_attack`. The plausible mechanism is `candidates_in`'s skip — a reply whose motifs the
best reply already covers is never evaluated, and the fork/skewer relabel changes those `covered`
sets — but that is a hypothesis and it has not been measured. A detector moving 69 % for reasons
unknown is a defect until it is explained.
