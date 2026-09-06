---
id: cas-exp-e86
title: 'E86 — Auditing every detector against a real definition, and finding the knowledge base cannot be one'
desc: 'The audit was designed to judge detectors against the sourced knowledge graph. The graph cannot do it: fourteen entries, none endorsed, and forks definition is a definition of a skewer. Audited against Lichess own theme text instead. Two defects demonstrated on positions: a fork is missed when a victim was already attacked, and a trapped piece is reported when it has a safe escape.'
updated: 1788683148955
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

---

## Round two — fixed against the author's own marked sheet

The audit above read code against definitions. This round read the **author's marks** on
`experiments/e55-detector-precision/results/detection-sheet copy.txt` — 84 `[y]`, 33 `[n]`, 18 `[?]`
— and, for every rejected firing, reconstructed the position from `expert-review/games/` and found
the mechanism. **Their comments beside the rejections did most of the work**: in six of seven cases
the comment stated the rule directly, and the rule generalised to all of that detector's rejections.

Every fix is verified twice: against the marked positions, and swept across all **47,932 positions**
of the reviewed games to see what it costs.

| detector | marks before | marks after | corpus firings |
|---|---|---|---|
| `missed_motif.pin` + `allowed_motif.pin` | 20% / 40% | **5/5** on the allowed marks | 2,015 → 806 |
| `missed_motif.capturingDefender` | 25% | 6/8 | 1,729 → 149 |
| `allowed_motif.hangingPiece` | 40% | **5/5** | 3,203 → 775 |
| `allows_square.any` + `.rook_seventh` | 60% / 60% | **10/10** | — |
| `allows_pressure.king` | 40% | **5/5** | — |
| `trappedPiece` (both claims) | 40% / 40% | 6/10, from 3/10 | 357 → 200 |

### The rules, and whose they are

Each is the author's sentence, not a threshold chosen here.

1. **A pawn is not a pin target, whatever stands behind it.** The king branch of `_is_pin` applied no
   material test at all where the rook/queen branch required `_wins_once_vacated`, so any slider
   reaching a line with an enemy pawn and king on it counted. Two further rejections were a pawn
   shielding a *rook*, and the author described that shape twice, so the test now sits above both
   branches.
2. **An exchange is not a hanging piece.** *"If the piece took another piece a move before and now is
   hanging then it is an exchange."* All three rejections were captures answered by the recapture;
   both accepted cases were quiet moves. Needs one ply of history, which the analysis board carries.
3. **A recaptured piece collects nothing.** Every `capturingDefender` rejection left a piece loose
   *while it was not the enemy's turn*, with the capturer itself standing to collect it — and the
   recapture removes the capturer. It now asks the question `_is_fork` already asks of its targets.
4. **A king is a target but never a prize.** Found while fixing 3: `wins_material` answers 100 for a
   king square, so **every capture on a square beside the enemy king** claimed the king as loot.
5. **An outpost is in the half you conceded.** The rank tuples were the classical "knight on its own
   fourth to sixth rank", which reaches one rank past the halfway line, so a knight in its **own**
   half counted as settled in the opponent's position.
6. **A rook that is simply taken was never established.** *"It lasted there for 1 move because it was
   taken."* Safety and preventability are separate questions — a rook can be both unstoppable and
   short-lived.
7. **An endgame king with pawns near it is not under attack.** `zone_attackers` counted pawns and the
   king, so three of them round a centralised endgame king read as an assembling attack.
8. **A check does not trap every piece on the board.** Under check the only legal replies are the ones
   answering it, so every other enemy piece appears to have nowhere to go. Three of five
   `trappedPiece` rejections were checks.

### Where counting was not enough

`allows_pressure.king` is the one place a count could not separate the marks: the third rejection had
**three attacking pieces, exactly like both accepted positions**. Their *weight* separates them — 3,
10 and 11 against 15 and 15 — so `PRESSURE_WEIGHT` was added at 13. Weight rather than "a queen must
be present", because two rooks and two minors is a real attack with no queen in it. **Five hand-marked
positions is a thin calibration**; the constant is named so that stays visible.

### What this cost, and what is still wrong

- **`capturingDefender` traded recall hard.** 1,729 → 149. Two of the author's four accepted cases are
  lost because they are **two-move combinations** — `Nxf6+ Nxf6 Bxe5` wins a piece, and a one-ply
  reply test cannot see it. Two weaker rules were built and measured (a recapture-settled test, and a
  "wins material somewhere" test); both scored 5/8 against this one's 6/8, so this is the best of
  three, not a good one. 68 of the 149 survivors are checks and most of the rest are pawn endings
  where nothing can flee.
- **`trappedPiece` is still wrong 4 times in 10.** Two of those the author diagnoses as a *different
  motif* — *"This is fork"*, *"This is fork motif in 2"* — which is a naming problem, not a detector
  one. The other two are accepted cases that D-2's escape fix already dropped. Worth knowing: the old
  `is_attacked_by` rule fired on **all ten** marked positions, so its apparent 4/10 was firing always,
  not discriminating.
- **`early_error.black` (33%) was not changed, deliberately.** See below.

### `early_error` — the author's question, answered

> *"first I need to know what this detector actually detects and what is the purpose of it."*

It counts **any error the player made within the first 30 plies (move 15), split by colour**. That is
all. It says nothing about opening theory, book depth, or understanding — `OPENING_END_PLY = 30` is
the only opening-shaped thing in it.

So the three rejections are **right about the claim and not about the detector**:

> *"This is just missed tactics, not the result of lack of opening understanding."*
> *"This is not opening anymore."*

The detector counted correctly; the phrasing — *"You go wrong early as Black"* — implies a cause it
never established, and 30 plies is deep enough that the author twice said the position was past the
opening. **This is a phrasing defect, and the author's decision to make**, which is why nothing was
changed here. Two options:

1. **Say what it measures**: *"more of your errors come in the first fifteen moves than for players at
   your level"* — true, actionable, and claims no cause.
2. **Retire it.** `slow_development`, `late_castling` and `out_of_book` already make opening claims
   that name a behaviour, which is what D22 asked for.

### Verification

Every rule is pinned by tests built from the reviewed positions rather than constructed by hand:
`test_pin_precision.py`, `test_capturing_defender_precision.py`, `test_allows_square_precision.py`,
`test_king_pressure_precision.py`, `test_trapped_piece_precision.py`.

**Five existing tests asserted the old behaviour and were corrected**, each saying so where it
changed. Four were fixtures unrealistic in a way orthogonal to what they tested — an arriving rook
simply hanging, a knight that could just hop away, a BLACK "mirror" whose knight blocked its own
bishop and whose pawns had changed colour. The fifth, `test_a_pawn_pinned_to_a_ROOK_is_untouched`,
was **written by me earlier in this same session** from my own reading that a winnable rear piece
makes a pawn-pin real; the author's sheet says otherwise twice. It now records their rule and names
the reading it replaced — L-051 in its sharpest form, since the test and the thing it tested were
authored an hour apart.

---

## What the fixes did to the *claims*, measured against the right baseline

The corpus sweeps above count detector firings. They do not say whether a claim still reaches a
player, because a firing becomes an instance only after the punishment filter, the phase filter and
the confidence gate. So the sheet was regenerated and compared.

**The first comparison was wrong, and it is worth recording why.** I took the baseline from
`6de59ad` — the HEAD recorded in a stale git status carried through a compaction — and there are
**28 commits between that and the fixes**, including D-1, D-2 and the whole `punishment.py` rewrite.
Claims I had never touched moved by ±100 % and to zero, and had I read that as noise I would have
concluded the sheet was unusable as an instrument. **The arms of the comparison were not what the
comparison claimed** — [[learning.lessons]] L-046 again, and the specific trap is that a compacted
summary's git status describes the session's *start*, not the work's.

Rebuilt at **`98184a6`**, the commit immediately before the first fix, where `git diff` is exactly
`tactics.py`, `squares.py` and `kingsafety.py`. Same 15 players, same peer reference, same evaluation
cache; only the detectors differ.

| claim | before | after |
|---|---|---|
| `allowed_motif.capturingDefender` | 105 | **0** |
| `missed_motif.capturingDefender` | 19 | **0** |
| `allows_pressure.king` | 31 | **0** |
| `missed_motif.trappedPiece` | 4 | **0** |
| `allowed_motif.pin` | 75 | 16 |
| `missed_motif.pin` | 34 | 8 |
| `allowed_motif.hangingPiece` | 81 | 14 |
| `allows_square.outpost` | 24 | 6 |

**Four claims now say nothing to any of the fifteen players.** The sheet's own header is the right
judgement on that: *"a detector that never fires is as much a defect as one that fires wrongly."*

Two claims rose — `allowed_motif.fork` 26 → 52 and `allowed_motif.discoveredAttack` 0 → 15 — without
their detectors being touched. The mechanism is `candidates_in`, which skips a reply whose motifs the
**best** reply already covers (`motifs <= covered`). Removing motifs from the best reply shrinks
`covered`, so moves previously skipped are now evaluated and counted. Named as the mechanism; not
separately verified.

### Was a threshold too tight? Measured, and no

`PRESSURE_WEIGHT` was the obvious suspect for silencing `allows_pressure.king`, being calibrated on
five positions. It is not the cause. Across the reviewed games:

| rule | crossings |
|---|---|
| old — any attacker, ≥3 | 1,251 |
| pieces only, ≥3, no weight gate | 382 |
| pieces only, ≥3, weight ≥ 10 | 374 |
| pieces only, ≥3, weight ≥ 13 (shipped) | 275 |

**The weight gate accounts for 107 of the 976 removed.** The cut is made by counting *pieces* rather
than pawns and kings, which is the change the author's own rejections demanded — *"This is an
endgame, a few checks happen regularly in the endgame."* Dropping the weight gate would restore about
a third of the loss, cost one of the five marks, and still very likely leave the claim under the
confidence gate. **So the claim is silent because the author's rule says most of what it used to
report was not king pressure**, not because a threshold was set badly.

The same reading applies to `capturingDefender`: 91 % of its firings were the recapture shape the
author rejected, and what survives is too thin to reach a player.

### The decision this leaves

This is a trade the author owns, not one to settle here:

1. **Accept the silence.** Four claims stop being made; the rest are far more trustworthy. Defensible
   for a coaching system where a false accusation costs more than a missed observation — but it means
   `capturingDefender` and `allows_pressure.king` are *de facto* retired, and the vocabulary should
   say so rather than listing claims that cannot fire.
2. **Loosen the confidence gate for these claims**, so a claim with few but sound instances can still
   be made. This is the option that keeps the corrections and the coverage, and it moves the problem
   to a place where it is about evidence strength rather than about chess.
3. **Revert the two strictest rules** and accept the false positives the author marked. Not
   recommended, and recorded only so the option is visible.

The regenerated sheet is `experiments/e55-detector-precision/results/detection-sheet-2026-09-06-fixed-detectors.txt`,
stamped `commit b6ea303`, 28 claims with instances. **Neither marked sheet was overwritten.**

---

## Round three — the claims were not gated out, they were compared against the old detectors

The author chose option 2, *"loosen the confidence gate"*. **The gate was not the cause and loosening
it would have manufactured findings.** Running each section's `measure()` — which reports what a
detector found whatever the gate then did — over all twelve review players:

| claim | instances | opportunities | rate | peer baseline |
|---|---|---|---|---|
| `allows_pressure.king` | 19 | 4,507 | 0.42 % | **1.31 %** |
| `allowed_motif.pin` | 64 | 1,416 | 4.5 % | **12.1 %** |
| `allowed_motif.hangingPiece` | 67 | 1,352 | 5.0 % | **11.0 %** |

The detectors were **never silent**. Every claim died on one line in `assign_tier`:

```python
if stats.rate <= stats.baseline_rate:
    return TierDecision(tier=ConfidenceTier.NONE, ...)
```

…and `peers-e84.json` was built at `c8ed84f`, **before the fixes**. So a player rate computed with
the corrected detectors was being compared against a peer rate computed with the over-firing ones.
The detectors were cut 60–91 %; the baseline still carried the old volume; nothing could clear it.
**L-046 once more, and the third time in this experiment alone.**

### The reference rebuilt

`experiments/e84-band-references/build.py`, six band/speed references over 262 player-slots on the
warm evaluation cache. 348 → **821 cells**. One peer, for scale: `capturingDefender` 19 → 2
instances, `hangingPiece` 14 → 4, `allows_pressure` 4 → 1, over identical opportunity counts.

| claim | peer rate before | after | players reported for |
|---|---|---|---|
| `allows_pressure.king` | 1.31 % | **0.57 %** | 0 → **1** |
| `allowed_motif.pin` | 12.1 % | **4.8 %** | 1 → **2** |
| `allowed_motif.hangingPiece` | 11.0 % | **5.2 %** | 1 → **2** |

**No gate threshold was changed, and none should be.** What remained silent afterwards is silent for
honest reasons: `missed_motif.capturingDefender` has one instance in seven opportunities, and
`allowed_motif.capturingDefender` sits *below* the player's own rate on other motifs — they are
better at avoiding it than at the rest, which is not a weakness to report.

### The register was stale in the same way, and it cost a section its claim

`chesscoach/separation.py` is **generated** from the reference, so it was stale for the same reason.
Regenerated: 21 → 24 entries.

- **`allowed_motif.trappedPiece`, `executed_motif.trappedPiece`, `missed_motif.trappedPiece` are no
  longer flat** — they get a peer comparison back.
- **`allows_pressure.king` and `missed_motif.pin` are newly flat.**

`allows_pressure.king` at dispersion **1.14, p = 0.23** against a 1.34 threshold over 50 players.
It is S8's only claim, so **S8 now asserts nothing at all**. The reading is uncomfortable and worth
stating plainly: the old detector counted pawns and the king as attackers, so what looked like
players differing on king safety was substantially **how many endgames each of them played**. Remove
that and the difference goes with it.

This was measured before being accepted. Across the twelve review players, old register against new:

| | stale register | regenerated |
|---|---|---|
| players with an asserted finding | 4 | 4 |
| asserted claim-instances | 12 across 10 claims | **12 across 10 claims** |
| watched claim-instances | 64 across 26 claims | 64 across **25** claims |

**Identical asserted coverage.** The regenerated register costs exactly one sub-threshold claim and
stops asserting a comparison the evidence no longer supports, so it ships.

### A design mismatch this exposed

`separation.py` states the intent plainly: *"Nothing here retires a detector … What this register
removes is the comparison"*, and `peer_rate`'s docstring says *"every consumer already handles a
missing peer rate by falling back"*. **S8 does not.** It has one claim and no sibling to form a self
baseline from, so a missing peer rate retires it outright.

For this claim that is arguably correct — *"more readily than players at your level"* is comparative
by construction, and without a comparison the sentence cannot be said. But the module's stated
contract and its behaviour disagree, and the next section with a single claim will hit the same edge.
Recorded, not fixed.

### Tests

Twelve tests failed and none of them was wrong about its own subject; they had all borrowed a claim
key that has since gone flat. `test_speed_strata` used `missed_motif.pin` while testing **speed
mixing**; `test_arbiter`, `test_planner` and `test_explainer` ranked `pin` against `fork` while
testing **ranking** — and `_unusualness` returns neutral for a flat claim, so there was no ranking
left to check. Each now uses a subject absent from the register, and each says why, because **the
register moves whenever the detectors do** and this will recur.

`test_s8_attack_and_defence.TestReporting` is the substantive one. Its five tests check what the
section does *once a peer rate exists*, which is still worth testing, so they lift the register entry
for their duration and say so. Two new tests record what a player actually gets: the claim withheld,
and `measure()` still reporting the instances it saw — which is what separates *"this claim cannot be
compared"* from *"this detector is broken"*.
