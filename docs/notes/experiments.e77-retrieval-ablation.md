---
id: cas-exp-e77
title: 'E77 — A 3.8B model answers correctly with retrieval and plausibly without'
desc: 'Stage 2 of the graph knowledge base, and its done-condition. 607 book passages embedded and searchable; 8 of 8 grounded answers cite a real locator and none invents one. The clearest case is a question where the model alone is confidently, generically wrong.'
updated: 1788264000000
created: 1788264000000
---

# E77 — Does retrieval make a small model better?

**Answers:** [[design.graph-knowledge-base]] stage 2's done-condition ·
**Code:** `experiments/e77-retrieval-ablation/`, `chesscoach/embedding.py`, `chesscoach/graph.py` ·
**Date:** 2026-09-01 · **Status:** done — **retrieval helps, and one case shows exactly how**

## What was built

- `chesscoach/embedding.py` — batched embeddings through Ollama's `mxbai-embed-large`, 1024
  dimensions, **raising rather than returning nothing** when the backend is unreachable.
- `BookLibrary.all_passages()` — the **one** place a passage boundary is decided. `passages()` used
  to chunk inline and the loader needed the same chunking; two loops stepping by `PASSAGE_CHARS` are
  two definitions of *"passage 7"*, and a citation meaning different text in the store than in a
  search result is worse than no citation.
- `GraphStore.load_passages` / `search` — **607 passages** from three books, embedded and stored with
  a vector index, in 96 seconds. Each carries a `book://slug#index` locator and an edge to a `Source`
  node holding author, year and **lineage**.

**No claims are extracted, and that is the stage.** A passage is the book's own words. Nothing has
been interpreted, so anything retrieved can be quoted and attributed.

## The result

Eight questions a 1400–1800 player would ask, `phi4-mini:3.8b`, temperature 0.3, seed 7.

| | |
|---|--:|
| grounded answers | **8** |
| offered a citation | **8** |
| citation was real | **8** |
| **citation was invented** | **0** |

Correctness about chess needs a chess player and is left to one — the answers are written side by
side for the author. What is scored automatically is what V8 demands everywhere else in this project:
**does the answer cite something, and is what it cites real.**

## The case that shows the point

*"What counts as a rapid game rather than blitz?"*

> **Alone:** *"A rapid game typically lasts between 15 to 30 minutes per player, whereas a blitz game
> is shorter, usually around 5 to 10 minutes per player…"*

Fluent, confident, and **wrong for the platform this system runs on**. Lichess classifies by
*estimated duration* — the starting clock plus forty increments — which is why 3+2 is blitz and 5+5
is rapid.

> **With retrieval:** *"A rapid game is one with an estimated duration under 1500 seconds, which
> includes the starting clock plus forty increments. A blitz game… under 480 seconds.
> SOURCE: `rule://rapid`"*

Correct, specific, and citing a node generated from the code that actually makes the classification.
This is the thesis claim in one question: **the failure mode of a small model is not incoherence, it
is confident generic plausibility**, and that is exactly what retrieval fixes.

## Three defects in my own harness, all of which understated the result

Worth recording because all three were measurement errors, not system failures, and each made the
system look worse than it is.

1. **The citation check required `SOURCE:` at the start of a line.** The model writes it at the end of
   its last sentence, so a real citation scored as *"none offered"* — reported as **1 of 7** when it
   was 8 of 8.
2. **The rules gate matched piece names only.** *"When can I capture en passant?"* got **no reference
   material at all**, because en passant lives in the pawn rule's `special` and the question does not
   say "pawn". That measured my keyword gate, not retrieval.
3. **The locator was truncated at the first space**, so `rule://how the pawn moves` became
   `rule://how` — which then matched by prefix and scored REAL for a string identifying nothing. The
   verdict happened to be right and the check was not.

## Honest limitations

- **Three books, 607 passages.** Expanding the shelf was attempted first and **Gutendex is
  unreachable** — 403 without a user agent, then repeated timeouts with one. R-17's shape again:
  check a dependency is alive, not merely documented. The shelf expansion is data volume, not
  mechanism, so stage 2 proceeded without it.
- **Retrieval quality on concepts is mixed and the numbers hide it.** *"Why should I castle early"*
  returned a passage about **giving odds**. The rules layer answers cleanly because it is generated;
  the book layer is at the mercy of 2,400-character chunks that ignore paragraph boundaries and start
  mid-word.
- **Old notation hurts.** The books are in descriptive notation (`P-K4`, `Kt-KB3`), which the
  embedder has little reason to relate to a modern question.
- **A real citation is not a correct answer.** This measures provenance, which is the half a script
  can judge. Whether the chess is right is unmeasured and belongs to the author.
- **One model, one seed, eight questions.** Enough to show the effect exists, not to size it.
