---
id: cas-design-opening-book-naming
title: 'Design — The opening book names lines; it does not know what people play'
desc: 'Measured: 3,810 named lines, median depth 9 plies, but 85 per cent of in-book positions have at most one known continuation. It is a list of corridors, not a tree, so "did you leave theory" really asks "did you match one recorded path". Fixing out_of_book means a different kind of source, not more of this one.'
updated: 2026-09-13
created: 2026-09-13
---

# Design — The opening book names lines; it does not know what people play

**Serves:** V4, V8, C1 · **Follows:** [[experiments.e47-opening-knowledge]],
[[experiments.e76-leaving-theory]] · **Status:** **measured** — no build proposed yet

## The author's question

> *"I would like you to see how to update the book that is currently available, what is the
> structure, how the system checks opening branching to the variants, how many variants there are and
> what is the move depth that most of them have?"*

Asked after four `out_of_book` rejections that all read *"this is a variant of the …"*.

## What the book is

`data/openings/book.json`, built by `experiments/e47-opening-knowledge/fetch_book.py` from
**`lichess-org/chess-openings`**, CC0. Four keys:

| key | |
|---|---|
| `source` | the GitHub URL |
| `licence` | `CC0-1.0` |
| `openings` | **3,810** entries: `{eco, name, epd, plies, pgn}` |
| `in_book` | **7,854** EPDs — every position *along* every line, not only its end |

An entry is one **named line**: `{"eco": "A00", "name": "Amar Opening", "plies": 1, "pgn": "1. Nh3"}`.
`OpeningBook` keeps `_by_epd` (position → name, for the 3,810 endpoints) and `_in_book` (the 7,854
positions that count as theory).

## How the system checks it

`OpeningBook.walk` replays a game and tracks the **deepest** ply whose position is in `_in_book`:

```python
for index, uci in enumerate(moves[:max_plies]):
    board.push(move)
    if board.epd() in self._in_book:
        plies_in_book = played          # deepest, not first
    if (named := self._by_epd.get(board.epd())) is not None:
        deepest = named
exit_ply = plies_in_book + 1            # the ply blamed
```

It deliberately does **not** stop at the first unnamed position, because the book has gaps and a game
can pass through one and back in. The exit is the ply after the deepest hit, and
`left_book_themselves` then drops the game when that ply was the opponent's.

**There is no branching check anywhere.** Membership is a set lookup per position. Nothing asks what
else could have been played.

## The measurements

### Depth — the lines are not shallow

| | |
|---|--:|
| median | **9 plies (move 5)** |
| mean | 9.7 |
| max | 36 |
| lines ending inside the 10-ply window | **2,337 of 3,810 (61 %)** |

The distribution peaks at 6–10 plies. So the *lines* reach move 5 typically, which is the whole window
`out_of_book` measures.

### Branching — and here is the problem

Known continuations per in-book position, sampled 2,000 of 7,854:

| continuations | positions | |
|---|--:|---|
| **0** | 580 | 29 % — a dead end |
| **1** | 1,113 | 56 % — one recorded reply |
| 2 | 207 | 10 % |
| 3 | 59 | |
| 4+ | 41 | |

**85 % of in-book positions have at most one known continuation.**

## What that means

**The book is a list of corridors, not a tree.** Each named line is a path; a position has a second
child only where two named lines happen to share a prefix. After `1.d4 d5 2.Bf4` — a named position,
*Queen's Pawn Game: Accelerated London System* — the book knows exactly **one** Black reply, `c5`.
`2…Bf5` and `2…c6`, both entirely normal, are out of theory by construction.

So *"did you leave known theory"* is really asking **"did your game match one recorded path"**. A
player following a perfectly ordinary line leaves the book the moment they diverge from the exact
recorded move — by transposition, by an equally main-line alternative, or by the reply the database
simply never listed.

**This is why the book cannot be "updated".** It is already the complete CC0 reference: all five TSVs,
nothing missing from the fetch. Adding lines from the same source adds more corridors. The resource
answers *"what is this opening called"* — which it does very well, and which is what
[[experiments.e47-opening-knowledge]] adopted it for — and it was then asked *"what do people play
here"*, which it was never built to answer.

**The author already framed the right question**, twice, without naming it:

> *"It is not the most popular move in the slav formation but it is not a significant loss in wp."*

> *"if it is suspected to be an out of book move then it should have at least significant loss in wp"*

They are thinking in **move popularity**, not line membership. The book has no popularity data at all.

## What a fix would need

A **position → move-frequency** table: for a position, which moves people actually play and how often.
That turns the claim from *"you diverged from a recorded path"* into *"you played a move almost nobody
at your level plays"*, which is what the claim has always meant to say.

Three routes, none built, none costed beyond a first look:

1. **Lichess opening explorer** — free HTTP API, gives move counts per position for a rating band and
   speed. Exactly the right shape and already band-aware, which this project needs anyway. Costs a
   network call per position, cacheable the way evaluations are; licence and rate limits need
   checking before anything is designed on it (C1, C7).
2. **Derive it from the peer corpus this project already has.** No new dependency and no network: the
   corpora behind the peer reference are real games at the target band. Thin in rare lines, which is
   the same problem one layer down — and measurable, since the corpus is on disk.
3. **Keep the book for naming and drop the theory claim.** `out_of_book` becomes *"you played an
   unusual move early"* judged by frequency, or is retired the way `out_of_book.any` already was.

## The interim rule, and why it is now better motivated

The *"do not charge a deviation where the book offered no real choice"* rule (≤1 continuation) was
proposed before these numbers existed. They support it and also cut it down to size: at **85 %** of
in-book positions there is no real choice, and **46 %** of the reviewed games' deviations happen at
such a node. It is a reasonable patch on a resource being used for the wrong question, and it is not a
fix for that.

## Open questions

1. **What does the Lichess explorer actually permit?** Licence, rate limit, and whether a bulk
   download exists. Answerable in an afternoon and blocks route 1.
2. **How thin is the project's own corpus per position?** Route 2 needs no permission and is
   measurable today.
3. **Is `out_of_book` worth keeping at all?** It has never separated players in the register, and the
   per-family baseline ([[experiments.e55-detector-precision]]) was the first thing that made it
   defensible. If a frequency source is a week of work, retirement is the honest alternative.
