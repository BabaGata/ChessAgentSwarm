---
id: cas-design-informative-claims
title: 'Design — from claims that are true to claims that can be worked on'
desc: 'The reviewer marked four claims. One detector is wrong (0/5, verified), two are true but not actionable, one is fine (4/5). Options for each, compared, with a recommendation and a sequence.'
updated: 1788307200000
created: 1788307200000
---

# Design — from claims that are true to claims that can be worked on

**Answers:** the author's *"see what are the ways to make detection more correct or if what is
detected is not really informative plan on how it could be more informative"* ·
**Status:** design, no code yet · **Feeds:** D17, D19, D20

## What the marks actually say

23 marks on `experiments/e46-motif-precision/results/detection-sheet.txt`, four claims covered:

| claim | ✓ | ✗ | ? | reading |
|---|--:|--:|--:|---|
| `allowed_motif.hangingPawn` | **4** | 1 | 0 | **works.** Leave it alone |
| `advantage_error.clear` | 0 | 0 | **5** | fires on real errors, **names nothing** |
| `early_error.white` | 0 | **4** | 1 | fires on real errors, **explains them wrongly** |
| `moved_into_attack` | 0 | **5** | 0 | **broken** |

**These are three different problems**, and conflating them would produce three wrong fixes. One
detector is incorrect. Two are correct-but-empty. One is fine.

## Problem 1 — `moved_into_attack` is broken, and the cause is verified

All five rejected instances are **captures with `exchange_value >= 0`**, reproduced from the
author's own counterexamples:

| player | move | capture | exchange_value | swap on destination | fires |
|---|---|---|--:|--:|---|
| Maximilian_Honigtopf | bxc3 | yes | **+2** | 1 | yes |
| Odin5306 | Nxg3 | yes | **0** | 3 | yes |
| Odin5306 | **Bxd8+** | yes | **+6** | 3 | yes |
| Odin5306 | Bxf3 | yes | **0** | 3 | yes |
| simonvj | Bxe5 | yes | **+1** | 2 | yes |

`Bxd8+` **wins a queen** and is reported as *"you put the piece you have just moved on a square where
it can be won."*

The code excludes only *losing* captures:

```python
if exchange_value(board, move) < 0 and board.is_capture(move):
    return False
return _swap(after, move.to_square) >= MATERIAL_LOSS
```

An even-or-better capture falls through to a test that measures **the recapture in isolation** and
ignores what was captured. Every ordinary trade fires. The author's word for all five was
"exchange", four times over.

**This is not an option to weigh — it is a fix.** `exchange_value` already nets the whole sequence,
and for a quiet move it equals `-swap` on the destination, so **one test covers both cases**:

- `moved_into_attack` = **quiet** move with `exchange_value < 0`
- `miscounted_exchange` = **capture** with `exchange_value < 0`

A clean partition, no overlap, and it restores what the docstring always claimed.

## Problem 2 — `early_error` explains errors it detects correctly

The author's objection is not that the moves are fine. It is the *story*: "the edge of your
repertoire" around move 15, when *"most players at this level will get out of the opening lines
before move 8 or just until the castling."* Their notes name the real causes — *"white is not
defending the king, that is the issue"*, *"he is out of the opening for plenty of moves already"*.

Three ways to replace the story. All three keep the same detection and change what is concluded from
it.

> **Options A1–A3 were superseded on 2026-08-23 by the author, and the reason is the important part.**
> The peer-derived book (A2) was recommended and is **refused**: *"Checking whether they deviate from
> what they usually do is not something that will help them if what they usually do is not good from
> the beginning."*
>
> That is correct and it generalises. **Peer-relative is the right frame for "is this unusual" and the
> wrong frame for "is this right."** A band that leaves theory at move 6 is not a standard to measure
> against; matching it is not a target. Everything else in this project is peer-relative, which is why
> the mistake was easy to make. Recorded as **L-045**.
>
> A3 survives — it refers only to how the player *fares*, never to what peers *play*.

### The replacement — three layers, all free, all verified to exist

The requirement is not only *where* knowledge ends but *what is missing*: **the main ideas for the
player and the main responses for the opponent**, so the system can teach the ideas rather than
report a deviation.

**Layer 1 — the lines.** `lichess-org/chess-openings`, **CC0 public domain**. Five TSVs, columns
`ECO`, `name`, `pgn`, `uci`, `epd`. The **`epd` column is the key**: entries are keyed by *position*,
so transpositions resolve for free and no move-sequence matching is needed.

**Layer 2 — the ideas.** Wikibooks *Chess Opening Theory*, **CC BY-SA 4.0**. The URL path *is* the
move sequence (`/1._e4/1...e5/2._Nf3/2...Nc6/3._Bc4`), so lookup is direct. Verified on the Italian:
prose plans for the side to move — *"From c4 the Bishop controls d5 and pressures Black's f7-pawn"*,
*"a swift attack on f7 and building a big centre with c3 and d4"* — **and named main responses for
the opponent**: 3…Nf6 Two Knights, 3…Bc5 Giuoco Piano, 3…Be7 Hungarian, 3…h6, 3…d6, 3…Nd4, 3…f5.
Exactly the pair asked for.

**Layer 3 — what opponents actually play at this level.**
`explorer.lichess.ovh/lichess?fen=…&speeds=rapid,blitz&ratings=1400,1600` — free, no auth. Returns
the move distribution **and results** filtered to the player's own band. Theory says what *should* be
played; this says what they will actually face, and at 1500 the two differ.

### What a claim built on these looks like

> *"You play the Scandinavian in 7 of your 20 games. You leave theory at **move 6** — the book
> continuation is …Nf6 — and in 4 of those 7 you were already worse by move 12. The idea you are
> missing: [quoted, attributed]. At your level **38 %** of opponents continue with Bd2."*

Against *"you go wrong early as White"*, that is the whole distance being asked for.

### The costs, stated before anything is built

- **Scope.** A download, a parser, a local store, a cached crawler, position→entry matching, and a
  section to speak it. **Days, not hours** — the largest new capability since the sections themselves.
- **Licence, and it needs an ADR.** CC0 for Layer 1 is unencumbered. **CC BY-SA 4.0 for Layer 2 is
  not**: attribution is mandatory and share-alike propagates to whatever embeds the text. Every stored
  excerpt carries its source URL. This is what keeps the ideas on the right side of **R-03** — quoted
  from a citable source, never generated and **never paraphrased**, because paraphrase is exactly
  where folklore re-enters.
- **Coverage is unknown, and it is the pre-check.** Wikibooks is uneven. **Before building**: take the
  positions the twelve review players actually reach and measure what fraction have a real page. At
  20 % Layer 2 is decoration; at 80 % it carries the claim.
- **Network stays in the outer loop.** Crawl once, cache to disk, never fetch during analysis (C1).

### Comparison

| | actionable | cost | licence | teaches the ideas |
|---|---|---|---|---|
| **L1 lines (CC0)** | high | low | **unencumbered** | no |
| **L2 ideas (Wikibooks)** | **highest** | moderate | CC BY-SA — attribution + share-alike | **yes** |
| **L3 explorer API** | high | low | free API | says what they will face |
| ~~peer-derived book~~ | — | — | — | **refused: a relative reference cannot say what is right** |
| A3 outcome per opening | medium | **none** | — | no — but free, worth doing anyway |

**Recommendation: A3 now, then L1 + L2, L3 last.** A3 is nearly free and ships regardless. **L1 is
load-bearing** — it turns "you go wrong early" into "you leave the Scandinavian at move 6", the whole
change in kind, and CC0 means no licence question. **L2 is what was actually asked for**, gated on the
coverage pre-check. L3 is the smallest addition and the easiest to defer.

L1 with A3 gives the distinction, now against theory rather than against the band:

| left theory | outcome | conclusion |
|---|---|---|
| early | worse | **the line** — learn more of it, and L2 supplies why the moves matter |
| late | worse | **the ideas** — knows the moves, not the plans. L2 is the whole answer |
| early | fine | nothing to say. Leaving theory early is not a fault by itself, and a claim treating it as one would measure conformity rather than skill — the error the peer book made |

## Layer 2 refused on reading — the prose is the wrong genre

The harvest succeeded and the author read it and rejected it:

> *"These ideas are better in explaining what happened than what should be focused on for the rest of
> the game. They also use sentences that are not really easily understandable for players at 1500 and
> they should make some conclusions based on the understanding they don't currently have."*

All three parts check out against the text. The Caro-Kann entry says the structure *"resembles a
Carlsbad structure with reversed colours, so some of the strategic ideas are analogous to the Queen's
Gambit Declined, Exchange Variation"* — unusable for someone who does not already know both of those.
The Italian entry is 33 words of move description. Even the strong Sicilian entry annotates the
**position** rather than prescribing a **plan**.

**Wikibooks *Chess Opening Theory* is theory annotation, not plan instruction**, and the two are
different genres. Wikipedia is no better: it is encyclopedic, reaches for the same Carlsbad
comparison, and assumes tempo, transposition and compensation.

**And the genre that is wanted appears not to exist under a free licence.** Everything aimed at
improvers with explicit middlegame plans — Chess.com lessons, Chessable, thechessworld,
chessatlas — is commercial, which C7 and R-03 both rule out. That is a real negative and worth
recording so it is not searched for again.

### What can replace it

**Option 1 — plans from what stronger players actually do.** `fetch-corpus --band LOW-HIGH` already
exists. From the position where the player leaves theory, show what **2000–2200** players do over the
next few moves: where the pieces go, when they castle, which pawn break arrives.

- **Zero jargon**, because it is expressed in moves, which the player already understands.
- The reference is **stronger players, not the band** — so L-045 is respected; this is not "what your
  peers do".
- Cost: one corpus fetch of 30–50 players with machinery that exists.
- **Weakness, and it is the important one: it shows *what*, not *why*.** A move list is not an idea,
  and the author's objection was precisely about ideas.

**Option 2 — the author writes the plans, for the fifteen openings that actually occur.** Evidence
class: named expert opinion, which `capacity.knowledge` already supports. Bounded at fifteen short
entries. Correct for the audience by construction, because a strong player is writing *for* 1500
rather than for an encyclopedia.

- Cost: **the author's own hours**, at a point when they were weighing whether to stop and write up.
- Does not generalise past these twelve players' repertoires.

**Option 3 — drafted by a model, verified and signed by the author.** Cheaper in author time.
**R-03 forbids folklore laundering**, and "verified by a named expert" is a genuinely different
evidence class from "generated" — but a thesis that defends a no-folklore rule and then ships model
text needs a very explicit account of the verification. **Would require its own ADR**, not a quiet
decision.

### Recommendation

**1 and 2 compose, and neither is sufficient alone.** Option 1 supplies *what* stronger players do —
free, scalable, no jargon. Option 2 supplies *why*, for the small set that matters. Together they are
"what to focus on for the rest of the game" in plain terms, which is the requirement.

**If only one: Option 2.** It meets the objection directly and is bounded. Option 1 on its own risks
delivering a move list, which is what the rejected prose already effectively was.

### Searching opening by opening — the author was right, and it does not solve the licence

The generic search was the wrong search. Asked about **one** opening, the web returns exactly the
register wanted:

> *"Your light-squared bishop must come out before playing …e6, otherwise it stays locked in for the
> entire game."* · *"In the 3…Qa5 variation, queenside castling is often the best plan… castling
> queenside immediately posts your rook on the d-file."* · *"Black will have to fight against the pawn
> on d4, by breaking the centre with e5 or c5."*

Plain, prescriptive, forward-looking, no assumed vocabulary. **This content exists in abundance, per
opening.**

**And none of it is licensed.** albertochueca.com, kingdomofchess.com, chessforsharks.co,
chessdoctrine.com, chesscheatsheets.com — all copyright. Even `freechesstrainer.org`, which sounds
promising, states plainly `© FreeChessTrainer.org` with **no licence declaration**: free to *read*,
not free to *reuse*.

**Books, checked because the author asked.** Public-domain chess books are 19th century — Staunton's
*Blue Book*, Edward Lasker. They predate almost every opening these players actually play; the
Scandinavian Modern, the Caro-Kann Advance Short and the Najdorf did not exist as named lines. They
would be **wrong**, not merely dated. Archive.org carries modern opening books (Seirawan, Batsford,
MCO) but **lends** them — that is not a licence.

### The conclusion this forces, and it is a better architecture

The good material cannot be **copied**. It can be **pointed at**.

> *"You play the Scandinavian in 7 of your 20 games and leave theory at move 4. In this line the
> light-squared bishop is the whole problem — it has to come out before …e6. A guide to the plans:
> ⟨link⟩."*

- **No licence issue.** Linking is not redistribution.
- **No folklore risk (R-03).** The system asserts nothing about chess; it says where the player left
  theory — which it measured — and routes to instruction it did not write.
- **Costs almost nothing:** a curated map of the ~15 openings that occur → one or two URLs each.
- **It is the honest division of labour.** This project's expertise is *measurement*, not chess
  pedagogy. A system that diagnoses precisely and then hands over to someone who teaches well is more
  defensible than one that paraphrases a blog and calls it knowledge.

**Weaknesses, stated:** link rot; quality varies by site; and **curating is endorsing**, so the fifteen
choices are the author's judgement — fifteen decisions rather than fifteen essays.

## Layer 3 after the outage — what else could supply it

`explorer.lichess.ovh` is **401 on every endpoint** (`/lichess`, `/masters`, `/player`), down since a
February 2026 infrastructure incident (R-17). `lichess.org/api` and `database.lichess.org` are both
**up**, so the data exists; only the ready-made service is gone.

**First, a distinction that matters, because it looks like a rejected idea returning.** The
peer-derived book was refused for Layer 1 because that layer is **normative** — it must say what is
*correct*, and a band cannot. Layer 3 is **descriptive**: *"what will you actually face."* A
peer-derived answer is not a second-best there, it is the **only** kind of answer that is even
meaningful. L-045 does not apply.

### A — the corpus already on disk

3,908 games from 137 players at 1400–1800, indexed in seconds. Measured against the 240 book-exit
positions these players actually reach:

| peer games at the exit position | share |
|---|--:|
| at least one | 89 % |
| more than 5 | 59 % |
| more than 20 | 35 % |
| more than 50 | 19 % |
| **median** | **8** |

**Eight games cannot carry a percentage.** *"38 % of opponents play Bd2"* from a sample of eight is
three games and a rounding error. It could support *"the most common continuation among players at
your level"*, and even that is shaky at n = 8. **Too thin as it stands.**

### B — the Lichess monthly database dump

`database.lichess.org`, **CC0**. July 2026 is 3.27 GB compressed, **12.3 million games**; January 2013
is 374 MB. Filterable to band and speed while streaming, and **it does not have to be read to the
end** — stop once enough in-band games are collected, which cuts the real download well below the
full file.

Roughly 100,000 in-band games would put ~200 games on a typical exit position, which *is* enough to
quote a share. That is about 25× the current corpus and a small fraction of one month.

**Old months are not a substitute for recent ones.** 2013 is cheap and describes a different
population — different rating distribution, different opening fashions. For *"what you will face"*,
recency is part of the claim.

### C — fetch more players through the working API

The project already has `fetch-corpus`, and `lichess.org/api` is up. But reaching ~100,000 games means
roughly 3,300 players at 30 games each, against API rate limits — far slower than one dump for a
worse result.

### Comparison and recommendation

| | games available | enough for a percentage | cost | freshness |
|---|--:|---|---|---|
| A own corpus | 3,908 | **no — median 8** | none | current |
| **B monthly dump** | 12.3 M | **yes** | one partial download | current |
| C API fetch | ~100 k | yes | very slow | current |

**Recommendation: B, and only if Layer 3 is wanted at all.** It is the only option that supports the
sentence the layer exists to say, the licence is CC0, and streaming means the cost is a fraction of
the 3.27 GB.

**But the sequencing does not change.** Layer 3 was always last and easiest to defer, and Layers 1
and 2 are built and carry the claim without it. A3 and the `moved_into_attack` fix are both cheaper
and both unstarted; they come first.

## Problem 3 — `advantage_error` detects real errors and names none

Every one of the five is `[?]`, and the author's notes are the answer: *"didn't defend pawn
properly"*, *"allowed black to deform his pawn structure"*, *"didn't defend king properly"*,
*"deformed pawn structure"*, *"didn't defend king properly"*. **They are not unsure whether the
moves are errors. They are unsure what the claim is telling them.**

### B1 — Say what the error was, conditioned on being ahead

Intersect the existing per-move detectors with "the player is winning". No new detector.

> *"When you are already better, your mistakes are king-safety mistakes — 6 of your 9."*

- **Cost:** near zero. A conditioning and composition step over detectors that exist.
- **Risk:** each (player × ahead × error-kind) bucket is small and may not clear the confidence gate.
  That is a real possibility and it is measurable before committing.
- **Fit:** three of the author's five notes are king or pawn defence. This is their observation,
  mechanised.

### B2 — A defensive resource was available and was not played

Detect that the engine's best move **defended** something under threat and the player's did not.

> *"In 7 of your winning positions there was a move that dealt with the threat, and you played
> something else."*

- **Cost:** moderate — needs a "this move defends" predicate, which does not exist.
- **Risk:** lower than it looks. L-042 says claims about what *befell* the player are the error rate
  renamed, while claims about what the player *did* are independent — and "played the ambitious move
  instead of the safe one" is action-shaped, so it has a real chance of surviving the screens.
- **Fit:** the closest literal match to *"you forget to defend."*

### B3 — Conversion ("you fail to convert winning positions")

**Refused before it is built.** It restates the outcome in different words and is exactly the shape
the author is objecting to. Recording it so it is not proposed again.

### Comparison

| | actionable | cost | new detector | survives the screens? |
|---|---|---|---|---|
| B1 name the error kind | high | **none** | no | **unknown — measurable first** |
| B2 defensive resource | **highest** | moderate | yes | plausible (L-042) |
| B3 conversion | low | none | no | irrelevant — refused |

**Recommendation: B1 first**, because it costs nothing and its whole risk (thin buckets) can be
measured before a line of production code is written. **B2 if B1's buckets are too thin**, which is
the likely outcome and worth knowing early.

## Sequence, and why this order

1. **Fix `moved_into_attack`** — verified defect, one-line test change, largest precision gain
   available. Then re-run the sheet so the author re-checks a detector that has actually changed.
2. **Screen B1** — cheap, and it either supplies `advantage_error`'s missing content or rules itself
   out in an afternoon.
3. **Build A3** — free, uses discarded data, improves the weakest-explained claim.
4. **Screen A2** — the one genuinely uncertain piece, and the one that makes A3 actionable.
5. **B2 / A1** only if 2 and 4 fail.

**What this does not touch:** `allowed_motif.hangingPawn` scored 4/5 and should be left alone. The
temptation to improve a working detector while the tools are out is how a 4/5 becomes a 2/5.

## The rule underneath all of this

The author's objection generalises past these two claims: **a claim that names a
*circumstance* is not actionable; a claim that names a *behaviour* is.** "You go wrong early" and
"you go wrong when winning" are circumstances. "You leave the Scandinavian at move 7" and "when
ahead, you stop defending the king" are behaviours. Every future claim should be read against that
test before it is built — and several shipping claims would fail it, which is worth its own pass
later.
