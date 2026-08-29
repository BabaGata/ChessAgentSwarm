---
id: cas-design-development
title: 'Design — opening knowledge measured as development behaviour, not as book depth'
desc: 'The author''s proposal: castling time, development completion, repeated piece moves and pawn moves. It replaces the book-depth half of correction 1 with something cheaper, more actionable, and free of asserted chess rules — the thresholds come from peers, not from principle. One headline measure, three explanations, and a correlation screen that decides whether all four survive.'
updated: 1788739200000
created: 1788739200000
---

# Opening knowledge as development behaviour

**Source:** the author, 2026-08-29 · **Supersedes:** claim **1a** of
[[design.detectors-name-consequences]] · **Status:** design only — no code yet, per the M4 rule

## The proposal

> *"Every opening has an approximate number of moves until the player should castle the king, until
> most pieces should be developed... until the castling and until every piece is developed, multiple
> moves by the same piece are not recommended, as well as too many moves by the pawns. Some openings
> in general allow more moves with pawns. Beginner players that don't know opening lines tend to not
> develop pieces but move already developed pieces and move too many pawns unnecessarily."*

## Why this replaces 1a rather than joining it

Correction 1 split `early_error` into **1a** *you leave theory earlier than your peers* and **1b**
*you score worse in this opening than in your others*. 1b is unaffected and still merges A3.

**1a should be dropped in favour of this.** Book depth answers *"you stopped knowing the line at move
6"*, which names a moment and no action — the player cannot go and know more theory this week. This
proposal answers *"you moved a piece that was already out while a knight sat at home"*, which is a
behaviour and repairable in one game. That is exactly the distinction the six corrections were built
on: **a detector that recognises a position is not a finding; one that recognises a consequence is**
([[design.detectors-name-consequences]]), and D22 one level further down.

It is also **cheaper**. 1a needed a new peer statistic *and* the CC0 book walked over the peer
corpus. This needs a new peer statistic and nothing else.

Book depth is not deleted — it is **held**, and the correlation screen below will say whether it has
anything left to add.

## The central design move: peers supply every threshold

The proposal contains real chess principles, and stating them as rules would breach the project's own
hard rule 7 and R-03 — *"no folklore laundering"*. **"Castle by move 10" is not a fact.** It is a
teaching heuristic, its correct value differs by opening, and asserting it would put an unfalsifiable
number at the centre of a claim.

So no threshold in this design is asserted. **Every one is read off the player's own rating band**,
through machinery that already exists: `ConditionMeasurement` → `build_reference` → `posterior`
shrinkage → Wilson intervals. The claim becomes *"you do this, and players rated like you do not"*,
which is measured, falsifiable, and cites the player's own games (V8).

**This also disposes of the hardest objection to the idea.** Some openings deliberately keep a piece
at home — the c8 bishop in the French and the King's Indian is the standard case — and a global
"all minors out by ply N" rule would punish correct play. Against opening-conditioned peers it
cannot: if peers in the French leave that bishop home too, the player's deviation is zero. The rule
fires on a **deviation from what this opening's players do**, never on a **state of the board**.

Where a per-opening cell is too thin to estimate, `chesscoach/shrinkage.py` already shrinks it toward
the band-wide prior. That is what it is for, and it needs no new code.

## What is measured

Everything the peer machinery accepts is **instances over opportunities**. Not every part of the
proposal is naturally a rate, and forcing them into that shape is where the design work is.

### The window

The opening window is **not** a fixed ply. `OPENING_END_PLY = 30` already exists in S4 and its own
comment admits it is *"conventional rather than derived"*. Here the window is a per-game event:

> **development span** — plies until the player has castled **and** all four minor pieces have moved
> at least once.

This makes the window the thing being measured rather than a constant chosen in advance, and it
scales with the opening automatically.

### The censoring trap, named before it is fallen into

**A game that ends at move 12 says nothing about how slowly the player develops.** It is
right-censored: development had not finished *and could not have*. Averaging spans over such games
would report the players with the shortest games as the slowest developers — a measurement of game
length wearing the costume of a diagnosis.

Averaging the span is therefore **refused**. Every measure below is a rate over games that *reached*
the relevant ply, which is censoring-safe and fits `ConditionMeasurement` unchanged.

### Four measurements

| | claim | instances | opportunities |
|---|---|---|---|
| **headline** | `slow_development` | games where development was incomplete at ply **K** | games reaching ply **K** |
| explains it | `repeat_move_in_opening` | moves in the window that move an already-moved piece | moves in the window |
| explains it | `pawn_moves_in_opening` | pawn moves in the window | moves in the window |
| explains it | `late_castling` | games not castled by ply **K₂**, or never castled | games reaching ply **K₂** |

**K and K₂ are peer medians, not constants** — the ply by which half of the player's band had
finished developing, or had castled, computed when the reference is rebuilt.

## Separate or together — the author's question

The author proposed *"count them together but then change the advice based on what they do more
often"*. That instinct is right, and the implementation should be the other way round:
**measure separately, present together.**

**Measure separately**, because merging destroys three things the project cannot afford to lose:
every claim must cite the player's own moves (V8) and a merged index points at nothing; the advice
genuinely differs — *castle earlier* and *stop re-moving that bishop* are different weeks of work;
and the peer machinery, the cost pool and the confidence tiers all operate per claim.

**Present together**, because a player told four versions of *"develop your pieces"* has been told
one thing four times, and the plan has three slots. `chesscoach/overlap.py` already exists for
exactly this: `drop_covered_claims` collapses a narrow finding into a wide one that covers it. The
headline takes the slot; the largest deviation among the three explanations supplies the sentence
that says **why**. That is the author's *"change the advice based on what they do more often"*, built
out of a mechanism already in the code.

**But whether all four survive is not an argument to win — it is a number to measure**, and the
project has run this screen before. E10 closed a section slot because two candidates correlated
**+0.917** and **+0.914** with the overall error rate and were therefore not new information. The
same screen applies here, and it is the first thing to run:

- **the three explanations against each other.** They will correlate — the player who pushes pawns is
  the player who leaves knights at home. If two exceed **|r| > 0.85** across the review corpus they
  are one signal with two names, and only the more actionable one ships.
- **all four against the overall error rate**, for the E10 reason: a "development" claim that is
  really a proxy for *is a weaker player* teaches nobody anything.
- **`slow_development` against `plies_in_book`**, which settles whether 1a is dead or merely
  redundant.

**Only claims that survive the screen are built.** Designing four and shipping two is the expected
outcome, not a failure.

## What still needs calibrating

| needs calibrating | first proposal | how it gets settled |
|---|---|---|
| ply **K** for "development complete" | band median | the peer reference, once rebuilt |
| ply **K₂** for castling | band median | the same |
| does a **queen** sortie count as development | no — minors and castling only | measure both; the early queen is the classic beginner error and may deserve its own claim |
| what counts as "already moved" for a repeat | the piece's second move onward, tracked from its origin square | fixture positions, hand-checked |
| opening granularity for peer cells | ECO letter (A–E), falling back to band-wide | cell occupancy across the peer corpus |
| correlation ceiling before a claim is cut | \|r\| > 0.85 | E10 used judgement at 0.917; this makes it a stated threshold |

## Testable

1. **It must name a different set of players than `early_error` does.** If it names the same twelve
   it has been renamed rather than corrected — the same test correction 1 already carries.
2. **A hand-built King's Indian game must not fire `slow_development`** for the c8 bishop, once the
   peer cell for that opening exists. This is the false positive the whole design is shaped around.
3. **A game ending at move 12 must contribute to no denominator it cannot answer.**
4. **The correlation screen must run before the fourth claim is written**, not after.

## Sources for the principle itself

The *thresholds* need no source. The *choice of what to measure* is a claim about chess and carries
one, per hard rule 7. Candidates, both free (C7):

- **Lasker, _Common Sense in Chess_ (1895)** — public domain, and states development rules including
  not moving the same piece twice before development is complete. **Unverified against the text** —
  it must be read before it is cited, which is exactly what R-03 forbids skipping.
- **Wikibooks _Chess Opening Theory_** — CC-BY-SA, and already harvested into the project's guide
  library, so the citation costs nothing.

Evidence class for the resulting claims is **measured**, not asserted: the source justifies looking,
the peer corpus supplies the number.

## Cost

**No engine work of its own** — all four measures are board-walking over PGN, the cheapest class of
signal in the project. The one real cost is that adding claims to an agent's `measure` means the peer
reference must be rebuilt, and `build_reference` runs the full analysis pass. **Free if the analysis
cache is warm at the same depth; one engine pass over the peer corpus if not.** Nothing here needs a
language model.

## Honest limitations

- **Development is not a virtue in itself.** Peers who develop fast may simply be better at chess.
  Measuring *deviation from peers within a band* is what keeps that from becoming advice — but only
  the correlation screen will show whether it worked.
- **"All four minors have moved" is a crude proxy for developed.** A knight on a3 has moved and is
  not developed. Square quality is deliberately not judged, because judging it needs exactly the kind
  of asserted rule this design exists to avoid.
- **The censoring remedy costs data.** Rates over games reaching ply K discard short games entirely,
  and short games are not a random sample — they are the decisive ones.
- **None of it is measured yet.** Every number in this note is a proposal.
