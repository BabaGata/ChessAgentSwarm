---
id: cas-exp-e86
title: 'E86 — Auditing every detector against a real definition, and finding the knowledge base cannot be one'
desc: 'The audit was designed to judge detectors against the sourced knowledge graph. The graph cannot do it: fourteen entries, none endorsed, and forks definition is a definition of a skewer. Audited against Lichess own theme text instead. Two defects demonstrated on positions: a fork is missed when a victim was already attacked, and a trapped piece is reported when it has a safe escape.'
updated: 1788717600000
created: 1788681600000
---

# E86 — Every detector, against a definition that can bear the weight

**Answers:** § A of [[design.detector-audit]] · **Date:** 2026-09-05 ·
**Status:** audit complete · **No detector was changed** — the author asked for the review only, and
a rebuild was running

## The reference had to be replaced before the audit could start

The design said to judge each detector against *"the sourced definition now in the graph"*. **It
cannot.** `data/knowledge.json` holds **14 entries, every one `reviewed: False`**, and the entries
that exist are largely filed under the wrong concept:

| entry | what its stored definition actually describes |
|---|---|
| **`fork`** | **a skewer** — *"a skewer happens when a chess piece attacks an opponent's chessman, which hides a less important piece behind it"*, drafted by `phi4-mini:3.8b`, sourced to a Wikipedia **zwischenzug** page and a chesskid **skewer** page |
| `allows_pressure` | advancing the king in a pawn endgame |
| `endgame_error` | the same king-advance text, again |
| `late_castling` | the rule about a player moving into check |
| `long_think_error` | a 19th-century rule on complaining about an opponent's clock |
| `trappedPiece` | a *capped* pawn — a different concept |
| `hangingPawn` | a passage about bishops |
| `moved_into_attack` | **nothing: zero sources** |
| `slow_development` | a fragment beginning mid-word (*"quares, has the better chance…"*) |

And **eleven claims have no entry at all**: `pin`, `skewer`, `discoveredAttack`, `backRankMate`,
`isolated`, `backward`, `doubled`, `outpost`, `rook_seventh`, `miscounted_exchange`,
`sacrificed_for_attack`.

**Auditing against this would have manufactured defects** — checking the fork detector against a
skewer definition would have "found" it wrong. That is [[learning.lessons]] L-053 exactly, and it is
worse than absence: a missing definition is visibly missing, a wrong one reads like a reference.

**The knowledge base is therefore itself the first finding, and re-extracting it is prerequisite
work, not a follow-up.** `reviewed: False` on every entry means nothing here was ever endorsed, so
nothing was hidden — the machinery worked, the extraction did not.

## The reference actually used

`tactics.py` states its own intent: *"Motif names are the **Lichess theme keys**, which is what will
let the detectors be validated against the CC0 puzzle database."* So Lichess's own theme text is the
reference the code already committed to, quoted verbatim from
[`puzzleTheme.xml`](https://raw.githubusercontent.com/lichess-org/lila/master/translation/source/puzzleTheme.xml)
(lichess-org/lila, AGPL — free, C7). Positional terms from
[Wikipedia's chess glossary](https://en.wikipedia.org/wiki/Glossary_of_chess) and its
[isolated](https://en.wikipedia.org/wiki/Isolated_pawn),
[backward](https://en.wikipedia.org/wiki/Backward_pawn) and
[doubled](https://en.wikipedia.org/wiki/Doubled_pawns) pawn articles. **Evidence class:
expert-consensus.**

---

## Two defects, demonstrated on positions rather than argued from reading

### D-1 — `fork` misses a fork when a victim was already attacked

`_newly_attacked` excludes any target that `board.is_attacked_by(mover, square)` before the move —
**attacked from anywhere, by any friendly piece**. So a second attacker on one of the victims removes
it from the count, and the fork falls below the two-target minimum.

```
4r1k1/8/8/8/6N1/8/8/4R1K1 w   Ng4-f6+ forks Kg8 and Re8   ->  detects NOTHING
4r1k1/8/8/8/6N1/8/8/6K1   w   the same move, no Re1       ->  detects fork
```

**Adding an attacker to a fork's victim makes the detector stop seeing the fork.** The intent —
*"they weren't attacked before"*, so a piece wandering into a pre-existing double attack is not a
fork — is right; the implementation asks the wrong question. It should ask whether the target was
attacked **by the moved piece** from its old square, not whether anything attacked it.

**FIXED 2026-09-06, after the author settled what "newly" means:**

> *"the 2 newly attacked pieces can be attacked previously by some other piece, but they both have to
> be attacked by the piece that was moved ... the piece that was last moved did not create a fork, it
> newly attacked just one piece."*

So **newly means newly by the piece that moved**. A previous attack by some *other* piece is not the
mover's business; what the rule must exclude is a move that newly attacks only **one** target while a
second was already attacked by something else.

`already = board.attacks(move.from_square)` asks exactly that. The old test asking
`board.is_attacked_by(mover, square)` asked whether *anything* friendly attacked the target, which
also discarded genuine forks.

**Measured on 6,249 real positions: 73 forks become 109.** **36 real forks were being thrown away**
and none is lost — the corrected exclusion set is a subset of the old one, so the change can only add.
Three of the 36, checked by eye:

| position | move | forks |
|---|---|---|
| `6k1/1pR3pp/8/p2np3/2B1P3/PR4P1/1P1r1rP1/6K1 w` | `Bxd5+` | the king on g8 and the pawn on b7, which `Rc7` already attacked |
| `r1bq1r2/pp3ppk/3p1N1B/2p2P2/2n1P3/6Q1/PPP3PP/R4RK1 b` | `Qxf6` | `b2` on the diagonal and `h6` along the rank |
| `rn1qkb1r/p1pppppp/1p6/8/2B5/3P1b2/PPP2PPP/R1BQK2R w` | `Qxf3` | `f7` up the file, which `Bc4` already attacked, and `a8` |

**This was withdrawn once and reinstated.** It was withdrawn because `tests/test_fork.py` asserted the
old reading and the author's written definition looked like it agreed; the author then clarified that
it does not. The test now carries the clarification in its own docstring.

**No rebuild needed.** All three `fork` claims are already withheld from peer comparison by the
separation register.

### D-2 — `trappedPiece` reports a piece that can escape safely

Escape squares are tested with `after.is_attacked_by(mover, e.to_square)`. **That is the naive test
D17 replaced everywhere else in this module** with an exchange-based one — `_lands_safely` and
`_is_worth_winning` both use `wins_material`, because *attacked by something* and *cannot go there*
are different questions.

```
n2k4/8/8/P7/8/8/7Q/6KB b   black Na8 attacked by Bh1
  escape c7  is_attacked_by = True, white actually gains 0   (Kd8 defends: Qxc7 Kxc7)
  escape b6  is_attacked_by = True, white actually gains 0
  _is_trapped_piece -> True, although Nc7 is simply safe
```

- **FIXED 2026-09-06.** `_lost_on_arrival` plays the escape and counts the exchange on the square it
  lands on, which is the test `_lands_safely` already applies to a fork's own attacker.
- **Measured on 6,249 real positions: 80 firings become 41.** The fix removes **42 false positives**
  — pieces that could simply step somewhere safe — and adds 3, where a square looked unattacked but
  the piece would still have been lost there.
- **No rebuild needed.** All three `trappedPiece` claims are already withheld from peer comparison by
  the separation register, so a reference measured under the old rule is not being compared against.

---

## Every detector, against the definition

Verdicts: **aligned** · **narrower** (stricter than the definition, on purpose) · **defect**.

### Tactical — `tactics.py`

| detector | Lichess definition | what the code does | verdict |
|---|---|---|---|
| `fork` | *"a piece attacks two or more opposing pieces simultaneously"* | ≥2 **newly** attacked by the moved piece, attacker lands safely, material definitely lost | **defect (D-1)** on top of a deliberate narrowing |
| `pin` | *"a piece is unable to move without revealing an attack on a higher value piece"* | slider pins front to rear; rear must be **≥ rook** (`PIN_TARGET_MIN_VALUE = 5`); pinner survives; pin holds or wins | **narrower** — Lichess says "higher value", the code says "rook, queen or king" |
| `skewer` | *"a high value piece attacked, moving out of the way, allowing a lower value piece behind it to be captured"* | front > behind in value, behind ≥ 3, wins once vacated, skewerer survives | **aligned** |
| `discoveredAttack` | *"moving a piece that previously blocked an attack by a long range piece out of the way"* | a friendly slider's attack set grows; revealed target worth **≥ 3** or the king, and winnable | **narrower** — the ≥3 floor is undocumented and has no source |
| `hangingPiece` | *"an opponent piece being undefended or insufficiently defended and free to capture"* | the move **is** a capture of an undefended piece worth ≥ 3, netting its full value | **narrower**, and describes the *act* where Lichess describes the *state* |
| `hangingPawn` | **not a Lichess theme** | the same test below the value line | **invented key** — see cross-cutting |
| `backRankMate` | *"checkmate the king on the home rank, when it is **trapped there by its own pieces**"* | mate + king on home rank + mate given **along** the rank by rook/queen | **narrower and incomplete** — the "trapped by its own pieces" clause is not tested at all |
| `capturingDefender` | *"removing a piece critical to the defence of another, allowing the now undefended piece to be captured"* | capture not losing material, and something the captured piece defended becomes winnable | **aligned** |
| `trappedPiece` | *"a piece is unable to escape capture as it has limited moves"* | attacked, winnable, has escapes, **all escapes attacked** | **defect (D-2)** |

### Material — `material.py`

| detector | definition used | what the code does | verdict |
|---|---|---|---|
| `moved_into_attack` | *en prise*: a piece left where it can be taken | **quiet** move whose exchange nets ≤ −1 | **aligned**; partitions cleanly against `miscounted_exchange` on capture-vs-quiet |
| `miscounted_exchange` | a capture that loses material once recaptures are counted | capture whose exchange nets ≤ −1 | **aligned** |
| `left_hanging` | pieces other than the moved one left winnable | exactly that | **aligned** |
| `sacrificed_for_attack` | the author's own: material given up to open an attack on the king | losing capture near the enemy king; **soundness deliberately not tested** | **aligned**, and the refusal to test soundness is measured (r = +0.682 vs +0.125) |

### Positional — `structure.py`, `squares.py`, `kingsafety.py`

| detector | definition | what the code does | verdict |
|---|---|---|---|
| `isolated` | *"no friendly pawn on an adjacent file"* | exactly that | **aligned** |
| `backward` | *"behind the pawns on adjacent files, cannot advance with pawn support"* | not pawn-defended, square ahead empty **and attacked by an enemy pawn** | **narrower** — the enemy-pawn control clause is the standard practical reading but is stricter than Wikipedia's |
| `doubled` | *"two pawns of the same colour on the same file"* | plus **≤ 2 ranks apart** and **persisting ≥ 3 moves**, both from the author | **narrower, author-endorsed** — the reasoning is recorded verbatim in the code |
| `outpost` | *"a square where a piece can sit on a hole in front of the pawn without risk of a pawn driving it away"* | `can_ever_be_covered` asks whether any enemy pawn could still advance to attack it | **aligned, and better than most** — the code note says casual definitions omit this clause, and Wikipedia's includes it |
| `rook_seventh` | geometry | rooks on the conceding side's second rank | **aligned** |
| `allows_pressure` | attackers in the king zone | zone attacker count rising | **unaudited** — the knowledge entry for it describes a pawn endgame, so there is no definition to audit against |

---

## What is left, measured on 6,249 positions

Both defects are fixed. The rest of the audit's concerns were then checked against real games rather
than left as readings, and **most of them dissolved**.

| detector | firings per 1,000 moves | verdict |
|---|--:|---|
| `left_hanging` | 164.2 | correct, **and reaches no report** — `s7` records it `REFUSED [+0.917] — the error rate renamed` |
| `hangingPawn` | 79.2 | |
| `hangingPiece` | 68.2 | |
| `pin` | 46.1 | three sampled, **all genuine** (pin to a queen, to a king, and a pawn to a rook) |
| `capturingDefender` | 36.3 | |
| `moved_into_attack` | 20.0 | |
| `fork` | 17.4 | **fixed** — 73 → 109 |
| `discoveredAttack` | 13.9 | |
| `miscounted_exchange` | 7.7 | |
| `trappedPiece` | 6.6 | **fixed** — 80 → 41 |
| `skewer` | 4.3 | |
| `sacrificed_for_attack` | 2.9 | |
| `backRankMate` | **1.0** | its missing clause is real and **fires 6 times in 6,249** |

**Concerns that did not survive contact with the data:**

- **"`trappedPiece` scans the whole board rather than the move."** True of the code and false in
  effect: of 41 firings, **40 were pieces the move newly trapped** and one was already trapped. The
  scan finds what the move did, because trapping generally requires the move that does it.
- **"`left_hanging` fires on a sixth of all moves."** It does, it is right to, and it reaches nobody.
  A sampled case that looked wrong — a knight defended by a pawn — had a second attacker down an open
  file, so the exchange does win material. **The detector was right and the reading was not.**
- **`backRankMate`'s missing "trapped by its own pieces" clause** is real and not worth fixing: at one
  firing per thousand moves it cannot move any rate that reaches a player.

**What remains, and none of it is a defect:** four unsourced value floors, which are project
conventions and are now recorded as such in the endorsed entries; and `hangingPiece` describing an act
where Lichess describes a state, which is correct for a claim about moves.

**Honest limitation.** This is a spot-check of a few firings per detector against a corpus of three
players. The author's impression came from reading the whole detection sheet, which is a far larger
sample, so a defect this pass did not reach is entirely possible.

## The 28 that "never fired" — none of them is a broken detector

The detection sheet lists 28 claims the system can make and did not, for any of the twelve review
players, with the note that *"a detector that never fires is as much a defect as one that fires
wrongly"*. Checked against the reference, **every one of the 28 produces instances** — `repeat_move`
52,684, `plays_queenless` 45,154, down to `endgame_error.pawn` at 12. **"Never fired" in that sheet
means never reached a report, which is a different thing from never triggered.**

| | count | why |
|---|--:|---|
| **correct by design** | 8 | `executed_motif.*` — S1's `NOT_ASSERTED`: *"it is not a weakness and must not be reported as one"*. The sheet lists these as a concern; they are working. |
| **withheld by the register** | 5 | a later decision, and correct |
| **reaches players another way** | 1 | `plays_queenless` is a `Tendency`, not a `Finding` — it appears under "HOW YOU PLAY" in every report |
| **measured, correctly silent** | 14 | below |

**Confirmed on five more players**: none of the 14 fired for them either, so across **17 players** they
have never once become a finding. That is systematic, and the reason splits cleanly in two.

**Five are too thin per player.** `endgame_error.minor`, `.pawn`, `.queen`, `.rook` and `.rook_minor`
have a **median per-player rate of 0.000** — more than half of players have no instances at all. A
thirty-game blitz corpus might reach three rook endings and err in none.

> **A claim can separate a population and still never be assertable for one player.** Dispersion pools
> every opportunity a player had; assertion needs enough *distinct games* from that one player.
> `endgame_error.rook` separates at 4.8x within band and is silent for everybody, and both are true.

**Six are universal.** `slow_development.own` 0.500, `late_castling.own` 0.500,
`slow_development.book` 0.454, `repeat_move` 0.423, `time_budget_error` 0.295, `early_error.any`
0.251. The gate asks a player's rate to exceed the population's, and on a behaviour everyone shares
almost nobody clears a Wilson interval on thirty games. **The gate is doing its job**: telling every
player "you repeat moves" is the anti-pattern R-12 names.

**Nothing here is a fix.** The detectors work, the gate works, and the silence is two different
correct behaviours meeting the same wall — which is [[design.better-claims]] arriving from the other
direction.

## Cross-cutting findings

**1. `hangingPawn` is not a Lichess theme.** The module's stated reason for using Lichess keys is to
allow validation against the CC0 puzzle database. `hangingPawn` was added for a good empirical reason
— *every one of 45 reviewer notes mentioning a pawn was unnameable* — but it **cannot be validated
that way**, and the module docstring's claim is now true of eight keys out of nine. Either the claim
narrows or the key does.

**2. Four value floors have no source.** `PIN_TARGET_MIN_VALUE = 5`, `SKEWER_TARGET_MIN_VALUE = 3`,
`HANGING_MIN_VALUE = 3`, `TRAPPABLE_MIN_VALUE = 3`, and `discoveredAttack`'s inline `< 3`. Each is
defensible and none is sourced; they are project conventions and should be recorded as such rather
than read as chess fact (R-03).

**3. `trappedPiece` scans the whole board, every other tactical detector scans the move.** It
iterates `after.piece_map()` and can fire on a piece the move had nothing to do with. That is a
different claim from the rest of the family and the difference is not stated anywhere.

**4. Two detectors describe a state, seven describe an act.** `hangingPiece`/`hangingPawn` fire on
*capturing* something hanging; Lichess's theme describes the position containing one. For
`missed_motif` and `allowed_motif` the act framing is right, but the shared name invites the wrong
reading in a report.

## What this does not establish

- **Precision is not measured here.** Every verdict above is a reading of code against a definition,
  plus two positions constructed to demonstrate two defects. What share of real firings are wrong is
  [[experiments.e04-motif-precision]]'s question and it has not been re-run.
- **The two demonstrated defects are the two I went looking for.** A third was tested and did not
  reproduce: my first fork position had the knight itself blocking the rook's line, so the fork was
  found and the test proved nothing until the position was rebuilt.
- **No detector was changed**, per the author's instruction while the reference rebuild is running.
- **The 28 never-firing claims are not diagnosed here.** [[design.detector-audit]]'s open question 2
  stands: a correct detector behind a wrong gate looks identical to a broken one.
