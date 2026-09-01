---
id: cas-design-graph-kb
title: 'Design — a graph knowledge base in Neo4j, for a small model to answer from'
desc: 'The author wants the Ollama agent to discuss chess with a player, not only hand them a report. That makes this retrieval infrastructure, and it is the thesis contribution: a small local model answering correctly because of what it retrieves. Corroboration across free books replaces per-entry endorsement as the evidence rule.'
updated: 1788256800000
created: 1788249600000
---

# A graph knowledge base

**Source:** the author, 2026-09-01 · **Status:** **plan, not built** ·
**Revised** after the author gave the purpose, which changed the design

## What it is for

> *"In the end I want the ollama agent to be able to have normal conversation with the player if the
> player asks it some questions about chess, so that it is not only able to give to the player the
> generated review but also to discuss it with the player… it is a good showcase for a thesis of how
> to use llm with knowledgebase to get more informed and correct answers with a smaller llm."*

This is the design's centre and it was missing from the first draft. The graph is not a filing
cabinet — it is **retrieval infrastructure for a small model**, so that `qwen3:8b` on a laptop can
answer a chess question correctly because of what it retrieves rather than what it remembers.

That reframes three things:

- **Coverage matters more than polish.** A node that lets the model answer *"what is a backward
  pawn"* with a citation is worth more than a beautifully written entry about one motif.
- **Retrieval quality is the metric**, not node count. The evaluation is: does the model answer
  better *with* the base than without, on questions a 1400–1800 player would actually ask?
- **It is the thesis result.** "Small model + curated retrieval beats small model alone" is a
  claim this project can measure, with an ablation it already knows how to run (E07 made the
  prober's classifier beat an embedding baseline before it was allowed to cost anything).

## A correction to my own objection

The first draft argued the binding constraint was sourcing, and projected
[[experiments.e63-knowledge-swarm]]'s **3 endorsable entries of 14** onto this.

**That projection does not hold, and the author was right to push back.** E63 measured a *different
method*: web search, through a search stack that was broken at the time, drafting definitions of
**modern tactical vocabulary** — and [[experiments.e64-chess-books]] then measured why that corpus
could not deliver, since "skewer" and "outpost" appear **zero times** across all three books on the
shelf. A books-first pipeline with corroboration is a different method and my number says nothing
about its yield.

What survives from that objection is narrower and still true: **sourcing is the work**, storage is
not, and the schema still has to make an unsourced node unservable.

## The evidence rule: corroboration, not endorsement

The author's proposal, and it is a better answer than mine:

> *"Downloading as much free chess books as possible and then using ollama to traverse them and
> extract what is written in the knowledgebase. And to get something like confirmed results count how
> many sources have mentioned some concept and described it in a similar way and then take what has
> been mentioned several times as a confirmed knowledge."*

This replaces per-entry human endorsement with a **rule the author endorses once**, which is the only
way the throughput problem is actually solved. It also turns "is this true?" — unanswerable — into
"how many independent sources say it, and do they agree?" — measurable. That is the shape this
project is good at.

**Three threats, and they decide the design.**

**1. Independence cannot be assumed.** Pre-1929 chess books copy each other freely. Three texts
agreeing may be one text repeated three times, and a corroboration count that does not check this
measures ancestry rather than agreement. **Mitigation:** treat corroboration as a count over
*publication lineages*, not files; record each book's author and date; and flag near-identical
phrasing between sources as a **shared-ancestor warning** rather than as confirmation — verbatim
agreement is the signature of copying, and it is paraphrase agreement that carries evidence.

**2. Corroboration measures consensus, not correctness.** *"Knights on the rim are dim"* is in every
old book and is a heuristic, not a truth. This is R-03's exact failure mode arriving through the
front door.
**Mitigation is framing, and it is not cosmetic.** The base never asserts *"this is true"*. It
asserts *"Capablanca, Lasker and Staunton all describe it this way"*, with the passages. That is a
claim about the literature, it is verifiable, and it is what V8 and C5 already require of everything
else here. Said that way, consensus is legitimate evidence; said as truth, it is folklore.

**3. The free shelf is old, and old books lack the modern vocabulary the detectors use.** Measured,
not feared: E64 found **zero** occurrences of "skewer" and "outpost". So corroboration will be strong
on openings, development, king safety and endgames, and **structurally silent** on part of the
motif vocabulary. Expect that, report it, and do not let the pipeline fill the gap by inventing.

## Extraction: select, never compose

The step where Ollama reads a book and produces a claim is where hallucination enters. The project
already solved this once and the solution transfers: in the knowledge swarm the model **chooses a
sentence by index** and may answer `-1`, so the stored text is a page's own words by construction and
never model prose. E63 records what happened without the refusal option — the model returns the
least-bad sentence rather than none.

So extraction produces: a **verbatim passage span**, a `book://slug#passage` locator, and a
**model-assigned concept label**. The label may be wrong and is checkable; the text cannot be
invented.

## Vector search belongs in the same database

The author is right that matching *"defined in a similar manner multiple times but… not worded the
same"* needs vectors — and it is exactly the problem E65 hit, where "outpost" and "hole" are one idea
under two words.

**It does not need a second store.** Neo4j carries native vector indexes with cosine similarity in
recent 5.x releases, in Community Edition, so a passage node holds both its embedding and its edges.
One database, one backup, one query language, and a retrieval that can do *"passages semantically
near this question, then walk to the concept, then to its prerequisites"* in a single Cypher
statement — which is the whole argument for a graph over a flat vector store.

**Verified 2026-09-01**: `neo4j:5-community` reports 5.26.30, and a `CREATE VECTOR INDEX`
with 1024 dimensions and cosine similarity succeeds. The single-store design holds and does
not need a second database.

**Both halves already exist in this repository**: `chesscoach/classifiers.py` embeds through Ollama
with `mxbai-embed-large`, and `chesscoach/books.py` already chunks a book into ~2,400-character
passages with `book://` locators and strips the Gutenberg licence wrapper. The vector layer is
wiring, not new capability.

## The rules layer, which needs no sourcing at all

> *"For legal moves I meant that there should be recorded patterns on how the pieces can move so that
> ollama's llm knows the basics just in case. Also general rules of chess are needed and different
> kinds of games like rapid, bullet, classical."*

All three resolve to things the project can **generate or already holds**, which puts them outside
the sourcing problem entirely:

- **Movement patterns** — generated from `python-chess`: how each piece moves, what it attacks from a
  given square, the special moves (castling, en passant, promotion). Computed and verifiable, so it
  takes the same exemption as `Claim` and `Detector` nodes: writing down what the code does is the
  opposite of folklore.
- **General rules** — check, checkmate, stalemate, the draw conditions, touch-move. Stated from the
  **FIDE Laws of Chess**, which are published free; short quotations with attribution rather than
  redistribution. *(Licence terms to be checked before ingesting more than short quotes.)*
- **Time controls** — already in code. `chesscoach/speed.py` classifies bullet, blitz, rapid and
  classical on Lichess's own rule, and that rule is the citation.

This is the layer most worth having for a small model, because it is exactly what such a model gets
confidently wrong, and it is free of every risk above.

## The model

**Nodes**

| node | what it is | provenance |
|---|---|---|
| `Rule` | how a piece moves; check, stalemate, draws | generated / FIDE |
| `TimeControl` | bullet, blitz, rapid, classical | `chesscoach/speed.py` |
| `Concept` | fork, pin, outpost, backward pawn, development | extracted, corroborated |
| `Passage` | ~a page of a book, with its embedding | `chesscoach/books.py` |
| `Source` | a book, its author, its date, its lineage | the shelf |
| `Claim` | one of the 57 things the detectors can say | the code |
| `Detector` | the function that decides a claim | the code |
| `Opening` | a named line | `book.json`, 3,810 CC0 rows |
| `Band` | 1400–1800 and its neighbours | ADR-0005 |
| `Practice` | a drill or puzzle theme | Lichess puzzles, CC0 |
| `LearningPrinciple` | spacing, retrieval practice | `domain.expertise-research` |

**Edges**

```
(:Passage)-[:FROM]->(:Source)                 every quote knows its book
(:Passage)-[:DESCRIBES]->(:Concept)           extracted, one edge per attestation
(:Concept)-[:PREREQUISITE_OF]->(:Concept)     the arbiter's missing structure
(:Concept)-[:EXPECTED_AT]->(:Band)            sourced only, or absent
(:Claim)-[:DETECTS]->(:Concept)               measurement to idea
(:Detector)-[:DECIDES]->(:Claim)
(:Opening)-[:CONTINUES|TRANSPOSES_TO]->(:Opening)
(:Practice)-[:TRAINS]->(:Concept)
(:LearningPrinciple)-[:GOVERNS]->(:Practice)
(:Rule)-[:GOVERNS]->(:Concept)                "a pin works because the king may not be left in check"
```

**The corroboration count is `DESCRIBES` edges from distinct lineages**, which is why `Source` carries
a lineage and why the count is not simply `COUNT(*)`.

## The gate

A `Concept` is **servable** when it has `DESCRIBES` edges from at least *N* independent lineages whose
passages agree by embedding similarity. Below that it is **stored and retrievable to the author,
never served to a player** — and the count of unservable concepts is a reported number, because it is
the honest measure of what the free shelf supports.

***N* is calibrated, not chosen.** L-054: a distribution says what a threshold discards, only running
the rule says what it buys. Sweep *N* and the similarity floor, and read off where corroborated
concepts stop being obviously right and start being coincidence.

`Rule`, `TimeControl`, `Claim`, `Detector` and `Opening` are exempt: generated or CC0 reference data,
not claims about chess.

## Stages, each usable alone (C6)

**Stage 1 — the rules layer and what the project already owns.** Movement patterns, rules, time
controls, claims, detectors, openings, bands. **No extraction, no corroboration, nothing invented.**
A small model can already answer *"how does a knight move"*, *"what is stalemate"*, *"what counts as
rapid"* with citations.
*Done when:* the graph builds from files and code, and answers those questions.

**Stage 2 — the shelf, passages and vectors.** Expand `books.py` beyond three books to as much free
public-domain chess as Gutenberg and the Internet Archive hold; chunk, embed, store as `Passage`
nodes. **Still no claims extracted** — this is retrieval over verbatim text, which alone makes the
model markedly better and is already honest, because every answer quotes a book.
*Done when:* an ablation shows the model answering better with retrieval than without.

**Stage 3 — extraction and corroboration.** Ollama labels passages with concepts by selection;
lineage-aware counting; embedding agreement; calibrated *N*. **Sourced only — the author's ruling.**
*Done when:* the corroborated set is measured, the unservable count reported, and the
shared-ancestor warnings inspected.

**Stage 4 — the structured layers.** Prerequisites, band expectations, practice. These need the most
judgement and benefit most from stages 1–3 existing first.

## What this buys the thesis

An ablation the project already knows how to run: the same questions asked of the model **alone**,
with **vector retrieval only**, and with **graph-plus-vector retrieval**, scored on whether the answer
is correct and whether it cites something real. That is a measurable result about small models and
curated knowledge, which is the showcase the author described — and it is falsifiable, which is what
makes it worth writing up either way.

## Honest limitations

- **Corroboration is consensus, and the framing carries the entire honesty burden.** If a rendered
  answer ever says "this is true" rather than naming its sources, this design has failed.
- **Independence is the weakest link** and cannot be fully established for old texts. Lineage is a
  proxy for it, not a solution.
- **Part of the motif vocabulary will not be corroborable** from a free, old shelf. Measured
  already; expect silence there rather than filling it.
- **Extraction quality is unmeasured.** A model labelling passages with concepts is a classifier and
  it needs the same treatment E07 gave the prober's: a baseline it has to beat before it is trusted.
- **Nothing here is built.** Every claim about what retrieval buys is an argument until stage 2's
  ablation exists.
