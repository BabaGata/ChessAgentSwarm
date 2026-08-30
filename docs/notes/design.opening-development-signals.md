---
id: cas-design-development
title: 'Design — opening knowledge as development behaviour, with per-opening norms'
desc: 'The author''s proposal: castling time, development completion, repeated piece moves and pawn moves, each judged against the norm for THAT opening rather than a global rule. No threshold is written down — every one is derived from peers, which E58 shows is both possible and necessary. Book depth stays beside it as learning feedback.'
updated: 1788739200000
created: 1788739200000
---

# Opening knowledge as development behaviour

**Source:** the author, 2026-08-29 · **Beside:** claim **1a** of
[[design.detectors-name-consequences]] · **Status:** measurement built —
[[experiments.e58-opening-development]]

> **Revised 2026-08-29, twice, both by the author.**
>
> **1a is reinstated.** This note first proposed superseding book depth. The author kept it: *"checking
> the played moves with the real opening lines should remain and can be used to test when the player
> usually stops knowing what to play by the book and use this as a potential learning feedback."*
> That is a different job from diagnosis — **feedback about what to study**, not a claim about a
> weakness — and it does not compete for a plan slot, so the correlation screen no longer decides its
> life. E58 confirms it is usable: median 1–5 moves in book with clear per-opening spread.
>
> **Norms are per opening, not global.** *"The tests should not be general for all opening but general
> rules per opening. Like in italian game the castles should occur around move 5 and in ruy lopez in
> between moves 8-10."* Confirmed as necessary by E58 — castling norms range from move 7 to move 17
> across families — and the norms are **derived** rather than written down, so every opening gets one.

## The proposal

> *"Every opening has an approximate number of moves until the player should castle the king, until
> most pieces should be developed... until the castling and until every piece is developed, multiple
> moves by the same piece are not recommended, as well as too many moves by the pawns. Some openings
> in general allow more moves with pawns. Beginner players that don't know opening lines tend to not
> develop pieces but move already developed pieces and move too many pawns unnecessarily."*

## Why this sits beside 1a rather than replacing it

Correction 1 split `early_error` into **1a** *you leave theory earlier than your peers* and **1b**
*you score worse in this opening than in your others*. 1b is unaffected and still merges A3.

**They answer different questions and only one of them is a diagnosis.**

Book depth answers *"you stopped knowing the line at move 6"*. As a **claim** that is weak — it names
a moment and no action, and the player cannot go and know more theory this week. But as **feedback**
it is strong and the author is right to keep it: it says *what to study*, it points at a specific
line, and it needs no plan slot to be useful. It is the natural companion to the opening brief the
swarm already produces.

The development signals answer *"you moved a piece that was already out while a knight sat at home"*,
which is a behaviour, repairable in one game, and therefore the diagnosis half. That is the
distinction the six corrections were built on: **a detector that recognises a position is not a
finding; one that recognises a consequence is** ([[design.detectors-name-consequences]]).

So: **book depth is learning feedback, development is diagnosis.** They are reported in different
places and neither displaces the other.

## Two populations, two different jobs

**Revised 2026-08-29 by the author**, after E58 derived its norms from the review corpus:

> *"I don't want this to be built by peer reference but by better players who usually know the
> opening. The comparison will later been done with peers for how regularly they develop later than
> expected."*

This is the correction that makes the claim mean something, and E58 is the evidence for it: norms
taken from ~1600 players describe **what 1600s do**, which is not what the opening asks for. The two
populations answer different questions and both are needed.

| | population | answers |
|---|---|---|
| **the expectation** | players who know the openings | *by when should this be done in THIS opening* |
| **the comparison** | the player's own rating band | *how often is this player later than that* |

So a claim is no longer *"you castle later than your peers"* — which flatters a player whose peers are
all bad at it — but **"you are late by the opening's own standard more often than your peers are"**.
The peer step keeps L-045 intact (peer-relative answers *is this unusual*, never *is this right*)
while the expectation supplies the *is this right* the peers cannot.

### Why this is not folklore after all

Hard rule 7 and R-03 forbid asserting *"castle by move 10"*. Nothing here asserts it. The expectation
is still **derived from games**, still falsifiable, still reproducible — only from a better-chosen
population. Strong players' timing is evidence about the opening in a way that a teaching heuristic
is not, and it costs one fetch rather than a source for each of 97 families.

**Source:** the public Lichess rapid leaderboard — a stable public list rather than a band this
project picked, so the selection cannot be tuned toward a wanted answer. Public usernames, public
rated games (R-10). `experiments/e58-opening-development/fetch_strong.py`.

## The tolerance, and why it is not optional

> *"The expected moves are not going to be the exact average or median of the higher ranked players
> but average/median + 1/2."*

**This is load-bearing, not a safety margin.** A threshold set at the median flags half the population
by definition — including half of the strong players it was derived from. A claim that fires on 50 %
of correct play is not a diagnosis, it is a coin. The tolerance is what turns *above average* into
*unusually late*, which is the only version worth telling a player.

It also has a natural calibration, which means the choice between **+1** and **+2** need not be
argued:

> **Set the tolerance so that the strong players themselves are flagged rarely.** They are a
> known-good population; the share of *their* games that the threshold calls late is a direct read of
> its false-positive rate.

Proposed target **≤ 25 %**, measured at +1 and +2 before either is adopted. This is the same shape as
`PRECISION_FLOOR = 0.70` in [[experiments.e55-detector-precision]]: a number anchored on a population
whose answer is already known, rather than chosen because it sounds reasonable.

## What is measured

Everything the peer machinery accepts is **instances over opportunities**, and with the expectation
supplying the threshold each measure lands in that shape naturally.

### The window

The opening window is **not** a fixed ply. `OPENING_END_PLY = 30` already exists in S4 and its own
comment admits it is *"conventional rather than derived"*. Here the window is a per-game event:

> **development span** — plies until the player has castled **and** all four minor pieces have moved
> at least once.

### The censoring trap, named before it is fallen into

**A game that ends at move 12 says nothing about how slowly the player develops.** It is
right-censored: development had not finished *and could not have*. Averaging spans over such games
would report the players with the shortest games as the slowest developers — a measurement of game
length wearing the costume of a diagnosis.

Averaging the span is therefore **refused**. Every measure below is a rate over games that *reached*
the relevant ply, which is censoring-safe and fits `ConditionMeasurement` unchanged.

**E58 committed this error one level up**, in the analysis rather than the measurement: its first
median counted only the games where castling happened, and reported Bishop's Opening at move 11 while
47 % of those games never castled at all. The survival median that replaced it moved that cell to 17.
Worth recording because the measurement module was *already* built to avoid this, and the mistake
happened anyway in the script that consumed it.

### Four measurements

Each compares one game against the expectation **for the opening that game was**, and counts how
often the player is past it:

**Screened 2026-08-30** — [[experiments.e59-strong-player-expectation]]. Standardised for the
opening mix, so a difference in repertoire cannot masquerade as a difference in play:

| claim | standardised gap | openings | AUC | verdict |
|---|--:|--:|--:|---|
| `slow_development` | **+10.6 pp** | 32/36 | **0.76** | **ships — headline** |
| `late_castling` | **+9.8 pp** | 30/36 | 0.73 | **ships** (r = 0.68 with headline, under the ceiling) |
| `repeat_move_in_opening` | +2.0 pp | 26/36 | 0.70 | ships at half the strength first measured |
| `pawn_moves_in_opening` | −0.13 count | 17/36 | — | **dropped as a rate** — but see below |

> **The pawn claim may return in a different form.** E59 dropped it because the *rate* does not
> discriminate: 1600s push the same number of pawns as 2600s once the opening is held fixed. But
> [[experiments.e61-habit-cost]] finds those pawn moves **cost** a median 12.8 wp/game — 22 % of
> all opening loss, at r = 0.64 with the general error rate. Same number of pawn moves, worse
> ones. That is a different claim from the one dropped and it has not been tested.

| | claim | instances | opportunities |
|---|---|---|---|
| **headline** | `slow_development` | games developed later than `E_develop(opening) + tolerance` | games reaching that ply |
| explains it | `late_castling` | games castled later than `E_castle(opening) + tolerance`, or never | games reaching that ply |
| explains it | `repeat_move_in_opening` | moves in the window that move an already-moved piece | moves in the window |
| explains it | `pawn_moves_in_opening` | pawn moves in the window | moves in the window |

The last two have no natural *"+2 moves"*, being shares rather than times, so their expectation is the
strong players' share for that opening and the tolerance is expressed in the same units — settled
by the same calibration.

## When nobody strong has played the opening

> *"The peer calculation here for some players that play the openings that no other players from the
> corpus play will be calculated against their own average/median, not by something that can be
> explained by population."*

E58 measured why this matters: **97 families, and only 26 clear 20 games** even in the pooled corpus.
The tail is not an edge case, it is most of the list.

**The fallback is the player's own median across their other openings**, and it must be labelled as a
different claim rather than quietly substituted, because **it answers a different question**:

| | says |
|---|---|
| against the expectation | *you are late by this opening's standard* |
| against the player's own median | *you are later here than you are in your own other openings* |

The second cannot say the timing is wrong — only that it is unusual for this player. Presenting both
in the same sentence would put two different kinds of evidence behind one claim, which is the failure
[[decisions.0011-detection-correctness-over-expert-agreement]] was raised about.

**Two degenerate cases that must not silently produce a claim:**

- **a player with one opening** has no own-median to compare against either, and gets nothing;
- **a player with two openings** has a median of two numbers, which is a difference and not a norm.
  A minimum of distinct openings is required before the fallback runs, proposed at **3**.

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
- **`slow_development` against `plies_in_book`** — no longer to decide 1a's life, since it is
  feedback rather than a competing claim, but because a strong correlation would mean the swarm can
  say *why* a player leaves book early instead of only that they do.

**Only claims that survive the screen are built.** Designing four and shipping two is the expected
outcome, not a failure.

## What still needs calibrating

| needs calibrating | first proposal | how it gets settled |
|---|---|---|
| **tolerance** above the strong-player median | +1 or +2 moves | the share of *strong players'* own games each flags; target ≤ 25 % |
| how strong is "knows the opening" | top-200 rapid leaderboard (~2500+) | opening coverage: if elite repertoires miss the families the subjects play, an arena band is added |
| minimum strong games before an opening has an expectation | 20 | how many families clear it |
| minimum distinct openings before the own-median fallback runs | 3 | a median of two numbers is a difference, not a norm |
| does a **queen** sortie count as development | no — minors and castling only | measure both; the early queen is the classic beginner error and may deserve its own claim |
| what counts as "already moved" for a repeat | the piece's second move onward, tracked from its origin square | fixture positions, hand-checked |
| opening granularity for peer cells | ECO letter (A–E), falling back to band-wide | cell occupancy across the peer corpus |
| correlation ceiling before a claim is cut | \|r\| > 0.85 | E10 used judgement at 0.917; this makes it a stated threshold |

## Testable

1. **It must name a different set of players than `early_error` does.** If it names the same twelve
   it has been renamed rather than corrected — the same test correction 1 already carries.
1b. **The tolerance must flag the strong players rarely.** They are the population the expectation
   came from; if the threshold calls a quarter of *their* games late, it is measuring something other
   than knowing the opening.
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

- **Development is not a virtue in itself, and the strong-player expectation makes this sharper.**
  Strong players develop faster because they are better at chess, not only because they know the
  opening, so some of the gap is unreachable by instruction. The peer step is what keeps this
  honest — *how often are you late compared to others who are also not 2500* — and the correlation
  screen is what tests whether anything is left after that.
- **Elite repertoires may not be the subjects' repertoires.** If the top 200 rarely play the openings
  a 1600 plays, the expectation will be thin exactly where it is needed, and the own-median fallback
  will carry more of the load than intended. Measured before the claim is wired up.
- **"All four minors have moved" is a crude proxy for developed.** A knight on a3 has moved and is
  not developed. Square quality is deliberately not judged, because judging it needs exactly the kind
  of asserted rule this design exists to avoid.
- **The censoring remedy costs data.** Rates over games reaching ply K discard short games entirely,
  and short games are not a random sample — they are the decisive ones.
- **None of it is measured yet.** Every number in this note is a proposal.
