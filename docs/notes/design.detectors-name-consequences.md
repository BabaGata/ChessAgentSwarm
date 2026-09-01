---
id: cas-design-consequences
title: 'Design — six detectors renamed, rebuilt or retired, because they name positions instead of consequences'
desc: 'The author corrected six detectors at once. Five share one fault: they fire on a state of the board rather than on something that happened to the player. The sixth is uninformative and is retired. Specifications, testable rules, and the parameters that still need calibrating.'
updated: 1788210000000
created: 1788652800000
---

# Six detectors, corrected

**Source:** the author, 2026-08-29, reading the precision sheet ·
**Status:** **5 of 6 built, and the sixth is screened and held.** 1a was superseded by [[design.opening-development-signals]] and is built; **1b is implemented, tested and NOT shipped** — it fails a depth sweep, naming four of five players inconsistently across window sizes ([[experiments.e73-opening-scores]]). `early_error` therefore stays, on evidence

## The fault they share

Five of the six fire on a **state of the board**, and a state is not something that happened to
anyone. Two pieces are attacked. A rook stands on the seventh. Two pawns share a file. Each is true
and none of it is a finding, because none of it says the player **lost** anything or **could have
done otherwise**.

Every correction below adds one of exactly two things:

- **a consequence** — and it actually cost material, and the loss was forced;
- **an alternative** — and it could have been prevented, or it persisted long enough to matter.

This is [[design.informative-claims]]'s D22 one level down. D22 said a claim naming a *circumstance*
is not actionable and one naming a *behaviour* is. This says the same of the detector beneath it:
**a detector recognising a position is not a finding; one recognising a consequence is.** Worth
holding when the next detector is written, because the fault is invisible in a unit test — every one
of these matches its own stated definition exactly.

---

## 1. `early_error` → an opening-knowledge claim

> *"Early error should be totally reformatted as opening error, meaning player knowing less number of
> an opening moves than peers and losing more often when playing some opening then another. Keep
> track that main openings of the players would be played much more often then other openings by the
> same player."*

**Now:** counts any diagnosable error inside a fixed opening window. The author marked it **0/4** —
*"fires on real errors, explains them wrongly"*. It names a circumstance ("you go wrong early") and
the player cannot act on it.

**Two separate claims replace it**, and they must not be merged:

**1a — you leave theory earlier than your peers.** `BookWalk.plies_in_book` already exists and the
CC0 book is loaded; what does not exist is a **peer baseline for book depth**. That is new work on
the peer corpus, not a threshold change.

> **Superseded 2026-08-29 by [[design.opening-development-signals]].** The author proposed measuring
> opening knowledge as **development behaviour** — castling time, development completion, repeated
> piece moves, pawn moves — instead of book depth. It is cheaper (no book walk over the peer corpus),
> more actionable (*"you moved a piece that was already out while a knight sat at home"* names
> something repairable this week; *"you left theory at move 6"* names a moment), and it fires on a
> deviation from peers rather than on a state of the board, which is the fault this whole note
> corrects. **1a is held, not deleted**: a correlation screen against `plies_in_book` decides whether
> book depth has anything left to add.
>
> **Screen run 2026-08-31 → [[experiments.e75-book-depth]]. Book depth survives it.** Over 84 players
> it is **reliable** (split-half r = **+0.81**), **distinct** from every development claim (strongest
> is `slow_development` at **−0.47**, far under E69's 0.85 ceiling) and **not merely rating**
> (+0.37, weaker than two of the development claims). So 1a is not redundant — but **redundancy was
> never the argument against it**, and the two that were, actionability and cost, are untouched. One
> new fact bears on them: the median player leaves theory after **5.3 plies, under move 3**, and the
> whole spread across 84 players is about six plies. A claim here would say a player leaves theory a
> move and a half earlier than their peers.

**1b — you score worse in this opening than in your others.** This is **A3**, already on the list as
unstarted and free, and it merges here rather than staying separate.

> **Built and held, 2026-08-31 → [[experiments.e73-opening-scores]].** `chesscoach/opening_scores.py`,
> 20 tests, wired into nothing. It fires for 2 of 12 players and both findings read well — bernes
> scores **29 % over 19 Caro-Kann games against 60 % over 39** elsewhere. Two screens then went
> against it. The note's own acceptance test is **PARTIAL**: both players it names are already named
> by `early_error`, a strict subset rather than a different set, so `early_error` cannot be retired in
> its favour. And a depth sweep from 15 to 60 games is **fatal**: four of the five players it names
> flip in and out, nobody is named at 30 games and four are at 45. R-13 forbids writing down an
> association that has not reproduced. Held rather than deleted — the instability may be sample size,
> and every corpus on hand stops at 60 games.

**The author's own caveat is the hard part.** A player has two or three main openings and a long tail
played once or twice. Comparing raw scores across them would rank the tail on noise every time. So
1b needs a **minimum games per opening** before an opening may be compared, and the comparison must
be against *that player's own* other openings rather than a population.

| needs calibrating | first proposal | how it gets settled |
|---|---|---|
| minimum games before an opening is comparable | 5 | **settled at 5, 2026-08-31 — and the stated method would not have found it.** The distribution argues for 3 or 4, because 5 discards 47 % of games; what settles it is which floor admits a defensible finding, and below 5 every extra separation is *0 % over 3 games* |
| how much worse counts as worse | Wilson intervals must not overlap | already the project's method elsewhere |
| book-depth baseline | per band and speed | rebuild peer stats with `plies_in_book` |

**Testable:** on the review twelve, 1a must name a *different* set of players than the current
`early_error` does. If it names the same people it has only been renamed.

---

## 2. `advantage_error` → retired, not deleted

> *"Advantage error should be totally removed, or kept for future but not used nor calculated. It is
> completely uninformative. It could be used only to check if there are tests for the origin of those
> kind of errors like improper defense or something like that."*

**Now:** fires 182 times across 6 players, the second-commonest claim in the system. The author
marked all five examples `?` — it fires on real errors and names nothing.

**Decision: stop calculating it, keep the code.** Not deleted, because the author named a future use
— as a *pointer* to whether the origin of such errors is detected elsewhere (improper defence and the
like), which is a question about coverage rather than a claim about a player.

Retiring rather than deleting also keeps the option cheap, and deleting a section is the kind of
thing that is easy now and expensive to reverse in three weeks.

**Testable:** it appears in no profile and costs no compute. The 182 instances stop being counted,
which will change the arbiter's ranking for the six players it fires on — **that change must be
inspected, not assumed harmless.**

---

## 3. `fork` — the definition is wrong

> *"Forks are moves that occur when at least 2 pieces were newly (so they weren't attacked before)
> attacked by one single piece after moving that piece and the result is definite loss of material."*

**Now** (`tactics.py:_is_fork`): the moved piece attacks two things "worth winning" and lands safely.
It never asks whether the attacks are **new**, and never asks whether material is **actually lost**.

**The corrected rule, in four parts:**

1. one piece moves, and **that piece** attacks the targets — not a discovered attack from elsewhere;
2. **at least two targets were not attacked before the move** — new attacks, not a piece wandering
   into an existing double attack;
3. the attacker survives (already implemented, `_lands_safely`);
4. **material is definitely lost** — the defender has no reply that saves both.

**Part 4 is the one that changes everything**, and the author gave the discriminating example:

> *"attacking by knight a rook and a bishop but bishop is undefended and can not be defended by the
> rook, so after moving a rook the bishop will fall or after moving a bishop the rook will fall. If
> bishop was defended the rook could be moved and there would occur only exchange of the pieces, not
> material loss."*

So a fork against two *defended* pieces is not a fork. That is a real search: for each defender reply,
does the best case still lose material? Bounded — the defender's plausible replies are moving either
target, capturing the attacker, or defending — and `wins_material` already exists in `material.py`.

**BUILT — see [[experiments.e57-fork-rebuilt]].** Nine fixtures pass, including the negative
case. Building the positives by hand failed three times: over random positions only **3 of
1,014** knight double-attacks on a rook and bishop are genuine forks, and the old detector
counted all 1,014. The claim now fires **zero** times on the review corpus, down from 146,
which is arithmetically consistent with a rule that strict but is not yet known to be right.

**Testable:** the author's three examples become fixtures — pawn forking knight and bishop one square
apart; knight forking queen and rook; knight forking rook and undefended bishop. **And the negative
case is the important one:** knight forking rook and *defended* bishop must NOT fire.

---

## 4. `allows_square.rook_seventh` — almost always available

> *"Rooks can pretty much always come to the seventh rank if it is a late endgame, not many pieces
> and pawns to block them. So basically whenever there are 3 or more open files there is not much
> possibility to block the opponent... This should be counted only if there was a real opportunity to
> block the rook from coming to the seventh file a move before or 2 moves before."*

**Now:** counts enemy rooks standing on the seventh. Fires 43 times across 6 players and says nothing
about whether it was preventable.

**The corrected rule:** the claim requires a *preventable* arrival.

The author supplied a cheap proxy and a precise one, and they are different in cost:

- **cheap:** if **3 or more files are open**, blocking is impractical — do not fire. Deterministic,
  no search, and it is the author's own stated threshold.
- **precise:** in the one or two plies before, was there a legal move that would have stopped the
  rook arriving? That is a two-ply search over the player's own moves.

**Proposal: implement the cheap screen first and measure how many firings it removes.** If it removes
most of the 43, the precise version has little left to buy. That is the project's usual order and it
avoids paying for a search that may be unnecessary.

> **Both are now built.** The screen removed **52 %** ([[experiments.e66-rook-seventh-and-doubled]]) —
> half, not most — so the search was still owed and is now written and wired
> ([[experiments.e74-rook-seventh-precise]]). Over 72 players and 764 arrivals it removes a further
> **29 % of what reaches it**, at **1.2 ms a search**, running only on arrivals the screen let
> through. The claim fires on **40 %** of arrivals where it once fired on all of them. The staged
> order was right and so was the decision to pay for the second stage.

**Testable:** a late endgame with four open files must not fire. A middlegame where one defensive
move would have covered the seventh must fire.

---

## 5. `concedes_weakness.doubled` — distance and persistence

> *"Doubled pawns are detected for pretty much any capture no matter how far away the pawns are. This
> should be counted only if they are directly one in front of the other or if there is only 1 square
> in between... Also the doubled pawns should be taken in the account if they are able to last for
> more then 3 moves, otherwise, they are in that state just until the end of exchange."*

**Now** (`structure.py:count_doubled`): any two friendly pawns on a file, at any distance, at any
moment.

**Two conditions, both required:**

- **adjacent or one gap** — the pawns are 1 or 2 ranks apart on the same file. A far-advanced pawn is
  usually attacking and about to be exchanged, which is the author's reasoning and is a claim about
  what the position *is for*, not merely about geometry;
- **persists more than 3 moves** — otherwise it is a transient state mid-exchange.

Persistence needs the detector to see **a span of positions rather than one**, which is a structural
change: `count_doubled` takes a board. It will need the game.

**Testable:** a capture that doubles pawns which are re-resolved two moves later must not fire. Pawns
on c2 and c3 surviving ten moves must fire. Pawns on c2 and c6 must not, at any duration.

---

## 6. `endgame_error` — consecutive imprecision, not single losses

> *"Endgame error should be calculated just when there are big drops of the advantage in a few
> consecutive moves. So that it can be seen that the player is imprecise one move after the other and
> lacks knowledge of how to play the endgame. Also, if the sudden loss of the advantage of the one
> move is detected by other motif tests this should not be taken in the account because those are
> tactical losses and this is lack of knowledge of the endgames."*

**Now:** counts any diagnosable error in the endgame. 40 instances across 3 players.

**Two conditions:**

- **a run, not a point** — several consecutive moves each losing advantage. One bad move in an
  endgame is a mistake; three in a row is not knowing the endgame, and only the second is what this
  claim is for;
- **not already explained by a motif** — if a drop is a hung piece or a missed fork, it is a
  *tactical* loss and belongs to S1. Counting it here would say "you do not understand endgames"
  about a player who hung a rook.

The second condition is the more interesting one: it makes this claim **explicitly residual** —
defined as what the tactical detectors do not explain. That is a new relationship between sections
and it needs stating, because it means `endgame_error` cannot be computed until S1 has run.

| needs calibrating | first proposal | how it gets settled |
|---|---|---|
| "big drop" | the existing error threshold | reuse rather than invent |
| ~~"a few consecutive moves"~~ | ~~3 within a 4-ply window~~ | **Settled: 3 in 3, strictly consecutive** ([[experiments.e68-run-calibration]]). Frequency was the wrong question — a permutation test shows 3-in-4 was matched by one shuffle in eight, so it barely told clustering from the error rate |

**Testable:** a single blunder in a rook endgame must not fire. Three consecutive inaccuracies, none
tactical, must. A three-move run where the first drop is a hung piece must count only the other two.

---

## Sequence

Ordered by what unblocks what, not by size:

1. ~~**`advantage_error` retired.**~~ **Done** — [[experiments.e56-retire-advantage-error]].
   Cheapest, and it changes the arbiter's ranking, so it should land
   before anything is re-measured against it.
2. ~~**`fork` rebuilt.**~~ **Done** — [[experiments.e57-fork-rebuilt]], and it now needs the
   author's eye on a few positions before the zero count can be trusted.
   The author's oldest complaint, the clearest specification, and the one whose
   fixtures are already written in their own words.
3. ~~**`doubled` and `rook_seventh`.**~~ **Done** — [[experiments.e66-rook-seventh-and-doubled]].
   The open-files screen removes **52 %** of rook firings, so the precise two-ply search still has
   something to buy — the opposite of what this note guessed. For `doubled` the author's two
   conditions are wildly unequal: distance −17 %, persistence **64 %**. `persistent_doubled` is
   built and tested and **not yet wired into S5**, which needs the span rather than one board.
4. ~~**`endgame_error`.**~~ **Done** — [[experiments.e67-persistence-and-endgame-runs]].
   211 firings become **50**, and the two conditions are unequal again: the residual one removes
   **10 %**, the run condition the rest. Also completes `doubled`'s persistence, which E66 left
   unwired, and extends it to **isolated** pawns on the author's own instruction.
5. **`early_error` → opening claims.** Largest, needs a new peer statistic, and merges A3.

**What this forecloses:** retiring `advantage_error` removes the second-most-frequent claim, and two
players may drop below the coverage floor as a result. That is the correct outcome — silence beats an
uninformative claim — but it must be measured and stated rather than discovered later.

**What none of this touches:** whether these detectors *miss* things. Precision is not recall, and
D15 defect (a) — five claims that never become candidates — is still open and still separate.
