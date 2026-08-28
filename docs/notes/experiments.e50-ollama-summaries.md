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

## Consequence

- **Adopt `qwen2.5:3b`** behind the `Summariser` protocol, optional everywhere. With no summariser
  the system behaves exactly as it did before.
- **Keep the quote arm as a real implementation**, not a special case, so the model always has
  something to beat — the shape `classifiers.py` uses.
- **`MAX_NOVELTY = 0.45`** sits above qwen2.5's mean of 18 % and below qwen3's 38 %, so it separates
  the arms on measured output rather than on a guess.
- **A stray finding for E49's candidate list:** the Indian Defense entry is served by a *London
  System* guide, so its summary describes the wrong opening. The extractor and the model both did
  their jobs; the candidate mapping is wrong.

## Honest limitations

- **Eight families, one machine, one run.** Timings include a cold model load on the first call.
- **The checker cannot read.** It compares tokens. A subject swap passes and one occurred.
- **`accepted` is not `good`.** Nothing here measures whether the rewrite is clearer than the quotes
  — that is the author's read, and it is the only instrument that can answer it.
- **No output reaches a player.** Every source page is still `reviewed=false`.
