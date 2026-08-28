---
id: cas-exp-e50
title: 'E50 — The 1.9 GB model beat the 5.2 GB one, and the checker caught a real hallucination'
desc: 'SearxSearcher works live, 6 of 6. qwen2.5:3b rephrases the quoted plans at 88 % accepted, 18 % novelty, 3.6 s — beating qwen3:8b on every axis. The grounding gate rejected an invented square in real output, and a subject swap got through.'
updated: 1788480000000
created: 1788480000000
---

# E50 — Can a local model make the quoted plans read as one voice?

**Answers:** the author's *"utilisation of ollama to handle this agent, perform web searches and
combine the information in a few sentences that sound natural"* · **Code:**
`chesscoach/grounding.py`, `chesscoach/opening_summary.py`, `experiments/e50-ollama-summaries/` ·
**Date:** 2026-08-28 · **Status:** done — **adopted, with the hole stated**

## Part 1 — `SearxSearcher` works against a live instance

[[experiments.e48-opening-agent]] shipped it with the caveat *"untested against a live instance"*.
A SearxNG container (`experiments/e50-ollama-summaries/searxng/`, ~200 MB) removes it:

| | |
|---|--:|
| uncovered openings asked about | 6 |
| **openings with at least one candidate** | **6 (100 %)** |

**And finding a link is still not finding a guide.** The Grob returned a *Duolingo blog post* and a
chess.com forum thread. E48's result survives contact with real search: the searcher cannot tell a
guide from a listicle, which is what the extractor and the author's review are for.

The `json` format must be enabled in `settings.yml`; SearxNG serves HTML only by default and returns
a body with no `results` key otherwise — which is why the searcher raises naming that setting rather
than reporting "found nothing" (L-046).

## Part 2 — the benchmark, after a harness bug was corrected

| arm | composed | novelty | per opening |
|---|--:|--:|--:|
| quotes (the floor) | — | — | 0.0 s |
| **`qwen2.5:3b` (1.9 GB)** | **88 %** | **18 %** | **3.6 s** |
| `qwen3:8b` (5.2 GB) | 38 % | 38 % | 8.2 s |

**The smaller model wins on every axis**, which is also the C1 answer: 1.9 GB fits beside Docker and
a desktop on a 15.7 GB machine, and 5.2 GB does not.

**A high acceptance rate is not a good result on its own** — a model that copies its input scores
100 % and achieves nothing. Read with novelty at 18 %, it says the rewrites are genuinely rewrites.

### The first run said qwen3 scored 0 %, and that was this harness

`qwen3:8b` returned **0 % composed with 0 % novelty and no rejection reason** — the signature of an
*empty* response, not a rejected one. Probing the raw API:

    num_predict=220             thinking 1008 chars, response 0 chars, done_reason "length"
    num_predict=900             thinking 1625 chars, response 273 chars
    num_predict=900 think=False thinking    0 chars, response 284 chars, 59 tokens

**The token budget was being spent entirely on a separate `thinking` field.** A fact about the
harness was one edit away from being written down as a fact about the model — the fourth time this
pattern has appeared (L-046), and the reason the probe was written before the note.

Thinking is now off by default: there is nothing to reason about in rephrasing supplied sentences,
so deliberation is cost without benefit.

## Part 3 — the checker earned its place on its first real run

`qwen2.5:3b`, Italian Game:

> REJECTED: names moves not in the source: **f6**

The model invented a square. The rewrite was dropped and the player would have read the publisher's
own sentences instead — **the fallback path, exercised by a real failure rather than a fixture.**

## Part 4 — and one got through, which matters more

Caro-Kann. The source said:

> *"**Each** creates a different type of pawn structure and middlegame plan."*

The rewrite said:

> *"**Black** creates a different type of pawn structure and middlegame plan."*

Every word and every square is the source's; only the **subject** changed. Both checks pass. This is
the hole [[decisions.0013-a-local-model-may-rephrase-what-it-cannot-assert]] predicted, found in
real output on the first run, and it is why `grounded` never means *correct*.

The adversarial case pinned in the tests is the same shape and worse: swapping White and Black
throughout passes both checks against a page saying the opposite.

## Part 5 — the stray finding was a structural defect, not a typo

The Indian Defense summary described the London System. The candidate entry's own title asserted
why — *"(the structure these games reach)"* — so it was a claim, and it half held:

| | |
|---|--:|
| games classified `Indian Defense` | 10 |
| **reaching a London (early Bf4)** | **5 (50 %)** |

4 of them are named `Indian Defense: Accelerated London System` outright.

**Half right is worse than wrong here.** A family-wide London guide is correct for five players and
misleading for five, and the misled five have no way to tell.

**The unit was the defect.** `Indian Defense` is `1. d4 Nf6` — a move, not something anyone sits down
to study. And it is systematic: the Sicilian candidates include a **Chess Doctrine Alapin page**,
right for 7 of 16 games and wrong for the other 9 (McDonnell, Old Sicilian, Bowdler, Taimanov).

So `for_opening` now honours **subline scope**: a guide naming a subline reaches only players who
play it, and sorts ahead of family-level guides — which is what its docstring always claimed and
never did. `build_resource` asks with the player's **most-played line** rather than the bare family.
The London entries are re-keyed under `Indian Defense: Accelerated London System`, so a Przepiorka
player is now told nothing, which is the right answer.

**The Sicilian is left for the author.** Deciding which Alapin page covers `Delayed Alapin Variation,
with d6` is curation, not code, and the mechanism is now there for it.

## Part 6 — and the main line was wrong for the same family

With the mapping fixed, the Indian Defense still printed
**`MAIN LINE 1. d4 Nf6 2. c4 e6 3. Qb3`** — an obscure sideline the source data also names plainly.

E49's rule took the *deepest* row carrying the family's bare name. Checking whether those rows form a
chain does not catch it, because this one **is** a continuation of `1. d4 Nf6`. What marks it is the
**jump**: three plies in one step, where the Pirc and Sicilian advance one or two at a time.

`MAX_MAINLINE_STEP = 2`, and the walk stops at a bigger gap:

| family | main line |
|---|---|
| Indian Defense | `1. d4 Nf6` ✔ corrected |
| Pirc Defense | `1. e4 d6 2. d4 Nf6 3. Nc3 g6` ✔ unchanged |
| Sicilian Defense | `1. e4 c5 2. Nf3 d6 3. d4 cxd4` ✔ unchanged |
| French Defense | `1. e4 e6 2. d4 d5` ✔ unchanged |
| **Caro-Kann Defense** | `1. e4 c6 2. Nc3 d5` — **legitimate, not the main line** |
| **Queen's Pawn Game** | `1. d4 d5 2. e3 Nf6` — same |

**The residue is stated rather than papered over.** Those two branch at equal depth, and the tie is
broken **alphabetically** — which puts `2. Nc3` ahead of `2. d4`. The players' own games cannot break
it either, since every branch here carries the same bare family name. Fixing it needs chess judgement
about which branch is the main one, which is the author's call and not this code's.

## Consequence

- **Adopt `qwen2.5:3b`** behind the `Summariser` protocol, optional everywhere. With no summariser
  the system behaves exactly as it did before.
- **Keep the quote arm as a real implementation**, not a special case, so the model always has
  something to beat — the shape `classifiers.py` uses.
- **`MAX_NOVELTY = 0.45`** sits above qwen2.5's mean of 18 % and below qwen3's 38 %, so it separates
  the arms on measured output rather than on a guess.
- **Guides may be scoped to a subline** (`for_opening`, `_covers`), and `build_resource` asks with
  the most-played line. Indian Defense re-keyed; **the Sicilian Alapin mis-scope is recorded and left
  for the author**, since which page covers which subline is curation.
- **`MAX_MAINLINE_STEP = 2`** stops the main line jumping onto a sideline that shares the family
  name. Two families still resolve an equal-depth branch alphabetically, and it is stated.

## Honest limitations

- **Eight families, one machine, one run.** Timings include a cold model load on the first call.
- **The checker cannot read.** It compares tokens. A subject swap passes and one occurred.
- **`accepted` is not `good`.** Nothing here measures whether the rewrite is clearer than the quotes
  — that is the author's read, and it is the only instrument that can answer it.
- **No output reaches a player.** Every source page is still `reviewed=false`.
