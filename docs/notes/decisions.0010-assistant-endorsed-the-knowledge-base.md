---
id: cas-adr-0010
title: 'ADR 0010 — The assistant endorsed the knowledge base, under delegation'
desc: 'The author delegated endorsement two days before the deadline. All eighteen entries are now reviewed and servable. Every note records that the review was the assistants and not a humans, and eight entries carry a recorded disagreement with the detector they describe — including two known defects.'
updated: 1788746400000
created: 1788746400000
---

# ADR 0010 — The assistant endorsed the knowledge base

**Date:** 2026-09-06 · **Status:** accepted, **reversible** · **Decided by:** the author, delegated

## The decision

The author delegated endorsement:

> *"You should endorse the statements yourself or update and add notes that are missing, you can
> check them against the web and create more or less good statements. Those endorsements we will use
> as I endorsed them … for now lets say that your review is enough."*

**All 18 entries are now `reviewed: true` and servable to a player.**

## What this overrides, and what it does not

`reviewed` is stated as author-only in four places — CLAUDE.md, the `Entry` field comment,
`KnowledgeBase.draft`, and `review.py`'s docstring. **The rule is the author's and the author waived
it.**

**What was kept.** Every note begins:

> *"Reviewed by the assistant on 2026-09-06 under the author's explicit delegation. Not a human
> reading."*

So the provenance survives in the data. If the thesis describes these as reviewed, the record says by
whom. **Nothing here should be presented as human expert validation** — R-16's point that hand-verified
samples are the only evidence that counts is untouched by this, and a model agreeing with a detector
is still two systems sharing a guess.

## What was done to each entry

**Eight were seeded verbatim from Lichess** (`fork`, `pin`, `skewer`, `discoveredAttack`,
`hangingPiece`, `backRankMate`, `capturingDefender`, `trappedPiece`) and endorsed as they stand.

**Two were already good and were endorsed**: `allows_square` (Wikipedia's outpost definition) and
`repeat_move` (Edward Lasker on losing a move).

**Eight were written for this decision**, because what was stored was wrong or absent:

| key | what it held before | what it holds now | source |
|---|---|---|---|
| `moved_into_attack` | **nothing, no source** | *en prise* — unprotected and exposed to capture | Wiktionary glossary |
| `hangingPawn` | a passage about a bishop | the same *en prise* sense, one rank down | Wiktionary glossary |
| `slow_development` | *"Hence, the process of development is about being efficient."* | development as an opening principle | Chess Strategy Online |
| `late_castling` | the rule on moving into check | castle early, before move 10 | Chess Strategy Online |
| `long_think_error` | a definition of **time trouble** | this project's own measurement, and *not* time trouble | own |
| `endgame_error` | study advice | this project's own measurement, by material class | own |
| `pawn_error` | *"Pawns at their fourth squares are more powerful than at their sixth."* | this project's own measurement | own |
| `allows_pressure` | a pawn ending | this project's own measurement | own |

**Four claims have no term in the literature** and are marked as this project's own operational
definitions rather than dressed in a borrowed one. That is the honest form: they are measurements,
not chess facts, and E65 already found nine of fourteen keys are jargon.

**`allows_square`'s attribution was corrected.** Its text is Wikipedia's and it was credited to
Philidor, whose source merely happened to be first in the list.

**Five entries gained a `not_this`** — the field no agent may fill, now filled under the same
delegation: `fork` (not a double attack by two pieces), `hangingPiece` (not a pawn), `hangingPawn`
(not Steinitz's structure), `moved_into_attack` (not a losing capture), `long_think_error` (not time
trouble).

## The eight disagreements with the code, recorded in the notes

**This is the part worth your time.** The definition is retrieved so that it can act as an independent
check on the detector, and eight of them do not agree with it:

| key | disagreement |
|---|---|
| **`trappedPiece`** | **KNOWN DEFECT.** Escape squares are tested with `is_attacked_by` rather than an exchange, so a piece that could escape safely is reported trapped (E86 D-2). Endorsed as a definition of the *concept*, not of what the code does. |
| **`fork`** | **KNOWN DEFECT.** A fork whose victim was already attacked by another friendly piece is missed (E86 D-1). The detector is also narrower by design: two *newly* attacked targets, the attacker surviving, material definitely lost. |
| `backRankMate` | the detector does not test Lichess's *"trapped there by its own pieces"* at all |
| `pin` | the rear piece must be a rook, queen or king — narrower than "a higher value piece" |
| `discoveredAttack` | an unsourced floor: the revealed target must be worth 3 or more |
| `hangingPiece` | the definition describes a **state**, the detector fires on the **act** of capturing one |
| `late_castling` | the source's *"before move 10"* is advice; the claim is measured against a per-opening norm |
| `slow_development` | likewise measured against a norm, not against the sentence |

## How to undo it

`review.py` writes the file; a single edit setting `reviewed: false` reverses any entry, and the notes
say exactly what was claimed for each. **Read the two known-defect entries first** — `fork` and
`trappedPiece` are endorsed as definitions of the *concept* while the code is known to be wrong, which
is the pair most likely to want changing.
