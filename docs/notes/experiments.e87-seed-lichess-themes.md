---
id: cas-exp-e87
title: 'E87 — Seeding the tactical definitions, and a gate that discriminates instead of matching a word'
desc: 'The tactical definitions are not in the classical shelf, so they are seeded verbatim from the Lichess theme file whose keys the detectors already use. The naming gate is made discriminating: it now rejects twelve of the fourteen stored entries, keeping the two that are genuinely definitions, and it rejected the seeds until they named their own subject.'
updated: 1788699600000
created: 1788699600000
---

# E87 — Seeding from Lichess, and fixing the gate

**Answers:** [[design.knowledge-re-extraction]]'s two actionable items ·
**Code:** `experiments/e87-seed-lichess-themes/`, `chesscoach/knowledge_swarm.py` ·
**Date:** 2026-09-05 · **Status:** both done · **Nothing endorsed** — all entries `reviewed: False`

## The gate: from word presence to discrimination

`_names` asked whether a sentence contained any of a claim's vocabulary. That caught `fork` defined
as a skewer, because the sentence contains no form of "fork". It did not catch five entries that
passed on a **single ordinary word** — a pawn ending standing as the definition of an attack on the
king, because it says "king".

Three changes, and the first two follow the old docstring's own principle, *broad for finding,
narrow for verifying*:

**1. `NAMES`, separate from `TERMS`.** The search table mixed two different things — synonyms of the
concept and neighbouring topics — in one tuple. `late_castling` had `"castle"` and `"king safety"`
side by side: the first names the concept, the second names a neighbourhood, and a gate keyed on the
union accepts anything containing "king".

Narrowing to the topic phrase alone was tried first and **broke two existing tests, both correct**:
`hangingPiece` is genuinely named by *"en prise"* and `late_castling` by *"castle"*, and neither is
recoverable by splitting a topic phrase — "castle" is not a substring of "castling". Synonyms are
irreducible data, so they are now data.

**2. Discrimination.** A sentence matching another claim's vocabulary *more* than its own is about
that other thing. Strength rather than presence, because a definition by contrast — *"a skewer is the
inverse of a pin"* — names its neighbour on purpose and is still a definition of the skewer.

**3. How often, then how early.** Occurrences first: a passage saying "pawn" twice and "king" once is
about pawns, which is exactly the pawn ending. Then position, because in an English definition the
thing being defined is the subject: *"A skewer is the inverse of a pin"* names both once, and the
skewer first.

### What it does to the stored entries

| | before | after |
|---|--:|--:|
| accepted | 8 | **2** |
| rejected | 6 | **12** |

**The two it keeps are the two that are genuinely definitions**, both from Edward Lasker:

- `hangingPiece` — *"To put a piece en prise, is to play it so that it may be captured."*
- `repeat_move` — *"To 'lose a move' means to make a move which is not essential to the attainment
  of a desired position."*

Everything it now rejects was wrong: a pawn ending under `allows_pressure` and again under
`endgame_error`, the rule on moving into check under `late_castling`, a clause about complaining over
an opponent's clock under `long_think_error`, a passage about a bishop under `hangingPawn`.

## The seed: eight motifs, from the source the code already committed to

`tactics.py` states the reason itself — *"Motif names are the **Lichess theme keys**, which is what
will let the detectors be validated against the CC0 puzzle database."* So the definitions come from
[`puzzleTheme.xml`](https://raw.githubusercontent.com/lichess-org/lila/master/translation/source/puzzleTheme.xml)
(lichess-org/lila, AGPL — free, C7), **verbatim**. Evidence class **expert-consensus**.

This is seeding rather than extraction because **the definitions are not in the corpus**: `TERMS`
says *"tactics: the web knows these, the classical books mostly do not"*, and
[[experiments.e64-chess-books]] measured `skewer` at **zero** occurrences across the shelf. No
extractor recovers what is not there.

| seeded | not seeded |
|---|---|
| `fork` `pin` `skewer` `discoveredAttack` `hangingPiece` `backRankMate` `capturingDefender` `trappedPiece` | **`hangingPawn` — Lichess has no such theme** |

**8 of 8 pass the fixed gate.** Ten pre-existing usable sources were carried alongside rather than
discarded, since a second independent statement of a concept is corroboration.

### The gate rejected the seeds first, and was right to

Seeded with Lichess's *description* alone, **all eight failed**. The descriptions are written to sit
under a heading, so they do not repeat the term: the fork description never says "fork", and the
skewer description says "pin" but not "skewer" — so it matched `pin` better than `skewer`, exactly as
the discrimination rule intends.

The fix is to seed the pair Lichess itself displays — name and description. Both halves are verbatim;
only the colon between them is this project's. **A definition that does not name its own subject
cannot be checked against it**, and a gate that accepted one would be back to matching words.

## `hangingPawn` is left for the author

It is not a Lichess theme, so it can be neither seeded from here nor validated against the puzzle
database — which is the whole stated reason for using these keys. It exists for a measured reason:
[[experiments.e31-move-level-agreement]] found **every one of 45 reviewer notes mentioning a pawn was
unnameable** without it. That is a real gap and a real key with no external definition, and which of
the two gives way is the author's call.

## Honest limitations

- **Nothing is endorsed.** All 17 entries are `reviewed: False`; `draft()` cannot set it and neither
  can this script. The seeds are *available* to a report, not yet usable by one.
- **Nine non-tactical entries still fail the gate** and are untouched: `allows_pressure`,
  `allows_square`, `endgame_error`, `late_castling`, `long_think_error`, `moved_into_attack`,
  `pawn_error`, `slow_development`, `hangingPawn`. For the pawn-structure ones the classical shelf
  *does* discuss the concepts, so re-extraction is the right instrument; the rest may need Wikipedia
  the way the tactics needed Lichess.
- **`moved_into_attack` has no quote and zero sources** — an entry holding nothing while reading as
  populated.
- **The discrimination threshold is unmeasured.** Whether "strictly greater" over-rejects on real
  extraction output is only answerable by running the swarm and reading what it returns, which has
  not been done here.
- **The gate is not a definition test.** It establishes *subject*, not *definition-hood*. The clause
  about complaining over an opponent's clock is refused because it names nothing else better —
  telling a definition from a rule is the compiler's judgement, not this one's.
